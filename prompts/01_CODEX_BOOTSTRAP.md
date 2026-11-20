# CODEX PROMPT 01 — Build the first working vertical slice

You are working inside a repository containing the SenseGraph project handoff kit. This is a real application-building task, not a request to create another specification. **Implement and test Phase 1 now.**

Read these files first, in this order: `AGENTS.md`, `START_HERE_VI.md`, `docs/PRODUCT_SPEC.md`, `docs/TECHNICAL_SPEC.md`, `docs/ACCESSIBILITY_AND_TESTS.md`, `contracts/diagram.schema.json`, both fixture JSON files. Treat them as authoritative, and explain any conflicts rather than ignoring them.

**Phase 1 scope (must implement):**

1. Scaffold runnable Python FastAPI app and minimal semantic HTML/CSS/vanilla JavaScript frontend. Make it easy to run with Windows PowerShell. Create `requirements.txt`, `.env.example`, `.gitignore` (exclude `.env`, `.venv`, caches, secrets).
2. Implement Pydantic `DiagramDocument` models matching the supplied contract. Validate unique node IDs, edge IDs, referenced endpoints, domain-specific kinds and relations. Keep meaningful errors.
3. Implement `GET /api/health`, `GET /api/examples`, `GET /api/examples/{id}`, `POST /api/validate`, `POST /api/confirm`, `POST /api/simulate` as specified. No provider integration yet.
4. Implement **Physics P0**: one-battery, one-switch, 1–2-bulb single series ring. Derive connectivity from edges; toggle switch and compute bulbs on/off deterministically. Reject unsupported topology.
5. Implement **Biology P0**: directed food/prey -> consumer arrows. Select neighbors, remove organism and incident relationships, report exact changes, reset without modifying original.
6. Build a polished but simple accessible frontend: intro, two example cards, visible "Pre-annotated demo — no AI used" label, summary, object list, relationship navigation, selected-object details, action area, results with polite live announcements, reset. Every interactive feature works with keyboard (Tab / Shift+Tab / Enter / Space) and native controls; visible focus; skip link; no canvas-only data.
7. Add unit and integration tests covering key invariants and expected results. The bundled fixtures must work without network or API key.
8. Update README with exact setup/run/test instructions for Windows, initial screenshots/instructions if possible, and candid limitations. Do not delete the original handoff docs.

**Explicitly defer:** Gemini/API integration, flowcharts, sign-in, databases, generic chatbots, voice recognition, deployment, fancy animations.

**Quality gate:** run `python -m pytest -q` and report the actual result. If dependencies or the environment prevent running tests, state the blocker and show corrective steps; do not claim success. Show which files you created/edited and 3 manual interactions to test. Do not stop after giving a plan—write the code.
