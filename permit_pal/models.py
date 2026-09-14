"""Deterministic heuristic model stand-in for the Strands Agents SDK.

Permit Pal's demo runs with NO LLM calls and NO AWS credentials. This Model
implementation plays the language model's role with fully deterministic,
inspectable logic:

* ``orchestrator`` — follows a fixed 6-step pipeline
  (research -> approval -> docs -> approval -> schedule -> approval),
  emitting exactly one tool call per turn, then a final summary.
* ``research`` — selects among its tools with keyword heuristics over the
  request text. THIS is what the eval harness measures (tool-selection
  accuracy across varied phrasings).
* ``docs`` / ``scheduler`` — follow fixed 3-step mini-pipelines with
  arguments derived from the knowledge base and prior tool results.

Why this design: every decision is explainable and reproducible, so the
evals genuinely test tool routing, KB completeness, and approval gating.
To run against a real model, swap ``build_model`` for
``build_bedrock_model`` — agents, tools, and the eval harness are unchanged.
"""

import json
import re
import uuid
from datetime import date, datetime, timedelta

from strands.models import Model

from . import kb as kbmod

# ---------------------------------------------------------------------------
# Shared message-history helpers
# ---------------------------------------------------------------------------


def _content_texts(blocks):
    return [b.get("text", "") for b in blocks if "text" in b]


def _user_texts(messages):
    out = []
    for m in messages:
        if m.get("role") == "user":
            out.extend(_content_texts(m.get("content", [])))
    return out


def _completed_calls(messages):
    """Return [(tool_name, result_text)] for finished tool calls, in order."""
    calls, pending = [], []
    for m in messages:
        for b in m.get("content", []):
            if m.get("role") == "assistant" and "toolUse" in b:
                pending.append(b["toolUse"].get("name", "unknown"))
            if "toolResult" in b:
                name = pending.pop(0) if pending else "unknown"
                texts = _content_texts(b["toolResult"].get("content", []))
                calls.append((name, "\n".join(texts)))
    return calls


def _grab(pattern, text, default="?"):
    m = re.search(pattern, text or "")
    return m.group(1) if m else default


# ---------------------------------------------------------------------------
# Tool-selection heuristics (the eval harness measures this)
# ---------------------------------------------------------------------------

RESEARCH_ROUTES = [
    ("get_project_types", ["project type", "types of project", "kinds of project",
                            "what projects", "project kinds", "kinds of home project",
                            "home projects"]),
    ("list_jurisdictions", ["jurisdiction", "which cities", "what cities", "cities do",
                             "where are you", "where do you", "covered", "locations",
                             "service area", "what areas"]),
]


def choose_tool(role: str, text: str) -> str:
    """Heuristic tool selection for a sub-agent role given the request text.

    Exposed for the eval harness: routing accuracy = fraction of test
    phrasings mapped to the expected tool.
    """
    t = (text or "").lower()
    if role == "research":
        for tool_name, keywords in RESEARCH_ROUTES:
            if any(k in t for k in keywords):
                return tool_name
        return "lookup_permit_requirements"
    raise ValueError(f"No heuristic routing defined for role {role!r}")


def _research_args(tool_name: str, user_text: str) -> dict:
    j, pid = kbmod.extract_case(user_text)
    if tool_name == "lookup_permit_requirements":
        return {"jurisdiction": j["name"], "project_type": pid}
    if tool_name == "get_project_types":
        return {"jurisdiction": j["name"]}
    return {}


# ---------------------------------------------------------------------------
# Orchestrator pipeline director
# ---------------------------------------------------------------------------


def _case_from(messages):
    return kbmod.extract_case("\n".join(_user_texts(messages)))


def _in_research(messages):
    j, _pid, pdata, name = _full_case(messages)
    return {"task": (
        f"Research the permit requirements for a {pdata['label'].lower()} in {j['name']} "
        f"for homeowner {name}. Return requirement IDs, required documents, fees, and inspections."
    )}


def _full_case(messages):
    j, pid = _case_from(messages)
    pdata = j["project_types"][pid]
    text = "\n".join(_user_texts(messages))
    name = kbmod.find_homeowner_name(text) or "the homeowner"
    return j, pid, pdata, name


def _in_approval(question):
    def build(messages):
        calls = _completed_calls(messages)
        last = calls[-1][1] if calls else ""
        details = (last[:500] + "…") if len(last) > 500 else last
        return {"step_summary": question, "details": details}
    return build


