# Call transcripts

Transcripts are saved here automatically as JSON when each call ends (from the WebSocket `stop` event). Each file contains:

- `call_sid` — Twilio call ID
- `scenario_id` — Scenario used (e.g. schedule_new, refill)
- `transcript` — List of `{"role": "agent"|"patient", "text": "..."}`

For submission, run:

```bash
python export_transcripts.py
```

to generate markdown files under `transcripts/export/` with both sides of each conversation.

You need at least 10 calls for the challenge. Use:

```bash
python run_calls.py --delay 120
```

to run all scenarios (10) with 2 minutes between calls.
