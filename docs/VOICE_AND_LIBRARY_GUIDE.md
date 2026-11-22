# SenseGraph 2.0 — Voice Interaction, Learning Library & Student UX Guide

This guide documents **Phases 15–17** of SenseGraph: Conversational Voice Learning, the 20-Lesson Validated STEM Learning Library, Educator Lesson Authoring, and the Calm Accessible Student Experience.

---

## 1. First-Time Learner Quick Start

1. Open SenseGraph (`http://127.0.0.1:8000`).
2. **Choose how you want to listen:**
   - **Using NVDA or VoiceOver?** Click **Start with Screen Reader** (keeps browser voice off so there is no duplicate speech).
   - **No screen reader?** Click **Start Spoken Guidance & Begin** for calm step-by-step browser speech.
3. **Choose a subject & lesson** from the 20 verified lessons (filter by subject, difficulty, or search).
4. **Explore one component at a time** using `Next Component`, `Previous`, `Repeat`, or voice commands.
5. **Ask questions** about the diagram anytime (e.g., *"Why is the bulb off?"* or *"What happens if I remove the rabbit?"*).
6. **Predict & Run Verified Experiment**, review the evidence, and continue to the **Next Lesson**.

---

## 2. Voice Command Reference (Phase 15)

Voice input is **strictly optional** and **push-to-talk only** (`Speak Command`). Every voice action has an equivalent keyboard button and typed command box.

| Category | Example Spoken / Typed Commands | Verified Action |
|---|---|---|
| **Navigation** | `"Start learning"`, `"Continue learning"`, `"Next"`, `"Previous"`, `"Repeat"`, `"Help"`, `"Go back"`, `"Next lesson"` | Navigates steps safely without arbitrary code execution |
| **Subject & Level** | `"Show Physics lessons"`, `"Open Biology"`, `"Computer Science"`, `"Mathematics"`, `"Chemistry"`, `"Beginner"`, `"Intermediate"`, `"Advanced"` | Filters or opens matching lessons in the Learning Library |
| **Exploration** | `"What is this?"`, `"Explain this component"`, `"Explain the diagram"`, `"Tell me more"` | Reads current component or diagram overview |
| **Experiments** | `"Start experiment"`, `"Option one"`, `"Option two"`, `"The bulb will turn on"`, `"Submit my answer"`, `"Try again"`, `"Close the switch"` | Selects option & runs deterministic Python engine |
| **Science Questions** | `"Why is the bulb off?"`, `"Where does energy flow from the rabbit?"`, `"What happens if I remove the rabbit?"` | Routed to Evidence-Grounded STEM Tutor (cites node/edge IDs; abstains if out of scope) |

---

## 3. Microphone Permission, Privacy & Browser Compatibility

- **No automatic recording:** SenseGraph never starts the microphone on page load and never listens in the background.
- **Language expectation:** Browser speech recognition currently expects **English (`en-US`)** spoken commands and questions.
- **Feedback-loop prevention & turn-taking:** In Guided Conversation mode, SenseGraph finishes speaking the complete prompt (`SpeechSynthesisUtterance.onend`), plays a soft listening chime, and opens one bounded 8-second listening turn. Cancelled or errored utterances never trigger automatic listening. Activating `Speak Now` immediately stops browser speech synthesis so SenseGraph never transcribes its own voice.
- **Privacy disclosure:** Browser Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) in Chrome and Edge may send audio to the browser vendor's cloud speech service for transcription.
- **Browser compatibility:**
  - **Chrome / Edge (Desktop):** Full support for `webkitSpeechRecognition` + `speechSynthesis` + keyboard/text fallback.
  - **Firefox / Safari / Unsupported environments:** Automatically displays `Mic: Unsupported (use keyboard/text)` and keeps the full keyboard UI and text command bar 100% functional.

---

## 4. Validated 20-Lesson STEM Learning Library (Phase 16)

Every lesson has a **distinct diagram configuration or dataset**, passes deterministic domain validation at startup, and generates verified prediction challenges:

