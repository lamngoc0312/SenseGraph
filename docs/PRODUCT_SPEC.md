# SenseGraph — Product Requirements Document (PRD)

**Version:** 1.0 | **Date:** 2026-11-15 | **Audience:** solo developer / Codex / STEM2Connect judges

## 1. Problem

Many STEM diagrams carry critical information through spatial arrangement, arrows, lines, symbols and visual connections. A static image or a generic one-sentence caption may not allow a blind or visually impaired learner to **independently explore relationships and manipulate the represented system**.

The prototype addresses one narrow, testable problem: helping learners independently explore **two graph-like categories of STEM diagrams** with a keyboard and screen reader, without relying exclusively on image descriptions or a general chatbot.

**Do not claim** that all blind learners have identical needs, that a product is clinically/educationally validated, or that all diagrams can be accurately extracted.

## 2. One-line solution

> Upload or select a STEM diagram; SenseGraph converts it to an editable semantic graph, describes its entities and connections in an accessible interface, and enables safe, deterministic domain-specific experiments.

## 3. Target audience and use cases

**Primary persona:** A blind or visually impaired university / secondary student using a Windows laptop with keyboard + NVDA, or macOS with VoiceOver, learning foundational STEM concepts.

**Secondary persona:** A sighted teacher who wants to review or correct extraction before sharing accessible study materials.

Primary use cases:

1. Listen to an overview of a textbook diagram and visit each labeled object in a logical order.
2. Explore what connects to a selected object, what a relation means, and navigate directly to its neighbor.
3. Verify or correct an ambiguous AI-identified object/connection.
4. Apply a domain action and hear an explanation grounded in deterministic model state.
5. Reset and repeat without changing the original source image.

## 4. Domain scope and priority

### P0 — Physics / Circuit Explorer

- Input: schematic of **one closed series loop** with exactly one battery, one switch, and one or two light bulbs, clear labels and wires.
- Output: device nodes, wire relations, component order, switch state, summary, warnings.
- Explore: device label, type, role, adjacent elements, current switch/bulb state.
- Interact: toggle switch; compute `ON` for bulbs iff `loop_wired = true` and all switches are closed; otherwise `OFF`. For P0, there is exactly one switch. No current, brightness, resistance, polarity, or electrical-safety predictions.
- Unsupported: parallel circuits, multi-switch control, resistors with values, LED orientation, wiring shorts, dynamic electrical analysis.
- If AI cannot establish one valid series loop, disable simulation, request correction and display safe message.

### P0 — Biology / Food-Web Explorer

- Input: simple food chain/web with ~3–8 named organisms and directed arrows.
- Convention: **arrow from food/prey to its consumer/predator** (energy flow). Explain this convention before exploration; if arrow convention is ambiguous, do not silently assume it.
- Output: organism nodes, directed `energy_to` edges, summary, warnings.
- Explore: incoming/outgoing feeding relations, direct neighbors, energy paths.
- Interact: temporarily remove one organism; remove its incident relations; report exactly which relationships disappeared and which still remain; undo/reset.
- Unsupported: predicting extinction, population sizes, multi-year environmental change, quantitative energy transfer.

### P2 — Computer Science / Flowchart Explorer (stretch)

- Represent `start`, `process`, `decision`, `end`, directed flow edges and optional branch labels.
- Navigate conditions and paths. Only execute a strict whitelist of simple arithmetic/comparison operations with bounded steps; never execute source code returned by an LLM.
- This module MUST NOT delay P0 completion.

## 5. Main user flow

**Mode A: deterministic showcase (works without API key)**

1. Visit landing page; see meaningful project statement and 2 example buttons.
2. Choose "Explore example circuit" or "Explore example food web".
3. UI clearly labels the result **Pre-annotated demo — no AI used**.
4. Diagram overview presented as visible text plus structured list of objects and relationships.
5. Tab / Shift+Tab between controls, Enter / Space to activate native buttons.
6. Selecting a node shows long description, neighbors and actions; status updates announced by assistive technology.
7. Run domain action; read exact state changes and reason; reset.

**Mode B: live AI analysis (requires key)**

1. Choose domain and upload allowed image (PNG/JPEG/WEBP, maximum 5 MB).
2. Before sending, see consent notice: image is shared with the configured AI provider; avoid personal/sensitive content.
3. User explicitly starts analysis; backend sends the image to provider.
4. Provider returns structured proposal; Pydantic/graph validator verifies shape and semantics.
5. Show result as **AI-generated — review required** with warnings; editable labels/connections and domain parameters.
6. User confirms the verified structure. Invalid/ambiguous diagrams cannot be simulated.
7. Enter Explore/Experiment mode; reset must restore confirmed baseline (not model output edited behind the scenes).

## 6. UX requirements

