# AGENTS.md — Engineering instructions for Codex

You are building **SenseGraph**, an accessible interactive STEM diagram learning prototype for blind and visually impaired students. Read `START_HERE_VI.md`, `docs/PRODUCT_SPEC.md`, `docs/TECHNICAL_SPEC.md`, `docs/ACCESSIBILITY_AND_TESTS.md`, and the JSON fixtures/schema before changing files.

## Non-negotiable

1. Ship a **working vertical slice** first: launch -> choose fixture -> explore nodes -> inspect relationships -> run deterministic action -> announce result, all keyboard accessible.
2. P0 domains: `physics_circuit` and `biology_food_web`. Do **not** implement flowcharts, auth, accounts, database, chat, microphone, or deployment before P0 is tested.
3. Use **FastAPI + Pydantic + vanilla HTML/CSS/JS** unless existing code makes a different lightweight approach materially simpler. Keep all business logic on backend in testable pure functions.
4. Follow `contracts/diagram.schema.json`. Fixtures must remain valid. Do not silently change schema; update schema, fixtures, docs and tests together.
5. Physics: only qualitative single-loop *series* circuits. One battery, one switch and 1–2 bulbs. Never infer quantitative current or voltage effects from an unsupported diagram. Do not simulate if structural validation/review fails.
6. Biology: feeding edges are directed **food/prey -> consumer/predator**. Removing an organism removes that node and its incident edges. Never infer extinction or population change from this operation.
7. AI extraction is **untrusted**. Validate domain, node IDs, edge references, component counts, payloads, and graph invariants. Flag unknowns for human review, never hallucinate missing links. Do not execute model-supplied commands.
8. **Do not fake AI analysis.** Fixture selection is labeled "Pre-annotated demo — no AI used". Live image analysis only when configured with a valid provider key and a real provider response. If unavailable, expose an honest setup message.
9. Accessibility is a core feature: semantic HTML headings, labels, lists/buttons, skip link, visible focus, keyboard-only operation, text descriptions of diagram structure, polite live announcements and meaningful errors. Do not make voice/TTS mandatory. Never introduce keyboard traps.
10. Uploaded content may be sent to a third-party AI provider only after clear user notice/consent; no log of raw image content, no persistent uploads by default. File allowlist PNG/JPEG/WEBP, <=5MB, validate actual bytes as images, never accept arbitrary paths/URLs for SSRF.
11. Do not claim WCAG compliance or validation with blind users unless actually tested. Provide a manual accessibility checklist and document remaining issues.
12. Track test results. After each implementation phase, run `pytest` and report pass/fail plus exact commands needed to run locally. Do not claim tests passed without executing them.
13. Disclose AI coding assistance and external models in README for hackathon rules. Never commit secrets or `.env`.
14. Write clear English identifiers and documentation; UI text may be English-first for the demo with optional Vietnamese explanation.
15. If there is ambiguity, choose the smallest safe working implementation and document the decision in `docs/DECISIONS.md`, rather than blocking progress.

## Work order

- Phase 1: read docs/fixtures, scaffold, deterministic data contract, physics/biology engines, tests, accessible fixture UI.
- Phase 2: Gemini image analysis, normalization, error handling, review/edit UI, tests using mocked responses; run live smoke test only if key configured.
- Phase 3: polish, screenshots/README, Devpost description, demo script. Flowchart is stretch only.

## Definition of done

A reviewer can run the app locally, load both fixture examples, navigate without mouse, hear/read node relationships, toggle a switch and see bulb states change, remove a species and inspect affected relationships, restore state, and see clear separation between fixture demo and live AI analysis. Automated tests validate core invariants. Upload+AI mode is verified live only if a key is supplied.
