# SenseGraph — Release Notes (`v1.0.0-rc1`)

## Overview
SenseGraph is an accessible, keyboard-first interactive STEM diagram learning platform combining human-reviewable semantic graphs, deterministic Python scientific engines, a Predict → Experiment → Explain Learning Lab, two equivalent explorers (text-first Guided Tour + supplementary SVG), and an evidence-grounded STEM Tutor.

## Highlights Across Phases 1–12
- **Core P0 Domains (Phases 1–2):** Qualitative single-loop series circuits (`physics_circuit`) and directed food webs (`biology_food_web`) with stateless FastAPI REST APIs and semantic HTML5/CSS/JS frontend.
- **Gemini Vision & Human Review (Phases 3–4):** Official `google-genai` SDK integration behind `VisionProvider`, Pillow byte/MIME/dimension (16 MP) security checks, explicit consent, strict `422` rejection of unsupported physics symbols, `[hidden]` CSS enforcement, and keyboard focus preservation.
- **Learning Lab & Equivalent Explorers (Phases 5–6):** Deterministic Predict → Experiment → Explain challenges, responsive `aria-hidden` SVG semantic graph, text-first Guided Tour, and optional user-initiated `speechSynthesis`.
- **STEM2Connect Submission Pack (Phase 7):** Judge-ready README, Devpost description, <6-minute demo script, shot list, judging alignment, and Vietnamese checklist.
- **Post-Hackathon Domain Expansions (Phases 8–10, feature-flaggable via `ENABLE_EXPERIMENTAL_DOMAINS`):**
  - Computer Science Restricted Flowchart Explorer (`cs_flowchart`, safe recursive-descent parser, zero `eval`/`exec`).
  - Mathematics XY Data & Function Graph Explorer (`math_plot`, exact vs interpolated distinction, CSV import, volume-limited Web Audio sonification).
  - Chemistry Molecular Structure Explorer (`chemistry_molecule`, pure-Python beginner SMILES parser & valence validator).
- **Evidence-Grounded STEM Tutor (Phase 11):** 6 deterministic graph query tools, exact node/edge citations, Learn-mode prediction scaffolding, and strict abstention ("Not established by this diagram.").
- **Evaluation & Production Readiness (Phase 12):** Repeatable `evaluation/benchmark.py` harness, GitHub Actions CI, per-IP rate limiting on `/api/analyze`, privacy-respecting error telemetry, ethical user-study protocol, and honest Evidence Matrix.

## Secure Deployment Checklist
- Keep `GEMINI_API_KEY` exclusively in server environment variables (never in client JS or git).
- Set `ENABLE_EXPERIMENTAL_DOMAINS=false` if deploying strictly the P0 Physics + Biology scope.
- Configure `ANALYZE_RATE_LIMIT_PER_MIN` appropriately behind a reverse proxy (HTTPS/TLS) for public deployments.
- Run `python -m pip install pip-audit && pip-audit` periodically to audit dependency vulnerabilities.
