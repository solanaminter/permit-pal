#!/usr/bin/env python3
"""Permit Pal — one-command end-to-end demo.

Runs the full multi-agent permit workflow for a deck addition in Austin, TX:
research -> human approval -> packet assembly -> human approval ->
inspection scheduling -> human approval -> submission-ready summary.

Human-approval steps are AUTO-APPROVED with a loud banner in demo mode
(PERMIT_PAL_DEMO=1, set below). Run without demo mode for the interactive
version that prompts on stdin:

    PERMIT_PAL_DEMO= .venv/bin/python demo.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PERMIT_PAL_DEMO"] = "1"

from permit_pal import config  # noqa: E402

config.DEMO_MODE = True

from permit_pal.agents import build_orchestrator  # noqa: E402

DEMO_PROMPT = (
    "I'm Solana Minter, a homeowner in Austin, TX. I want to build a 320 sq ft "
    "deck (deck addition) in my backyard. Please shepherd my permit application "
    "end to end: first research the permit requirements, then get my approval, "
    "then assemble the application packet and checklist, get my approval again, "
    "then schedule the required inspections and set deadline reminders, and "
    "finally get my approval to submit the application."
)


def main() -> int:
    print("=" * 70)
    print("PERMIT PAL — end-to-end demo (Agents for Humans Hackathon)")
    print("Multi-agent permit shepherd · Strands Agents SDK · demo model (no AWS)")
    print("=" * 70)
    print(f"\nHomeowner request: {DEMO_PROMPT}\n")
    print("-" * 70)

    agent = build_orchestrator()
    result = agent(DEMO_PROMPT)

    print("-" * 70)
    print("\nDEMO COMPLETE.")
    print("Tool-call trace (in order):")
    for i, (name, args) in enumerate(config.CALL_LOG, 1):
        arg_str = ", ".join(f"{k}={str(v)[:40]}" for k, v in args.items())
        print(f"  {i:2d}. {name}({arg_str})")
    print(f"\nApprovals granted: {sum(1 for n, _ in config.CALL_LOG if n == 'request_human_approval')}/3")
    print("Packet file: output/permit-packet-austin-tx-deck-addition.md")
    print("Run the eval suite: .venv/bin/python evals/run_evals.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
