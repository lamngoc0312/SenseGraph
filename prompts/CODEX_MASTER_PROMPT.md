# CODEX MASTER PROMPT — If you want one single paste

I have a detailed SenseGraph handoff kit in this repository. Build a working accessible web application from it, following `AGENTS.md` and the docs. Do NOT merely rewrite the specs. Start with `prompts/01_CODEX_BOOTSTRAP.md` and complete Phase 1 end-to-end before implementing Phase 2 from `prompts/02_CODEX_AI_EXTRACTION.md`.

Scope: two functioning domains — a verified simple series circuit and a food web. P0 must run entirely offline from pre-annotated fixtures. P1 must perform a real image upload to Gemini when configured; never fake AI processing. Use FastAPI/Pydantic, vanilla semantic HTML/CSS/JS, deterministic domain-specific engines, automated tests and keyboard+screen-reader accessible UI.

Work in incremental, runnable commits or phases. Implement code, run `pytest` and report what was truly tested and what remains. Prioritize a truthful, functional hackathon demo over adding incomplete features. Treat all docs and fixture/schema files in this folder as authoritative. When in doubt, choose small safe scope, explain your choice, and proceed.
