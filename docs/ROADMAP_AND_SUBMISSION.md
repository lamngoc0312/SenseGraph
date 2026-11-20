# SenseGraph — 7-Day Engineering Roadmap & Devpost Checklist

## Timeline (local time: Asia/Ho_Chi_Minh)

**Official submission deadline:** 2026-11-21 23:59 EST = **2026-11-22 11:59 ICT**. Aim to submit **on November 21 Vietnam time** with a buffer. Demo Day November 24 EST; refer to Discord for live or prerecorded logistics.

| Day | Objective | Acceptance gate |
|---|---|---|
| Nov 15 | Finalize scope, fixtures, contracts, set up Git repo | PRD clear, repo initialized |
| Nov 16 | Scaffold FastAPI, fixtures, models, validators, tests | Two example APIs return valid graphs |
| Nov 17 | Physics + Biology deterministic engines | All tests for scientific actions pass |
| Nov 18 | Accessible UI, keyboard exploration | Full fixture walkthrough without mouse |
| Nov 19 | Real Gemini upload integration, review & edit | At least 1 genuine image extraction works if key configured |
| Nov 20 | Test live sample images, fix major errors, README | Known limitations documented, tests pass |
| Nov 21 | Demo recording (<=6m), upload public/unlisted, Devpost | Repository, video, project form submitted |

**Fallback if behind:** Make the two fixture journeys reliable, then prioritize genuine AI image extraction of one supported image and disclosure. Do not trade away a functional project for untested new modules.

## Must-have submission assets

- [ ] Public GitHub repository with source code.
- [ ] README: project goal, setup (Windows), screenshots, supported/unsupported diagrams, architecture and tests.
- [ ] README disclosures: external AI provider, AI coding assistants (e.g. Codex), attribution for libraries/diagram images, work created during event.
- [ ] Demo video <= 6 minutes on YouTube or Vimeo, publicly accessible or unlisted.
- [ ] Devpost description: problem, target users, primary **Education** track, AI use, product features, challenges, learning and next steps.
- [ ] Individual participant added to Devpost submission.
- [ ] Demo Day participation November 24 EST, live or prerecorded instructions checked in Discord.
- [ ] If participation certificate desired, request it after complete submission + Demo Day participation, per organizers' guidance.
- [ ] Do not publish personal/sensitive diagrams or unauthorized copyrighted material.

## Suggested 5-minute demo (adapt after actual implementation)

| Approx time | Content |
|---|---|
| 0:00–0:35 | Real challenge: visual STEM diagrams and access barriers |
| 0:35–1:00 | SenseGraph overview and supported scope |
| 1:00–2:05 | Load circuit fixture, keyboard navigation, switch on/off and explanation |
| 2:05–3:00 | Load food-web fixture, navigate directional relations, remove & reset |
| 3:00–4:00 | Actual live AI extraction: upload image, show review/correction and confirm (only if truly working) |
| 4:00–4:35 | Architecture: vision -> semantic graph -> deterministic domain engine |
| 4:35–5:00 | Testing, what was learned, remaining limits, future work |

Do not record claims of live AI or accessibility validation without actually carrying them out. When live AI isn't available, make that transparent and focus on genuine accessible interaction and documented AI development contribution.

## Suggested Devpost copy starter (edit to match the finished implementation)

**Project title:** SenseGraph — Explore STEM Beyond Sight

**Elevator pitch:** SenseGraph turns selected STEM diagrams into interactive, accessible structures that learners can explore with a keyboard and screen reader. Instead of only captioning an image, it makes relationships navigable and enables simple verified experiments.

**Problem:** Important STEM concepts are often encoded visually as wires, arrows, nodes and spatial relations. A short alt-text caption may not let a blind learner explore each relation or modify a model independently.

**Solution:** For basic series circuits and food webs, SenseGraph represents a diagram as a semantic graph, offers accessible descriptions and navigation, and uses deterministic domain logic to explain changes. When configured, a vision model proposes a graph from a user-uploaded image; the user reviews it before simulations.

**AI disclosure:** [Fill in the real image model, exact SDK/service, Codex assistance, which features were implemented and tested. If live extraction is not delivered, state this explicitly.]

**Challenges & lessons:** [Actual, specific technical problems encountered and resolutions; not fictional achievements.]

**Limitations:** Physics supports simple series loops, Biology supports direct food-web relationships, extracted diagram structure needs review, and formal user studies are future work.

**What's next:** Flowcharts, graph/chart sonification, user testing with blind learners and educators, improved error recovery, optional voice control.

## Judging alignment (20% each per official rules)

1. Problem & Impact — educational accessibility, narrow user journey, honest research limitations.
2. Use of AI — actual image-to-graph interpretation if available; transparently disclose AI coding assistance.
3. Functionality — fully working deterministic exploration and simulation on two domains.
4. Learning & Growth — show actual errors, tests, corrections and research learnings.
5. Presentation — clear keyboard-first user story and truthful video.

Official rules: https://stem2connect-online-hackathon.devpost.com/rules
