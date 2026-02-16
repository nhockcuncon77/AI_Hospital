"""
Flask server: TwiML webhook for outbound calls and WebSocket for bidirectional media.
Run with: python server.py
Use ngrok to expose TWILIO_WEBHOOK_BASE_URL (e.g. https://xxx.ngrok.io).
"""
import base64
import json
import logging
import os
import time

from flask import Flask, request
from flask_sockets import Sockets

from audio_utils import mulaw_chunks_to_base64
from config import TWILIO_WEBHOOK_BASE_URL, TRANSCRIPTS_DIR
from patient_bot import patient_response
from scenarios import get_scenario
from stt_tts import transcribe_mulaw, text_to_mulaw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
sockets = Sockets(app)


@app.before_request
def log_request():
    """Log every request so we can see if Twilio/ngrok hits our app."""
    logger.info("Request: %s %s", request.method, request.path)


@app.errorhandler(404)
def not_found(e):
    """So we can tell our app is responding (not ngrok 404)."""
    logger.warning("404 for path: %s", request.path)
    return "Not found (voice bot app). Path: " + request.path, 404


# Minimum buffer size before running STT (~1.5 sec at 8kHz mulaw = 12000 bytes)
MIN_BUFFER_BYTES = 12000
# Process every N inbound media messages (each ~320 bytes = 20ms) -> ~2 sec
MEDIA_BATCH_SIZE = 100


def process_and_reply(
    scenario_id: str,
    stream_sid: str,
    conversation: list[dict],
    inbound_buffer: bytearray,
    ws_send_fn,
) -> None:
    """Run STT on buffer, get patient reply, TTS, send to Twilio. Caller clears inbound_buffer."""
    if len(inbound_buffer) < 800:
        return
    mulaw = bytes(inbound_buffer)
    text = transcribe_mulaw(mulaw)
    if not text or not text.strip():
        return

    # Append agent turn
    conversation.append({"role": "agent", "text": text})
    reply = patient_response(scenario_id, conversation, text)
    conversation.append({"role": "patient", "text": reply})

    if not reply.strip():
        return

    mulaw_audio = text_to_mulaw(reply)
    if not mulaw_audio:
        return

    chunks_b64 = mulaw_chunks_to_base64(mulaw_audio)
    mark_name = f"mark-{time.time()}"

    for payload in chunks_b64:
        msg = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {"payload": payload},
        }
        try:
            ws_send_fn(json.dumps(msg))
        except Exception as e:
            logger.warning("Send media failed: %s", e)
            return

    try:
        ws_send_fn(
            json.dumps(
                {
                    "event": "mark",
                    "streamSid": stream_sid,
                    "mark": {"name": mark_name},
                }
            )
        )
    except Exception as e:
        logger.warning("Send mark failed: %s", e)


@sockets.route("/media")
def media_stream(ws):
    """WebSocket: receive Twilio media, run STT -> LLM -> TTS, send audio back."""
    media_stream_body(ws)


# Flask-Sockets adds routes with websocket=False; Werkzeug then raises WebsocketMismatch
# when Twilio sends a WebSocket request. Mark the /media rule as websocket so it matches.
def _fix_media_websocket_rule():
    for rule in sockets.url_map.iter_rules():
        if rule.rule == "/media":
            rule.websocket = True
            logger.info("Set /media rule.websocket=True for Twilio stream")
            break


_fix_media_websocket_rule()


def _save_transcript(conversation: list, path: str, scenario_id: str, call_sid: str = None):
    """Write transcript to a JSON file (used for live saves and final save)."""
    try:
        payload = {"scenario_id": scenario_id, "transcript": conversation}
        if call_sid:
            payload["call_sid"] = call_sid
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("Saved transcript to %s", path)
    except Exception as e:
        logger.warning("Could not save transcript: %s", e)


