# SenseGraph — Demo Recording Shot List

**Recommended resolution:** 1920×1080 (or 1280×720) at 100%–125% browser zoom so text and focus rings are crystal clear.  
**Max length:** 6 minutes (target ~5:15–5:25).  
**Pre-recording prep:**
1. Close personal tabs/notifications; open Chrome/Edge to `http://127.0.0.1:8000`.
2. Start server: `python -m uvicorn app.main:app --reload`.
3. Keep a second PowerShell terminal ready showing `python -m pytest -v` (**82 passed**) and `python -m ruff check app tests evaluation` (**All checks passed**).

| Shot | Time | On-Screen Action | What Judges Should See |
|---|---|---|---|
| 1 | 0:00–0:35 | Landing page (`http://127.0.0.1:8000`) | SenseGraph branding, purpose statement, honest mode separation callout, backend status badge |
| 2 | 0:35–1:10 | Press `Tab` from top of page across cards and Analyze form | "Skip to main content" link visible on focus; high-contrast focus rings; `Pre-annotated demo — no AI used` badges; Analyze Your Own Diagram form with explicit consent checkbox |
| 3 | 1:10–2:20 | Press `Enter` on **Explore Example Circuit** -> click **Next component** in Guided Tour -> switch to **Guided Learning Lab** -> choose **Bulb L1 will be ON** -> **Submit Prediction & Run Experiment** -> **Reset Experiment** | Guided Tour narration, synchronized SVG loop, Predict → Experiment → Explain workflow, Bulb L1 turning ON in stats + SVG + evidence list, Reset restoring OFF |
| 4 | 2:20–3:15 | Click **Load Biology Food Web** -> select **Rabbit** -> click **Remove Rabbit** -> click **Reset Experiment** | Food-to-consumer arrow convention, incoming (Grass) & outgoing (Fox), exact 2 removed edges + non-extinction disclaimer, SVG updating from 5 to 4 nodes, Reset restoring all 5 |
| 5 | 3:15–4:10 | Scroll to **Evidence-Grounded STEM Tutor** -> ask *"Is there a path from Grass to Fox?"* -> then ask *"Will Fox go extinct if Rabbit is removed?"* | Tool-backed verified answer with exact `node:`/`edge:` citations, followed by honest abstention *"Not established by this diagram."* |
| 6 | 4:10–4:50 | Click **Load CS Flowchart** -> click **Run Trace** -> click **Next step** 2–3 times | Safe restricted interpreter (no `eval`/`exec`), bounded step trace, branch condition readout, live variable environment (`n`, `total`), synchronized SVG flowchart |
| 7 | 4:50–5:25 | Switch to PowerShell showing `python -m pytest -v` (**82 passed**) and `ruff` (**All checks passed**) *(or insert 20s live Gemini upload clip if a real local API key was tested)* | Verified automated tests, CI discipline, honest limitations (no fabricated live-AI or WCAG claims), and next steps |
