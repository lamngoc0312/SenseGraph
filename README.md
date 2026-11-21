# SenseGraph — Explore STEM Beyond Sight

**Making STEM Diagrams Accessible, Interactive, and Understandable.**

- **Hackathon:** STEM2Connect AI Hackathon 2026
- **Primary Track:** Education · **Related Social Impact:** Community Impact
- **Stack:** Python 3.11–3.13, FastAPI, Pydantic v2, Vanilla HTML5/CSS/JS (modular `voice.js`, `library.js`, `guidance.js`), Google Gemini (`google-genai`), Pytest
- **Current Build:** **SenseGraph 2.0** (Phases 1–17 complete; **98 automated tests passing**; **20 distinct validated STEM lessons** across 5 domains)

> **New in SenseGraph 2.0 (Phases 14–17):** Calm **Audio-First Student Experience** (default) with contextual step guidance, optional **Push-to-Talk Conversational Voice Interaction** (`POST /api/voice/interpret`, routed to the Evidence-Grounded Tutor), a **20-Lesson Validated STEM Learning Library** (`GET /api/lessons`) with local-only progress tracking, and **Educator JSON Lesson Package Authoring** (`POST /api/lessons/validate-package`). See [docs/VOICE_AND_LIBRARY_GUIDE.md](docs/VOICE_AND_LIBRARY_GUIDE.md) for the complete Voice Command Reference, privacy disclosure, and lesson catalog.

---

## 1. Problem & Target User

Many foundational STEM concepts—electrical circuits, food webs, algorithm flowcharts, mathematical plots, and molecular structures—are taught through diagrams whose meaning lives in **wires, arrows, symbols, branches, and graph connectivity**. A static image or a single-sentence alt-text caption does not allow a blind or visually impaired student to **independently inspect relationships, trace paths, or experiment with how the system behaves**.

- **Primary user:** A blind or visually impaired secondary or university student using a laptop with keyboard navigation and assistive technology (such as NVDA or VoiceOver).
- **Secondary user:** A sighted educator who reviews and corrects extracted diagrams before sharing accessible learning materials.

---

## 2. Core Value & Six-Step Learning Pipeline

SenseGraph represents supported STEM diagrams as a validated, editable semantic graph (`contracts/diagram.schema.json`) and combines **Explore Freely**, a **Guided Learning Lab (Predict → Experiment → Explain)**, a **Text-First Guided Tour**, a synchronized **Interactive SVG Graph**, and an **Evidence-Grounded STEM Tutor**:

```text
1. Select Pre-Annotated Demo, Import Structured Data (CSV/SMILES), or Upload Diagram Image
        ↓
2. Optional Gemini Vision Proposal (Physics, Biology, CS Flowchart; requires explicit consent)
        ↓
3. Deterministic Structural & Scientific Validation (Python)
        ↓
4. Human Review & Correction (labels, types, wires, arrow directions, branches)
        ↓
5. Two Equivalent Explorers: Text/Keyboard Guided Tour + Interactive SVG (aria-hidden)
        ↓
6. Deterministic Experiments, Guided Learning Lab & Evidence-Grounded STEM Tutor
```

---

## 3. Supported Domains & Honest Scientific Boundaries

Core P0 hackathon domains (`physics_circuit`, `biology_food_web`) are always enabled. Post-hackathon domain expansions (`cs_flowchart`, `math_plot`, `chemistry_molecule`) can be toggled via `ENABLE_EXPERIMENTAL_DOMAINS` (`true` by default; set `false` for P0-only mode).

