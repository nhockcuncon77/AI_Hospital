"""
Patient bot: LLM that generates natural patient responses given conversation history and scenario.
"""
import logging
from typing import Optional

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_API_BASE, PATIENT_NAME, PATIENT_DOB
from scenarios import Scenario, get_scenario

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _client_or_default() -> OpenAI:
    global _client
    if _client is None:
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_API_BASE:
            kwargs["base_url"] = OPENAI_API_BASE
        _client = OpenAI(**kwargs)
    return _client


SYSTEM_TEMPLATE = """You are {name}, DOB {dob}. You are on a phone call with a medical office's AI agent. Speak as a real patient: short, natural phrases. One or two sentences per turn. Do not list options or be formal. No "I would like to..." unless natural. You can say "um", "yeah", "okay". Never break the fourth wall or mention you are an AI.

Scenario goal: {goal}
Additional instructions: {instructions}

Respond with ONLY what the patient says out loud, nothing else. No quotes, no labels."""


def build_system_prompt(scenario: Scenario) -> str:
    return SYSTEM_TEMPLATE.format(
        name=PATIENT_NAME,
        dob=PATIENT_DOB,
        goal=scenario.goal,
        instructions=scenario.instructions or "Respond naturally and briefly.",
    )


def patient_response(
    scenario_id: str,
    conversation: list[dict],
    last_agent_text: str,
) -> str:
    """
    Given scenario and conversation history (list of {"role": "agent"|"patient", "text": "..."}),
    and the latest agent utterance, return the next patient utterance.
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        scenario = Scenario(
            id=scenario_id,
            name="General",
            goal="Have a natural conversation with the office.",
            instructions="Respond briefly and naturally.",
        )

    system = build_system_prompt(scenario)
    messages = [{"role": "system", "content": system}]

    for turn in conversation:
        role = "user" if turn["role"] == "agent" else "assistant"
        messages.append({"role": role, "content": turn["text"]})

    messages.append({"role": "user", "content": f"Agent said: {last_agent_text}"})

    try:
        client = _client_or_default()
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150,
            temperature=0.8,
        )
        text = (r.choices[0].message.content or "").strip()
        # Remove any accidental quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        return text
    except Exception as e:
        logger.warning("Patient LLM failed: %s", e)
        return "Sorry, I didn't catch that. Can you repeat?"
