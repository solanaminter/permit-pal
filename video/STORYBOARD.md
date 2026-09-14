---
format: 1920x1080
duration: 83s
message: "Permit Pal shepherds a homeowner through a permit application end to end — multi-agent, human-gated, honestly evaluated."
arc: Pain → System → Architecture → Phase 1 → Governance → Phase 2 → Phase 3 → Proof + CTA
audience: hackathon judges and GitHub visitors
mode: autonomous
---

## Frame 1 — The maze

- scene: Ghost word "MAZE" behind a headline; drifting PDF cards; cost/delay chips
- duration: 9.2s
- poster: 4s
- transition_in: cut
- status: animated
- voiceover: "Getting a building permit is a maze of city-specific rules buried in PDFs. Homeowners overpay expediters, or wait weeks on corrections."

Pain first. City-specific requirements live in PDFs and portal FAQs; the cost of
going it alone is an expediter ($500–$2,000 per permit, per README) or weeks of
corrections on an incomplete packet.

## Frame 2 — Meet Permit Pal

- scene: Big "Permit Pal" title with house mark; orbiting agent dots; SDK badge
- duration: 10s
- poster: 5s
- transition_in: cut
- status: animated
- voiceover: "Meet Permit Pal: a background multi-agent system on the Strands Agents SDK that shepherds a homeowner through the whole application, end to end."

The product promise in one line: background (not a chatbot), multi-agent,
Strands Agents SDK, end-to-end shepherding.

## Frame 3 — Architecture

- scene: The real architecture diagram in a card; orchestrator + 3 specialists labeled
- duration: 12.2s
- poster: 6s
- transition_in: cut
- status: animated
- voiceover: "One orchestrator delegates to three specialists: research, docs, and scheduler, each with a narrow set of tools. It never touches the data itself. It delegates, and gates."

Shows `assets/architecture.webp` (the generated diagram). Orchestrator never
touches KB/packet/booking directly — only delegates and enforces approvals.

## Frame 4 — Phase 1: Research

- scene: KB card for Austin TX deck addition; requirement chips materialize; tool chip
- duration: 7.52s
- poster: 4s
- transition_in: cut
- status: animated
- voiceover: "Phase one: the research agent pulls Austin's requirements for a three hundred twenty square foot deck addition from the knowledge base."

Grounded in `permit_pal/data/permits.json`: Austin, TX · deck-addition · 320 sq ft;
chips show real KB entries (AUS-DECK-01 residential building permit, site plan,
construction drawings) and the `lookup_permit_requirements` tool.

## Frame 5 — Governance

- scene: Three amber approval gates in sequence; homeowner headline
- duration: 7.71s
- poster: 4s
- transition_in: cut
- status: animated
- voiceover: "Nothing advances without the homeowner. Three approval gates sit between the phases, and each one is a first-class tool."

3 gates between research→docs→schedule→submit. `request_human_approval` is a
first-class tool; demo mode auto-approves with a loud banner.

## Frame 6 — Phase 2: Docs

- scene: Checklist items tick off; packet file card; big PASS stamp
- duration: 8.72s
- poster: 5s
- transition_in: cut
- status: animated
- voiceover: "Phase two: the docs agent assembles the checklist, generates the packet, and validates it. Validation: PASS."

Tools: `assemble_checklist` → `generate_application_packet` → `validate_packet`.
The real artifact: `output/permit-packet-austin-tx-deck-addition.md`.

## Frame 7 — Phase 3: Scheduler

- scene: Calendar card; booking confirmation chip PP-XXXXXX; reminder bells; final gate
- duration: 8.17s
- poster: 4s
- transition_in: cut
- status: animated
- voiceover: "Phase three: the scheduler books the inspection and sets deadline reminders. The final approval gate fires before submission."

Tools: `get_inspection_windows` → `book_inspection` (mock confirmation PP-XXXXXX)
→ `add_deadline_reminder`. Final gate = submission approval.

## Frame 8 — Proof

- scene: Stat hits (13-step trace, 3/3 approvals, 29/29 evals); honest-model card; terminal command
- duration: 19.47s
- poster: 6s
- transition_in: cut
- status: animated
- voiceover: "The proof: a thirteen-step audit trail, three out of three approvals, twenty-nine out of twenty-nine evals. The demo runs offline on a deterministic heuristic model, and the same agents swap to a live Bedrock model. One command: dot venv slash bin slash python demo dot py."

Two-part visual: (A) stat hits with eval breakdown (15/15 unit routing · 3/3
integration · 6/6 completeness · 5/5 gating); (B) honest framing
(deterministic heuristic model · zero LLM calls · zero AWS credentials →
Bedrock-swappable) and the one-command terminal card `.venv/bin/python demo.py`.