| Domain | Input Modes | Deterministic Engine Responsibility | Strict Scientific Boundary |
|---|---|---|---|
| **Physics P0 (`physics_circuit`)** | Pre-annotated fixture; optional Gemini Vision upload + human review | Single-loop series circuit (1 battery, 1 switch, 1–2 bulbs); derives `loop_wired` from edges; qualitative bulb ON/OFF toggle | Rejects unknown symbols (`422`) rather than coercing to bulbs; no voltage, current, resistance, or parallel circuits |
| **Biology P0 (`biology_food_web`)** | Pre-annotated fixture; optional Gemini Vision upload + human review | Directed `food/prey -> consumer/predator` energy flow; neighbor/path queries; organism removal reporting exact disappeared & remaining edges | Graph relationship changes only; explicitly disclaims extinction or population predictions |
| **CS Flowchart (`cs_flowchart`, experimental)** | Pre-annotated fixture; optional Gemini Vision upload + human review | Safe recursive-descent expression parser (zero `eval`/`exec`); integer/boolean assignments, True/False decisions, bounded step trace (`<= 200` steps, `0.5s` timeout) | Restricted integer/boolean grammar only; halts infinite loops safely |
| **Mathematics (`math_plot`, experimental)** | Pre-annotated fixture; **CSV structured data import** (not image-to-graph recognition) | Finite unique-`x` XY plots; global/local extrema, monotonic intervals, average rates of change, exact vs interpolated intercepts; optional volume-limited Web Audio sonification | Strictly finite given dataset; never extrapolates or invents asymptotes |
| **Chemistry (`chemistry_molecule`, experimental)** | Pre-annotated fixture; **SMILES structured input** (not image-to-graph recognition) | Pure-Python beginner SMILES parser & covalent valence validator (`H, C, N, O, F, Cl, Br, S, P`); single/double/triple bonds, atom counts, bond paths | Rejects aromaticity, stereochemistry, ionic charges, duplicate bonds, and invalid valence; never infers toxicity, yields, or lab safety |

### What AI Does vs. Deterministic Python Engines
- **Gemini Vision (`app/services/ai_vision.py`):** Proposes tentative `unreviewed` graphs for Physics, Biology, and CS Flowchart images only when configured with `GEMINI_API_KEY` and explicit user consent. Treated strictly as untrusted; never auto-confirmed; embedded text is treated strictly as data.
- **Evidence-Grounded STEM Tutor (`app/services/tutor.py`):** Answers questions strictly by calling 6 deterministic graph tools (`get_neighbors`, `shortest_path`, `component_state`, `energy_flow`, `run_verified_simulation`, `get_learning_feedback`), citing exact node/edge IDs, and abstaining with `"Not established by this diagram."` for out-of-scope or adversarial prompts.

---

## 4. Architecture & Project Structure

```text
SenseGraph/
  app/
    main.py                 # FastAPI app, REST API, rate limiting, same-origin static UI
    models.py               # Pydantic v2 models matching contracts/diagram.schema.json
    settings.py             # Environment settings & feature flags (server-only secrets)
    domains/
      physics.py            # Qualitative single-loop series circuit engine
      biology.py            # Directed food-web relationship engine
      flowchart.py          # Safe restricted CS flowchart interpreter (no eval/exec)
      mathematics.py        # Finite XY plot analysis & CSV importer
      chemistry.py          # Pure-Python beginner SMILES parser & valence validator
    services/
      validators.py         # Structural (valid) vs domain (simulation_ready) checks
      fixtures.py           # Bundled pre-annotated demo loader (deep-copied)
      description.py        # Deterministic plain-language diagram & node summaries
      ai_vision.py          # VisionProvider abstraction, Pillow security, GeminiVisionProvider
      learning.py           # Deterministic Guided Learning Lab across all 5 domains
      tutor.py              # Evidence-Grounded STEM Tutor (6 tools + abstention guard)
    static/
      index.html            # Semantic HTML5 UI (Welcome, Review, Explorer, Lab, Tour, Tutor)
      styles.css            # High-contrast responsive CSS ([hidden], focus, reduced-motion)
      app.js                # Vanilla JS client, focus management, SVG graphs, optional TTS/sonification
  contracts/
    diagram.schema.json     # Authoritative JSON Schema (Draft 2020-12)
  evaluation/
    dataset_manifest.json   # Curated original-asset benchmark manifest
    benchmark.py            # Repeatable precision/recall harness (dry-run & live modes)
  fixtures/                 # 5 curated pre-annotated JSON fixtures + 2 original PNGs
  tests/                    # 82 automated unit & integration tests across 9 test files
  docs/                     # Product/technical specs, decisions, user-study protocol, evidence matrix
  submission/               # STEM2Connect Devpost copy, demo script, shot list, checklist
  .github/workflows/ci.yml  # GitHub Actions CI (Python 3.11 & 3.13: ruff + pytest + dry-run)
```

---

## 5. Setup & Running Locally (Windows PowerShell)

### Mode A — Pre-Annotated Demo & Structured-Input Mode (No API Key Required)

```powershell
cd D:\AI-tools\Project\SenseGraph
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload
```

Open **`http://127.0.0.1:8000`** in your browser (`http://127.0.0.1:8000/docs` for OpenAPI, `http://127.0.0.1:8000/api/health` for health).

### Mode B — Live Gemini Vision Mode (Optional, Local `.env`)

