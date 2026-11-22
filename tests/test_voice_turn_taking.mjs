/**
 * Unit tests for Guided Conversation turn-taking event ordering, cancellation,
 * duplicate-session prevention, permission denial, and timeout recovery.
 *
 * Executes the real `app/static/js/voice.js` module with mocked browser
 * SpeechSynthesis and SpeechRecognition APIs.
 */

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const voiceJsPath = path.resolve("app/static/js/voice.js");
const voiceJsSource = fs.readFileSync(voiceJsPath, "utf8");

function createMockEnv() {
  const events = [];
  let activeUtterance = null;
  let activeRecognition = null;
  let recognitionStartCount = 0;
  let speechCancelCount = 0;

  class MockUtterance {
    constructor(text) {
      this.text = text;
      this.rate = 1.0;
      this.voice = null;
      this.onstart = null;
      this.onend = null;
      this.onerror = null;
    }
  }

  class MockSpeechRecognition {
    constructor() {
      this.lang = "";
      this.interimResults = false;
      this.continuous = false;
      this.maxAlternatives = 1;
      this.onstart = null;
      this.onresult = null;
      this.onerror = null;
      this.onend = null;
      activeRecognition = this;
    }
    start() {
      recognitionStartCount += 1;
      events.push(`rec:start#${recognitionStartCount}`);
      if (this.onstart) this.onstart();
    }
    stop() {
      events.push("rec:stop");
      if (this.onend) this.onend();
    }
    abort() {
      events.push("rec:abort");
      if (this.onerror) this.onerror({ error: "aborted" });
      if (this.onend) this.onend();
    }
  }

  const windowObj = {
    SpeechSynthesisUtterance: MockUtterance,
    SpeechRecognition: MockSpeechRecognition,
    speechSynthesis: {
      cancel() {
        speechCancelCount += 1;
        events.push(`tts:cancel#${speechCancelCount}`);
        activeUtterance = null;
      },
      speak(utter) {
        activeUtterance = utter;
        events.push(`tts:speak:${utter.text.slice(0, 24)}`);
        if (utter.onstart) utter.onstart();
      },
    },
    setTimeout,
    clearTimeout,
  };

  const sandbox = { window: windowObj, console, setTimeout, clearTimeout };
  vm.createContext(sandbox);
  vm.runInContext(voiceJsSource, sandbox);

  return {
    window: windowObj,
    SenseGraphVoice: windowObj.SenseGraphVoice,
    events,
    getActiveUtterance: () => activeUtterance,
    getActiveRecognition: () => activeRecognition,
    getRecognitionStartCount: () => recognitionStartCount,
    getSpeechCancelCount: () => speechCancelCount,
  };
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function testGuidedTurnTakingOrderAndNoPrematureCancel() {
  const env = createMockEnv();
  const { ConversationController, LearningSessionController } = env.SenseGraphVoice;

  let speechToken = 0;
  let ctrl = null;

  const speak = (text) => {
    speechToken += 1;
    const token = speechToken;
    env.window.speechSynthesis.cancel();
    const u = new env.window.SpeechSynthesisUtterance(text);
    u.onstart = () => {
      if (token !== speechToken) return;
      ctrl.notifySpeaking(true);
    };
    u.onend = () => {
      if (token !== speechToken) return;
      ctrl.notifySpeaking(false, "ended");
    };
    u.onerror = () => {
      if (token !== speechToken) return;
      ctrl.notifySpeaking(false, "error");
    };
    env.window.speechSynthesis.speak(u);
  };

  const stopSpeech = () => {
    speechToken += 1;
    env.window.speechSynthesis.cancel();
    ctrl.notifySpeaking(false, "cancelled");
  };

  ctrl = new ConversationController({
    getContext: () => ({ step: "subjects", domain: null, availableOptions: [] }),
    stopAppSpeech: stopSpeech,
    announceResponse: speak,
    onUiUpdate: () => {},
    interpreter: {
      async interpret(transcript) {
        if (transcript.toLowerCase().includes("stop listening")) {
          return {
            intent: "navigate",
            action: "stop_guided_voice",
            parameters: {},
            spoken_response: "Guided voice conversation paused.",
          };
        }
        return {
          intent: "select_subject",
          action: "select_subject",
          parameters: { domain: "physics_circuit" },
          spoken_response: "Showing Physics lessons.",
        };
      },
    },
    sessionController: new LearningSessionController({
      selectSubject: () => {
        speak("Showing Physics lessons. Say Beginner to start.");
        return "Showing Physics lessons. Say Beginner to start.";
      },
      stopGuidedVoice: () => {
        ctrl.stopGuidedConversation(true);
        return "Guided voice conversation paused.";
      },
    }),
  });

  // 1. Start Guided Conversation with intro text
  const started = ctrl.startGuidedConversation("Guided voice started. Choose Physics or Biology.");
  assert.equal(started, true);
  assert.equal(ctrl.guidedTurnTaking, true);
  assert.equal(ctrl.micState, "speaking");
  // Intro must NOT have been cancelled by startListening()
  assert.ok(env.getActiveUtterance(), "Intro utterance must still be active while speaking");
  assert.equal(env.getRecognitionStartCount(), 0, "Mic must NOT start before TTS onend");

  // 2. Natural TTS onend fires -> wait 420ms -> recognition starts for 1 bounded turn
  env.getActiveUtterance().onend();
  assert.equal(env.getRecognitionStartCount(), 0, "Mic waits brief turn pause after onend");
  await wait(420);
  assert.equal(env.getRecognitionStartCount(), 1, "Mic activates after natural TTS onend");
  assert.equal(ctrl.micState, "listening");

  // 3. Duplicate startListening() while already listening must be ignored
  const dup = ctrl.startListening();
  assert.equal(dup, false);
  assert.equal(env.getRecognitionStartCount(), 1, "Must not start duplicate recognition session");

  // 4. Learner speaks "Physics" -> interprets -> speaks reply -> onend -> next turn opens
  env.getActiveRecognition().onresult({ results: [[{ transcript: "Physics" }]] });
  await wait(20);
  assert.equal(ctrl.micState, "speaking");
  env.getActiveUtterance().onend();
  await wait(420);
  assert.equal(env.getRecognitionStartCount(), 2, "Second turn opens after reply onend");

  // 5. Learner says "Stop listening" -> guidedTurnTaking stops and NO 3rd turn opens
  env.getActiveRecognition().onresult({ results: [[{ transcript: "Stop listening" }]] });
  await wait(20);
  assert.equal(ctrl.guidedTurnTaking, false);
  if (env.getActiveUtterance() && env.getActiveUtterance().onend) {
    env.getActiveUtterance().onend();
  }
  await wait(420);
  assert.equal(env.getRecognitionStartCount(), 2, "Must not open new turn after Stop listening");
}

async function testCancellationAndErrorNeverAutoStartMic() {
  const env = createMockEnv();
  const { ConversationController, LearningSessionController } = env.SenseGraphVoice;

  let ctrl = null;
  const speak = (text) => {
    const u = new env.window.SpeechSynthesisUtterance(text);
    u.onstart = () => ctrl.notifySpeaking(true);
    u.onend = () => ctrl.notifySpeaking(false, "ended");
    u.onerror = () => ctrl.notifySpeaking(false, "error");
    env.window.speechSynthesis.speak(u);
  };

  ctrl = new ConversationController({
    getContext: () => ({ step: "explore" }),
    stopAppSpeech: () => {
      env.window.speechSynthesis.cancel();
      ctrl.notifySpeaking(false, "cancelled");
    },
    announceResponse: speak,
    onUiUpdate: () => {},
    interpreter: { async interpret() { return { intent: "clarify", action: "clarify", spoken_response: "?" }; } },
    sessionController: new LearningSessionController({}),
  });

  // Case A: Explicit stopAppSpeech ("cancelled") must NOT start mic
  ctrl.startGuidedConversation("Hello learner.");
  ctrl.notifySpeaking(false, "cancelled");
  await wait(420);
  assert.equal(env.getRecognitionStartCount(), 0, "Cancelled TTS must not trigger mic");

  // Case B: Speech synthesis error ("error") must disable guidedTurnTaking and NOT start mic
  ctrl.startGuidedConversation("Hello again.");
  env.getActiveUtterance().onerror();
  await wait(420);
  assert.equal(ctrl.guidedTurnTaking, false, "TTS error should safely pause guided turn-taking");
  assert.equal(env.getRecognitionStartCount(), 0, "Errored TTS must not trigger mic");
}

async function testPermissionDenialAndTimeoutRecovery() {
  const env = createMockEnv();
  const { ConversationController, LearningSessionController } = env.SenseGraphVoice;
  const announcements = [];

  const ctrl = new ConversationController({
    getContext: () => ({ step: "subjects" }),
    stopAppSpeech: () => {},
    announceResponse: (msg) => announcements.push(msg),
    onUiUpdate: () => {},
    interpreter: { async interpret() { return { intent: "clarify", action: "clarify", spoken_response: "?" }; } },
    sessionController: new LearningSessionController({}),
  });

  // Override timeout to 80ms for fast deterministic testing
  ctrl.input.listeningTimeoutMs = 80;
  ctrl.guidedTurnTaking = true;
  ctrl.startListening();
  assert.equal(ctrl.micState, "listening");

  // Permission denied -> stops guidedTurnTaking, announces recovery guidance
  env.getActiveRecognition().onerror({ error: "not-allowed" });
  assert.equal(ctrl.guidedTurnTaking, false);
  assert.equal(ctrl.micState, "error");
  assert.ok(announcements.some((m) => m.toLowerCase().includes("permission was denied")));

  // Timeout recovery -> stops cleanly after bounded window
  ctrl.guidedTurnTaking = true;
  ctrl.startListening();
  await wait(140);
  assert.equal(ctrl.guidedTurnTaking, false, "Silence timeout must stop guided loop");
  assert.equal(ctrl.micState, "ready");
  assert.ok(announcements.some((m) => m.toLowerCase().includes("timed out")));
}

await testGuidedTurnTakingOrderAndNoPrematureCancel();
await testCancellationAndErrorNeverAutoStartMic();
await testPermissionDenialAndTimeoutRecovery();
console.log("ALL_VOICE_TURN_TAKING_TESTS_PASSED");