- Homepage: project purpose; two example actions; image upload section; notice that voice is optional.
- Explorer: heading with diagram type, concise overview, summary stats, **numbered objects list**, selected-object detail and **relationship list**, domain-specific action panel, status region, reset button.
- All information necessary to understand a diagram available as text, not only SVG/canvas/colors.
- Distinguish diagram interpretation from verified outcome: "AI proposes...", "Confirmed graph...", "Simulation result...".
- Visible labels for every button and input; avoid icon-only interactions.
- Keep UI English-first for simple international demo, use plain language.
- No authentication, profiles, student records, storage of uploaded personal data or analytics in MVP.

## 7. AI responsibilities vs deterministic responsibilities

| Component | Responsibility | Must never do |
|---|---|---|
| Vision model | Extract tentative diagram type, labels, entities, relations, flags for ambiguity | Invent unseen connections, claim guaranteed accuracy |
| Schema & validator | Reject malformed IDs/edges/domain models and impossible P0 topology | Quietly patch uncertain science concepts |
| Human review | Confirm/correct labels, edges and domain-specific values | Automatically approve unsupported graphs |
| Physics engine | Evaluate simple series-loop switch/bulb state | Compute unsupported current or brightness |
| Biology engine | Traverse feeding graph / remove and restore nodes & edges | Predict ecological population changes |
| Accessible UI | Present readable structure, keyboard interactions and status | Force user to rely on sight or speech input |

## 8. Requirements with priority IDs

| ID | Priority | Requirement | Acceptance |
|---|---|---|---|
| FR-01 | P0 | Load 2 bundled pre-annotated diagrams | Both load without external keys/network |
| FR-02 | P0 | Render graph as semantic list and long description | Every node/edge discoverable via keyboard |
| FR-03 | P0 | Physics toggle updates bulb state | Series open -> off, closed -> on, reset -> initial |
| FR-04 | P0 | Food-web remove node updates edges | Only incident edges removed; reset restores |
| FR-05 | P0 | Selection shows direct neighbors | Labels and arrow direction announced |
| FR-06 | P0 | Validate diagram before simulations | Bad ref/type/domain rejected with actionable error |
| FR-07 | P0 | Distinguish fixture vs live AI mode | Honest source badge + text in view and README |
| FR-08 | P0 | Accessible keyboard navigation and status | Critical journey possible without mouse |
| FR-09 | P1 | Upload image & actual Gemini model extraction | Model called only if configured and consented |
| FR-10 | P1 | Human correction of AI proposal | Change node names/edges, revalidate, confirm |
| FR-11 | P1 | Handle AI provider failure gracefully | No crash, retries not infinite, clear fallback |
| FR-12 | P1 | Test, README, demo/video story | Tests and public repo ready for Devpost |
| FR-13 | P2 | Flowchart exploration | Only if P0 and P1 stable |
| FR-14 | P2 | Optional text-to-speech control | OFF by default; no duplicated involuntary speech |

## 9. Non-functional requirements

- Python >=3.11 (prefer support for user's Python 3.13); no Node build requirement.
- Simple local setup on Windows PowerShell; single FastAPI server serves static frontend and JSON API.
- Dependencies listed in `requirements.txt`, `.env.example` committed, `.env` and secrets ignored.
- Unit tests for validators and simulators; integration tests for endpoints; manual tests for keyboard + NVDA/VoiceOver if available.
- Upload limit 5MB; MIME and image bytes checked; reject corrupt files; avoid upload persistence.
- Gemini key only on backend; never hardcode or expose in browser.
- External request duration limited; meaningful error codes; model output considered untrusted.

## 10. Evaluation plan (no fabricated metrics)

**Functional:** 2 curated fixtures; at least 20 automated unit/integration assertions; full no-mouse walkthrough in one browser.

**Extraction:** Prepare 5–10 different simple input images per supported domain, manually annotate expected nodes/edges; evaluate extraction only on inputs actually run, reporting: node precision/recall, relation precision/recall, percentage of diagrams needing correction. Do not claim a percentage until measured. Record at least two actual successful live AI analyses if provider access exists.

**Accessibility:** keyboard walk-through with Tab/Shift+Tab/Enter/Space; verify focus order, status announcements, long descriptions and no keyboard trap; manual screen reader check if available. Report gaps candidly.

**Educational learning:** only claim *potential*, not demonstrated learning outcomes, until user studies are conducted.

## 11. Exclusions / honest limitations

- Arbitrary STEM image recognition, complex charts, handwriting, OCR-heavy textbooks, all circuit types, advanced biology simulation.
- Production safety critical use, medical decisions, automatic curriculum grading.
- Guarantees of screen reader behavior on all devices, WCAG certification, or validation by real blind participants without conducting study.
- A general AI assistant, multilingual speech tutor, accounts, cloud hosting as core scope.

## 12. Definition of done for the hackathon

A judge can launch the application locally, experience two working accessible examples, see meaningful domain actions that can be explained and tested, and—if a provider key is configured—upload an image and observe an actual AI-produced graph with human review. The public repo includes run steps, credits, AI disclosure, demo and limitations.