def _in_docs(messages):
    j, _pid, pdata, name = _full_case(messages)
    return {"task": (
        f"Assemble the application packet and checklist for a {pdata['label'].lower()} "
        f"in {j['name']} (homeowner: {name}). Validate the packet when done."
    )}


def _in_scheduler(messages):
    j, _pid, pdata, _name = _full_case(messages)
    return {"task": (
        f"Schedule the required inspections and set deadline reminders for a "
        f"{pdata['label'].lower()} in {j['name']}."
    )}


ORCHESTRATOR_PIPELINE = [
    ("delegate_to_research_agent", _in_research),
    ("request_human_approval", _in_approval("Research complete — approve moving to packet assembly?")),
    ("delegate_to_docs_agent", _in_docs),
    ("request_human_approval", _in_approval("Packet assembled and validated — approve scheduling inspections?")),
    ("delegate_to_scheduler_agent", _in_scheduler),
    ("request_human_approval", _in_approval("Everything is ready — approve SUBMITTING the permit application?")),
]


def _orchestrator_summary(messages):
    calls = _completed_calls(messages)
    by_name = {}
    for name, text in calls:
        by_name.setdefault(name, []).append(text)
    research = by_name.get("delegate_to_research_agent", [""])[0]
    docs = by_name.get("delegate_to_docs_agent", [""])[0]
    sched = by_name.get("delegate_to_scheduler_agent", [""])[0]
    approvals = sum(1 for name, _ in calls if name == "request_human_approval")
    j, _pid, pdata, name = _full_case(messages)

    n_req = _grab(r"Requirements found: (\d+)", research)
    n_docs = _grab(r"Checklist items: (\d+)", docs)
    packet = _grab(r"Packet file: (\S+)", docs)
    conf = _grab(r"booked \((\S+)\)", sched, _grab(r"Confirmation: (\S+)", sched))
    verdict = "PASS" if "PACKET VALIDATION — PASS" in docs else "see packet"

    return (
        f"Permit application ready for submission (demo) ✅\n\n"
        f"• Research: {n_req} requirements identified for a {pdata['label'].lower()} "
        f"in {j['name']} ({j['authority']}).\n"
        f"• Packet: assembled at {packet} — {n_docs} checklist items, validation {verdict}.\n"
        f"• Inspections: booked under confirmation {conf}; deadline reminders set.\n"
        f"• Human approvals: {approvals}/3 granted — nothing advanced without {name}'s OK.\n\n"
        f"Next step in production: submit via {j['portal']} (mock submission in this demo)."
    )


# ---------------------------------------------------------------------------
# Sub-agent directors
# ---------------------------------------------------------------------------


def _research_next(messages):
    calls = _completed_calls(messages)
    if calls:
        result = calls[0][1]
        n_req = _grab(r"Requirements found: (\d+)", result)
        first_line = result.splitlines()[0] if result else ""
        return {"type": "text",
                "text": f"Research complete. Requirements found: {n_req} — {first_line}. "
                        f"Full requirement details returned above."}
    texts = _user_texts(messages)
    user_text = texts[-1] if texts else ""
    tool_name = choose_tool("research", user_text)
    return {"type": "tool", "name": tool_name, "args": _research_args(tool_name, user_text)}


DOCS_STEPS = ["assemble_checklist", "generate_application_packet", "validate_packet"]


def _docs_next(messages):
    calls = _completed_calls(messages)
    n = len(calls)
    if n >= len(DOCS_STEPS):
        gen_result = calls[1][1] if len(calls) > 1 else ""
        val_result = calls[-1][1] if calls else ""
        packet_path = _grab(r"Packet file: (\S+)", gen_result)
        n_items = _grab(r"Checklist items: (\d+)", gen_result)
        verdict_line = val_result.splitlines()[0] if val_result else "validation unknown"
        return {"type": "text",
                "text": f"Docs phase complete. Packet file: {packet_path} — "
                        f"Checklist items: {n_items}. {verdict_line}. Full packet returned above."}
    texts = _user_texts(messages)
    user_text = texts[-1] if texts else ""
    j, pid = kbmod.extract_case(user_text)
    name = kbmod.find_homeowner_name(user_text) or "the homeowner"
    step = DOCS_STEPS[n]
    if step == "assemble_checklist":
        args = {"jurisdiction": j["id"], "project_type": pid}
    elif step == "generate_application_packet":
        args = {"jurisdiction": j["id"], "project_type": pid, "homeowner_name": name}
    else:
        # Validate the actual packet FILE produced by the previous step.
        gen_result = calls[-1][1]
        packet_path = _grab(r"Packet file: (\S+)", gen_result)
        try:
            with open(packet_path, encoding="utf-8") as f:
                packet_text = f.read()
        except OSError:
            packet_text = gen_result
        args = {"packet_text": packet_text[:8000]}
    return {"type": "tool", "name": step, "args": args}


