# BRIEF.md — Permit Pal narrated demo video

- **Project:** `permit-pal-demo` — 60–90s narrated motion-graphics explainer for the
  Permit Pal hackathon project (Agents for Humans Hackathon, AWS, Everyday track).
- **Route:** `/faceless-explainer` — topic explained with invented typography,
  abstract graphics, diagrams, and data-viz; one supplied real asset (architecture
  diagram). Intent interview skipped per parent brief (autonomous, no interactive user).
- **Audience:** hackathon judges + GitHub visitors. 16:9 landscape (README embed).
- **Length:** ~75s, 8 beats of ~8–10s each. Beat durations are finalized from measured
  TTS narration durations (+0.8s padding per beat) in `STORYBOARD.md`.
- **Voiceover:** single narrator, `tts speak --voice avocado_v2:MAI_03`, spoken form
  (numbers spelled out, no markup/stage directions). Concatenated narration muxed
  over the rendered video with ffmpeg; composition itself is silent visuals.
- **Design:** modern dark aesthetic, one accent hue (emerald/green tint toward
  "permit approved"), 1920x1080, 30fps, GSAP + CSS motion graphics.
- **Grounded facts (README-verified, nothing else):**
  - Background multi-agent system on the Strands Agents SDK shepherding a homeowner
    through a home-improvement permit application end-to-end.
  - 1 orchestrator + 3 specialists (research / docs / scheduler), agents-as-tools,
    narrowly scoped toolsets; orchestrator never touches KB/packet/booking —
    only delegates and gates.
  - 3 human-approval gates between phases (research→docs→schedule→submit);
    approvals are first-class tools; demo mode auto-approves with a loud banner.
  - Demo scenario: homeowner in Austin TX, 320 sq ft deck addition; produces a real
    packet file (`output/permit-packet-austin-tx-deck-addition.md`), mock inspection
    booking (`PP-XXXXXX`), reminders, 13-step tool trace, 3/3 approvals.
  - Evals: 29/29 — routing 15/15 unit + 3/3 integration, requirement completeness
    6/6, approval gating 5/5.
  - Honest framing: demo runs on a deterministic heuristic model with zero LLM
    calls and zero AWS credentials; same agents/evals swap to a live Bedrock model.
  - One command: `.venv/bin/python demo.py`.
- **Do not invent features.** No live Bedrock/AgentCore usage claims.
- **Deliverables:**
  - `~/workspace/hackathons/permit-pal/video/` — HyperFrames project, this brief, STORYBOARD.md, narration mp3s.
  - `~/workspace/hackathons/permit-pal/assets/permit-pal-demo.mp4` — final MP4
    (H.264, yuv420p, crf ~23, AAC).
  - README `## Demo` section added after the opening tagline; committed on master
    locally (DO NOT PUSH).
- **Quality gate (mandatory):** extract frames via ffmpeg, view with the read tool,
  fix anything broken/off-brand/misspelled before final render.
- **Flow:** autonomous — no sketch board, no Studio preview pauses; checks
  (`lint`, `check`, frame snapshots) gate the render.
