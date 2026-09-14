"""Permit Pal agent assembly.

Multi-agent architecture (agents-as-tools pattern):

    ┌────────────────────────────────────────────────────────────┐
    │  ORCHESTRATOR ("Permit Pal")                               │
    │  tools: delegate_to_research_agent / delegate_to_docs_agent │
    │         / delegate_to_scheduler_agent / request_human_      │
    │         approval                                           │
    └──────┬──────────────┬───────────────┬───────────────────────┘
           │              │               │
    ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼────────┐
    │ RESEARCH    │ │ DOCS       │ │ SCHEDULER     │
    │ agent       │ │ agent      │ │ agent         │
    │ - lookup_   │ │ - assemble_│ │ - get_inspec- │
    │   permit_   │ │   checklist│ │   tion_windows│
    │   require-  │ │ - generate_│ │ - book_inspec-│
    │   ments     │ │   applica- │ │   tion        │
    │ - list_     │ │   tion_    │ │ - add_dead-   │
    │   jurisdic- │ │   packet   │ │   line_remind-│
    │   tions     │ │ - validate_│ │   er          │
    │ - get_pro-  │ │   packet   │ │               │
    │   ject_types│ │            │ │               │
    └─────────────┘ └────────────┘ └───────────────┘

Every specialist owns a narrow, scoped toolset (disciplined tool design).
The orchestrator never touches a KB, a packet, or a booking directly — it
only delegates and gates each phase transition on human approval.
"""

from strands import Agent, tool

from . import config
from . import tools_approval as ta
from . import tools_docs as td
from . import tools_research as tr
from . import tools_scheduler as ts
from .models import build_bedrock_model, build_model

RESEARCH_SYSTEM = """You are the Research specialist of Permit Pal, a home-improvement permit assistant.
You have three narrowly-scoped tools. Pick EXACTLY the tool that matches the request:
- lookup_permit_requirements: what a permit requires (requirements, documents, fees, inspections).
- list_jurisdictions: which cities/areas are covered.
- get_project_types: which project types are supported in a jurisdiction.
Never invent requirements — everything comes from the knowledge-base tools."""

DOCS_SYSTEM = """You are the Docs specialist of Permit Pal.
You assemble permit application packets in three disciplined steps:
1. assemble_checklist — build the document checklist from the KB.
2. generate_application_packet — write the packet file.
3. validate_packet — verify every required document is present.
Do not skip validation."""

SCHEDULER_SYSTEM = """You are the Scheduler specialist of Permit Pal.
You schedule inspections in three disciplined steps:
1. get_inspection_windows — find available windows for the inspection type.
2. book_inspection — book the chosen window.
3. add_deadline_reminder — set a prep reminder for the day before.
Never book without first checking windows."""

ORCHESTRATOR_SYSTEM = """You are Permit Pal, a permit-application shepherd for homeowners.
You coordinate three specialist agents THROUGH YOUR TOOLS — you never look up
requirements, build packets, or book inspections yourself.

Your phase discipline is absolute:
1. Delegate research to the research agent.
2. Get HUMAN APPROVAL before leaving the research phase.
3. Delegate packet assembly to the docs agent.
4. Get HUMAN APPROVAL before leaving the docs phase.
5. Delegate scheduling to the scheduler agent.
6. Get HUMAN APPROVAL before anything is submitted.

If the homeowner rejects a step, stop and report what needs to change."""


def build_research_agent() -> Agent:
    return Agent(
        model=build_model("research"),
        tools=[tr.lookup_permit_requirements, tr.list_jurisdictions, tr.get_project_types],
        system_prompt=RESEARCH_SYSTEM,
    )


def build_docs_agent() -> Agent:
    return Agent(
        model=build_model("docs"),
        tools=[td.assemble_checklist, td.generate_application_packet, td.validate_packet],
        system_prompt=DOCS_SYSTEM,
    )


def build_scheduler_agent() -> Agent:
    return Agent(
        model=build_model("scheduler"),
        tools=[ts.get_inspection_windows, ts.book_inspection, ts.add_deadline_reminder],
        system_prompt=SCHEDULER_SYSTEM,
    )


def build_orchestrator(use_bedrock: bool = False) -> Agent:
    """Build the full multi-agent system.

    Set use_bedrock=True to run the same agents against Amazon Bedrock
    (requires AWS credentials with Bedrock model access).
    """
    research = build_research_agent()
    docs = build_docs_agent()
    scheduler = build_scheduler_agent()

    @tool
    def delegate_to_research_agent(task: str) -> str:
        """Delegate permit-requirement research to the specialist research agent. Use when you need permit requirements, covered jurisdictions, or supported project types."""
        config.log_call("delegate_to_research_agent", {"task": task[:60]})
        return str(research(task))

    @tool
    def delegate_to_docs_agent(task: str) -> str:
        """Delegate application-packet assembly to the specialist docs agent. Use when you need the document checklist, the application packet file, or packet validation."""
        config.log_call("delegate_to_docs_agent", {"task": task[:60]})
        return str(docs(task))

    @tool
    def delegate_to_scheduler_agent(task: str) -> str:
        """Delegate inspection scheduling to the specialist scheduler agent. Use when you need inspection windows, bookings, or deadline reminders."""
        config.log_call("delegate_to_scheduler_agent", {"task": task[:60]})
        return str(scheduler(task))

    model = build_bedrock_model() if use_bedrock else build_model("orchestrator")
    return Agent(
        model=model,
        tools=[
            delegate_to_research_agent,
            ta.request_human_approval,
            delegate_to_docs_agent,
            delegate_to_scheduler_agent,
        ],
        system_prompt=ORCHESTRATOR_SYSTEM,
    )
