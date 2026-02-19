# Pretty Good AI — Voice Bot

Automated voice bot that calls the test line **805-439-8008**, simulates patient scenarios (scheduling, refills, questions), records and transcribes conversations, and helps identify bugs or quality issues in the AI agent.

**Patient persona:** Minh Huynh, DOB July 14th, 2001.

---

## Setup

### 1. Python

- Python 3.10+ recommended.
- Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_PHONE_NUMBER` | Your Twilio phone number (E.164, e.g. `+15551234567`) |
| `TWILIO_WEBHOOK_BASE_URL` | Public HTTPS URL for webhooks (e.g. ngrok: `https://abc123.ngrok.io`) |
| `OPENAI_API_KEY` | OpenAI API key (for Whisper, TTS, and patient LLM) |
| `TEST_LINE_NUMBER` | Optional; defaults to `+18054398008` |

Do not commit `.env` or any real secrets.

### 3. Twilio

- Get credentials and a phone number from [Twilio Console](https://console.twilio.com).
- No need to attach the number to a TwiML Bin; the bot uses the `url` parameter when placing outbound calls.

### 4. Expose the server (ngrok)

Twilio must reach your app over HTTPS. Use [ngrok](https://ngrok.com/download):

```bash
ngrok http 5000
```

Set `TWILIO_WEBHOOK_BASE_URL` in `.env` to the ngrok URL (e.g. `https://abc123.ngrok.io`), with no trailing slash.

---

## Check server health

Verify that the Flask app responds correctly (no port needed):

```bash
python check_health.py
```

You should see `200` for root, health, and twiml.

**Default port is 5050** (not 5000) so the server avoids common port conflicts. To free the port before starting: **Windows (PowerShell):** `.\kill_port_5000.ps1` (script uses `PORT` env or 5050). Then run `python server.py` or `python run_with_ngrok.py`. For ngrok use: `ngrok http 5050`.

---

## Run

### Single command (after setup)

1. **Start the server** (in one terminal):

```bash
python server.py
```

2. **In another terminal, place a call**:

```bash
python make_call.py schedule_new
```

Replace `schedule_new` with any scenario id (see below). Transcripts are written to `transcripts/` when the call ends.

### Scenario IDs

- `schedule_new` — Schedule new appointment  
- `reschedule` — Reschedule existing appointment  
- `cancel` — Cancel appointment  
- `refill` — Medication refill  
- `office_hours` — Office hours  
- `location` — Location / address  
- `insurance` — Insurance (e.g. Blue Cross)  
- `multiple_requests` — Office hours + schedule  
- `vague_request` — Vague opening, then clarify  
- `wrong_number` — Brief wrong-number then continue  

### Batch runs

Run multiple scenarios with a delay between calls (e.g. 120 seconds):

```bash
python run_calls.py --delay 120
```

Or specific scenarios:

```bash
python run_calls.py --scenarios schedule_new,refill,office_hours --delay 60
```

### Bug report from transcripts

After you have transcripts in `transcripts/`:

```bash
python analyze_bugs.py
```

This writes `bug_report.md` with LLM-generated notes on each call (incorrect info, hallucinations, misunderstandings, awkward phrasing, etc.).

### Export transcripts for submission

To get one markdown file per call (both sides) for the “minimum 10 calls” deliverable:

```bash
python export_transcripts.py
```

Output is written under `transcripts/export/` (or as directed in the script).

---

## Project layout

- `server.py` — Flask app: `/twiml` (TwiML for outbound), WebSocket `/media` (bidirectional audio), `/health`
- `make_call.py` — Start one outbound call with a scenario
- `run_calls.py` — Run several scenarios with a delay
- `patient_bot.py` — LLM patient responses given scenario and history
- `scenarios.py` — Scenario definitions (goal, first utterance)
- `stt_tts.py` — Whisper STT, OpenAI TTS → 8 kHz mulaw for Twilio
- `audio_utils.py` — Mulaw ↔ PCM and Twilio chunking
- `config.py` — Env and paths
- `analyze_bugs.py` — Build `bug_report.md` from transcripts
- `transcripts/` — Saved call transcripts (JSON)
- `ARCHITECTURE.md` — Short design and design choices

---

## API keys and cost

- **Twilio:** voice usage for outbound calls.  
- **OpenAI:** Whisper (STT), TTS, and GPT-4o-mini (patient bot and bug analysis).

Expect roughly $10–20 for telephony + APIs for a full set of test calls. Do not commit API keys; use `.env` and document required variables in this README and `.env.example`.
