# SenseGraph — Explore STEM Beyond Sight

**Making STEM Diagrams Accessible, Interactive, and Understandable.**

SenseGraph is an accessible interactive STEM diagram learning prototype designed for blind and visually impaired students. Structured science diagrams are converted into a **human-reviewable semantic graph** (`nodes` + `edges` + domain payload) so learners can explore objects and relationships using a keyboard and screen reader, then run deterministic domain-specific experiments with plain-language feedback.

- **Primary hackathon track:** Education
- **Related social impact:** Community Impact
- **Current status:** Phases 1–6 implemented and verified with automated tests (Core Backend, Accessible Frontend, Gemini Vision & Human Review, Stability/Security Audit, Guided Learning Lab, and Interactive SVG Graph + Text-First Guided Tour).

---

## Implemented Features

### Backend (FastAPI + Pydantic + Pure Python Engines + Google Gemini)
- **Semantic Graph Contract:** Strict Pydantic v2 models matching [contracts/diagram.schema.json](contracts/diagram.schema.json).
- **Physics P0 (`physics_circuit`):** Qualitative single-loop series circuit engine (1 battery, 1 switch, 1–2 bulbs). Derives wire loop connectivity from edges, toggles switch state, computes qualitative bulb ON/OFF outcomes, and rejects unsupported topologies or unreviewed diagrams.
- **Biology P0 (`biology_food_web`):** Directed food-web engine (`food/prey -> consumer/predator`). Exposes incoming/outgoing feeding relationships, energy paths, organism removal with exact removed/remaining edge reporting, and explicit non-prediction disclaimers.
- **Gemini Vision Extraction (`app/services/ai_vision.py`):**
  - Replaceable `VisionProvider` abstraction with `GeminiVisionProvider` using the official `google-genai` SDK.
  - Validates uploaded PNG/JPEG/WEBP files (<= 5 MB, <= 4096×4096 / 16 MP pixel cap to guard against decompression bombs, strict declared-vs-actual MIME match, full Pillow decode). Never persists uploaded images by default, never logs raw image bytes or API keys, and treats embedded image text strictly as untrusted data.
  - Enforces strict scientific integrity: unknown or unsupported physics component types (e.g. resistors) are rejected (`422 AI_EXTRACTION_INVALID`) rather than silently coerced to bulbs.
  - Always returns `source.mode="ai"`, `source.provider="gemini"`, and `review_status="unreviewed"` so human verification is mandatory before simulation.
- **Stateless REST API:**
  - `GET /api/health`
  - `GET /api/examples`
  - `GET /api/examples/{example_id}`
  - `POST /api/analyze` (`multipart/form-data`: `file`, `domain`, `consent`)
  - `POST /api/validate`
  - `POST /api/confirm`
  - `POST /api/state` (explicit backend-calculated circuit/food-web state)
  - `POST /api/simulate`
  - `POST /api/learning/challenges` (deterministic Guided Learning Lab challenge generation)
  - `POST /api/learning/evaluate` (deterministic prediction evaluation + concept explanation)

### Accessible Frontend (Semantic HTML5 + CSS + Vanilla JavaScript)
- Served directly by FastAPI at `http://127.0.0.1:8000` (no Node build step required).
- **Clear provenance badges:**
  - **Pre-annotated demo — no AI used** for bundled fixtures
  - **AI-generated — review required** during human verification
  - **Confirmed diagram — ready to explore** in the interactive explorer
- **Analyze Your Own Diagram & Human Review Workflow:**
  - Upload PNG/JPEG/WEBP -> Choose Domain -> Explicit external-provider consent -> Analyze with Gemini -> Review AI warnings & validation errors -> Edit labels, types, connections, Physics loop sequence, or Biology arrow directions -> Validate -> Confirm -> Explore & Experiment.
- **Two Learning Modes in the Shared Explorer:**
  - **Explore Freely:** Inspect components, follow direct connections, toggle switches or remove organisms, and reset at any time.
