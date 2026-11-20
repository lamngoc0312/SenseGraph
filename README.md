# SenseGraph — Explore STEM Beyond Sight

**Making STEM Diagrams Accessible, Interactive, and Understandable.**

SenseGraph is an accessible interactive STEM diagram learning prototype designed for blind and visually impaired students. Structured science diagrams are represented as a **verified semantic graph** (`nodes` + `edges` + domain payload) so learners can explore objects and relationships using a keyboard and screen reader, then run deterministic domain-specific experiments with plain-language feedback.

- **Primary hackathon track:** Education
- **Related social impact:** Community Impact
- **Current status:** Phase 1 (Core Backend & Simulation Engines) and Phase 2 (Accessible Frontend) implemented and verified. Phase 3 (Live Gemini Vision extraction & human review editor) is planned next.

---

## Implemented Features

### Backend (FastAPI + Pydantic + Pure Python Engines)
- **Semantic Graph Contract:** Strict Pydantic v2 models matching [contracts/diagram.schema.json](contracts/diagram.schema.json).
- **Physics P0 (`physics_circuit`):** Qualitative single-loop series circuit engine (1 battery, 1 switch, 1–2 bulbs). Derives wire loop connectivity from edges, toggles switch state, computes qualitative bulb ON/OFF outcomes, and rejects unsupported topologies or unreviewed diagrams.
- **Biology P0 (`biology_food_web`):** Directed food-web engine (`food/prey -> consumer/predator`). Exposes incoming/outgoing feeding relationships, energy paths, organism removal with exact removed/remaining edge reporting, and explicit non-prediction disclaimers.
- **Stateless REST API:**
  - `GET /api/health`
  - `GET /api/examples`
  - `GET /api/examples/{example_id}`
  - `POST /api/validate`
  - `POST /api/confirm`
  - `POST /api/simulate`

### Accessible Frontend (Semantic HTML5 + CSS + Vanilla JavaScript)
- Served directly by FastAPI at `http://127.0.0.1:8000` (no Node build step required).
- **Honest provenance labeling:** Bundled examples are clearly labeled **Pre-annotated demo — no AI used**. No AI extraction is faked.
- **Keyboard-first & screen-reader-oriented UI:**
  - Semantic landmarks (`<header>`, `<main>`, `<footer>`, hierarchical `<h1>`–`<h4>`), skip-to-content link, and high-contrast visible focus indicators.
  - Native `<button>` controls for all component selection, neighbor navigation, experiment actions, and reset (no keyboard traps, no click-only `<div>` controls).
  - Polite live announcements (`role="status"` / `aria-live="polite"`) and explicit text lists of all relationships so every task works without relying on visual diagrams or color alone.
  - Supplementary visual preview for sighted users with descriptive alt text linked to the textual overview.
  - All simulation state changes come from `POST /api/simulate`; no electrical math is implemented in JavaScript. Reset restores an immutable client-side baseline.

---

## Quick Start on Windows (PowerShell)

```powershell
cd D:\AI-tools\Project\SenseGraph
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Then open in your browser:
- **Web application:** `http://127.0.0.1:8000`
- **API documentation (OpenAPI):** `http://127.0.0.1:8000/docs`
- **Health endpoint:** `http://127.0.0.1:8000/api/health`

### Running Automated Tests

```powershell
python -m pytest -v
```

---

## Project Documentation

- Vietnamese setup guide: [START_HERE_VI.md](START_HERE_VI.md)
- Engineering rules: [AGENTS.md](AGENTS.md)
- Product requirements: [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md)
- Technical architecture & API contract: [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md)
- Accessibility requirements & test plan: [docs/ACCESSIBILITY_AND_TESTS.md](docs/ACCESSIBILITY_AND_TESTS.md)
- Architecture decisions & risks: [docs/DECISIONS.md](docs/DECISIONS.md)
- Authoritative JSON Schema: [contracts/diagram.schema.json](contracts/diagram.schema.json)

---

## Honest Limitations & Accessibility Notes

- **Pre-annotated demos vs. live AI:** The two bundled examples (`physics_series`, `biology_food_web`) are curated fixtures, not evidence of live AI image extraction. Live image upload and Gemini Vision extraction will be added in Phase 3.
- **Domain scope:** Physics covers only qualitative single-loop series circuits (no voltage, current, resistance, or parallel circuits). Biology reports only graph relationship changes when an organism is removed (no population or extinction predictions).
- **Assistive technology testing:** Semantic landmarks, skip link, live regions, and static asset serving are verified by automated tests, **not** yet audited with live Chrome browser automation, NVDA, JAWS, VoiceOver, or blind user study participants. No WCAG compliance certification is claimed.
- **Voice / TTS:** Optional and intentionally not required; the interface relies on standard browser/screen-reader text output.

---

## AI Coding Assistance Disclosure

This prototype was built with AI coding assistance (Google Antigravity / Gemini models) following the project specifications in `docs/` and `AGENTS.md`. All bundled sample diagrams are original fixtures in `fixtures/`. Never commit `.env` or API keys.
