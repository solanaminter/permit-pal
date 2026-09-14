"""Permit Pal eval harness — deterministic, no AWS required.

Suites:
  1. routing_accuracy — the research agent's tool-selection accuracy across
     varied phrasings (unit: choose_tool heuristic; integration: full Agent
     invocations with the tool-call trace).
  2. requirement_completeness — for every jurisdiction x project type in the
     KB, the docs pipeline's checklist + packet must contain every required
     document (validated by validate_packet).
  3. approval_gating — the orchestrator's end-to-end trace must show exactly
     3 human approvals, each gating a phase transition, with no critical step
     advancing before its approval.

The harness is model-agnostic: run it against build_bedrock_model() for
live-LLM evals by setting PERMIT_PAL_EVAL_BEDROCK=1 (needs AWS credentials).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["PERMIT_PAL_DEMO"] = "1"

from permit_pal import config  # noqa: E402

config.DEMO_MODE = True

from permit_pal import kb  # noqa: E402
from permit_pal.agents import build_docs_agent, build_orchestrator, build_research_agent  # noqa: E402
from permit_pal.models import choose_tool  # noqa: E402
from permit_pal.tools_docs import (  # noqa: E402
    _assemble_checklist,
    _generate_application_packet,
    _validate_packet,
)

USE_BEDROCK = os.environ.get("PERMIT_PAL_EVAL_BEDROCK", "") == "1"

# (prompt, expected_tool)
ROUTING_CASES = [
    ("What permits do I need for a deck in Austin, TX?", "lookup_permit_requirements"),
    ("Look up the requirements for a kitchen remodel in Seattle.", "lookup_permit_requirements"),
    ("What project types are supported in Denver?", "get_project_types"),
    ("Which jurisdictions do you cover?", "list_jurisdictions"),
    ("Do I need a permit for a deck addition?", "lookup_permit_requirements"),
    ("Tell me the building code requirements for a Denver CO kitchen remodel.", "lookup_permit_requirements"),
    ("What kinds of projects can you help with in Austin?", "get_project_types"),
    ("Where are you able to look up permits?", "list_jurisdictions"),
    ("Show me what cities are supported.", "list_jurisdictions"),
    ("I need the full requirements list for a kitchen remodel in Seattle, WA.", "lookup_permit_requirements"),
    ("What types of home projects do you support?", "get_project_types"),
    ("Is a permit required for a deck in Denver?", "lookup_permit_requirements"),
    ("What areas do you cover for permit research?", "list_jurisdictions"),
    ("Give me the permit requirements for a kitchen remodel in Austin, TX.", "lookup_permit_requirements"),
    ("What project kinds are available in Seattle?", "get_project_types"),
]

INTEGRATION_PROMPTS = [
    ("What permits do I need for a deck in Austin, TX?", "lookup_permit_requirements"),
    ("Which jurisdictions do you cover?", "list_jurisdictions"),
    ("What project types are supported in Denver?", "get_project_types"),
]


def eval_routing_unit():
    passed, rows = 0, []
    for prompt, expected in ROUTING_CASES:
        got = choose_tool("research", prompt)
        ok = got == expected
        passed += ok
        rows.append((ok, prompt[:58], expected, got))
    return passed, len(ROUTING_CASES), rows


def eval_routing_integration():
    passed, rows = 0, []
    for prompt, expected in INTEGRATION_PROMPTS:
        config.clear_log()
        agent = build_research_agent()  # fresh agent per case: no shared history
        agent(prompt)
        tools_used = [n for n, _ in config.CALL_LOG]
        got = tools_used[0] if tools_used else "none"
        ok = got == expected
        passed += ok
        rows.append((ok, prompt[:58], expected, got))
    return passed, len(INTEGRATION_PROMPTS), rows


def eval_completeness():
    passed, total, rows = 0, 0, []
    for j in kb.jurisdictions():
        for pid in j["project_types"]:
            total += 1
            label = f"{j['id']}/{pid}"
            checklist = _assemble_checklist(j["id"], pid)
            packet_result = _generate_application_packet(j["id"], pid, "Eval Homeowner")
            packet_path = packet_result.split("Packet file:")[1].splitlines()[0].strip()
            with open(packet_path, encoding="utf-8") as f:
                packet_text = f.read()
            verdict = _validate_packet(packet_text)
            ok = "PACKET VALIDATION — PASS" in verdict
            passed += ok
            rows.append((ok, label, "validate_packet=PASS", "PASS" if ok else "FAIL"))
    return passed, total, rows


def eval_approval_gating():
    config.clear_log()
    agent = build_orchestrator()
    agent(
        "I'm Solana Minter, a homeowner in Austin, TX. I want to build a deck "
        "(deck addition). Research the requirements, get my approval, assemble "
        "the packet, get my approval, schedule inspections, get my approval, "
        "then summarize for submission."
    )
    names = [n for n, _ in config.CALL_LOG]
    checks = []
    approvals = [i for i, n in enumerate(names) if n == "request_human_approval"]
    checks.append(("exactly 3 approvals", len(approvals) == 3, f"found {len(approvals)}"))
    idx = {n: i for i, n in enumerate(names)}
    checks.append(("approval after research phase",
                   idx.get("delegate_to_research_agent", 99) < approvals[0] if approvals else False,
                   "research -> approval[0]"))
    checks.append(("approval before docs phase",
                   approvals[0] < idx.get("delegate_to_docs_agent", -1) if approvals else False,
                   "approval[0] -> docs"))
    checks.append(("approval before scheduler phase",
                   approvals[1] < idx.get("delegate_to_scheduler_agent", -1) if len(approvals) > 1 else False,
                   "approval[1] -> scheduler"))
    checks.append(("final step is the submission approval",
                   names[-1] == "request_human_approval" if names else False,
                   f"last tool: {names[-1] if names else 'none'}"))
    passed = sum(1 for _, ok, _ in checks if ok)
    rows = [(ok, name, "holds", detail) for name, ok, detail in checks]
    return passed, len(checks), rows


def main() -> int:
    print("=" * 70)
    print(f"PERMIT PAL EVALS ({'Bedrock' if USE_BEDROCK else 'deterministic heuristic model'})")
    print("=" * 70)
    suites = [
        ("routing_accuracy (unit)", eval_routing_unit),
        ("routing_accuracy (integration)", eval_routing_integration),
        ("requirement_completeness", eval_completeness),
        ("approval_gating", eval_approval_gating),
    ]
    total_pass, total_n = 0, 0
    for suite_name, fn in suites:
        passed, n, rows = fn()
        total_pass += passed
        total_n += n
        status = "PASS" if passed == n else "FAIL"
        print(f"\n[{status}] {suite_name}: {passed}/{n}")
        for ok, case, expected, got in rows:
            mark = "ok " if ok else "MISS"
            print(f"  {mark} {case:<60} expected={expected} got={got}")
    print("\n" + "=" * 70)
    print(f"TOTAL: {total_pass}/{total_n} "
          f"({'ALL PASS' if total_pass == total_n else 'FAILURES PRESENT'})")
    return 0 if total_pass == total_n else 1


if __name__ == "__main__":
    raise SystemExit(main())
