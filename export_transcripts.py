"""
Export transcript JSON files to markdown (both sides) for submission.
Output: transcripts/export/call_*.md
"""
import json
from pathlib import Path

from config import TRANSCRIPTS_DIR

EXPORT_DIR = Path(TRANSCRIPTS_DIR) / "export"


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(TRANSCRIPTS_DIR)
    if not src.exists():
        print("No transcripts dir:", TRANSCRIPTS_DIR)
        return
    count = 0
    for f in sorted(src.glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as e:
            print("Skip", f, e)
            continue
        conv = data.get("transcript") or data.get("conversation") or []
        lines = [
            f"# Call: {data.get('call_sid', '?')} — {data.get('scenario_id', '?')}",
            "",
            "| Speaker | Text |",
            "|--------|------|",
        ]
        for turn in conv:
            role = turn.get("role", "")
            text = (turn.get("text") or "").replace("|", "\\|").replace("\n", " ")
            label = "Agent" if role == "agent" else "Patient (Minh Huynh)"
            lines.append(f"| {label} | {text} |")
        out_name = f.name.replace(".json", ".md")
        out_path = EXPORT_DIR / out_name
        out_path.write_text("\n".join(lines), encoding="utf-8")
        count += 1
        print("Wrote", out_path)
    print(f"Exported {count} transcript(s) to {EXPORT_DIR}")


if __name__ == "__main__":
    main()
