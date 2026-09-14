"""Shared configuration for Permit Pal.

No secrets live here. The demo runs entirely offline against a deterministic
heuristic model stand-in (see permit_pal/models.py). Swap in Bedrock via
permit_pal.models.build_bedrock_model() when AWS credentials are available.
"""

import os

# Demo mode: human-approval steps are auto-approved with a loud, visible
# banner instead of prompting on stdin. demo.py enables this automatically;
# set PERMIT_PAL_DEMO=1 to force it from the environment.
DEMO_MODE = os.environ.get("PERMIT_PAL_DEMO", "") == "1"

# Global tool-call trace. Every tool logs (name, args) here so the demo,
# the eval harness, and the approval-gating audit can inspect exactly which
# tools ran, in which order, with which arguments.
CALL_LOG: list[tuple[str, dict]] = []


def log_call(name: str, args: dict) -> None:
    CALL_LOG.append((name, dict(args)))


def clear_log() -> None:
    CALL_LOG.clear()


# In-memory reminder store for the scheduler agent (mock persistence).
REMINDERS: list[dict] = []
