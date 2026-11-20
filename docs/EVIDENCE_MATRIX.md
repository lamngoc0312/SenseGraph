# SenseGraph — Final Evidence Matrix

**Last verified:** 2026-11-20 (`v1.0.0-rc2`, 82 automated tests passing, Ruff clean)  
**Strict Honesty Policy:** Automated unit/integration tests verify code invariants, NOT live Gemini recognition accuracy, WCAG certification, or blind-user educational efficacy.

| Capability / Area | Status | Automated Tests | Live Browser / User Verification | Planned / Next |
|---|---|---|---|---|
| **Physics P0 (`physics_circuit`)** — single-loop series circuit, ring derivation, toggle & reset | Implemented (Core P0) | Yes (`tests/test_physics.py`, `test_models.py`, `test_api.py`) | Manual browser & NVDA/VoiceOver `not tested` | Live keyboard & AT audit |
| **Biology P0 (`biology_food_web`)** — directed `food -> consumer`, paths, removal & reset | Implemented (Core P0) | Yes (`tests/test_biology.py`, `test_models.py`, `test_api.py`) | Manual browser & NVDA/VoiceOver `not tested` | Live keyboard & AT audit |
| **Gemini Vision Extraction (`POST /api/analyze`)** — Physics, Biology, CS Flowchart (`google-genai`, Pillow security, consent, 422 unknown-symbol rejection) | Implemented | Yes, mocked provider (`tests/test_ai_vision.py`, `test_flowchart.py`) | Live Gemini API `not tested` (no local key) | Run `evaluation/benchmark.py --mode live` with key |
| **Human Review & Correction UI** — edit labels/types/edges, swap arrows, validate & confirm | Implemented | Yes, API & markup (`tests/test_ai_vision.py`) | Live browser `not tested` | Live upload-to-confirm walkthrough |
| **Guided Learning Lab (`Predict → Experiment → Explain`)** — all 5 domains | Implemented | Yes (`tests/test_learning.py` + domain tests) | Live browser & users `not tested` | Educator review of explanations |
| **Two Equivalent Explorers** — domain-accurate Text Guided Tour + optional TTS + `aria-hidden` SVG graphs for all 5 domains | Implemented | Yes, markup & CSS (`tests/test_api.py`) | Live browser & NVDA/VoiceOver `not tested` | 200% zoom & AT audit |
| **CS Flowchart Explorer (`cs_flowchart`)** — safe parser (no `eval`), bounded steps, trace stepper | Implemented (Experimental, feature-flaggable) | Yes (`tests/test_flowchart.py`) | Live browser `not tested` | Original flowchart image benchmark |
| **Mathematics XY Plot Explorer (`math_plot`)** — extrema, intervals, intercepts, **CSV import UI & API**, optional sonification (structured data, not vision) | Implemented (Experimental, feature-flaggable) | Yes (`tests/test_mathematics.py`) | Live browser `not tested` | Multi-series plot comparison |
| **Chemistry Molecule Explorer (`chemistry_molecule`)** — pure-Python beginner **SMILES parser & valence validator** (structured data, not vision) | Implemented (Experimental, feature-flaggable) | Yes (`tests/test_chemistry.py`) | Live browser `not tested` | Optional RDKit extension |
| **Evidence-Grounded STEM Tutor (`POST /api/tutor/ask`)** — 6 tools, citations, abstention guard | Implemented | Yes (`tests/test_tutor.py`: 7/7 grounded, 6/6 abstained) | Live browser & users `not tested` | Expanded adversarial question set |
| **Production Readiness & CI** — GitHub Actions (Py 3.11 & 3.13), Ruff clean (`SIM102` fixed), rate limiting, feature flags, privacy telemetry | Implemented | Yes (`tests/test_evaluation_and_prod.py`) | Push pending user approval to verify CI green on GitHub | Public cloud deployment (optional) |
