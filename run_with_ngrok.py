"""
Start the Flask server with an ngrok tunnel so Twilio can reach it.
Requires: pip install ngrok, and NGROK_AUTHTOKEN in .env (get free at https://ngrok.com).
Run: python run_with_ngrok.py
Then set TWILIO_WEBHOOK_BASE_URL in .env to the printed URL (no trailing slash).
"""
import os
import sys
import threading
import time

# Load .env before importing server (which uses config)
from dotenv import load_dotenv

load_dotenv()

try:
    import ngrok
except ImportError:
    print("Install ngrok first: pip install ngrok")
    sys.exit(1)

if not os.environ.get("NGROK_AUTHTOKEN"):
    print("Set NGROK_AUTHTOKEN in .env (get a free token at https://dashboard.ngrok.com/get-started/your-authtoken)")
    sys.exit(1)

# Start ngrok FIRST so we can set TWILIO_WEBHOOK_BASE_URL before the server reads config
try:
    port = int(os.environ.get("PORT", 5050))
    listener = ngrok.forward(port, authtoken_from_env=True)
    base = listener.url()
    if base.endswith("/"):
        base = base.rstrip("/")
    os.environ["TWILIO_WEBHOOK_BASE_URL"] = base
    print("")
    print("=" * 60)
    print("ngrok tunnel is up. TwiML URL (already set for this run):")
    print(f"  {base}/twiml")
    print("")
    print("Add to .env for make_call.py (if not already):")
    print(f"  TWILIO_WEBHOOK_BASE_URL={base}")
    print("=" * 60)
    print("")
except Exception as e:
    print("ngrok error:", e)
    sys.exit(1)

# Start server AFTER ngrok so server sees current TWILIO_WEBHOOK_BASE_URL
def run_server():
    import server

    port = int(os.environ.get("PORT", 5050))
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server_instance = pywsgi.WSGIServer(
        ("", port), server.app, handler_class=WebSocketHandler
    )
    print(f"Server listening on port {port}")
    server_instance.serve_forever()


thread = threading.Thread(target=run_server, daemon=True)
thread.start()
time.sleep(1.5)

thread.join()
