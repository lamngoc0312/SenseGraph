# SenseGraph — Release Notes (`v1.0.0-rc2`)

## Overview
SenseGraph is an accessible, keyboard-first interactive STEM diagram learning platform combining human-reviewable semantic graphs, deterministic Python scientific engines, a Predict → Experiment → Explain Learning Lab, two equivalent explorers (text-first Guided Tour + supplementary SVG), and an evidence-grounded STEM Tutor.

## Phase 13 Audit Fixes (`v1.0.0-rc2`)
- **Fixed GitHub Actions CI Ruff `SIM102` failure:** Combined nested `elif node.kind == "end": if out_edges:` into `elif node.kind == "end" and out_edges:` in `app/domains/flowchart.py`.
- **Fixed cross-domain frontend regressions across all 5 modules:**
  - Prevented 404 broken image previews on non-raster fixtures (`cs_flowchart.json`, `math_plot.json`, `chemistry_molecule.json`).
  - Updated Guided Tour (`buildTourOverviewText`, `buildTourConnectionsText`), Complete Relationship List, and SVG comparison badges/sub-labels to accurately reflect all 5 domains.
  - Added dedicated SVG layouts for Mathematics XY plots (with labeled axes), CS Flowcharts (non-overlapping grid for loops), and Chemistry molecules (central-atom radial layout).
  - Added keyboard-accessible **Import custom XY data (CSV)** UI directly inside the Mathematics Explorer (`POST /api/math/import-csv`).
  - Wired `ENABLE_EXPERIMENTAL_DOMAINS` feature flag to hide experimental quick-switch buttons and analyze options when disabled, and cleared Tutor history when switching diagrams.
- **Synchronized all submission materials:** Updated test counts to **82 passed**, replaced all local `file:///` links with GitHub-relative links, clarified structured-data workflows (CSV/SMILES) vs. vision extraction, and finalized the <6-minute demo script.

## Highlights Across Phases 1–12
- **Core P0 Domains:** Qualitative single-loop series circuits (`physics_circuit`) and directed food webs (`biology_food_web`).
- **Gemini Vision & Human Review:** Official `google-genai` SDK integration behind `VisionProvider`, Pillow byte/MIME/dimension (16 MP) security checks, explicit consent, strict `422` rejection of unsupported physics symbols, `[hidden]` CSS enforcement, and keyboard focus preservation.
- **Learning Lab, Equivalent Explorers & Grounded Tutor:** Predict → Experiment → Explain challenges, responsive `aria-hidden` SVG graphs, text-first Guided Tour, optional TTS/sonification, and 6-tool Evidence-Grounded Tutor with abstention.
- **Experimental Post-Hackathon Domains (`ENABLE_EXPERIMENTAL_DOMAINS`):** CS Flowchart Explorer (no `eval`/`exec`), Mathematics XY Plot Explorer (CSV), and Chemistry Molecule Explorer (beginner SMILES).

## Verification Summary
- `python -m ruff check app tests evaluation`: **All checks passed**
- `python -m pytest -v`: **82 passed** (`0 failed`, `0 warnings`)
- `python -m evaluation.benchmark --mode dry-run`: **6/6 manifest cases validated**
- Live Gemini Vision & NVDA/VoiceOver manual audits: **Not yet executed** (no local `GEMINI_API_KEY`; assistive-technology audit pending manual session).
