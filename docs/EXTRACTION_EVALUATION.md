# SenseGraph — Vision Extraction Evaluation & Manual QA Checklist

**Last updated:** 2026-11-20  
**Local Gemini API key status during Phase 04 audit:** Not configured (`AI_PROVIDER=none`, no `.env` file).

> **Honesty notice:** Automated tests in `tests/test_ai_vision.py` use mocked `VisionProvider` responses to verify validation, error mapping, security bounds, and review workflows. Mocked test results are **not** evidence of live Gemini vision recognition accuracy. All live extraction cases below are accurately marked `not tested` until executed with a real local `GEMINI_API_KEY`.

---

## 1. Live Vision Extraction Evaluation Log

Evaluation convention:
- **Physics (`physics_circuit`):** Undirected wire pairs; 1 battery, 1 switch, 1–2 bulbs in one series ring.
- **Biology (`biology_food_web`):** Directed `energy_to` edges strictly from `food/prey -> consumer/predator`.

| Case ID | Source Image | Domain | Expected Nodes | Expected Edges | Actual AI Proposal | Review Corrections Required | Outcome | Failure / Observation Notes |
|---|---|---|---|---|---|---|---|---|
| EVAL-P1 | `fixtures/images/physics_series.png` | `physics_circuit` | `battery_1` (Battery B1), `switch_1` (Switch S1), `bulb_1` (Bulb L1) | `battery_1–switch_1`, `switch_1–bulb_1`, `bulb_1–battery_1` (switch open) | `not tested` | `not tested` | `not tested` | No local `GEMINI_API_KEY` configured |
| EVAL-B1 | `fixtures/images/biology_food_web.png` | `biology_food_web` | `grass`, `rabbit`, `mouse`, `fox`, `owl` | `grass->rabbit`, `grass->mouse`, `rabbit->fox`, `mouse->owl` | `not tested` | `not tested` | `not tested` | No local `GEMINI_API_KEY` configured |
| EVAL-P2 | Original 2-bulb series circuit (to be added) | `physics_circuit` | 1 battery, 1 switch, 2 bulbs | 4 wires forming 1 ring | `not tested` | `not tested` | `not tested` | Pending live key and test image |
| EVAL-P3 | Unsupported parallel / resistor circuit (negative test) | `physics_circuit` | Unsupported symbol / parallel branch | Non-series topology | `not tested` | Expected rejection or blocked confirmation | `not tested` | Pending live key and test image |

---

## 2. Manual QA & Keyboard Accessibility Checklist

Run locally with `python -m uvicorn app.main:app --reload` and open `http://127.0.0.1:8000`.

| # | Check | Expected Result | Status |
|---|---|---|---|
| 1 | Section visibility (`[hidden]` CSS rule) | On initial load, only Welcome is visible; Error banner, Review section, and Explorer section are completely hidden and not in Tab order. | Automated CSS check passed; live Chrome check `not tested` (Chrome DevTools port unavailable) |
| 2 | Skip-to-content link | Pressing `Tab` on load reveals "Skip to main content" with high-contrast focus ring; pressing `Enter` moves focus to `<main>`. | `not tested` in live browser |
| 3 | Physics fixture walkthrough (keyboard-only) | Load Physics Circuit -> Tab through Battery B1, Switch S1, Bulb L1 -> focus stays on selected component -> Close Switch S1 -> focus stays on toggle button, Bulb L1 updates to ON via `/api/state` -> Reset Experiment -> Bulb L1 returns to OFF. | Backend & API verified by `pytest`; live Chrome walkthrough `not tested` |
| 4 | Biology fixture walkthrough (keyboard-only) | Load Biology Food Web -> Select Rabbit -> Inspect incoming (Grass) and outgoing (Fox) -> Jump to neighbor -> Remove Rabbit -> exact 2 removed edges + non-prediction disclaimer shown -> Reset restores 5 organisms and 4 edges. | Backend & API verified by `pytest`; live Chrome walkthrough `not tested` |
| 5 | Upload error recovery (no key / bad file) | Submitting upload without key returns `503` alert; dismissing error restores focus to active heading; pre-annotated examples remain usable. | Backend & API verified by `pytest`; live Chrome walkthrough `not tested` |
| 6 | Live Gemini upload -> review -> confirm -> simulate | With local `.env`, upload `physics_series.png`, review warnings, validate, confirm, and toggle switch in Explorer. | `not tested` (no local API key) |
| 7 | Assistive technology check (NVDA / VoiceOver) | Verify announcements in `role="status"` and heading/landmark navigation with a real screen reader. | `not tested` |
