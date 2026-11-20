# SenseGraph — Demo Video Script (Target: ~5 Minutes, Strictly Under 6 Minutes)

**Format:** Live screen recording of the running local web app (`http://127.0.0.1:8000`) with clear voiceover. Show the real application—not slides-only.  
**Honesty Rule:** Clearly distinguish **Pre-annotated demo — no AI used** from **Live Gemini Vision** (show live upload ONLY if you have configured a real `GEMINI_API_KEY` in `.env` and tested it beforehand; otherwise honestly demonstrate the safe `503` no-key fallback and the mocked-test architecture).

---

## 0:00 – 0:35 | The Problem & Mission
**[Screen: SenseGraph Homepage (`http://127.0.0.1:8000`)]**
> "Hi, I'm presenting **SenseGraph** — an accessible STEM diagram learning platform for blind and visually impaired students.
>
> In physics and biology, key concepts live in wires, arrows, and connections. A short alt-text caption tells you *what* an image is, but it doesn't let you independently explore relationships or test what happens when something changes.
>
> SenseGraph turns supported STEM diagrams into a verifiable semantic graph that students can explore by keyboard and experiment with using deterministic Python engines."

---

## 0:35 – 1:10 | Accessibility & Honest Mode Separation
**[Screen: Press `Tab` on Homepage to reveal the "Skip to main content" link; tab to the two Pre-annotated Module cards]**
> "Every control in SenseGraph is built with semantic HTML, native buttons, high-contrast focus rings, and polite live-region announcements—no mouse required, and voice output is completely optional.
>
> Notice our honest provenance labels: the two bundled examples are clearly marked **Pre-annotated demo — no AI used**. Below them is **Analyze Your Own Diagram**, which calls Google Gemini Vision only when an API key is configured and the user gives explicit consent."

---

## 1:10 – 2:30 | Physics Explorer + Guided Learning Lab (Keyboard-Only)
**[Screen: Press `Enter` on "Explore Example Circuit"]**
> "Let's open the **Basic Series Circuit** using only the keyboard.
>
> At the top, we see the diagram overview, backend-calculated stats—Switch S1 is Open, Bulb L1 is OFF—a text-first **Guided Tour**, and a synchronized **Interactive Semantic Graph** for sighted teachers that is hidden from screen-reader tab order so it never creates duplicate stops.
>
> Let's step through **Next component** and **Connections** in the Guided Tour to hear how Battery B1, Switch S1, and Bulb L1 form one closed wire loop.
>
> Now let's switch to **Guided Learning Lab** — our **Predict → Experiment → Explain** mode."

**[Screen: Activate "Guided Learning Lab", select radio option "Bulb L1 will be ON", press "Submit Prediction & Run Experiment"]**
> "Before touching the circuit, the student predicts what happens when Switch S1 closes. When I submit, SenseGraph calls our deterministic Python physics engine—never guessing in JavaScript or asking an LLM. Switch S1 closes, Bulb L1 turns ON in both the text stats and the SVG graph, and the lab explains *why* using verified single-loop connectivity. Let's click **Reset Experiment** to restore the baseline."

---

## 2:30 – 3:40 | Biology Explorer: Directed Food Web
**[Screen: Activate "Load Biology Food Web"]**
> "Next, let's switch to the **Grassland Food Web**. Right away, SenseGraph states the arrow convention: every arrow points from **food or prey to consumer or predator**.
>
> Selecting **Rabbit** shows that it receives energy from Grass and provides energy to Fox, with direct neighbor jump buttons.
>
> Now let's run **Remove Rabbit**."

**[Screen: Activate "Remove Rabbit", show Feedback panel, updated SVG, and Reset Experiment]**
> "The Python biology engine removes Rabbit and *only* its two incident relationships—Grass to Rabbit and Rabbit to Fox—leaving Grass to Mouse and Mouse to Owl intact. Importantly, SenseGraph explicitly states that this shows graph relationship changes only and does **not** predict extinction or population changes. Clicking **Reset Experiment** restores all five organisms cleanly."

---

## 3:40 – 4:40 | AI Vision Extraction & Human Review
**[Branch A — If you configured a real `GEMINI_API_KEY` in `.env` before recording:]**
> "Now let's test **Analyze Your Own Diagram** with live Google Gemini Vision. I select Physics, upload `physics_series.png`, check the external-provider consent box, and click **Analyze with Gemini**.
>
> Notice the result is labeled **AI-generated — review required**—simulation is intentionally disabled! I can inspect warnings, edit labels or connections, click **Validate Diagram**, and once valid, click **Confirm & Open Explorer** to run the exact same deterministic simulation."

**[Branch B — If recording without a Gemini API key:]**
> "In **Analyze Your Own Diagram**, images are validated in memory with Pillow for format, 5 MB limit, MIME match, and pixel dimensions, and require explicit consent. Because no API key is active in this offline demo, submitting returns a clear, honest setup message instead of faking an AI result—while our 54 automated tests verify the complete upload, mocked Gemini extraction, unknown-symbol rejection, human review, and confirmation pipeline."

---

## 4:40 – 5:15 | Architecture, Testing & Honest Limitations
**[Screen: Quick terminal view of `python -m pytest -v` showing 54 passed]**
> "Under the hood, SenseGraph separates untrusted AI extraction from deterministic Python validation and simulation, backed by 54 passing automated tests.
>
> We're candid about our boundaries: Physics covers qualitative single-loop series circuits, Biology covers directed graph changes, and formal testing with NVDA, VoiceOver, and blind students is our next priority. Thank you for watching SenseGraph!"
