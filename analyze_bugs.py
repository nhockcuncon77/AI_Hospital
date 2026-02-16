"""
Analyze saved call transcripts and produce a bug/quality report.
Reads all JSON files from transcripts/ and uses an LLM to identify issues.
Output: bug_report.md
"""
import json
import logging
import os
from pathlib import Path

from openai import OpenAI

from config import TRANSCRIPTS_DIR, OPENAI_API_KEY, OPENAI_API_BASE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_transcripts():
    """Load all transcript JSON files from transcripts/."""
    path = Path(TRANSCRIPTS_DIR)
    if not path.exists():
        return []
    out = []
    for f in path.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fp:
                out.append((f.name, json.load(fp)))
        except Exception as e:
            logger.warning("Skip %s: %s", f, e)
    return out


def transcript_to_markdown(data: dict) -> str:
    """Turn conversation list into readable markdown."""
    lines = []
    for turn in data.get("transcript") or data.get("conversation") or []:
        role = turn.get("role", "")
        text = turn.get("text", "")
        label = "Agent" if role == "agent" else "Patient"
        lines.append(f"**{label}:** {text}")
    return "\n\n".join(lines)


SYSTEM = """You are evaluating call transcripts between a patient (bot) and a medical office AI agent. For each call, identify:
1. Incorrect or misleading information from the agent
2. Hallucinations (facts or details the agent made up)
3. Failures to understand the patient (mishearing, wrong intent)
4. Awkward or unprofessional phrasing
5. Missing expected behaviors (e.g. didn't ask for DOB when scheduling, didn't confirm details)
6. Repetition, loops, or poor flow
7. Any other quality or correctness issues

Be specific: quote or paraphrase the problematic part and say why it's an issue. If a call has no notable issues, say "No significant issues found." Keep each finding concise."""


def analyze_one(name: str, data: dict, client: OpenAI) -> str:
    """Return analysis text for one transcript."""
    md = transcript_to_markdown(data)
    scenario = data.get("scenario_id", "?")
    prompt = f"Call file: {name}\nScenario: {scenario}\n\nTranscript:\n\n{md}\n\nList any bugs or quality issues (or say none):"
    try:
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as e:
        return f"(Analysis failed: {e})"


def main():
    if not OPENAI_API_KEY:
        print("Set OPENAI_API_KEY in .env")
        return
    kwargs = {"api_key": OPENAI_API_KEY}
    if OPENAI_API_BASE:
        kwargs["base_url"] = OPENAI_API_BASE
    client = OpenAI(**kwargs)
    transcripts = load_transcripts()
    if not transcripts:
        print("No transcripts found in", TRANSCRIPTS_DIR)
        return

    out_path = Path(__file__).parent / "bug_report.md"
    sections = [
        "# Bug & Quality Report",
        "",
        "Generated from call transcripts. Each section is one call.",
        "",
    ]
    for name, data in transcripts:
        sections.append(f"## {name}")
        sections.append("")
        sections.append(analyze_one(name, data, client))
        sections.append("")
        sections.append("---")
        sections.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sections))
    print("Wrote", out_path)


if __name__ == "__main__":
    main()
