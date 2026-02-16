"""
Initiate one outbound call to the test line with a given scenario.
Usage: python make_call.py [scenario_id]
Default scenario: schedule_new
"""
import sys
from twilio.rest import Client

from config import (
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_PHONE_NUMBER,
    TWILIO_WEBHOOK_BASE_URL,
    TEST_LINE_NUMBER,
)
from scenarios import SCENARIOS, get_scenario


def main():
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else "schedule_new"
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env")
        sys.exit(1)
    if not TWILIO_PHONE_NUMBER:
        print("Set TWILIO_PHONE_NUMBER in .env")
        sys.exit(1)
    if not TWILIO_WEBHOOK_BASE_URL:
        print("Set TWILIO_WEBHOOK_BASE_URL (e.g. https://xxx.ngrok.io) in .env")
        sys.exit(1)

    twiml_url = f"{TWILIO_WEBHOOK_BASE_URL}/twiml?scenario_id={scenario_id}"
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        from_=TWILIO_PHONE_NUMBER,
        to=TEST_LINE_NUMBER,
        url=twiml_url,
        timeout=30,
    )
    scenario = get_scenario(scenario_id)
    name = scenario.name if scenario else scenario_id
    print(f"Call started: {call.sid}")
    print(f"Scenario: {name} ({scenario_id})")
    print(f"To: {TEST_LINE_NUMBER}")
    print("Transcript will be saved to transcripts/ when the call ends.")


if __name__ == "__main__":
    main()
