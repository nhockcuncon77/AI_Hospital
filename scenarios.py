"""
Patient scenarios for testing the AI agent.
Each scenario defines a goal and optional constraints for the patient bot.
"""
from dataclasses import dataclass, field
from typing import Optional

from config import PATIENT_NAME, PATIENT_DOB


@dataclass
class Scenario:
    id: str
    name: str
    goal: str
    instructions: str = ""
    first_utterance: Optional[str] = None  # What to say when call connects (optional)


def _base_identity() -> str:
    return f"You are {PATIENT_NAME}, DOB {PATIENT_DOB}. Speak as a real patient on a phone call: brief, natural, sometimes incomplete sentences."


SCENARIOS: list[Scenario] = [
    Scenario(
        id="schedule_new",
        name="Schedule new appointment",
        goal="Schedule a new appointment with the doctor.",
        instructions="Ask to book an appointment. Prefer morning if they offer. Keep it short.",
        first_utterance="Hi, I’d like to schedule an appointment please.",
    ),
    Scenario(
        id="reschedule",
        name="Reschedule appointment",
        goal="Reschedule an existing appointment to a different day or time.",
        instructions="Say you need to reschedule. Give a reason like work conflict. Ask what times are available.",
        first_utterance="I need to reschedule my appointment. Something came up at work.",
    ),
    Scenario(
        id="cancel",
        name="Cancel appointment",
        goal="Cancel an existing appointment.",
        instructions="Politely cancel. You can say you’ll call back to rebook later.",
        first_utterance="Hi, I need to cancel my upcoming appointment.",
    ),
    Scenario(
        id="refill",
        name="Medication refill",
        goal="Request a refill for a current medication.",
        instructions="Ask for a refill. If they ask, say it’s for something like blood pressure or allergy medicine. Keep answers short.",
        first_utterance="I need a refill on my prescription please.",
    ),
    Scenario(
        id="office_hours",
        name="Office hours",
        goal="Find out when the office is open.",
        instructions="Ask what the office hours are, maybe for weekdays and weekends.",
        first_utterance="What are your office hours?",
    ),
    Scenario(
        id="location",
        name="Location / address",
        goal="Get the office address or directions.",
        instructions="Ask where the office is or how to get there.",
        first_utterance="Where is the office located? I’m not sure I have the right address.",
    ),
    Scenario(
        id="insurance",
        name="Insurance",
        goal="Ask whether the practice takes your insurance.",
        instructions="Ask if they accept a specific insurance (e.g. Blue Cross) or what insurance they take.",
        first_utterance="Do you take Blue Cross Blue Shield?",
    ),
    Scenario(
        id="multiple_requests",
        name="Multiple requests in one call",
        goal="Both get office hours and schedule an appointment.",
        instructions="First ask office hours, then say you’d like to book an appointment.",
        first_utterance="What are your hours? And I’d like to book an appointment too.",
    ),
    Scenario(
        id="vague_request",
        name="Vague request",
        goal="Start with something unclear and let the agent clarify.",
        instructions="Say something vague like 'I need help with something' or 'I was calling about…' and answer when they ask for details.",
        first_utterance="Hi, I was calling about something I needed to do.",
    ),
    Scenario(
        id="wrong_number",
        name="Wrong number / confusion",
        goal="Act briefly confused (e.g. thought it was another office) then continue.",
        instructions="Say 'Oh wait, is this Dr. Smith’s office?' then when they respond, say you need an appointment anyway.",
        first_utterance="Is this the dentist office? Oh okay, I actually need to make an appointment.",
    ),
]


def get_scenario(scenario_id: str) -> Optional[Scenario]:
    for s in SCENARIOS:
        if s.id == scenario_id:
            return s
    return None
