# SenseGraph — Demo Recording Shot List

**Recommended resolution:** 1920×1080 (or 1280×720) at 100%–125% browser zoom so text and focus rings are crystal clear.  
**Max length:** 6 minutes (target 5:00–5:20).  
**Pre-recording prep:**
1. Close personal tabs/notifications; open Chrome to `http://127.0.0.1:8000`.
2. Start server: `python -m uvicorn app.main:app --reload`.
3. Keep a second terminal window ready showing `python -m pytest -v` (54 passed).

| Shot | Time | On-Screen Action | What Judges Should See |
|---|---|---|---|
| 1 | 0:00–0:35 | Landing page (`http://127.0.0.1:8000`) | Clean SenseGraph branding, value statement, honest mode callout, backend status badge |
| 2 | 0:35–1:10 | Press `Tab` repeatedly from top of page | "Skip to main content" link appears on focus; high-contrast focus rings across Physics/Biology cards and Analyze form |
| 3 | 1:10–1:50 | Press `Enter` on **Explore Example Circuit**; click **Next component** and **Connections** in Guided Tour | `Pre-annotated demo — no AI used` badge, Overview, Switch Open / Bulb OFF stats, Guided Tour plain-language text, synchronized SVG loop |
| 4 | 1:50–2:30 | Click **Guided Learning Lab** -> choose **"Bulb L1 will be ON"** -> **Submit Prediction & Run Experiment** -> **Reset Experiment** | Predict → Experiment → Explain flow; deterministic Python result; Bulb L1 turns ON in stats + SVG + evidence list; Reset restores OFF |
| 5 | 2:30–3:40 | Click **Load Biology Food Web** -> select **Rabbit** -> inspect incoming/outgoing -> click **Remove Rabbit** -> click **Reset Experiment** | Food-to-consumer arrow convention; Grass -> Rabbit -> Fox links; exact 2 removed edges + non-prediction disclaimer; SVG updates from 5 to 4 nodes; Reset restores 5 nodes / 4 edges |
| 6 | 3:40–4:40 | Return home -> **Analyze Your Own Diagram** | **With key:** Upload `fixtures/images/physics_series.png`, check consent, show `AI-generated — review required`, Validate, Confirm, Explore. **Without key:** Show consent + honest `503` setup message (no fake AI) |
| 7 | 4:40–5:15 | Switch to PowerShell terminal running `python -m pytest -v` | All **54 passed** in ~2s, closing statement on honest limitations & next steps |
