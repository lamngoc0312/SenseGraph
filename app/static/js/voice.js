/* SenseGraph Phase 15 + Non-Visual Redesign — Modular Conversational Voice Layer
 *
 * Architecture:
 *  - SpeechInputAdapter: feature-detected browser SpeechRecognition with bounded listening timeout
 *  - SpeechOutputAdapter: optional browser SpeechSynthesis with feedback-loop protection
 *  - VoiceCommandInterpreter: controlled backend intent parser (/api/voice/interpret)
 *  - LearningSessionController: safe allowlisted bridge to verified SenseGraph student actions
 *  - ConversationController: orchestrates Push-to-Talk AND optional Guided Turn-Taking
 *    (TTS finishes -> gentle listening cue -> bounded listening window -> interpret -> reply)
 */

(() => {
  "use strict";

  function playListeningCue() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(520, now);
      osc.frequency.linearRampToValueAtTime(660, now + 0.11);
      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.08, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.15);
      osc.onended = () => {
        if (typeof ctx.close === "function") ctx.close().catch(() => {});
      };
    } catch {
      // AudioContext unavailable or blocked; degrade silently
    }
  }

  class SpeechInputAdapter {
    constructor(options = {}) {
      this.lang = options.lang || "en-US";
      this.listeningTimeoutMs = options.listeningTimeoutMs || 8000;
      this.onStateChange = options.onStateChange || (() => {});
      this.onResult = options.onResult || (() => {});
      this.onError = options.onError || (() => {});
      this._recognition = null;
      this._isListening = false;
      this._cancelled = false;
      this._timeoutHandle = null;
    }

    static isSupported() {
      return (
        typeof window !== "undefined" &&
        (typeof window.SpeechRecognition === "function" ||
          typeof window.webkitSpeechRecognition === "function")
      );
    }

    isListening() {
      return this._isListening;
    }

    _clearTimer() {
      if (this._timeoutHandle) {
        window.clearTimeout(this._timeoutHandle);
        this._timeoutHandle = null;
      }
    }

    start() {
      if (!SpeechInputAdapter.isSupported()) {
        this.onStateChange("unsupported");
        this.onError(
          "Browser speech recognition is unavailable here. Use keyboard controls or type a command instead."
        );
        return false;
      }

      if (this._isListening) {
        this.cancel();
      }

      const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
      const rec = new Ctor();
      rec.lang = this.lang;
      rec.interimResults = false;
      rec.continuous = false;
      rec.maxAlternatives = 1;

      this._recognition = rec;
      this._cancelled = false;

      rec.onstart = () => {
        this._isListening = true;
        this.onStateChange("listening");
        playListeningCue();
        // Enforce bounded listening window — never listen indefinitely in background.
        this._clearTimer();
        this._timeoutHandle = window.setTimeout(() => {
          if (this._isListening) {
            this._cancelled = true;
            try {
              rec.stop();
            } catch {
              // Ignore stop error
            }
            this._isListening = false;
            this.onStateChange("ready");
            this.onError(
              "Listening timed out after 8 seconds of silence. Press Speak Now or use keyboard controls."
            );
          }
        }, this.listeningTimeoutMs);
      };

      rec.onresult = (event) => {
        this._clearTimer();
        this._isListening = false;
        if (this._cancelled) return;
        const transcript =
          event.results &&
          event.results[0] &&
          event.results[0][0] &&
          event.results[0][0].transcript
            ? event.results[0][0].transcript.trim()
            : "";
        if (!transcript) {
          this.onStateChange("ready");
          this.onError("No speech was detected. Try speaking again or use the keyboard.");
          return;
        }
        this.onStateChange("processing");
        this.onResult(transcript);
      };

      rec.onerror = (event) => {
        this._clearTimer();
        this._isListening = false;
        if (this._cancelled && event.error === "aborted") {
          this.onStateChange("ready");
          return;
        }
        this.onStateChange("error");
        const errorMap = {
          "not-allowed":
            "Microphone permission was denied. You can continue using keyboard controls or type your command.",
          "service-not-allowed":
            "Speech recognition service is blocked by this browser. Use keyboard controls or type your command.",
          "no-speech":
            "No speech detected. Press Speak Now when you are ready, or use the keyboard.",
          network:
            "Speech recognition requires a network connection in this browser. Use keyboard controls or type your command.",
          aborted: "Listening stopped.",
        };
        this.onError(
          errorMap[event.error] ||
            `Voice input error (${event.error || "unknown"}). Use keyboard controls or try again.`
        );
      };

      rec.onend = () => {
        this._clearTimer();
        const wasListening = this._isListening;
        this._isListening = false;
        if (wasListening && !this._cancelled) {
          this.onStateChange("ready");
        }
      };

      try {
        rec.start();
        return true;
      } catch (err) {
        this._clearTimer();
        this._isListening = false;
        this.onStateChange("error");
        this.onError(`Could not start microphone: ${err.message}`);
        return false;
      }
    }

    stop() {
      this._clearTimer();
      if (this._recognition && this._isListening) {
        try {
          this._recognition.stop();
        } catch {
          // Ignore already-stopped recognition instance
        }
      }
      this._isListening = false;
    }

    cancel() {
      this._clearTimer();
      this._cancelled = true;
      if (this._recognition) {
        try {
          this._recognition.abort();
        } catch {
          // Ignore abort errors
        }
      }
      this._isListening = false;
      this.onStateChange("ready");
    }
  }

  class SpeechOutputAdapter {
    constructor(options = {}) {
      this.getRate = options.getRate || (() => 1.0);
      this.getVoice = options.getVoice || (() => null);
      this.onStart = options.onStart || (() => {});
      this.onEnd = options.onEnd || (() => {});
    }

    static isSupported() {
      return (
        typeof window !== "undefined" &&
        "speechSynthesis" in window &&
        typeof window.SpeechSynthesisUtterance === "function"
      );
    }

    stop() {
      if (SpeechOutputAdapter.isSupported()) {
        window.speechSynthesis.cancel();
      }
      this.onEnd();
    }

    speak(text) {
      if (!text || !SpeechOutputAdapter.isSupported()) return false;
      window.speechSynthesis.cancel();
      const utter = new window.SpeechSynthesisUtterance(text);
      utter.rate = this.getRate();
      const voice = this.getVoice();
      if (voice) utter.voice = voice;
      utter.onstart = () => this.onStart();
      utter.onend = () => this.onEnd();
      utter.onerror = () => this.onEnd();
      window.speechSynthesis.speak(utter);
      return true;
    }
  }

  class VoiceCommandInterpreter {
    constructor(apiRequestFn) {
      this.apiRequest = apiRequestFn;
    }

    async interpret(transcript, context) {
      const payload = {
        transcript,
        step: context.step || "welcome",
        domain: context.domain || null,
        selected_node_id: context.selectedNodeId || null,
        challenge_id: context.challengeId || null,
        available_options: context.availableOptions || [],
        diagram: context.diagram || null,
      };
      return this.apiRequest("/api/voice/interpret", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
  }

  class LearningSessionController {
    constructor(handlers) {
      this.handlers = handlers || {};
    }

    async execute(result) {
      const h = this.handlers;
      const action = result.action;
      const params = result.parameters || {};

      switch (action) {
        case "stop_guided_voice":
          return h.stopGuidedVoice ? h.stopGuidedVoice() : result.spoken_response;
        case "where_am_i":
          return h.whereAmI ? h.whereAmI() : result.spoken_response;
        case "start_learning":
          return h.startLearning ? h.startLearning() : result.spoken_response;
        case "continue_learning":
          return h.continueLearning ? h.continueLearning() : result.spoken_response;
        case "select_subject":
          return h.selectSubject ? h.selectSubject(params.domain) : result.spoken_response;
        case "select_difficulty":
          return h.selectDifficulty
            ? h.selectDifficulty(params.difficulty)
            : result.spoken_response;
        case "next":
          return h.next ? h.next() : result.spoken_response;
        case "previous":
          return h.previous ? h.previous() : result.spoken_response;
        case "repeat":
          return h.repeat ? h.repeat() : result.spoken_response;
        case "help":
          return h.help ? h.help() : result.spoken_response;
        case "go_back":
          return h.goBack ? h.goBack() : result.spoken_response;
        case "explain_component":
          return h.explainComponent ? h.explainComponent() : result.spoken_response;
        case "explain_diagram":
          return h.explainDiagram ? h.explainDiagram() : result.spoken_response;
        case "tell_me_more":
          return h.tellMeMore ? h.tellMeMore() : result.spoken_response;
        case "start_experiment":
          return h.startExperiment ? h.startExperiment() : result.spoken_response;
        case "select_option":
          return h.selectOption
            ? h.selectOption(params.option_id, params.option_label)
            : result.spoken_response;
        case "submit_answer":
          return h.submitAnswer ? h.submitAnswer() : result.spoken_response;
        case "try_again":
          return h.tryAgain ? h.tryAgain() : result.spoken_response;
        case "next_lesson":
          return h.nextLesson ? h.nextLesson() : result.spoken_response;
        case "toggle_switch":
          return h.toggleSwitch ? h.toggleSwitch() : result.spoken_response;
        case "confirm_yes":
          return h.confirmYes ? h.confirmYes() : result.spoken_response;
        case "confirm_no":
          return h.confirmNo ? h.confirmNo() : result.spoken_response;
        case "answer_tutor":
          return h.displayTutorReply
            ? h.displayTutorReply(result.tutor_response, result.spoken_response)
            : result.spoken_response;
        default:
          return result.spoken_response;
      }
    }
  }

  class ConversationController {
    constructor(config) {
      this.getContext = config.getContext;
      this.stopAppSpeech = config.stopAppSpeech || (() => {});
      this.announceResponse = config.announceResponse || (() => {});
      this.onUiUpdate = config.onUiUpdate || (() => {});
      this.interpreter = config.interpreter;
      this.sessionController = config.sessionController;
      this.micState = SpeechInputAdapter.isSupported() ? "ready" : "unsupported";
      this.guidedTurnTaking = false; // Strictly OFF by default — never auto-starts
      this._pendingTurnTimer = null;
      this.lastTranscript = "";
      this.lastReply = "";
      this.lastError = "";

      this.input = new SpeechInputAdapter({
        listeningTimeoutMs: 8000,
        onStateChange: (nextState) => {
          this.micState = nextState;
          this.emitUi();
        },
        onResult: (transcript) => {
          this.handleTranscript(transcript);
        },
        onError: (msg) => {
          this.lastError = msg;
          // Stop automatic turn loop on permission denial or error so we never loop endlessly
          this.guidedTurnTaking = false;
          this._clearPendingTurn();
          this.emitUi();
          this.announceResponse(msg);
        },
      });
    }

    _clearPendingTurn() {
      if (this._pendingTurnTimer) {
        window.clearTimeout(this._pendingTurnTimer);
        this._pendingTurnTimer = null;
      }
    }

    emitUi() {
      this.onUiUpdate({
        micState: this.micState,
        supported: SpeechInputAdapter.isSupported(),
        guidedTurnTaking: this.guidedTurnTaking,
        lastTranscript: this.lastTranscript,
        lastReply: this.lastReply,
        lastError: this.lastError,
      });
    }

    startGuidedConversation(introText = "") {
      if (!SpeechInputAdapter.isSupported()) {
        this.guidedTurnTaking = false;
        this.lastError =
          "Guided voice input requires Chrome or Edge speech recognition. Falling back to keyboard and spoken guidance.";
        this.emitUi();
        this.announceResponse(this.lastError);
        return false;
      }
      this.guidedTurnTaking = true;
      this.lastError = "";
      this.emitUi();
      if (introText) {
        this.announceResponse(introText);
      } else {
        this.startListening();
      }
      return true;
    }

    stopGuidedConversation(silent = false) {
      this.guidedTurnTaking = false;
      this._clearPendingTurn();
      this.input.cancel();
      this.micState = SpeechInputAdapter.isSupported() ? "ready" : "unsupported";
      this.emitUi();
      if (!silent) {
        this.announceResponse(
          "Guided voice conversation paused. Use keyboard controls or press Speak Now anytime."
        );
      }
    }

    startListening() {
      // Critical speech safety: stop app TTS before opening microphone
      // so SenseGraph never transcribes its own voice.
      this._clearPendingTurn();
      this.stopAppSpeech();
      this.lastError = "";
      this.input.start();
    }

    cancelListening() {
      this.guidedTurnTaking = false;
      this._clearPendingTurn();
      this.input.cancel();
      this.lastError = "";
      this.micState = SpeechInputAdapter.isSupported() ? "ready" : "unsupported";
      this.emitUi();
      this.announceResponse("Listening cancelled.");
    }

    notifySpeaking(isSpeaking) {
      if (isSpeaking) {
        this._clearPendingTurn();
        if (this.input.isListening()) {
          this.input.cancel();
        }
      }
      if (!SpeechInputAdapter.isSupported()) {
        this.micState = "unsupported";
        this.emitUi();
        return;
      }
      if (isSpeaking) {
        this.micState = "speaking";
        this.emitUi();
        return;
      }

      if (this.micState === "speaking") {
        this.micState = "ready";
        this.emitUi();
        // Guided Turn-Taking: once TTS finishes cleanly, pause 350ms then open one bounded listening turn.
        if (this.guidedTurnTaking) {
          this._clearPendingTurn();
          this._pendingTurnTimer = window.setTimeout(() => {
            if (this.guidedTurnTaking && this.micState === "ready") {
              this.input.start();
            }
          }, 350);
        }
      }
    }

    async handleTranscript(rawText) {
      const transcript = (rawText || "").trim();
      if (!transcript) return;

      this._clearPendingTurn();
      this.stopAppSpeech();
      this.lastTranscript = transcript;
      this.lastError = "";
      this.micState = "processing";
      this.emitUi();

      try {
        const ctx = this.getContext();
        const result = await this.interpreter.interpret(transcript, ctx);
        if (result.action === "stop_guided_voice") {
          this.guidedTurnTaking = false;
        }
        const actionFeedback = await this.sessionController.execute(result);
        const finalReply =
          typeof actionFeedback === "string" && actionFeedback.trim()
            ? actionFeedback
            : result.spoken_response;

        this.lastReply = finalReply;
        this.micState = SpeechInputAdapter.isSupported() ? "ready" : "unsupported";
        this.emitUi();

        if (
          result.intent === "clarify" ||
          result.intent === "tutor_question" ||
          result.intent === "select_option" ||
          result.intent === "confirm_no" ||
          result.action === "stop_guided_voice" ||
          result.action === "where_am_i"
        ) {
          this.announceResponse(finalReply);
        }
      } catch (err) {
        this.guidedTurnTaking = false;
        this.lastError = `Could not process command: ${err.message}`;
        this.micState = "error";
        this.emitUi();
        this.announceResponse(this.lastError);
      }
    }
  }

  window.SenseGraphVoice = {
    playListeningCue,
    SpeechInputAdapter,
    SpeechOutputAdapter,
    VoiceCommandInterpreter,
    LearningSessionController,
    ConversationController,
  };
})();