- **Guided Learning Lab (Predict → Experiment → Explain):** Structured, session-only challenges with native radio/checkbox prediction controls, deterministic Python engine verification, evidence-based explanations, linked component jump buttons, retry, skip, and session reset (works for both pre-annotated fixtures and confirmed AI diagrams; zero LLM grading).
- **Two Equivalent Explorers (Visual + Text/Audio-First):**
  - **Interactive Semantic Graph (SVG):** Lightweight responsive SVG generated directly from the confirmed graph (component shapes/wire loop for Physics; layered organisms and directional energy arrows for Biology), synchronized with selection, switch toggles, organism removals, reset, and AI confirmation, and marked `aria-hidden="true"` so it never creates duplicate keyboard tab stops.
  - **Text-First Guided Tour + Optional Voice:** Native keyboard controls (`Overview`, `Previous component`, `Next component`, `Connections`, `Back to overview`, `Repeat explanation`) grounded strictly in confirmed graph data (never inventing spatial positions), plus optional user-initiated browser `speechSynthesis` with pause/stop and speech-rate controls (off by default, never autoplays).
- **Keyboard-first & screen-reader-oriented UI:**
  - Semantic landmarks (`<header>`, `<main>`, `<footer>`, hierarchical `<h1>`–`<h4>`), skip-to-content link, and high-contrast visible focus indicators.
  - Native `<button>` controls and accessible `<label>`-bound form inputs (no keyboard traps).
  - Deliberate focus preservation/restoration across component selection, neighbor jumps, switch toggling, organism removal, experiment reset, and AI confirmation.
  - Polite live announcements (`role="status"` / `aria-live="polite"`) and explicit text lists of all relationships.
  - Bulb and switch states are read directly from `POST /api/state` (zero electrical calculations or summary-text parsing in JavaScript).

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

### Enabling Live Gemini Vision Analysis (Optional)

By default, `.env.example` sets `AI_PROVIDER=none`, so both pre-annotated demo modules work immediately with no API key.

To enable live image extraction on your local machine:
1. Edit your local `.env` file (never commit `.env` to git):
   ```dotenv
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_actual_key_here
   GEMINI_MODEL=gemini-2.5-flash
   AI_TIMEOUT_SECONDS=30
   MAX_UPLOAD_MB=5
   ```
2. Restart `uvicorn`. The header badge will update to **Gemini Vision configured**.
3. **Data-sharing notice:** Uploaded images are sent to Google's Gemini API only after you explicitly check the consent box. Avoid uploading personal or sensitive content. Images are processed in memory and not persisted by SenseGraph.

### Running Automated Tests

```powershell
python -m pytest -v
```

Automated tests use mocked `VisionProvider` responses and never call the live Gemini API.

---

## Project Documentation

- Vietnamese setup guide: [START_HERE_VI.md](START_HERE_VI.md)
- Engineering rules: [AGENTS.md](AGENTS.md)
- Product requirements: [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md)
- Technical architecture & API contract: [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md)
- Accessibility requirements & test plan: [docs/ACCESSIBILITY_AND_TESTS.md](docs/ACCESSIBILITY_AND_TESTS.md)
- Architecture decisions & risks: [docs/DECISIONS.md](docs/DECISIONS.md)
- Extraction evaluation & manual QA checklist: [docs/EXTRACTION_EVALUATION.md](docs/EXTRACTION_EVALUATION.md)
- Authoritative JSON Schema: [contracts/diagram.schema.json](contracts/diagram.schema.json)

---

## Honest Limitations & Accessibility Notes

- **Pre-annotated demos vs. live AI:** The two bundled examples (`physics_series`, `biology_food_web`) are curated fixtures, not evidence of live AI image extraction.
- **Vision extraction accuracy:** Multimodal vision models can misread symbols, wires, or arrow directions. Every AI output starts as `unreviewed`, requires human verification/editing, and cannot be simulated until it passes deterministic validation and explicit confirmation.
- **Domain scope:** Physics covers only qualitative single-loop series circuits (no voltage, current, resistance, or parallel circuits). Biology reports only graph relationship changes when an organism is removed (no population or extinction predictions).
- **Assistive technology testing:** Semantic landmarks, skip link, live regions, focus handling code, and backend/API/AI-mock behavior are verified by automated tests, **not** yet audited with live NVDA, JAWS, VoiceOver, or blind user study participants. No WCAG compliance certification is claimed.
- **Voice / TTS:** Optional and intentionally not required.

---

## AI Coding Assistance & External Services Disclosure

This prototype was built with AI coding assistance (Google Antigravity / Gemini models) following the project specifications in `docs/` and `AGENTS.md`. Live image extraction uses the official `google-genai` Python SDK when configured by the user. All bundled sample diagrams are original fixtures in `fixtures/`. Never commit `.env` or API keys.
