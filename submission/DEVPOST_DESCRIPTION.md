# SenseGraph — Devpost Submission Description

**Project Title:** SenseGraph — Explore STEM Beyond Sight  
**Tagline:** Making STEM Diagrams Accessible, Interactive, and Understandable  
**Primary Track:** Education  
**Related Impact:** Community Impact  
**Repository:** https://github.com/lamngoc0312/SenseGraph  

---

## Inspiration

In STEM classrooms, essential concepts live inside diagrams—how a switch completes a series circuit, how energy flows along directed arrows in a food web, how a loop branches in a flowchart, or how a function rises to a maximum. For blind and visually impaired students, a static image or a one-sentence alt-text caption is not enough to independently inspect relationships or run "what if" experiments.

We built **SenseGraph** to solve one concrete, testable educational barrier: turning structured STEM diagrams into a **human-reviewable semantic graph** that learners can explore entirely by keyboard and test with **deterministic, scientifically verifiable Python engines**.

---

## What It Does

SenseGraph implements a transparent six-step learning pipeline across two core P0 hackathon domains (**Physics Series Circuits** and **Biology Food Webs**) plus three feature-flaggable experimental domains (**Computer Science Flowcharts**, **Mathematics XY Plots**, and **Chemistry Molecular Structures**):

1. **Choose a Curated Demo, Import Structured Data, or Upload an Image:** Learners immediately explore curated pre-annotated diagrams clearly badged *"Pre-annotated demo — no AI used"*, import CSV plots or beginner SMILES molecules, or—when configured with a local Gemini API key—upload PNG/JPEG/WEBP diagrams for Physics, Biology, or CS Flowcharts with explicit consent.
2. **AI Image-to-Graph Proposal (Google Gemini):** Using the official `google-genai` SDK, `GeminiVisionProvider` extracts tentative nodes, edges, warnings, and domain structure into an `unreviewed` `DiagramDocument`.
3. **Deterministic Validation:** Python validators check schema shape (`contracts/diagram.schema.json`), unique IDs, valid endpoints, domain rules, and series-ring topology—strictly rejecting unsupported physics symbols (`422`) rather than guessing.
4. **Accessible Human Review & Correction:** Before any AI-generated diagram can be simulated, users inspect warnings/errors, edit labels/types/connections, swap inverted biology arrows, verify circuit order or branch labels, and explicitly confirm the graph.
5. **Two Equivalent Explorers:**
   - **Text & Keyboard Explorer + Guided Tour:** Structured component lists, direct neighbor jump buttons, complete plain-text relationship lists, polite live announcements (`role="status"` / `aria-live="polite"`), and optional user-initiated browser voice (`speechSynthesis`, off by default).
   - **Interactive Semantic Graph (SVG):** A clean, synchronized visual graph for sighted teachers/peers marked `aria-hidden="true"` so it never adds duplicate keyboard tab stops.
6. **Deterministic Experiments, Guided Learning Lab & Evidence-Grounded Tutor:**
   - **Physics & Biology Explorers:** Toggle Switch S1 for qualitative ON/OFF circuit outcomes, or remove an organism to see exact disappeared and remaining feeding relationships (explicitly disclaiming extinction/population predictions).
   - **Experimental Modules:** Step forward/backward through safe, bounded CS flowcharts (zero `eval`/`exec`); explore finite XY math plots point-by-point with interval analysis, CSV import, and optional volume-limited sonification; inspect beginner covalent molecules from validated SMILES.
   - **Guided Learning Lab (`Predict → Experiment → Explain`):** Native radio/checkbox prediction challenges graded strictly by the Python engines.
   - **Evidence-Grounded STEM Tutor:** Answers questions exclusively through 6 deterministic graph query tools with exact node/edge citations, and honestly abstains (`"Not established by this diagram."`) on out-of-scope or adversarial prompts.

---

## How We Built It

- **Backend:** Python 3.11–3.13, FastAPI, Pydantic v2, Pillow (MIME match, 5 MB limit, and 16 MP decompression-bomb guard), and `google-genai` behind a replaceable `VisionProvider` interface, plus per-IP rate limiting and `ENABLE_EXPERIMENTAL_DOMAINS` feature flags.
- **Deterministic Engines:** Pure Python modules (`app/domains/physics.py`, `biology.py`, `flowchart.py`, `mathematics.py`, `chemistry.py`, `app/services/learning.py`, `tutor.py`) strictly separated from AI extraction and frontend rendering.
- **Frontend:** Semantic HTML5, high-contrast responsive CSS (`[hidden] { display: none !important; }`, `:focus-visible`, `prefers-reduced-motion`), and vanilla JavaScript served from the same FastAPI origin with XSS-safe `textContent` rendering.
- **Quality & CI:** **82 automated unit and integration tests** (`pytest`), Ruff lint checks, repeatable evaluation harness (`evaluation/benchmark.py`), and GitHub Actions CI across Python 3.11 and 3.13.

---

## Challenges We Ran Into

- **Preventing AI hallucinations from becoming "science":** Early normalization coerced unknown physics symbols to bulbs; we replaced this with strict `422` rejection so unsupported components can never pass confirmation.
- **CSS `[hidden]` & keyboard focus bugs:** Flex/grid display rules overrode the native `hidden` attribute, and re-rendering buttons risked dropping focus. We enforced `[hidden] { display: none !important; }` and built deliberate focus restoration across selection, neighbor jumps, simulations, resets, and confirmation.
- **Eliminating frontend science guessing:** Replaced prose-based bulb state parsing with an explicit `POST /api/state` backend endpoint.
- **Cross-domain UI consistency:** Caught and fixed broken non-image previews, domain-specific Guided Tour text, SVG layouts for all 5 domains, and Tutor keyword disambiguation (`"current state"` vs `"electric current"`).

---

## Honest Limitations & AI Disclosure

- **AI Coding Assistance:** Built with AI coding assistance (Google Antigravity / Gemini models) and integrates Google's `google-genai` SDK for optional live diagram extraction.
- **Implemented vs. Live-Verified Status:** All **82 automated tests** pass using mocked vision providers. Live Gemini API smoke testing against local credentials, live Chrome browser automation, NVDA/VoiceOver screen-reader audits, and blind-learner user studies have **not** been executed yet—no WCAG certification or unmeasured recognition accuracy is claimed.
- **Structured Input vs. Vision:** Mathematics (`math_plot`) and Chemistry (`chemistry_molecule`) use validated CSV and SMILES input workflows rather than image-to-graph recognition.

---

## What's Next

- Run `python -m evaluation.benchmark --mode live` with a configured Gemini API key across curated test images and publish empirical precision/recall metrics.
- Execute the ethical accessibility study protocol (`docs/USER_STUDY_PROTOCOL.md`) with NVDA, VoiceOver, and blind/visually impaired learners and educators.
