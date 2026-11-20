# SenseGraph — Final Evidence Matrix

**Strict Honesty Policy:** Automated unit/integration tests verify code invariants, NOT live Gemini recognition accuracy, WCAG certification, or blind-user educational efficacy.

| Capability / Area | Implemented | Automated Tests | Verified With Users | Planned / Next |
|---|---|---|---|---|
| **Physics P0 (`physics_circuit`)** — single-loop series circuit, ring derivation, toggle & reset | Yes | Yes (`tests/test_physics.py`, `test_models.py`, `test_api.py`) | No (`not tested`) | Multi-bulb visual polish |
| **Biology P0 (`biology_food_web`)** — directed `food -> consumer`, paths, removal & reset | Yes | Yes (`tests/test_biology.py`, `test_models.py`, `test_api.py`) | No (`not tested`) | Larger curated food webs |
| **Gemini Vision Extraction (`POST /api/analyze`)** — `google-genai`, Pillow security, consent, 422 unknown-symbol rejection | Yes | Yes, mocked provider (`tests/test_ai_vision.py`) | Live API `not tested` (no local key) | Run `evaluation/benchmark.py --mode live` with key |
| **Human Review & Correction UI** — edit labels/types/edges, swap arrows, validate & confirm | Yes | Yes, API & markup (`tests/test_ai_vision.py`) | No (`not tested`) | Live browser walkthrough |
| **Guided Learning Lab (`Predict → Experiment → Explain`)** — Physics, Biology, CS, Math, Chemistry | Yes | Yes (`tests/test_learning.py` + domain tests) | No (`not tested`) | Educator feedback on wording |
| **Two Equivalent Explorers** — Text Guided Tour + optional TTS + `aria-hidden` SVG graph | Yes | Yes, markup & CSS (`tests/test_api.py`) | No (`not tested`) | NVDA & VoiceOver audit |
| **CS Flowchart Explorer (`cs_flowchart`)** — safe parser (no `eval`), bounded steps, trace stepper | Yes (feature-flaggable) | Yes (`tests/test_flowchart.py`) | No (`not tested`) | Flowchart image benchmark |
| **Mathematics XY Plot Explorer (`math_plot`)** — extrema, intervals, intercepts, CSV, optional sonification | Yes (feature-flaggable) | Yes (`tests/test_mathematics.py`) | No (`not tested`) | Multi-series comparison |
| **Chemistry Molecule Explorer (`chemistry_molecule`)** — pure-Python beginner SMILES & valence checks | Yes (feature-flaggable) | Yes (`tests/test_chemistry.py`) | No (`not tested`) | Optional RDKit plugin if needed |
| **Evidence-Grounded STEM Tutor (`POST /api/tutor/ask`)** — 6 tools, citations, abstention guard | Yes | Yes (`tests/test_tutor.py`: 7/7 grounded, 6/6 abstained) | No (`not tested`) | Expanded adversarial question set |
| **Production Readiness** — CI workflow, rate limiting on `/api/analyze`, feature flags, privacy telemetry | Yes | Yes (`tests/test_evaluation_and_prod.py`) | N/A | Public cloud deployment (if authorized) |
