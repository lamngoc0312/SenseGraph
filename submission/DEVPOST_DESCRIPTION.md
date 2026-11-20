# SenseGraph — Devpost Submission Description

**Project Title:** SenseGraph — Explore STEM Beyond Sight  
**Tagline:** Making STEM Diagrams Accessible, Interactive, and Understandable  
**Primary Track:** Education  
**Related Impact:** Community Impact  
**Repository:** https://github.com/lamngoc0312/SenseGraph  

---

## Inspiration

In physics and biology classrooms, critical ideas live inside diagrams—how a switch completes a series loop, or how energy flows along directed arrows in a food web. For blind and visually impaired students, a static image or a short one-sentence alt-text caption is not enough to independently explore connections, trace paths, or test "what if" questions.

We wanted to build a focused, honest prototype that solves one concrete educational barrier: converting structured STEM diagrams into a **human-reviewable semantic graph** that learners can navigate entirely by keyboard and test with **deterministic, scientifically grounded simulations**.

---

## What It Does

SenseGraph follows a transparent six-step learning pipeline:

1. **Choose a Verified Demo or Upload an Image:** Learners can immediately explore two curated pre-annotated diagrams (**Basic Series Circuit** and **Grassland Food Web**, clearly badged *"Pre-annotated demo — no AI used"*), or—when configured with a Gemini API key—upload a PNG, JPEG, or WEBP diagram with explicit consent.
2. **AI Image-to-Graph Proposal (Gemini Vision):** Using Google's `google-genai` SDK, `GeminiVisionProvider` extracts tentative components, connections, warnings, and domain structure into an `unreviewed` `DiagramDocument`.
3. **Deterministic Validation:** A Python validator checks schema shape, unique IDs, valid endpoints, domain rules, and single-loop wire connectivity—strictly rejecting unsupported physics symbols (such as resistors) rather than guessing.
4. **Accessible Human Review & Correction:** Before any AI-generated diagram can be simulated, users inspect warnings/errors, edit labels/types/connections, swap inverted biology arrows, verify circuit order, and explicitly confirm the graph.
5. **Two Equivalent Explorers:**
   - **Text & Keyboard Explorer + Guided Tour:** Structured component lists, direct neighbor navigation buttons, complete plain-text relationship lists, polite live announcements (`role="status"` / `aria-live="polite"`), and optional user-initiated browser voice (`speechSynthesis`, off by default).
   - **Interactive Semantic Graph (SVG):** A clean, synchronized visual graph for sighted teachers/peers marked `aria-hidden="true"` so it never creates duplicate keyboard tab stops.
6. **Deterministic Experiments & Guided Learning Lab (`Predict → Experiment → Explain`):**
   - **Physics Explorer:** Toggle Switch S1 via the Python physics engine to observe verified qualitative bulb ON/OFF outcomes and loop continuity explanations (no fabricated voltage/current claims).
   - **Biology Explorer:** Remove an organism to see exact disappeared and remaining feeding relationships, with an explicit note that removal does not predict extinction or population changes.
   - **Guided Learning Lab:** Learners predict outcomes with native radio/checkbox controls, run the backend engine, and compare their prediction against verifiable graph evidence.

---

## How We Built It

- **Backend:** Python 3.13, FastAPI, Pydantic v2, Pillow (image byte/dimension/MIME security validation), and the official `google-genai` SDK behind a replaceable `VisionProvider` interface.
- **Deterministic Domain Engines:** Pure Python modules (`app/domains/physics.py`, `app/domains/biology.py`, `app/services/learning.py`) separated completely from AI extraction and frontend rendering.
- **Frontend:** Semantic HTML5, high-contrast responsive CSS, and vanilla JavaScript served from the same FastAPI origin (no heavy frontend bundler required). All untrusted strings are rendered safely with `textContent`.
- **Testing:** 54 automated unit and integration tests (`pytest`) covering JSON Schema validation, Physics/Biology invariants, upload security (MIME mismatch, corrupt bytes, >5 MB, decompression-bomb pixel cap), mocked Gemini flows, and Learning Lab grading.

---

## Challenges We Ran Into

- **Preventing AI hallucinations from becoming "science":** Early normalization coerced unknown physics symbols to bulbs. We replaced this with a strict rejection policy (`422 AI_EXTRACTION_INVALID`) so unsupported components can never silently pass confirmation.
- **CSS `[hidden]` vs. layout display rules:** Flex/grid utility classes overrode the native HTML `hidden` attribute. Adding an explicit `[hidden] { display: none !important; }` rule ensured hidden panels stay completely out of view and keyboard tab order.
- **Keyboard focus preservation:** Re-rendering component lists and experiment buttons risked dropping focus. We engineered deliberate focus restoration across component selection, neighbor jumps, switch toggles, organism removals, resets, and AI confirmation.
- **No frontend science guessing:** Initially, initial bulb state was inferred from summary prose. We added `POST /api/state` so every displayed switch and bulb state comes directly from the Python physics engine.

---

## Accomplishments That We're Proud Of

- A clean separation of **untrusted AI extraction**, **deterministic Python validation/simulation**, and **accessible keyboard-first UI**.
- 54 passing automated tests with 0 warnings and 0 lint errors.
- Two genuinely equivalent exploration experiences (text-first Guided Tour + synchronized SVG semantic graph) plus a deterministic **Predict → Experiment → Explain** Learning Lab.
- Honest provenance badges distinguishing pre-annotated demos from AI-generated unreviewed proposals and confirmed diagrams.

---

## What We Learned

- Accessibility cannot be bolted on at the end—native `<button>`, `<fieldset>`, `<legend>`, skip links, live regions, and careful focus restoration make keyboard operation predictable and calm.
- Narrow, verifiable scientific scope (single-loop series circuits and directed food-web relationships) produces far more trustworthy educational feedback than unconstrained LLM chat.

---

## Honest Limitations & AI Disclosure

- **AI Assistance:** This project was built during the hackathon with AI coding assistance (Google Antigravity / Gemini models) and integrates Google's `google-genai` SDK for optional live diagram extraction.
- **Live AI & Assistive Tech Status:** All 54 automated tests pass using mocked vision providers; live Gemini extraction against local keys and formal NVDA/VoiceOver sessions with blind learners are documented as manual verification steps and future work—no WCAG compliance or unmeasured accuracy percentages are claimed.
- **Domain Boundaries:** Physics covers qualitative single-loop series circuits only; Biology covers directed graph relationship changes only.

---

## What's Next

- Live multi-image Gemini extraction benchmarking (logged in `docs/EXTRACTION_EVALUATION.md`).
- Manual testing with NVDA, VoiceOver, and blind/visually impaired students and educators.
- Computer Science Flowchart Explorer (P2) using a strict safe expression whitelist.
