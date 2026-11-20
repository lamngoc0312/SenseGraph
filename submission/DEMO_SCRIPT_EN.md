# SenseGraph — Final Demo Video Script (Target: ~5:15, Strictly Under 6 Minutes)

**Format:** Live screen recording of the running local web app (`http://127.0.0.1:8000`) with clear voiceover. Show the real working application—not slides-only.  
**Honesty Rule:** Never claim a real Gemini image was analyzed unless you configured a local `GEMINI_API_KEY` and successfully ran it live. Otherwise use Branch B and clearly disclose that live Gemini extraction is implemented and tested with mocked providers.

---

## 0:00 – 0:35 | 1. The Accessibility Problem & Image-to-Semantic-Graph Approach
**[Screen: SenseGraph Homepage (`http://127.0.0.1:8000`)]**
> "Hi, I'm presenting **SenseGraph** — an accessible interactive STEM diagram learning platform for blind and visually impaired students.
>
> In physics, biology, and computer science, key knowledge lives inside wires, arrows, and branches. A static alt-text caption tells you *what* a diagram is, but it doesn't let a student independently explore connections or run experiments.
>
> SenseGraph converts supported STEM diagrams into a **human-reviewable semantic graph** backed by deterministic Python engines—never relying on an unchecked chatbot to invent science."

---

## 0:35 – 1:10 | 2. Keyboard Exploration & Honest Mode Separation
**[Screen: Press `Tab` from top of page to reveal the "Skip to main content" link; tab across the module cards and Analyze form]**
> "Every control uses semantic HTML, native buttons, high-contrast focus indicators, and polite `aria-live` status updates—no mouse required, and voice output is completely optional.
>
> Notice our honest provenance labels: bundled examples are clearly marked **Pre-annotated demo — no AI used**. Below them, **Analyze Your Own Diagram** connects to Google Gemini Vision for Physics, Biology, and Flowchart images only when configured with an API key and explicit user consent—and every AI proposal requires human validation and confirmation before simulation."

---

## 1:10 – 2:20 | 3. Physics: Predict → Experiment → Explain
**[Screen: Press `Enter` on "Explore Example Circuit"; step through Guided Tour; open Guided Learning Lab]**
> "Let's open the **Basic Series Circuit** using only the keyboard.
>
> We see the diagram overview, explicit backend-calculated stats—Switch S1 Open, Bulb L1 OFF—our text-first **Guided Tour**, and a synchronized **Interactive Semantic Graph** marked `aria-hidden` so sighted teachers get a visual view without adding duplicate screen-reader tab stops.
>
> Switching to **Guided Learning Lab**, SenseGraph asks the learner to predict what happens when Switch S1 closes *before* running the experiment. I select **Bulb L1 will be ON** and submit. The Python physics engine toggles Switch S1, updates Bulb L1 to ON across both text and SVG views, and explains why using verified single-loop connectivity—without inventing voltage or current. Clicking **Reset Experiment** cleanly restores the baseline."

---

## 2:20 – 3:15 | 4. Biology: Directed Food Web Graph Interaction
**[Screen: Activate "Load Biology Food Web"; select Rabbit; click "Remove Rabbit"; click "Reset Experiment"]**
> "Next, let's load the **Grassland Food Web**. SenseGraph states the arrow convention upfront: every arrow points from **food or prey to consumer or predator**.
>
> Selecting **Rabbit** shows that it receives energy from Grass and provides energy to Fox, with direct neighbor jump buttons.
>
> When I click **Remove Rabbit**, the Python biology engine removes Rabbit and *only* its two incident links—Grass to Rabbit and Rabbit to Fox—while leaving Grass to Mouse and Mouse to Owl untouched. Importantly, SenseGraph explicitly notes that this shows graph relationship changes only and does **not** predict extinction or population changes. **Reset Experiment** restores all five organisms."

---

## 3:15 – 4:10 | 5. Evidence-Grounded STEM Tutor (Citations & Honest Abstention)
**[Screen: Scroll to "Evidence-Grounded STEM Tutor" panel under Biology or Physics]**
> "Instead of a generic chatbot, SenseGraph includes an **Evidence-Grounded STEM Tutor** backed by six deterministic graph tools.
>
> If I ask: *'Is there a path from Grass to Fox?'*, the tutor calls `shortest_path` and cites the exact nodes and edge IDs: `grass -> rabbit -> fox`.
>
> Now watch an adversarial question: *'Will Fox go extinct if Rabbit is removed?'* Instead of hallucinating, the tutor abstains honestly: **'Not established by this diagram.'** and offers a clarifying follow-up."

---

## 4:10 – 4:50 | 6. Post-Hackathon Expansion: CS Flowchart Explorer
**[Screen: Activate "Load CS Flowchart"; click "Run Trace"; press "Next step" twice]**
> "Beyond our two core P0 hackathon modules, we built feature-flaggable expansions including a **Computer Science Flowchart Explorer** with a safe restricted expression parser—zero `eval` or `exec`—and bounded step limits so infinite loops halt safely. Users can enter an initial value for `n`, run a trace, and step forward or backward through every assignment, True/False branch, and live variable state."

---

## 4:50 – 5:25 | 7. Live AI Status, Automated Tests & Honest Limitations
**[Screen: Terminal showing `python -m pytest -v` (82 passed) and `python -m ruff check app tests evaluation` (All checks passed)]**
> *(Branch A — if you ran a real Gemini API key live before recording: show a 20-second clip of uploading `physics_series.png` → Review AI-Generated Diagram → Validate → Confirm.)*
>
> *(Branch B — if recording without a local Gemini API key:)*
> "Our entire backend, upload security, mocked Gemini Vision review workflow, Guided Learning Lab, and Grounded Tutor are verified by **82 passing automated tests** and GitHub Actions CI.
>
> We're candid about what comes next: live Gemini extraction benchmarking with an API key, plus formal NVDA, VoiceOver, and blind-student usability studies following our ethical protocol. Thank you for watching SenseGraph!"