def media_stream_body(ws):
    """WebSocket handler body (stream_sid, conversation, etc.)."""
    stream_sid = None
    scenario_id = "schedule_new"  # updated from start message customParameters
    conversation = []
    inbound_buffer = bytearray()
    media_count = 0
    first_utterance_sent = False
    live_transcript_path = None  # save as we go so closing terminal doesn't lose transcript

    def send(msg: str):
        try:
            ws.send(msg)
        except Exception as e:
            logger.warning("ws.send failed: %s", e)

    def save_live():
        if live_transcript_path and conversation:
            _save_transcript(conversation, live_transcript_path, scenario_id)

    logger.info("WebSocket connected, scenario_id=%s", scenario_id)

    while not ws.closed:
        message = ws.receive()
        if message is None:
            continue

        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            continue

        event = data.get("event")

        if event == "connected":
            logger.info("Stream connected")

        elif event == "start":
            stream_sid = data.get("streamSid") or (data.get("start") or {}).get("streamSid")
            custom = (data.get("start") or {}).get("customParameters") or {}
            scenario_id = custom.get("scenario_id") or scenario_id
            logger.info("Stream start streamSid=%s scenario_id=%s", stream_sid, scenario_id)
            if stream_sid:
                live_transcript_path = os.path.join(
                    TRANSCRIPTS_DIR,
                    f"call_live_{stream_sid}_{scenario_id}.json",
                )

            # Optional: speak first (e.g. "Hi, I'd like to schedule an appointment")
            scenario = get_scenario(scenario_id)
            if scenario and scenario.first_utterance and stream_sid and not first_utterance_sent:
                first_utterance_sent = True
                conversation.append({"role": "patient", "text": scenario.first_utterance})
                save_live()
                mulaw_audio = text_to_mulaw(scenario.first_utterance)
                if mulaw_audio:
                    for payload in mulaw_chunks_to_base64(mulaw_audio):
                        send(
                            json.dumps(
                                {
                                    "event": "media",
                                    "streamSid": stream_sid,
                                    "media": {"payload": payload},
                                }
                            )
                        )
                    send(
                        json.dumps(
                            {
                                "event": "mark",
                                "streamSid": stream_sid,
                                "mark": {"name": "first"},
                            }
                        )
                    )

        elif event == "media":
            track = (data.get("media") or {}).get("track", "inbound")
            if track != "inbound":
                continue
            payload = (data.get("media") or {}).get("payload")
            if payload:
                try:
                    inbound_buffer.extend(base64.b64decode(payload))
                except Exception:
                    pass
                media_count += 1

                if media_count >= MEDIA_BATCH_SIZE and stream_sid:
                    media_count = 0
                    if len(inbound_buffer) >= MIN_BUFFER_BYTES:
                        buf_snapshot = bytearray(inbound_buffer)
                        inbound_buffer.clear()
                        process_and_reply(
                            scenario_id,
                            stream_sid,
                            conversation,
                            buf_snapshot,
                            send,
                        )
                        save_live()

        elif event == "stop":
            # Flush remaining buffer
            if stream_sid and len(inbound_buffer) >= 800:
                process_and_reply(
                    scenario_id,
                    stream_sid,
                    conversation,
                    inbound_buffer,
                    send,
                )
            inbound_buffer.clear()
            save_live()

            # Save final transcript (full conversation = both sides)
            call_sid = (data.get("stop") or {}).get("callSid") or "unknown"
            out_path = os.path.join(
                TRANSCRIPTS_DIR,
                f"call_{call_sid}_{scenario_id}_{int(time.time())}.json",
            )
            _save_transcript(conversation, out_path, scenario_id, call_sid=call_sid)
            if live_transcript_path and os.path.isfile(live_transcript_path):
                try:
                    os.remove(live_transcript_path)
                except Exception as e:
                    logger.warning("Could not remove live transcript file: %s", e)
            break

    logger.info("WebSocket closed")


@app.route("/twiml", methods=["GET", "POST"], strict_slashes=False)
def twiml():
    """Return TwiML that connects the call to our WebSocket stream (for outbound)."""
    logger.info("Serving TwiML for scenario_id=%s", request.args.get("scenario_id"))
    scenario_id = request.args.get("scenario_id", "schedule_new")
    base = TWILIO_WEBHOOK_BASE_URL or request.host_url.rstrip("/")
    if not base.startswith("http"):
        base = f"https://{base}"
    wss_url = base.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{wss_url}/media"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{stream_url}">
      <Parameter name="scenario_id" value="{scenario_id}" />
    </Stream>
  </Connect>
</Response>"""
    return twiml, 200, {"Content-Type": "application/xml"}


@app.route("/")
def index():
    """So we can verify the server and ngrok tunnel are up (e.g. open ngrok URL in browser)."""
    return "Voice bot server is running. TwiML at /twiml", 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    # Default 5050: port 5000 is often blocked or in use on Windows
    port = int(os.environ.get("PORT", 5050))
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    # Default: plain WSGI so /, /health, /twiml work. gevent-websocket's WebSocketHandler
    # returns 404 for normal HTTP on many setups, so we only use it when explicitly requested.
    use_websocket = os.environ.get("VOICE_BOT_WEBSOCKET", "").strip().lower() in ("1", "true", "yes")
    if use_websocket:
        server = pywsgi.WSGIServer(("", port), app, handler_class=WebSocketHandler)
        logger.info("Server listening on port %s (WebSocket enabled for /media)", port)
    else:
        server = pywsgi.WSGIServer(("", port), app)
        logger.info("Server listening on port %s (/, /health, /twiml OK; for voice set VOICE_BOT_WEBSOCKET=1)", port)
    server.serve_forever()
