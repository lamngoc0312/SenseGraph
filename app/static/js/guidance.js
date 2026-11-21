/* SenseGraph Phase 17 — Contextual Student Guidance Module
 *
 * Answers three questions calmly at every step:
 *  1. Where am I?
 *  2. What can I do?
 *  3. How do I do it? (voice + keyboard equally)
 */

(() => {
  "use strict";

  function buildContextualGuidance({
    step,
    voiceEnabled = false,
    lessonTitle = "",
    compIndex = 0,
    compCount = 0,
    compLabel = "",
    hasResult = false,
  }) {
    const inputHint = voiceEnabled
      ? "Press Speak Command or type below, or use Tab and Enter."
      : "Use Tab and Enter to choose an action, or press Speak Command anytime.";

    switch (step) {
      case "welcome":
        return {
          where: "Step 1 of 5 · Welcome to SenseGraph",
          what: "Choose Screen Reader mode (recommended for NVDA/VoiceOver) or Spoken Guidance mode.",
          how: inputHint,
        };
      case "subjects":
        return {
          where: "Step 2 of 5 · STEM Learning Library (20 verified lessons)",
          what: "Filter by subject or difficulty, or say a subject name like 'Physics' or 'Biology'.",
          how: inputHint,
        };
      case "explore":
        return {
          where: `Step 3 of 5 · Exploring ${lessonTitle || "lesson"} — component ${compIndex + 1} of ${compCount || 1}: ${compLabel || "item"}`,
          what:
            compIndex + 1 < compCount
              ? "Say 'Next' or activate Next Component to continue, or ask a question about this diagram."
              : "You reached the last component. Say 'Start experiment' or activate Predict & Experiment.",
          how: inputHint,
        };
      case "experiment":
        return {
          where: `Step 4 of 5 · Prediction & Verified Experiment (${lessonTitle || "lesson"})`,
          what: "Choose one prediction option by voice (e.g., 'Option one') or arrow keys, then run the verified experiment.",
          how: inputHint,
        };
      case "summary":
        return {
          where: `Step 5 of 5 · Learning Summary (${lessonTitle || "lesson"})`,
          what: hasResult
            ? "Review the verified explanation, then say 'Next lesson', 'Try again', or 'Back to Subjects'."
            : "Review your result or choose the next lesson.",
          how: inputHint,
        };
      default:
        return {
          where: "SenseGraph Student Experience",
          what: "Say 'Help' or activate the Help button for keyboard and voice instructions.",
          how: inputHint,
        };
    }
  }

  window.SenseGraphGuidance = {
    buildContextualGuidance,
  };
})();
