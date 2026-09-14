# Permit Pal — Demo Video Script (≤ 5 minutes)

**Format:** screen recording + voiceover. Terminal running `.venv/bin/python demo.py`.
Target: show a REAL end-to-end multi-agent run, not slides.

## Setup (before recording)

1. Fresh terminal, repo at `~/workspace/hackathons/permit-pal`, `.venv` installed.
2. `rm -rf output && .venv/bin/python demo.py` once to confirm a clean run (~10 seconds).
3. `rm -rf output` again so the recording shows the packet being created live.

## Shot list

| Time | Visual | Narration |
|---|---|---|
| 0:00–0:25 | Title card / repo in editor: `README.md` architecture diagram visible. | "Meet Permit Pal — a background multi-agent system that shepherds a homeowner through a building-permit application end-to-end. Research, paperwork, inspections — with the homeowner approving every critical step. Built on the Strands Agents SDK." |
| 0:25–0:50 | Terminal. Type `.venv/bin/python demo.py`, hit enter. Homeowner prompt prints. | "One command runs the whole thing. Our homeowner, Solana in Austin, Texas, wants to build a 320-square-foot deck. Watch the orchestrator delegate — it never does specialist work itself." |
| 0:50–1:30 | `delegate_to_research_agent` → `lookup_permit_requirements` runs. Scroll the requirements output. | "First, the research agent looks up Austin's actual permit requirements from our knowledge base — six requirements, required documents, fees, inspections. The orchestrator didn't touch the knowledge base; the specialist did. That's disciplined tool design." |
| 1:30–1:55 | **HUMAN APPROVAL REQUIRED** banner prints, auto-approves. | "And here's the governance backbone: nothing advances without the homeowner's approval. In demo mode it's auto-approved with this banner — in production, Solana taps approve on her phone." |
| 1:55–2:40 | `delegate_to_docs_agent` → `assemble_checklist` → `generate_application_packet` → `validate_packet`. `open output/permit-packet-austin-tx-deck-addition.md` in a second pane; scroll the packet. | "Phase two: the docs agent assembles the checklist, generates the actual application packet file, and then validates it — every required document present, PASS. A complete product, not a proof of concept." |
| 2:40–3:00 | Second approval banner. | "Approval number two. The packet doesn't move forward without the homeowner's OK." |
| 3:00–3:40 | `delegate_to_scheduler_agent` → `get_inspection_windows` → `book_inspection` (confirmation code `PP-EE15ED`) → `add_deadline_reminder`. | "Phase three: the scheduler agent finds inspection windows, books the footing inspection, and sets a prep reminder for the day before. Real workflow, real artifacts." |
| 3:40–4:05 | Third approval banner: "approve SUBMITTING the permit application?" | "The final gate — submission itself requires approval. Three for three. No silent actions, ever." |
| 4:05–4:35 | Final summary prints. Scroll the tool-call trace (13 steps). | "The full audit trail: thirteen tool calls across four agents, three human approvals, one submission-ready packet. Every step explainable." |
| 4:35–5:00 | `evals/run_evals.py` output: `TOTAL: 29/29 (ALL PASS)`. End on the repo. | "And we don't just claim good architecture — we test it: 29 evals covering tool-selection accuracy, requirement completeness, and approval gating, all passing deterministically. Swap in Bedrock and the same harness runs live evals. That's Permit Pal." |

## Recording notes

- Keep the terminal font large (≥18pt); the approval banners are the visual anchor — pause half a beat on each.
- If any step scrolls too fast, it's fine — the trace recap at the end shows everything.
- Total runtime of `demo.py` is ~10 seconds; pad with the narration beats above, not with waiting.
- Do NOT edit out the "(demo)" / "mock" labels — the honesty about the mock model is a feature for these judges.
