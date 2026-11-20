# CODEX PROMPT 03 — Verify, polish, prepare STEM2Connect submission

Audit SenseGraph against `docs/PRODUCT_SPEC.md`, `docs/ACCESSIBILITY_AND_TESTS.md`, `docs/ROADMAP_AND_SUBMISSION.md`, and `AGENTS.md`. Do not add new domains until acceptance criteria are met.

Tasks:

1. Run full pytest suite, fix failures; verify physics and biology fixture scenarios, API errors and reset behavior. Provide exact pass/fail output.
2. Review keyboard-only navigation: skip link, visible focus, Tab / Shift+Tab / Enter / Space, semantic relationships, live status messages and no keyboard traps. Document which checks were automated versus manually verified. Do not claim NVDA/VoiceOver testing unless actually done.
3. Verify honest provenance: selected fixtures explicitly say pre-annotated / no AI; live AI analysis calls provider and requires review; README disclosure correct.
4. Improve copy and visual polish for demo without introducing inaccessible controls. All key interactions must work on localhost and be easy to narrate in a <=6-minute video.
5. Update README: problem, features, supported vs unsupported science, tech stack, architecture, Windows setup, environmental variables, screenshots, demo workflow, test results, AI tool disclosures, known limitations and future work.
6. Draft a concise English Devpost description with: primary Education track, challenge, solution, how AI was used, what you built, learning, limitations, GitHub link placeholder and video link placeholder. Do not invent metrics or real-user feedback.
7. Produce an accurate demo shot list based only on implemented features. Include a strong keyboard-only flow and a genuine AI upload only if it works.
8. Give final punch list of what the human must do manually: create public GitHub repo / push, record/upload video to YouTube or Vimeo, submit Devpost before deadline, check Discord for Nov 24 Demo Day presentation.

Do not claim deployment, upload, submission, user testing or video creation happened unless you actually completed those tasks.
