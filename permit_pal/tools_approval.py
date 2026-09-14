"""Human-in-the-loop approval tool.

This is the governance backbone of Permit Pal: no critical step (moving from
research to packet assembly, from packet to scheduling, or the final
submission) happens without the homeowner's explicit approval.

In demo mode the approval is auto-granted with a loud banner so the
end-to-end demo runs unattended — the banner makes the auto-approval
unmissable rather than silent. In interactive mode it prompts on stdin.
"""

from strands import tool

from . import config


def _request_human_approval(step_summary: str, details: str = "") -> str:
    config.log_call("request_human_approval", {"step_summary": step_summary})
    banner = [
        "",
        "!" * 70,
        "HUMAN APPROVAL REQUIRED — nothing proceeds without the homeowner's OK",
        f"Step: {step_summary}",
    ]
    if details:
        banner.append(f"Details: {details}")
    banner.append("!" * 70)

    if config.DEMO_MODE:
        banner.append(">>> DEMO MODE: auto-approved (in production the homeowner approves here) <<<")
        print("\n".join(banner))
        return "APPROVED — homeowner consent recorded (demo auto-approval)"

    print("\n".join(banner))
    answer = input("Approve this step? [y/N]: ").strip().lower()
    if answer in ("y", "yes"):
        return "APPROVED — homeowner consent recorded"
    return "REJECTED — homeowner did not approve; halting this step"


@tool
def request_human_approval(step_summary: str, details: str = "") -> str:
    """Request the homeowner's explicit approval before a critical step (advancing phases or submitting). NOTHING critical proceeds without this. Always call it before moving to the next phase and before submission."""
    return _request_human_approval(step_summary, details)
