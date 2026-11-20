# SenseGraph — Ethical Accessibility & Usability Study Protocol

**Status:** Draft protocol ready for owner approval. **No participants have been recruited, contacted, or tested.**

## 1. Purpose
Evaluate whether blind, low-vision, and sighted-educator participants can independently complete core STEM diagram exploration and experiment tasks using SenseGraph with keyboard and assistive technologies (e.g., Windows Chrome + NVDA, macOS Safari + VoiceOver).

## 2. Informed Consent & Voluntary Participation
- Participation is 100% voluntary; participants may pause, skip any task, or withdraw at any time without penalty.
- Provide the consent notice in accessible plain-text HTML and screen-reader-friendly format at least 24 hours before the session.
- Explicitly disclose:
  - What is being tested (SenseGraph prototype usability, not the participant).
  - Whether screen/audio recording is requested (optional; default is written researcher notes only).
  - That no personal, medical, or academic records are collected.

## 3. Privacy Safeguards
- Assign anonymous participant codes (`P01`, `P02`, ...); never store real names alongside session logs.
- Conduct sessions using pre-annotated local fixtures (`AI_PROVIDER=none`) unless a participant explicitly consents to test a non-sensitive sample image with an external vision provider.
- Delete any temporary recordings within 30 days of analysis or immediately upon participant request.

## 4. Accessible Task Set (45 Minutes Max)
1. **Orientation (5 min):** Locate the skip link, read the homepage notice, and open the Physics Series Circuit using keyboard only.
2. **Physics Experiment & Learning Lab (10 min):** Inspect Switch S1 and Bulb L1, predict bulb state in Guided Learning Lab, close Switch S1, verify explanation, and reset.
3. **Biology Food Web (10 min):** Identify what Rabbit eats and what eats Rabbit, remove Rabbit, verify exact removed relationships, and reset.
4. **Grounded Tutor & Guided Tour (10 min):** Step through Guided Tour, ask one in-scope question and one out-of-scope question (verify honest abstention).
5. **Debrief (10 min):** Gather open-ended feedback on focus order, announcement verbosity, mental model clarity, and cognitive load.

## 5. Assistive Technology Test Matrix (Actual Runs Only)

| Date | Device / OS | Browser | Assistive Tech | Zoom / Contrast | Tasks Completed | Critical Issues Found |
|---|---|---|---|---|---|---|
| — | Windows 11 | Chrome | NVDA | 200% | `not tested` | Pending manual run |
| — | macOS | Safari | VoiceOver | 200% | `not tested` | Pending manual run |
| — | Windows 11 | Chrome | Keyboard-only | High contrast + Reduced motion | `not tested` | Pending manual run |
