/* SenseGraph Phase 17 + Non-Visual Dialogue Redesign — Contextual Guidance Module
 *
 * Proactively guides a blind learner through every step without requiring sight:
 *  1. Where am I?
 *  2. What is SenseGraph telling me?
 *  3. What 2–3 choices do I have?
 *  4. How do I respond (by voice OR keyboard/screen reader)?
 */

(() => {
  "use strict";

  function buildContextualGuidance({
    step,
    voiceEnabled = false,
    guidedTurnTaking = false,
    lessonTitle = "",
    compIndex = 0,
    compCount = 0,
    compLabel = "",
    hasResult = false,
  }) {
    const how = guidedTurnTaking
      ? "Guided voice is active: wait for the soft chime, then speak your choice (or say 'Stop listening' anytime)."
      : voiceEnabled
        ? "Speak using Alt+Shift+V or Speak Now, or press Tab and Enter."
        : "Use Tab and Enter to choose an action, or press Alt+Shift+V to speak.";

    switch (step) {
      case "welcome":
        return {
          where: "Step 1 of 5 · Welcome to SenseGraph",
          what: "Choose 1 of 2 listening options: Screen Reader Mode or Guided Voice Learning.",
          how: "Press Tab and Enter to choose. Audio never plays automatically.",
        };
      case "subjects":
        return {
          where: "Step 2 of 5 · Choose a Subject & Lesson",
          what: "Choose Physics, Biology, Computer Science, Mathematics, or Chemistry.",
          how,
        };
      case "explore":
        return {
          where: `Step 3 of 5 · ${lessonTitle || "Lesson"} — part ${compIndex + 1} of ${compCount || 1}: ${compLabel || "item"}`,
          what:
            compIndex + 1 < compCount
              ? "Choices: say 'Next' to continue, 'Explain more' for details, or ask a science question."
              : "You reached the final part. Choices: say 'Start experiment' to make a prediction, or 'Previous' to review.",
          how,
        };
      case "experiment":
        return {
          where: `Step 4 of 5 · Prediction & Verified Experiment (${lessonTitle || "Lesson"})`,
          what: "Choices: say 'Option one' or 'Option two' (or use Arrow keys), then submit to run the verified engine.",
          how,
        };
      case "summary":
        return {
          where: `Step 5 of 5 · Learning Summary (${lessonTitle || "Lesson"})`,
          what: hasResult
            ? "Choices: say 'Next lesson' to continue, or 'Try again' to repeat the experiment."
            : "Review the verified explanation or choose the next lesson.",
          how,
        };
      default:
        return {
          where: "SenseGraph Student Experience",
          what: "Say 'Where am I' or 'Help' for guidance.",
          how,
        };
    }
  }

  function buildSpokenDialogue(ctx) {
    const g = buildContextualGuidance(ctx);
    return `${g.where}. ${g.what} ${g.how}`;
  }

  window.SenseGraphGuidance = {
    buildContextualGuidance,
    buildSpokenDialogue,
  };
})();
