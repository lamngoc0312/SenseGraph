# Architecture Decisions & Open Risks

## Chosen decisions (2026-11-15)

- D1: **Simple web app**, no auth. Reasons: one solo developer and short hackathon deadline.
- D2: **Two P0 domains**, flowcharts a stretch goal. Reasons: demonstrated depth beats shallow support of many domains.
- D3: **Semantic graph + domain-specific payload**. Reasons: reuse accessible explorer while respecting different science semantics.
- D4: **Single-loop series physics** only. Reasons: honest deterministic simulation within deadline; electrical network analysis is much harder.
- D5: **Directed food web, food -> consumer** and relationship-change simulation only. Reasons: avoid fabricated population predictions.
- D6: **Native keyboard widgets first**, no custom graph keyboard shortcuts. Reasons: predictable browser + screen reader support.
- D7: **Explicit fixture vs live AI provenance**. Reasons: do not misrepresent the capability to judges or end users.
- D8: **Provider adapter** with Gemini as initial multimodal implementation. Reasons: swap if availability/pricing changes.
- D9 (Phase 1): **Fixture IDs use the exact `id` values in `fixtures/*.json`** (`physics_series`, `biology_food_web`) rather than hyphenated aliases, matching `contracts/diagram.schema.json` and the bundled JSON files directly.
- D10 (Phase 1): **`remove_organism` disallows removing the last remaining organism** (`400 INVALID_ACTION`) so that every `updated_diagram` returned by `/api/simulate` remains strictly valid against `contracts/diagram.schema.json` (`nodes.minItems >= 1`).
- D11 (Phase 3): **Added read-only `POST /api/state` endpoint** to expose explicit backend-calculated physics (`bulb_states`, `switch_states`, `loop_wired`, `bulbs_on`) and biology counts so the frontend never derives scientific state by parsing natural-language summaries.
- D12 (Phase 4): **Strict rejection of unknown/unsupported Physics component kinds (`422 AI_EXTRACTION_INVALID`)**. Unknown symbols (e.g., `resistor`, `capacitor`, `unknown`) are never coerced to `bulb`, preserving `contracts/diagram.schema.json` and preventing scientifically misleading confirmations.
- D13 (Phase 4): **Strict upload security bounds**: image pixel dimensions capped at `4096x4096` (16 MP) before full decode to prevent decompression bombs, and declared MIME types must match actual decoded image format (`415 MIME_MISMATCH`).
- D14 (Phase 5): **Guided Learning Lab (`/api/learning/challenges`, `/api/learning/evaluate`)** generates and evaluates all Physics and Biology challenges deterministically in Python using `evaluate_circuit_state`, `toggle_switch`, `get_organism_relations`, `get_energy_paths`, and `remove_organism`, with zero LLM grading and session-only browser progress (no auth/DB).
- D15 (Phase 6): **Supplementary SVG semantic graph uses `aria-hidden="true"` and `focusable="false"`** so sighted users get an interactive clickable graph without adding duplicate tab stops for keyboard/screen-reader users, who have 100% equivalent access through the native Component List, Relationships, and text-first Guided Tour. Optional `speechSynthesis` is strictly user-initiated and never autoplays.
- D16 (Phase 8): **Computer Science Flowchart Explorer (`cs_flowchart`)** uses an explicit recursive-descent expression parser (`app/domains/flowchart.py`, zero `eval`/`exec`) for integer/boolean assignments and comparisons, bounded to `max_steps <= 200` and `0.5s` wall-clock timeout to halt infinite loops safely. Schema (`contracts/diagram.schema.json`), Pydantic models, fixtures, Gemini normalization, Learning Lab, and tests were updated together.
- D17 (Phase 9): **Mathematics XY Plot Explorer (`math_plot`)** stores numeric series semantics in `MathPlotModel` (`x_label`, `x_unit`, `y_label`, `y_unit`, finite sorted unique-`x` points with explicit `exact` vs estimated flag). Extrema, monotonic intervals, and intercepts are computed strictly over the provided finite dataset; optional Web Audio sonification is volume-limited (`gain <= 0.12`), user-triggered, and paired with equivalent text.

## Open risks and mitigation

| Risk | Mitigation |
|---|---|
| AI mistakes a wire or food web arrow | Require human review, validation; block unsupported simulation |
| User has no API key / quota | Fixture mode remains useful, but accurately disclose lack of live extraction |
| Inconsistent AI structured output | Pydantic schema, constrained prompt, robust 422 error |
| Hard to test with blind students in one week | Test keyboard + available screen reader, disclose lack of formal user studies |
| Two domains delay final submission | Deliver physics slice first, then biology; stop feature work before video day |
| Public demo exposes private image | Prefer original/curated non-sensitive diagrams, no persistent upload/logging |
| Model is changed/deprecated | Configurable `GEMINI_MODEL`, documented provider errors |
