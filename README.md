# SenseGraph — Explore STEM Beyond Sight

**Making STEM Diagrams Accessible, Interactive, and Understandable.**

- **Hackathon:** STEM2Connect AI Hackathon 2026
- **Primary Track:** Education · **Related Social Impact:** Community Impact
- **Stack:** Python 3.11–3.13, FastAPI, Pydantic v2, Vanilla HTML5/CSS/JS, Google Gemini (`google-genai`), Pytest
- **Release Candidate:** `v0.10.0-dev` (Phases 1–10 complete: Physics, Biology, CS Flowchart, Mathematics XY Plot, and Chemistry Molecular Structure)

---

## 1. Problem & Target User

Many foundational STEM concepts—series electrical circuits, food webs, and energy flows—are taught through diagrams whose meaning lives in **wires, arrows, symbols, and graph connectivity**. A static image or a single-sentence alt-text caption does not allow a blind or visually impaired student to **independently inspect relationships, trace paths, or experiment with how the system behaves**.

- **Primary user:** A blind or visually impaired secondary or university student using a laptop with keyboard navigation and assistive technology (such as NVDA or VoiceOver).
- **Secondary user:** A sighted educator who reviews and corrects AI-extracted diagrams before sharing accessible learning materials.

---

## 2. Core Value & Six-Step Learning Pipeline

SenseGraph turns supported STEM diagrams into an editable, verifiable semantic graph and combines **Explore Freely** with a **Guided Learning Lab (Predict → Experiment → Explain)**:

```text
1. Select Pre-Annotated Demo or Upload Diagram Image
        ↓
2. Gemini Vision Proposes Semantic Graph (optional, with explicit consent)
        ↓
3. Deterministic Structural & Scientific Validation (Python)
        ↓
4. Human Review & Correction (labels, types, wires, arrow directions)
        ↓
5. Two Equivalent Explorers: Text/Keyboard Guided Tour + Interactive SVG
        ↓
6. Deterministic Experiment & Guided Learning Lab (Predict → Experiment → Explain)
```

---

## 3. What AI Does vs. What Deterministic Python Engines Do

| Layer | Responsibility | Strict Boundary |
|---|---|---|
| **Google Gemini (`google-genai`)** | Extracts tentative nodes, edges, warnings, and domain payload from an uploaded PNG/JPEG/WEBP image | Treated as **untrusted**; never auto-confirmed; never runs simulations; embedded image text is treated strictly as data |
| **Schema & Validator (`app/services/validators.py`)** | Enforces `contracts/diagram.schema.json`, unique IDs, valid endpoints, domain kinds/relations, and series-ring topology | Rejects unknown Physics symbols (`422`) instead of coercing them to bulbs; never invents missing wires |
| **Human Review UI** | Lets users inspect warnings/errors, edit labels/types/edges, swap Biology arrows, and explicitly confirm | Simulation stays blocked (`403`/`422`) until valid and confirmed |
| **Physics Engine (`app/domains/physics.py`)** | Evaluates qualitative single-loop series circuits (1 battery, 1 switch, 1–2 bulbs) | Qualitative ON/OFF only; no voltage, current, resistance, or parallel circuits |
| **Biology Engine (`app/domains/biology.py`)** | Queries directed `food/prey -> consumer/predator` relations/paths and removes an organism + incident edges | Graph relationship changes only; explicitly disclaims extinction or population predictions |
| **CS Flowchart Engine (`app/domains/flowchart.py`)** | Parses and executes restricted integer/boolean assignments, True/False decisions, and finite loops step-by-step | Explicit recursive-descent parser only (never `eval`/`exec`); bounded to `<= 200` steps & `0.5s` timeout |
| **Learning Lab (`app/services/learning.py`)** | Generates & grades Predict → Experiment → Explain challenges directly from Python engines | Zero LLM grading; session-only progress (no accounts/DB) |

---

## 4. Architecture & Project Structure

```text
SenseGraph/
  app/
    main.py                 # FastAPI app, REST API, same-origin static serving
    models.py               # Pydantic v2 models matching contracts/diagram.schema.json
    settings.py             # Environment settings (server-only credentials)
    domains/
      physics.py            # Qualitative single-loop series circuit engine
      biology.py            # Directed food-web relationship engine
    services/
      validators.py         # Structural (valid) vs domain (simulation_ready) checks
      fixtures.py           # Bundled pre-annotated demo loader (deep-copied)
      description.py        # Deterministic plain-language diagram & node summaries
      ai_vision.py          # VisionProvider abstraction, Pillow security checks, GeminiVisionProvider
      learning.py           # Deterministic Guided Learning Lab engine
    static/
      index.html            # Semantic HTML5 UI (Welcome, Review, Explorer, Lab, Guided Tour)
      styles.css            # High-contrast responsive CSS with [hidden] & reduced-motion rules
      app.js                # Vanilla JS client, focus management, SVG graph, optional TTS
  contracts/
    diagram.schema.json     # Authoritative JSON Schema (Draft 2020-12)
  fixtures/
    physics_series.json     # Curated Physics demo fixture
    biology_food_web.json   # Curated Biology demo fixture
    images/                 # Original sample PNGs for preview & upload testing
  tests/
    test_models.py          # JSON Schema + Pydantic + validator tests (10)
    test_physics.py         # Physics engine & topology invariant tests (10)
    test_biology.py         # Biology graph, path, and removal tests (7)
    test_api.py             # REST endpoints, static assets, Phase 2 & 6 UI checks (8)
    test_ai_vision.py       # Upload security, mocked Gemini, integrity & review tests (13)
    test_learning.py        # Guided Learning Lab scoring & API tests (6)
  docs/
    PRODUCT_SPEC.md
    TECHNICAL_SPEC.md
    ACCESSIBILITY_AND_TESTS.md
    DECISIONS.md
    EXTRACTION_EVALUATION.md
    ROADMAP_AND_SUBMISSION.md
  submission/               # STEM2Connect Devpost & demo assets
```