- **Physics (4 lessons):** `phy_01_simple_series` (Beginner), `phy_02_closed_switch` (Beginner), `phy_03_two_bulb_open` (Intermediate), `phy_04_two_bulb_closed` (Advanced).
- **Biology (4 lessons):** `bio_01_simple_chain` (Beginner), `bio_02_grassland_web` (Beginner), `bio_03_forest_web` (Intermediate), `bio_04_pond_web` (Advanced).
- **Computer Science (4 lessons):** `cs_01_sequential` (Beginner), `cs_02_conditional_branch` (Beginner), `cs_03_even_odd` (Intermediate), `cs_04_bounded_loop` (Advanced).
- **Mathematics (4 lessons):** `math_01_linear_increase` (Beginner), `math_02_peak_extrema` (Beginner), `math_03_valley_minimum` (Intermediate), `math_04_cooling_comparison` (Advanced).
- **Chemistry (4 lessons):** `chem_01_water` (Beginner, `H2O`), `chem_02_methane` (Beginner, `CH4`), `chem_03_co2` (Intermediate, `CO2`), `chem_04_ethanol` (Advanced, `C2H6O`).

### Local Progress Storage
- Progress (`currentLessonId`, `completedLessonIds`, `attempts`) is stored **locally in browser `localStorage` only** (`sensegraph_progress_v1`).
- No personal data is collected and progress does not sync across devices. Use **Reset Progress** anytime to clear it.

---

## 5. Educator Lesson Authoring & Safe JSON Packages

1. Switch to **Educator / Advanced** in the header.
2. Load a verified diagram or upload & review an image via Gemini Vision (when configured).
3. Confirm the diagram in **Human Review** (unreviewed AI drafts are always blocked from lesson export/import).
4. Fill in Lesson Title, Difficulty, Description, and Learning Objectives in **Educator Lesson Package Authoring**.
5. Click **Validate & Export Lesson JSON** (calls `POST /api/lessons/validate-package`) to download a portable `.sensegraph.json` file, or click **Import Lesson JSON** to validate and preview a package in Student Experience.

---

## 6. Accessibility Status & Remaining Limitations (Honest Disclosure)

- **Automated verification:** 98 pytest tests (including Phase 15 voice intent/tutor routing, Phase 16 20-lesson validation & package security, and Phase 17 end-to-end voice + keyboard journeys), `ruff --target-version py311`, `node --check` on all modular JS files, and `evaluation.benchmark --mode dry-run`.
- **Not yet tested in this environment:** Live manual usability testing with **NVDA** (Windows) or **VoiceOver** (macOS), live microphone transcription in Chrome/Edge, and live Gemini Vision API calls (no `.env` key configured). Do not claim WCAG certification or blind-user validation until live assistive-technology sessions are completed.

---

## 7. Manual Real-Microphone Verification Script (Chrome / Edge, ~90 Seconds)

Use this checklist on Windows Chrome or Edge to verify real browser speech recognition and speech synthesis end-to-end:

1. Start the server: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` and open `http://127.0.0.1:8000`.
2. Verify **zero autoplay** on page load and that `Mic: Ready` is shown.
3. Click **Start Spoken Guidance & Begin** → confirm SenseGraph speaks Step 2 guidance calmly.
4. Click **Speak Command** (or Tab to it and press `Enter`) → grant microphone permission when prompted → verify app speech stops immediately and badge shows `Mic: Listening…`.
5. Say **"Physics"** → confirm library filters to 4 Physics lessons.
6. Click **Speak Command** → say **"Beginner"** → confirm *Simple Series Circuit (Open Switch)* opens at Component 1 of 3.
7. Click **Speak Command** → say **"Why is the bulb off?"** → confirm the Evidence-Grounded Tutor replies citing `bulb_1` and `all_switches_closed=False`.
8. Click **Speak Command** → say **"Start experiment"** → then say **"Option one"** → then say **"Submit my answer"** → confirm the verified Python simulation toggles Switch S1 and reports Bulb L1 ON with evidence.
9. Test **Pause**, **Resume**, **Stop**, **Repeat**, and **Cancel Listening**, plus typing `"Next lesson"` in the keyboard command box to confirm the non-voice fallback works identically.
