# SenseGraph — Codex Project Handoff Kit

**SenseGraph: Making STEM Diagrams Accessible, Interactive and Understandable.**

An accessible learning prototype for blind and visually impaired students. A diagram is converted into a **reviewable semantic graph** so students can navigate its components and relationships using a keyboard and screen reader, then experiment with domain-specific deterministic interactions.

**Primary hackathon track:** Education. **Related social impact:** Community Impact.

This folder is an **implementation handoff kit, not the finished app**. Codex should generate the application following the specs and tests in this folder.

## Product narrative

`Input diagram -> Vision AI -> Structural validation -> Human review -> Accessible graph exploration -> Domain simulator -> Learning feedback`

P0: physics simple series circuits; biology food webs. P2: computer-science flowcharts. The **shared semantic graph** (nodes and directed edges) represents exploration; domain-specific payloads determine the behavior of a scientific simulator.

## Quick start

- Vietnamese step-by-step setup: [START_HERE_VI.md](START_HERE_VI.md)
- Codex rules: [AGENTS.md](AGENTS.md)
- Product requirements: [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md)
- Engineering contracts: [docs/TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md)
- Accessibility and acceptance: [docs/ACCESSIBILITY_AND_TESTS.md](docs/ACCESSIBILITY_AND_TESTS.md)
- Handoff prompts: [prompts/01_CODEX_BOOTSTRAP.md](prompts/01_CODEX_BOOTSTRAP.md)

## Important limitations

- The application must not claim to correctly interpret arbitrary scientific diagrams.
- Vision extraction can fail: the user reviews and corrects the structured result before simulation.
- Demo fixtures are curated, not evidence that AI extracted an uploaded image.
- Physics simulation covers only a single-loop series circuit; biology exploration shows graph changes, not ecological forecasts.
- Keyboard and screen reader accessibility require manual review with assistive technologies; no claims of user validation are made yet.

## Official references

- Hackathon rules: https://stem2connect-online-hackathon.devpost.com/rules
- W3C complex images: https://www.w3.org/WAI/tutorials/images/complex/
- W3C keyboard accessibility: https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/
- Gemini SDK: https://googleapis.github.io/python-genai/

## License and attribution

Choose an appropriate open-source license before publishing. Document third-party SDKs, models, external datasets, AI coding assistants, and which work was completed during the hackathon period. Use original or freely licensed sample diagrams; do not reuse private group project code without authorization.
