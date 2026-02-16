"""
Run a batch of test calls (one per scenario) with a delay between them.
Usage: python run_calls.py [--delay 120] [--scenarios id1,id2,...]
Default: run all scenarios with 120s delay. Server must be running and ngrok exposed.
"""
import argparse
import subprocess
import sys
import time

from scenarios import SCENARIOS


def main():
    ap = argparse.ArgumentParser(description="Run multiple test calls")
    ap.add_argument("--delay", type=int, default=120, help="Seconds between calls")
    ap.add_argument(
        "--scenarios",
        type=str,
        default="",
        help="Comma-separated scenario ids (default: all)",
    )
    args = ap.parse_args()

    if args.scenarios:
        ids = [s.strip() for s in args.scenarios.split(",") if s.strip()]
        scenarios = [s for s in SCENARIOS if s.id in ids]
        if len(scenarios) != len(ids):
            unknown = set(ids) - {s.id for s in SCENARIOS}
            if unknown:
                print("Unknown scenario ids:", unknown)
                sys.exit(1)
    else:
        scenarios = SCENARIOS

    print(f"Will run {len(scenarios)} call(s) with {args.delay}s delay between them.")
    for i, s in enumerate(scenarios):
        print(f"\n[{i+1}/{len(scenarios)}] {s.id}: {s.name}")
        subprocess.run([sys.executable, "make_call.py", s.id], check=True)
        if i < len(scenarios) - 1:
            print(f"Waiting {args.delay}s...")
            time.sleep(args.delay)
    print("\nDone. Check transcripts/ for saved conversations.")


if __name__ == "__main__":
    main()
