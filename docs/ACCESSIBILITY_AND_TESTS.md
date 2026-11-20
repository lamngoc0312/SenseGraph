# SenseGraph — Accessibility Requirements & Test Plan

## 1. Accessibility is a core feature

SenseGraph must work for keyboard-only and screen reader users. Design target: **WCAG 2.2 AA principles**, without claiming audited compliance. Prefer semantic HTML and native controls over custom ARIA widgets.

## 2. Page semantics

- `<html lang="en">`; correct main heading H1 and hierarchical H2/H3.
- Skip-to-content link visible on focus; one main landmark.
- `<label>` for file input, domain selection, editing fields.
- Use `<button>` for actions; do not simulate button behavior using generic `div`/`span`.
- Images receive concise alternate text and a **separate long textual description** of essential diagram structure.
- Node/edge data shown in actual HTML lists/definition lists. Images and canvas are supplementary; users never need to inspect a picture to access relationships.
- Every scientific change conveys state by words, not color alone. Example: "Switch S1: closed; Bulb 1: on".
- Good contrast, readable font, avoid small grey body text; support browser zoom 200%.

## 3. Keyboard contract

| Key | Required behavior |
|---|---|
| `Tab` | Move forward across native links, buttons, inputs, node selectors, actions |
| `Shift+Tab` | Move backward without traps |
| `Enter` | Activate focused button / submit labeled form |
| `Space` | Activate focused native button or checkbox |
| `Esc` | Exit optional modal; P0 avoid modals entirely |
| Arrow keys | **Not custom-required** for P0; if using complex tree/graph widgets later, implement established WAI-ARIA patterns and test them |

Selecting a node displays its name, category, description, connected neighbors and available actions. The new information should be discoverable by screen reader and a concise summary announced in `aria-live="polite"`/`role="status"`. Avoid reading the whole page repeatedly. Focus stays predictable; after changing context, position focus only when it helps the user, and do not steal it during typing.

## 4. Proposed screen layout

1. Skip link + app title.
2. Domain selection and Example / Upload mode.
3. Current diagram title, provenance label (Fixture vs Live AI), review state, long overview.
4. Structured **Objects** list with native Select buttons.
5. **Selected object detail** and connected objects list with Navigate buttons.
6. **Experiment controls** (e.g. toggle switch / remove organism), result status area.
7. Reset button restoring confirmed baseline.
8. Image preview for sighted users with linked textual long description; NOT required for core function.

## 5. Screen reader behavior examples

**Physics:** "Switch S1, button. Open. Connected to battery and bulb. Press Enter for details." When action is activated: "Switch S1 closed. Series circuit complete. Bulb 1 is now on."

**Biology:** "Rabbit, organism. Receives energy from grass. Provides energy to fox." After removing rabbit: "Rabbit removed from this diagram. Removed two relationships: grass to rabbit; rabbit to fox. This does not predict population changes."

The exact wording can differ, but it must be understandable without visual inspection.

## 6. Manual keyboard acceptance sequence

1. Load page. Press Tab; skip link appears and works.
2. Without mouse, choose "Explore example circuit" and activate with Enter.
3. Listen/read diagram overview and domain/source label.
4. Navigate to each object; select Switch S1 using Tab + Enter.
5. Activate "Close switch" using Space or Enter. Verify status announced and bulb shows ON in text.
6. Activate "Reset". State returns to switch OPEN, bulb OFF.
7. Switch to food web example; navigate rabbit relationships.
8. Remove rabbit. Verify exact removed relations read out, graph updates, reset restores.
9. Tab through *all* controls; no keyboard trap or invisible action.
10. If live AI configured: keyboard-only upload, visible consent, analyze, review/edit, confirm and explore.

Where possible test Windows Chrome + NVDA and macOS Safari + VoiceOver; document which combinations were **actually** tested.

## 7. Automated tests (minimum coverage)

### Model and validator tests

- Accept both valid bundled fixtures.
- Reject duplicate node IDs, duplicate edge IDs and edges referencing unknown nodes.
- Reject bad domain, bad component kinds, invalid `energy_to` direction field/missing IDs.
- Physics: accept exactly 1 battery + 1 switch + 1 or 2 bulbs with exactly one ring.
- Physics: reject missing wire, extra edge, non-series branch, two batteries, unknown switch ID, dangling node.
- Biology: reject feeding edge with nonexistent organism; reject `wire` in food web.
- Reject simulation when `review_status=unreviewed`.

### Simulation tests

- Physics default switch OPEN -> bulb OFF.
- Toggle switch -> CLOSED and bulbs ON; toggle -> OPEN and OFF.
- Physics two bulbs in same series -> both ON only if loop complete and switch closed.
- Biology removal of rabbit removes rabbit and exactly all incident edges; unrelated edges remain.
- Original source diagram remains unchanged (deep copy / immutability).
- Reset restores baseline in frontend or relevant state helper.

### API tests

- `/api/health` indicates correct provider configuration, no secret leakage.
- Both example endpoints return correct source.mode `fixture`.
- Unsupported example returns 404.
- Invalid upload MIME/oversize/corrupt image returns proper error, not 500.
- Missing API key -> explicit 503; never returns fake fixture graph as AI response.
- Mock Gemini response -> parser+validator -> `unreviewed` document; explicit confirmation required.
- Unknown action/type/target -> graceful 400/422.

### Accessibility smoke checks

- Keyboard focus indicator shown, no elements with click-only handlers.
- Key controls have accessible names, results in `role=status`/`aria-live=polite`.
- `axe-core` browser check if feasible; manual verification still required.

## 8. Empirical evaluation protocol

For an extraction benchmark, label a small set of test images (5–10 unique images/domain) manually with expected node names and edge pairs. Use the exact same evaluation convention (physics undirected wires; biology directed energy edges). Report:

- `node_precision = correct_extracted_nodes / extracted_nodes`
- `node_recall = correct_extracted_nodes / expected_nodes`
- `edge_precision = correct_extracted_edges / extracted_edges`
- `edge_recall = correct_extracted_edges / expected_edges`

Handle empty denominators explicitly. Also report number of invalid/ambiguous extractions and number of corrections required. **Do not invent accuracy scores**, and don't use fixture cases to claim vision extraction performance.

## 9. Test log template

| Date | Environment | Test | Pass/Fail | Evidence/Notes |
|---|---|---|---|---|
| YYYY-MM-DD | Windows/Chrome + NVDA | Full keyboard circuit walkthrough | Not run | ... |
| YYYY-MM-DD | Windows/Chrome | Food-web remove/reset | Not run | ... |
| YYYY-MM-DD | Gemini configured | Live image extraction | Not run | ... |

## 10. Official references

- https://www.w3.org/WAI/tutorials/images/complex/
- https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- https://www.w3.org/WAI/fundamentals/accessibility-principles/