1. Edit your local `.env` (excluded from git via `.gitignore`):
   ```dotenv
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   AI_TIMEOUT_SECONDS=30
   MAX_UPLOAD_MB=5
   ENABLE_EXPERIMENTAL_DOMAINS=true
   ANALYZE_RATE_LIMIT_PER_MIN=20
   ```
2. Restart `uvicorn`. The header badge updates to **Gemini Vision configured**.
3. Upload a PNG, JPEG, or WEBP diagram (<= 5 MB, <= 4096×4096 / 16 MP), check the explicit external-provider consent box, review and validate the AI proposal, then confirm to open the Explorer.
4. **Privacy boundary:** Uploaded images are processed in memory only, never persisted on disk, and never logged. Never upload personal or sensitive content.

---

## 6. Verification Results & Honest Limitations

### Automated Verification
```powershell
python -m ruff check app tests evaluation
python -m pytest -v
python -m evaluation.benchmark --mode dry-run
```
- **Observed results:**
  - **Pytest:** **82 passed** (`0 failed`, `0 warnings`) across 9 test modules (`test_models`, `test_physics`, `test_biology`, `test_api`, `test_ai_vision`, `test_learning`, `test_flowchart`, `test_mathematics`, `test_chemistry`, `test_tutor`, `test_evaluation_and_prod`).
  - **Ruff:** **All checks passed** (including `SIM102` fix in `app/domains/flowchart.py`).
  - **Benchmark dry-run:** All 6 manifest cases validated (`status: "not_tested"` for live AI).
  - **Grounded Tutor scripted test set (`tests/test_tutor.py`):** 7/7 in-scope questions answered with verified citations; 6/6 out-of-scope/adversarial questions abstained with `"Not established by this diagram."`.

### Honest Limitations & What Has Not Been Verified Yet
- **Live Gemini Vision smoke test:** **Not executed** in this environment because no local `GEMINI_API_KEY` was configured (`AI_PROVIDER=none`). Automated AI tests use mocked `VisionProvider` instances only. See [docs/EXTRACTION_EVALUATION.md](docs/EXTRACTION_EVALUATION.md).
- **Live browser & screen-reader audit:** Live Chrome browser automation (DevTools port unavailable), NVDA, JAWS, VoiceOver sessions, and blind-learner user studies have **not** been executed yet. No WCAG compliance certification or demonstrated learning outcome is claimed. See [docs/EVIDENCE_MATRIX.md](docs/EVIDENCE_MATRIX.md) and [docs/USER_STUDY_PROTOCOL.md](docs/USER_STUDY_PROTOCOL.md).
- **Structured-data domains:** Mathematics (`math_plot`) and Chemistry (`chemistry_molecule`) use validated CSV and SMILES inputs rather than image-to-graph recognition.

---

## 7. Key Documentation & Submission Assets

- Evidence matrix (`implemented` vs `tested` vs `verified with users` vs `planned`): [docs/EVIDENCE_MATRIX.md](docs/EVIDENCE_MATRIX.md)
- Release notes: [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md)
- Architecture decisions (`D1`–`D20`): [docs/DECISIONS.md](docs/DECISIONS.md)
- Ethical user-study protocol: [docs/USER_STUDY_PROTOCOL.md](docs/USER_STUDY_PROTOCOL.md)
- Extraction evaluation & manual QA checklist: [docs/EXTRACTION_EVALUATION.md](docs/EXTRACTION_EVALUATION.md)
- Submission pack: [submission/DEVPOST_DESCRIPTION.md](submission/DEVPOST_DESCRIPTION.md), [submission/DEMO_SCRIPT_EN.md](submission/DEMO_SCRIPT_EN.md), [submission/DEMO_SHOT_LIST.md](submission/DEMO_SHOT_LIST.md), [submission/JUDGING_ALIGNMENT.md](submission/JUDGING_ALIGNMENT.md), [submission/SUBMISSION_CHECKLIST_VI.md](submission/SUBMISSION_CHECKLIST_VI.md)

---

## 8. Attribution & AI Coding Assistance Disclosure

- **AI coding assistance:** Built with AI coding assistance (Google Antigravity / Gemini models) following the project specifications in `docs/` and `AGENTS.md`.
- **External AI SDK:** Official Google `google-genai` Python SDK (`GeminiVisionProvider`).
- **Original assets:** Bundled fixtures (`fixtures/*.json`) and sample images (`fixtures/images/*.png`) are original project assets. `.env` and credentials are excluded via `.gitignore` and verified absent from git.