SCHED_STEPS = ["get_inspection_windows", "book_inspection", "add_deadline_reminder"]


def _sched_next(messages):
    calls = _completed_calls(messages)
    n = len(calls)
    if n >= len(SCHED_STEPS):
        conf = _grab(r"Confirmation: (\S+)", calls[1][1] if len(calls) > 1 else "")
        return {"type": "text",
                "text": f"Scheduling complete — inspection booked ({conf}) and reminders set. Details above."}
    texts = _user_texts(messages)
    user_text = texts[-1] if texts else ""
    j, pid = kbmod.extract_case(user_text)
    inspections = j["project_types"][pid]["inspections"]
    first = inspections[0]
    step = SCHED_STEPS[n]
    if step == "get_inspection_windows":
        args = {"inspection_type": first["label"]}
    elif step == "book_inspection":
        window = _grab(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", calls[0][1], default="")
        args = {"inspection_type": first["label"], "window": window or "TBD"}
    else:
        window = _grab(r"Window: (\d{4}-\d{2}-\d{2})", calls[1][1], default=date.today().isoformat())
        try:
            due = (datetime.strptime(window, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()
        except ValueError:
            due = date.today().isoformat()
        args = {"label": f"{first['label']} tomorrow — confirm site access",
                "due_date": due}
    return {"type": "tool", "name": step, "args": args}


# ---------------------------------------------------------------------------
# The Model implementation
# ---------------------------------------------------------------------------


class HeuristicModel(Model):
    """Deterministic stand-in model provider for the Strands Agents SDK."""

    def __init__(self, role: str):
        if role not in ("orchestrator", "research", "docs", "scheduler"):
            raise ValueError(f"Unknown agent role: {role}")
        self.role = role
        self._config: dict = {}

    # -- Model interface ----------------------------------------------------
    def update_config(self, **model_config) -> None:
        self._config.update(model_config)

    def get_config(self):
        return self._config

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        yield {}

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        yield {"messageStart": {"role": "assistant"}}
        action = self._decide(messages)
        if action["type"] == "tool":
            tool_use_id = f"tooluse_{uuid.uuid4().hex[:12]}"
            yield {"contentBlockStart": {"start": {"toolUse": {
                "name": action["name"], "toolUseId": tool_use_id}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {
                "input": json.dumps(action["args"])}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            text = action["text"]
            yield {"contentBlockStart": {"start": {}}}
            for i in range(0, len(text), 160):
                yield {"contentBlockDelta": {"delta": {"text": text[i:i + 160]}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}

    # -- Decision logic ------------------------------------------------------
    def _decide(self, messages):
        if self.role == "orchestrator":
            calls = _completed_calls(messages)
            if len(calls) >= len(ORCHESTRATOR_PIPELINE):
                return {"type": "text", "text": _orchestrator_summary(messages)}
            name, builder = ORCHESTRATOR_PIPELINE[len(calls)]
            return {"type": "tool", "name": name, "args": builder(messages)}
        if self.role == "research":
            return _research_next(messages)
        if self.role == "docs":
            return _docs_next(messages)
        return _sched_next(messages)


def build_model(role: str) -> HeuristicModel:
    """Build the deterministic demo model for an agent role."""
    return HeuristicModel(role)


def build_bedrock_model():
    """Production swap: run the SAME agents against Amazon Bedrock.

    Requires AWS credentials with Bedrock model access (e.g. via the
    AWS CLI, environment variables, or an AgentCore runtime role).
    The agents, tools, and eval harness work unchanged — only the model
    provider is swapped.
    """
    from strands.models import BedrockModel
    return BedrockModel(model_id="YOUR-BEDROCK-MODEL-ID")  # e.g. a Claude model ID