### REST API Endpoints
- `GET /api/health` — Backend health, supported domains, and `ai_configured` boolean (never exposes secrets)
- `GET /api/examples` & `GET /api/examples/{example_id}` — Pre-annotated fixtures (`Pre-annotated demo — no AI used`)
- `POST /api/analyze` — Multipart image upload (`file`, `domain`, `consent`) → Pillow security validation → Gemini Vision (`unreviewed`)
- `POST /api/validate` — Separates structural validity (`valid`) from domain readiness (`simulation_ready`)
- `POST /api/confirm` — Validates and confirms an unreviewed diagram (`review_status="confirmed"`)
- `POST /api/state` — Explicit backend-calculated circuit/food-web state
- `POST /api/simulate` — Stateless deterministic `toggle_switch` and `remove_organism` actions
- `POST /api/learning/challenges` & `POST /api/learning/evaluate` — Guided Learning Lab challenge generation and grading

---

## 5. Setup & Running Locally (Windows PowerShell)

### Mode A — Pre-Annotated Demo Mode (No API Key Required)

```powershell
cd D:\AI-tools\Project\SenseGraph
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Open **`http://127.0.0.1:8000`** in your browser (`http://127.0.0.1:8000/docs` for OpenAPI).

### Mode B — Live Gemini Vision Mode (Optional, Local `.env`)

1. Edit your local `.env` (already excluded from git via `.gitignore`):
   ```dotenv
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   AI_TIMEOUT_SECONDS=30
   MAX_UPLOAD_MB=5
   ```
2. Restart `uvicorn`. The header badge updates to **Gemini Vision configured**.
3. Upload a PNG, JPEG, or WEBP diagram (<= 5 MB, <= 4096×4096 / 16 MP), check the explicit external-provider consent box, review and validate the AI proposal, then confirm to open the Explorer.
4. **Privacy boundary:** Uploaded images are processed in memory only, never persisted on disk, and never logged. Never upload personal or sensitive images.

---

## 6. Accessibility Design

- **Semantic HTML5:** `<html lang="en">`, `<header>`, `<main id="main-content" tabindex="-1">`, `<footer>`, hierarchical `<h1>`–`<h4>`, `<label>`-bound form fields, `<fieldset>`/`<legend>` for Learning Lab predictions, and native `<button>` controls everywhere.
- **Keyboard-only operation:** Skip-to-content link visible on focus, high-contrast `:focus-visible` outlines, `[hidden] { display: none !important; }` to keep hidden panels out of tab order, and deliberate focus restoration after component selection, neighbor jumps, simulations, resets, error dismissal, and AI confirmation.
- **Two equivalent explorers:** The responsive SVG semantic graph is marked `aria-hidden="true"` and `focusable="false"` so it visually assists sighted users without introducing duplicate tab stops, while keyboard/screen-reader users have 100% equivalent access via the structured Component List, Relationships, Complete Text List, and text-first **Guided Tour**.
- **Optional user-initiated voice:** Browser `speechSynthesis` with Pause/Resume, Stop, and Speech Rate (`0.8x`–`1.5x`) is off by default, never autoplays, and is never required.

---

## 7. Testing Results & Honest Limitations

### Automated Verification
Run locally:
```powershell
python -m pytest -v
python -m ruff check app tests
```
- **Observed result:** **54 passed** (`0 failed`, `0 warnings`), **Ruff: All checks passed**.
- Automated AI tests use mocked `VisionProvider` instances and never call the live Gemini API.

### Honest Limitations & What Has Not Been Tested Yet
- **Live Gemini Vision smoke test:** Not yet executed in the development environment because no local `GEMINI_API_KEY` was configured. All live extraction rows in [docs/EXTRACTION_EVALUATION.md](docs/EXTRACTION_EVALUATION.md) are candidly marked `not tested`.
- **Live browser & screen-reader audit:** Live Chrome automation, NVDA, JAWS, and VoiceOver sessions, and user studies with blind students have **not** been conducted yet. No WCAG compliance certification or demonstrated educational efficacy is claimed.
- **Scientific scope:** Physics covers only qualitative single-loop series circuits (1 battery, 1 switch, 1–2 bulbs). Biology covers only directed feeding relationship changes (no population dynamics or extinction forecasts).
- **Roadmap (post-hackathon):** Computer Science Flowchart Explorer (P2), live multi-image Gemini extraction benchmark, formal NVDA/VoiceOver and blind-learner user testing, and optional cloud hosting.

---

## 8. Attribution & AI Coding Disclosure

- **AI coding assistance:** Built with AI coding assistance (Google Antigravity / Gemini models) following the specifications in `docs/` and `AGENTS.md`.
- **External AI SDK:** Official Google `google-genai` Python SDK (`GeminiVisionProvider`).
- **Sample assets:** Bundled fixtures (`fixtures/*.json`) and sample images (`fixtures/images/*.png`) are original handoff assets created for this project.
- **Secrets:** `.env` and credentials are excluded via `.gitignore` and verified absent from git history.
