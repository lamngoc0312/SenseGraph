/* SenseGraph — Phase 3 Accessible Frontend Application
 * - Uses backend REST APIs for all simulation, state evaluation, validation, and AI analysis.
 * - Preserves/restores keyboard focus across component selection, neighbor jumps, simulations,
 *   resets, and AI confirmation.
 * - Renders all untrusted/API strings via textContent (never innerHTML).
 */

(() => {
  "use strict";

  const MODULE_COPY = {
    physics_circuit: {
      heading: "Physics Explorer",
      summary:
        "Inspect a single-loop series circuit with a battery, switch, and light bulb. Toggle the switch using the Python simulation engine and read qualitative bulb state changes.",
      buttonLabel: "Explore Example Circuit",
      cardClass: "module-card-physics",
      buttonClass: "btn-primary",
    },
    biology_food_web: {
      heading: "Biology Explorer",
      summary:
        "Navigate a grassland food web where arrows show energy flow from food to consumer. Temporarily remove an organism to see exactly which relationships disappear.",
      buttonLabel: "Explore Example Food Web",
      cardClass: "module-card-biology",
      buttonClass: "btn-teal",
    },
    cs_flowchart: {
      heading: "Computer Science Explorer",
      summary:
        "Step through a restricted executable flowchart with assignments, True/False decisions, and a finite loop. Enter initial inputs and inspect every step and variable change safely.",
      buttonLabel: "Explore Example Flowchart",
      cardClass: "module-card-cs",
      buttonClass: "btn-primary",
    },
    math_plot: {
      heading: "Mathematics Explorer",
      summary:
        "Explore an XY line plot point-by-point or by intervals. Inspect exact extrema, monotonic trends, intercepts, and optional pitch sonification.",
      buttonLabel: "Explore Example Math Plot",
      cardClass: "module-card-math",
      buttonClass: "btn-teal",
    },
  };

  const state = {
    health: null,
    examples: [],
    // Explorer state
    baselineDiagram: null,
    currentDiagram: null,
    backendState: null, // Explicit backend-calculated state from POST /api/state
    selectedNodeId: null,
    lastSimulation: null,
    // Review state (AI-generated unreviewed draft)
    reviewDraft: null,
    reviewValidation: null,
    reviewArrowConfirmed: false,
    // Guided Learning Lab (session-only, per browser tab)
    explorerMode: "explore", // "explore" | "lab"
    labAvailable: false,
    labUnavailableReason: null,
    labChallenges: [],
    labIndex: 0,
    labCompletedIds: new Set(),
    labCorrectIds: new Set(),
    labCurrentResult: null,
    // Phase 6: Guided Tour & Optional TTS
    tourStep: "overview", // "overview" | "component" | "connections"
    tourText: "",
    ttsSpeaking: false,
    ttsPaused: false,
    // Phase 8: Flowchart Trace State
    flowchartTrace: null,
    flowchartStepIdx: 0,
    flowchartInputValues: {},
    // Phase 9: Mathematics Plot State
    mathAnalysis: null,
    mathPointIdx: 0,
    isBusy: false,
  };

  const dom = {
    healthBadge: document.getElementById("health-badge"),
    brandHomeLink: document.getElementById("brand-home-link"),
    statusAnnouncer: document.getElementById("status-announcer"),
    errorBanner: document.getElementById("error-banner"),
    errorBannerText: document.getElementById("error-banner-text"),
    errorDismissBtn: document.getElementById("error-dismiss-btn"),

    welcomeSection: document.getElementById("welcome-section"),
    examplesLoading: document.getElementById("examples-loading"),
    examplesGrid: document.getElementById("examples-grid"),
    aiStatusText: document.getElementById("ai-status-text"),

    // Upload / Analyze form
    analyzeForm: document.getElementById("analyze-form"),
    analyzeDomainSelect: document.getElementById("analyze-domain-select"),
    diagramFileInput: document.getElementById("diagram-file-input"),
    analyzeConsentCheckbox: document.getElementById("analyze-consent-checkbox"),
    analyzeSubmitBtn: document.getElementById("analyze-submit-btn"),
    analyzeProgress: document.getElementById("analyze-progress"),

    // Review section
    reviewSection: document.getElementById("review-section"),
    reviewCancelBtn: document.getElementById("review-cancel-btn"),
    reviewHeading: document.getElementById("review-heading"),
    reviewDomainBadge: document.getElementById("review-domain-badge"),
    reviewValidationSummary: document.getElementById("review-validation-summary"),
    reviewWarningsBlock: document.getElementById("review-warnings-block"),
    reviewWarningsList: document.getElementById("review-warnings-list"),
    reviewErrorsBlock: document.getElementById("review-errors-block"),
    reviewErrorsList: document.getElementById("review-errors-list"),
    reviewTitleInput: document.getElementById("review-title-input"),
    reviewAddNodeBtn: document.getElementById("review-add-node-btn"),
    reviewNodesList: document.getElementById("review-nodes-list"),
    reviewEdgesHint: document.getElementById("review-edges-hint"),
    reviewAddEdgeBtn: document.getElementById("review-add-edge-btn"),
    reviewEdgesList: document.getElementById("review-edges-list"),
    reviewDomainControls: document.getElementById("review-domain-controls"),
    reviewValidateBtn: document.getElementById("review-validate-btn"),
    reviewConfirmBtn: document.getElementById("review-confirm-btn"),
    reviewConfirmHint: document.getElementById("review-confirm-hint"),

    // Explorer section
    explorerSection: document.getElementById("explorer-section"),
    backToHomeBtn: document.getElementById("back-to-home-btn"),
    switchPhysicsBtn: document.getElementById("switch-physics-btn"),
    switchBiologyBtn: document.getElementById("switch-biology-btn"),
    switchCsBtn: document.getElementById("switch-cs-btn"),
    switchMathBtn: document.getElementById("switch-math-btn"),
    modeExploreBtn: document.getElementById("mode-explore-btn"),
    modeLabBtn: document.getElementById("mode-lab-btn"),
    learningLabPanel: document.getElementById("learning-lab-panel"),
    labHeading: document.getElementById("lab-heading"),
    labProgressText: document.getElementById("lab-progress-text"),
    labUnavailableMsg: document.getElementById("lab-unavailable-msg"),
    labActiveContent: document.getElementById("lab-active-content"),
    labChallengeTitle: document.getElementById("lab-challenge-title"),
    labChallengePrompt: document.getElementById("lab-challenge-prompt"),
    labChallengeHint: document.getElementById("lab-challenge-hint"),
    labPredictionForm: document.getElementById("lab-prediction-form"),
    labOptionsLegend: document.getElementById("lab-options-legend"),
    labOptionsContainer: document.getElementById("lab-options-container"),
    labSubmitBtn: document.getElementById("lab-submit-btn"),
    labRetryBtn: document.getElementById("lab-retry-btn"),
    labSkipBtn: document.getElementById("lab-skip-btn"),
    labNextBtn: document.getElementById("lab-next-btn"),
    labResetBtn: document.getElementById("lab-reset-btn"),
    labResultBox: document.getElementById("lab-result-box"),
    labResultStatus: document.getElementById("lab-result-status"),
    labResultSummary: document.getElementById("lab-result-summary"),
    labResultExplanation: document.getElementById("lab-result-explanation"),
    labResultEvidence: document.getElementById("lab-result-evidence"),
    labRelatedLinks: document.getElementById("lab-related-links"),
    labScientificNote: document.getElementById("lab-scientific-note"),
    diagramTitle: document.getElementById("diagram-title"),
    sourceBadge: document.getElementById("source-badge"),
    reviewBadge: document.getElementById("review-badge"),
    domainBadge: document.getElementById("domain-badge"),

    diagramSummary: document.getElementById("diagram-summary"),
    domainConvention: document.getElementById("domain-convention"),
    diagramStats: document.getElementById("diagram-stats"),

    // Phase 6: Guided Tour & SVG Graph
    tourStepBadge: document.getElementById("tour-step-badge"),
    tourTextOutput: document.getElementById("tour-text-output"),
    tourOverviewBtn: document.getElementById("tour-overview-btn"),
    tourPrevBtn: document.getElementById("tour-prev-btn"),
    tourNextBtn: document.getElementById("tour-next-btn"),
    tourConnectionsBtn: document.getElementById("tour-connections-btn"),
    tourBackOverviewBtn: document.getElementById("tour-back-overview-btn"),
    tourRepeatBtn: document.getElementById("tour-repeat-btn"),
    tourTtsSpeakBtn: document.getElementById("tour-tts-speak-btn"),
    tourTtsPauseBtn: document.getElementById("tour-tts-pause-btn"),
    tourTtsStopBtn: document.getElementById("tour-tts-stop-btn"),
    tourTtsRate: document.getElementById("tour-tts-rate"),
    tourTtsStatus: document.getElementById("tour-tts-status"),
    svgStateComparison: document.getElementById("svg-state-comparison"),
    semanticGraphSvg: document.getElementById("semantic-graph-svg"),

    feedbackPanel: document.getElementById("feedback-panel"),
    feedbackAnnouncement: document.getElementById("feedback-announcement"),
    feedbackChanges: document.getElementById("feedback-changes"),

    componentList: document.getElementById("component-list"),
    selectedHeading: document.getElementById("selected-heading"),
    selectedDetail: document.getElementById("selected-detail"),
    selectedRelationships: document.getElementById("selected-relationships"),

    experimentGuidance: document.getElementById("experiment-guidance"),
    flowchartInputsBlock: document.getElementById("flowchart-inputs-block"),
    experimentActions: document.getElementById("experiment-actions"),
    flowchartTracePanel: document.getElementById("flowchart-trace-panel"),
    traceStepCounter: document.getElementById("trace-step-counter"),
    traceStepAction: document.getElementById("trace-step-action"),
    traceStepVars: document.getElementById("trace-step-vars"),
    tracePrevBtn: document.getElementById("trace-prev-btn"),
    traceNextBtn: document.getElementById("trace-next-btn"),
    mathControlsPanel: document.getElementById("math-controls-panel"),
    mathPointCounter: document.getElementById("math-point-counter"),
    mathPointReadout: document.getElementById("math-point-readout"),
    mathPrevPtBtn: document.getElementById("math-prev-pt-btn"),
    mathNextPtBtn: document.getElementById("math-next-pt-btn"),
    mathSonifyPtBtn: document.getElementById("math-sonify-pt-btn"),
    mathSonifyAllBtn: document.getElementById("math-sonify-all-btn"),
    mathIntervalStart: document.getElementById("math-interval-start"),
    mathIntervalEnd: document.getElementById("math-interval-end"),
    mathCompareBtn: document.getElementById("math-compare-btn"),
    mathIntervalResult: document.getElementById("math-interval-result"),
    mathAnalysisList: document.getElementById("math-analysis-list"),
    experimentLimitation: document.getElementById("experiment-limitation"),

    allRelationsList: document.getElementById("all-relations-list"),
    visualPreviewSection: document.getElementById("visual-preview-section"),
    diagramPreviewImg: document.getElementById("diagram-preview-img"),
    diagramPreviewCaption: document.getElementById("diagram-preview-caption"),
  };

  function deepClone(obj) {
    if (typeof structuredClone === "function") {
      return structuredClone(obj);
    }
    return JSON.parse(JSON.stringify(obj));
  }

  function announce(message) {
    if (!dom.statusAnnouncer) return;
    dom.statusAnnouncer.textContent = "";
    window.requestAnimationFrame(() => {
      dom.statusAnnouncer.textContent = message;
    });
  }

  function showError(message) {
    dom.errorBannerText.textContent = message;
    dom.errorBanner.hidden = false;
  }

  function clearError(restoreFocus = false) {
    dom.errorBanner.hidden = true;
    dom.errorBannerText.textContent = "";
    if (restoreFocus) {
      if (!dom.explorerSection.hidden) {
        dom.diagramTitle.focus();
      } else if (!dom.reviewSection.hidden) {
        dom.reviewHeading.focus();
      } else {
        const heading = document.getElementById("welcome-heading");
        if (heading) {
          heading.setAttribute("tabindex", "-1");
          heading.focus();
        }
      }
    }
  }

  async function apiRequest(url, options = {}) {
    const isFormData = options.body instanceof FormData;
    const headers = {
      Accept: "application/json",
      ...(!isFormData && options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    };

    const response = await fetch(url, { ...options, headers });

    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }

    if (!response.ok) {
      const errMsg =
        (payload && payload.error && payload.error.message) ||
        `Request failed with status ${response.status}.`;
      const details =
        payload && payload.error && Array.isArray(payload.error.details)
          ? payload.error.details
          : [];
      const fullMessage =
        details.length > 0 ? `${errMsg} (${details.join(" ")})` : errMsg;
      throw new Error(fullMessage);
    }

    return payload;
  }

  async function fetchBackendState(diagram) {
    return apiRequest("/api/state", {
      method: "POST",
      body: JSON.stringify(diagram),
    });
  }

  function getNodeMap(diagram) {
    const map = new Map();
    for (const node of diagram.nodes) {
      map.set(node.id, node);
    }
    return map;
  }

  function formatDomainLabel(domain) {
    if (domain === "physics_circuit") return "Physics — Series Circuit";
    if (domain === "biology_food_web") return "Biology — Food Web";
    if (domain === "cs_flowchart") return "Computer Science — Flowchart";
    if (domain === "math_plot") return "Mathematics — XY Line Plot";
    return domain;
  }

  function formatSourceLabel(source) {
    if (source && source.mode === "fixture") {
      return "Pre-annotated demo — no AI used";
    }
    if (source && source.mode === "ai") {
      return `AI-generated (${source.provider || "gemini"}) — user reviewed`;
    }
    return "Unknown source";
  }

  function getBulbDisplayState(bulbId) {
    if (
      state.backendState &&
      state.backendState.bulb_states &&
      state.backendState.bulb_states[bulbId]
    ) {
      return state.backendState.bulb_states[bulbId];
    }
    return "unavailable";
  }

  function getSwitchDisplayState(diagram, switchId) {
    if (
      state.backendState &&
      state.backendState.switch_states &&
      state.backendState.switch_states[switchId]
    ) {
      return state.backendState.switch_states[switchId];
    }
    if (diagram.domain_model && diagram.domain_model.switch_states) {
      return diagram.domain_model.switch_states[switchId] || "unknown";
    }
    return "unknown";
  }

  function showSection(sectionName) {
    dom.welcomeSection.hidden = sectionName !== "welcome";
    dom.reviewSection.hidden = sectionName !== "review";
    dom.explorerSection.hidden = sectionName !== "explorer";
  }

  // --- Welcome & Health ---

  function renderHealth() {
    if (!state.health) return;
    if (state.health.ai_configured) {
      dom.healthBadge.textContent = "Backend ready · Gemini Vision configured";
      dom.aiStatusText.textContent =
        "Gemini Vision is configured on the server. Upload a PNG, JPEG, or WEBP diagram (max 5 MB), provide consent, and review the AI output before running experiments.";
    } else {
      dom.healthBadge.textContent = "Backend ready · Demo mode (no AI key)";
      dom.aiStatusText.textContent =
        "No Gemini API key is currently configured on the server. Pre-annotated examples above work without a key. To enable live image analysis, configure AI_PROVIDER=gemini and GEMINI_API_KEY in .env.";
    }
  }

  function renderExamplesGrid() {
    dom.examplesGrid.textContent = "";

    for (const example of state.examples) {
      const copy = MODULE_COPY[example.domain] || {
        heading: example.title,
        summary: "Explore this verified STEM diagram.",
        buttonLabel: `Explore ${example.title}`,
        cardClass: "",
        buttonClass: "btn-primary",
      };

      const card = document.createElement("article");
      card.className = `module-card ${copy.cardClass}`.trim();

      const content = document.createElement("div");

      const badge = document.createElement("span");
      badge.className = "badge badge-demo";
      badge.textContent = example.source_label || "Pre-annotated demo — no AI used";
      content.appendChild(badge);

      const heading = document.createElement("h3");
      heading.textContent = `${copy.heading}: ${example.title}`;
      content.appendChild(heading);

      const desc = document.createElement("p");
      desc.textContent = copy.summary;
      content.appendChild(desc);

      card.appendChild(content);

      const actions = document.createElement("div");
      actions.className = "module-card-actions";

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `btn ${copy.buttonClass}`;
      btn.textContent = copy.buttonLabel;
      btn.addEventListener("click", () => loadExample(example.id));
      actions.appendChild(btn);

      card.appendChild(actions);
      dom.examplesGrid.appendChild(card);
    }

    dom.examplesLoading.hidden = true;
    dom.examplesGrid.hidden = false;
  }

  // --- Phase 3: Upload & Analyze ---

  async function handleAnalyzeSubmit(event) {
    event.preventDefault();
    clearError();

    const file = dom.diagramFileInput.files && dom.diagramFileInput.files[0];
    const domain = dom.analyzeDomainSelect.value;
    const consented = dom.analyzeConsentCheckbox.checked;

    if (!file) {
      showError("Please choose a PNG, JPEG, or WEBP diagram image to analyze.");
      dom.diagramFileInput.focus();
      return;
    }

    if (!consented) {
      showError(
        "You must check the consent box before sending an image to the external AI provider."
      );
      dom.analyzeConsentCheckbox.focus();
      return;
    }

    state.isBusy = true;
    dom.analyzeSubmitBtn.disabled = true;
    dom.analyzeProgress.textContent = "Analyzing diagram with Gemini…";
    announce("Uploading diagram and analyzing with Gemini. Please wait.");

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("domain", domain);
      formData.append("consent", "true");

      const draft = await apiRequest("/api/analyze", {
        method: "POST",
        body: formData,
      });

      state.reviewDraft = draft;
      state.reviewArrowConfirmed = false;
      state.reviewValidation = await apiRequest("/api/validate", {
        method: "POST",
        body: JSON.stringify(draft),
      });

      state.isBusy = false;
      dom.analyzeSubmitBtn.disabled = false;
      dom.analyzeProgress.textContent = "";

      showSection("review");
      renderReviewWorkspace();
      dom.reviewHeading.focus();
      announce(
        `AI extraction complete for ${draft.title}. Review required before running experiments.`
      );
    } catch (err) {
      state.isBusy = false;
      dom.analyzeSubmitBtn.disabled = false;
      dom.analyzeProgress.textContent = "";
      showError(err.message);
      announce(`Analysis failed: ${err.message}`);
    }
  }

  // --- Phase 3: Human Review & Correction Workspace ---

  function syncDraftPhysicsModel(draft) {
    if (draft.domain !== "physics_circuit") return;
    const nodeIds = draft.nodes.map((n) => n.id);
    const seq = (draft.domain_model.sequence || []).filter((id) => nodeIds.includes(id));
    for (const id of nodeIds) {
      if (!seq.includes(id) && seq.length < 4) {
        seq.push(id);
      }
    }
    draft.domain_model.sequence = seq;

    const switches = draft.nodes.filter((n) => n.kind === "switch");
    if (switches.length > 0) {
      const primarySw = switches[0].id;
      const prevState =
        draft.domain_model.switch_states &&
        Object.values(draft.domain_model.switch_states)[0];
      draft.domain_model.switch_states = {
        [primarySw]: prevState === "closed" ? "closed" : "open",
      };
    }
  }

  function updateReviewConfirmButton() {
    const draft = state.reviewDraft;
    const val = state.reviewValidation;
    const isBiology = draft && draft.domain === "biology_food_web";
    const arrowOk = !isBiology || state.reviewArrowConfirmed;
    const ready = Boolean(val && val.valid && val.simulation_ready && arrowOk && !state.isBusy);

    dom.reviewConfirmBtn.disabled = !ready;

    if (!val) {
      dom.reviewConfirmHint.textContent =
        "Click Validate Diagram to check structure before confirming.";
    } else if (!val.valid || !val.simulation_ready) {
      dom.reviewConfirmHint.textContent =
        "Fix all validation errors listed above, then click Validate Diagram before confirming.";
    } else if (isBiology && !state.reviewArrowConfirmed) {
      dom.reviewConfirmHint.textContent =
        "Check the arrow-direction confirmation box above to enable Confirm & Open Explorer.";
    } else {
      dom.reviewConfirmHint.textContent =
        "Diagram passed validation. Click Confirm & Open Explorer to begin experiments.";
    }
  }

  function renderReviewValidation() {
    const draft = state.reviewDraft;
    const val = state.reviewValidation;
    if (!draft) return;

    const allWarnings = Array.from(
      new Set([...(draft.warnings || []), ...((val && val.warnings) || [])])
    );
    const errors = (val && val.errors) || [];

    if (!val) {
      dom.reviewValidationSummary.textContent =
        "Edits made. Click Validate Diagram to verify structure and simulation readiness.";
    } else if (val.valid && val.simulation_ready) {
      dom.reviewValidationSummary.textContent =
        "Validation passed: this diagram is structurally valid and ready for confirmation.";
    } else {
      dom.reviewValidationSummary.textContent =
        "Validation found issues that must be corrected before simulation can be enabled.";
    }

    dom.reviewWarningsList.textContent = "";
    if (allWarnings.length > 0) {
      for (const w of allWarnings) {
        const li = document.createElement("li");
        li.textContent = w;
        dom.reviewWarningsList.appendChild(li);
      }
      dom.reviewWarningsBlock.hidden = false;
    } else {
      dom.reviewWarningsBlock.hidden = true;
    }

    dom.reviewErrorsList.textContent = "";
    if (errors.length > 0) {
      for (const e of errors) {
        const li = document.createElement("li");
        li.textContent = e;
        dom.reviewErrorsList.appendChild(li);
      }
      dom.reviewErrorsBlock.hidden = false;
    } else {
      dom.reviewErrorsBlock.hidden = true;
    }

    updateReviewConfirmButton();
  }

  function markDraftDirty() {
    state.reviewValidation = null;
    renderReviewValidation();
  }

  function renderReviewNodes() {
    const draft = state.reviewDraft;
    if (!draft) return;
    dom.reviewNodesList.textContent = "";

    draft.nodes.forEach((node, index) => {
      const row = document.createElement("div");
      row.className = "editor-row";

      // Label input
      const labelField = document.createElement("div");
      labelField.className = "form-field";
      const labelLbl = document.createElement("label");
      const labelId = `review-node-label-${index}`;
      labelLbl.setAttribute("for", labelId);
      labelLbl.textContent = `Object ${index + 1} label (${node.id})`;
      const labelInput = document.createElement("input");
      labelInput.type = "text";
      labelInput.id = labelId;
      labelInput.value = node.label;
      labelInput.addEventListener("input", () => {
        node.label = labelInput.value;
        markDraftDirty();
      });
      labelField.appendChild(labelLbl);
      labelField.appendChild(labelInput);
      row.appendChild(labelField);

      // Kind selector (Physics) or fixed text (Biology)
      const kindField = document.createElement("div");
      kindField.className = "form-field";
      const kindLbl = document.createElement("label");
      const kindId = `review-node-kind-${index}`;
      kindLbl.setAttribute("for", kindId);
      kindLbl.textContent = "Type";
      const kindSelect = document.createElement("select");
      kindSelect.id = kindId;
      const allowedKinds =
        draft.domain === "physics_circuit"
          ? ["battery", "switch", "bulb"]
          : draft.domain === "cs_flowchart"
            ? ["start", "end", "input", "assignment", "decision"]
            : ["organism"];
      for (const k of allowedKinds) {
        const opt = document.createElement("option");
        opt.value = k;
        opt.textContent = k;
        opt.selected = node.kind === k;
        kindSelect.appendChild(opt);
      }
      kindSelect.disabled = allowedKinds.length === 1;
      kindSelect.addEventListener("change", () => {
        node.kind = kindSelect.value;
        syncDraftPhysicsModel(draft);
        markDraftDirty();
        renderReviewDomainControls();
      });
      kindField.appendChild(kindLbl);
      kindField.appendChild(kindSelect);
      row.appendChild(kindField);

      // Description input
      const descField = document.createElement("div");
      descField.className = "form-field";
      const descLbl = document.createElement("label");
      const descId = `review-node-desc-${index}`;
      descLbl.setAttribute("for", descId);
      descLbl.textContent = "Description";
      const descInput = document.createElement("input");
      descInput.type = "text";
      descInput.id = descId;
      descInput.value = node.description;
      descInput.addEventListener("input", () => {
        node.description = descInput.value;
        markDraftDirty();
      });
      descField.appendChild(descLbl);
      descField.appendChild(descInput);
      row.appendChild(descField);

      // Remove object button
      const actions = document.createElement("div");
      actions.className = "editor-row-actions";
      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "btn btn-danger btn-sm";
      removeBtn.textContent = `Remove ${node.label || node.id}`;
      removeBtn.disabled = draft.nodes.length <= 1;
      removeBtn.addEventListener("click", () => {
        const removedId = node.id;
        draft.nodes = draft.nodes.filter((n) => n.id !== removedId);
        draft.edges = draft.edges.filter(
          (e) => e.source !== removedId && e.target !== removedId
        );
        syncDraftPhysicsModel(draft);
        markDraftDirty();
        renderReviewWorkspace();
        dom.reviewAddNodeBtn.focus();
        announce(`Removed ${node.label} from draft.`);
      });
      actions.appendChild(removeBtn);
      row.appendChild(actions);

      dom.reviewNodesList.appendChild(row);
    });
  }

  function renderReviewEdges() {
    const draft = state.reviewDraft;
    if (!draft) return;
    dom.reviewEdgesList.textContent = "";

    dom.reviewEdgesHint.textContent =
      draft.domain === "biology_food_web"
        ? "Each row represents an energy_to arrow from food/prey (Source) to consumer/predator (Target). Use Swap direction if an arrow is reversed."
        : "Each row represents a wire connection between two circuit components.";

    if (draft.edges.length === 0) {
      const p = document.createElement("p");
      p.className = "empty-relation";
      p.textContent = "No connections yet. Use Add connection to define relationships.";
      dom.reviewEdgesList.appendChild(p);
      return;
    }

    draft.edges.forEach((edge, index) => {
      const row = document.createElement("div");
      row.className = "editor-row";

      // Source dropdown
      const srcField = document.createElement("div");
      srcField.className = "form-field";
      const srcLbl = document.createElement("label");
      const srcId = `review-edge-src-${index}`;
      srcLbl.setAttribute("for", srcId);
      srcLbl.textContent =
        draft.domain === "biology_food_web" ? "Food / prey (Source)" : "Component A";
      const srcSelect = document.createElement("select");
      srcSelect.id = srcId;
      for (const n of draft.nodes) {
        const opt = document.createElement("option");
        opt.value = n.id;
        opt.textContent = `${n.label} (${n.id})`;
        opt.selected = edge.source === n.id;
        srcSelect.appendChild(opt);
      }
      srcSelect.addEventListener("change", () => {
        edge.source = srcSelect.value;
        markDraftDirty();
      });
      srcField.appendChild(srcLbl);
      srcField.appendChild(srcSelect);
      row.appendChild(srcField);

      // Target dropdown
      const tgtField = document.createElement("div");
      tgtField.className = "form-field";
      const tgtLbl = document.createElement("label");
      const tgtId = `review-edge-tgt-${index}`;
      tgtLbl.setAttribute("for", tgtId);
      tgtLbl.textContent =
        draft.domain === "biology_food_web" ? "Consumer / predator (Target)" : "Component B";
      const tgtSelect = document.createElement("select");
      tgtSelect.id = tgtId;
      for (const n of draft.nodes) {
        const opt = document.createElement("option");
        opt.value = n.id;
        opt.textContent = `${n.label} (${n.id})`;
        opt.selected = edge.target === n.id;
        tgtSelect.appendChild(opt);
      }
      tgtSelect.addEventListener("change", () => {
        edge.target = tgtSelect.value;
        markDraftDirty();
      });
      tgtField.appendChild(tgtLbl);
      tgtField.appendChild(tgtSelect);
      row.appendChild(tgtField);

      if (draft.domain === "cs_flowchart") {
        const relField = document.createElement("div");
        relField.className = "form-field";
        const relLbl = document.createElement("label");
        const relId = `review-edge-rel-${index}`;
        relLbl.setAttribute("for", relId);
        relLbl.textContent = "Branch / Flow";
        const relSel = document.createElement("select");
        relSel.id = relId;
        for (const r of ["flow", "branch_true", "branch_false"]) {
          const opt = document.createElement("option");
          opt.value = r;
          opt.textContent = r;
          opt.selected = edge.relation === r;
          relSel.appendChild(opt);
        }
        relSel.addEventListener("change", () => {
          edge.relation = relSel.value;
          markDraftDirty();
        });
        relField.appendChild(relLbl);
        relField.appendChild(relSel);
        row.appendChild(relField);
      }

      // Description
      const descField = document.createElement("div");
      descField.className = "form-field";
      const descLbl = document.createElement("label");
      const descId = `review-edge-desc-${index}`;
      descLbl.setAttribute("for", descId);
      descLbl.textContent = "Description";
      const descInput = document.createElement("input");
      descInput.type = "text";
      descInput.id = descId;
      descInput.value = edge.description;
      descInput.addEventListener("input", () => {
        edge.description = descInput.value;
        markDraftDirty();
      });
      descField.appendChild(descLbl);
      descField.appendChild(descInput);
      row.appendChild(descField);

      // Actions: Swap (biology) + Delete
      const actions = document.createElement("div");
      actions.className = "editor-row-actions";

      if (draft.domain === "biology_food_web") {
        const swapBtn = document.createElement("button");
        swapBtn.type = "button";
        swapBtn.className = "btn btn-secondary btn-sm";
        swapBtn.textContent = "Swap direction";
        swapBtn.addEventListener("click", () => {
          const prevSrc = edge.source;
          edge.source = edge.target;
          edge.target = prevSrc;
          markDraftDirty();
          renderReviewEdges();
          const newSwapBtn = dom.reviewEdgesList.querySelector(
            `[data-swap-edge="${index}"]`
          );
          if (newSwapBtn) newSwapBtn.focus();
          announce(`Swapped arrow direction for connection ${index + 1}.`);
        });
        swapBtn.dataset.swapEdge = String(index);
        actions.appendChild(swapBtn);
      }

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn btn-danger btn-sm";
      delBtn.textContent = "Delete";
      delBtn.addEventListener("click", () => {
        draft.edges.splice(index, 1);
        markDraftDirty();
        renderReviewEdges();
        dom.reviewAddEdgeBtn.focus();
        announce(`Deleted connection ${index + 1}.`);
      });
      actions.appendChild(delBtn);
      row.appendChild(actions);

      dom.reviewEdgesList.appendChild(row);
    });
  }

  function renderReviewDomainControls() {
    const draft = state.reviewDraft;
    if (!draft) return;
    dom.reviewDomainControls.textContent = "";

    if (draft.domain === "physics_circuit") {
      syncDraftPhysicsModel(draft);

      const hint = document.createElement("p");
      hint.className = "panel-hint";
      hint.textContent =
        "Verify the single-loop series sequence order (3 or 4 components) and the initial switch state.";
      dom.reviewDomainControls.appendChild(hint);

      const seqGrid = document.createElement("div");
      seqGrid.className = "sequence-grid";

      const slotCount = Math.min(Math.max(draft.nodes.length, 3), 4);
      while (draft.domain_model.sequence.length < slotCount && draft.nodes.length > 0) {
        draft.domain_model.sequence.push(draft.nodes[0].id);
      }
      draft.domain_model.sequence = draft.domain_model.sequence.slice(0, slotCount);

      draft.domain_model.sequence.forEach((compId, slotIdx) => {
        const field = document.createElement("div");
        field.className = "form-field";
        const lbl = document.createElement("label");
        const selectId = `review-seq-slot-${slotIdx}`;
        lbl.setAttribute("for", selectId);
        lbl.textContent = `Loop position ${slotIdx + 1}`;
        const sel = document.createElement("select");
        sel.id = selectId;
        for (const n of draft.nodes) {
          const opt = document.createElement("option");
          opt.value = n.id;
          opt.textContent = `${n.label} (${n.kind})`;
          opt.selected = compId === n.id;
          sel.appendChild(opt);
        }
        sel.addEventListener("change", () => {
          draft.domain_model.sequence[slotIdx] = sel.value;
          markDraftDirty();
        });
        field.appendChild(lbl);
        field.appendChild(sel);
        seqGrid.appendChild(field);
      });
      dom.reviewDomainControls.appendChild(seqGrid);

      const switches = draft.nodes.filter((n) => n.kind === "switch");
      if (switches.length > 0) {
        const swNode = switches[0];
        const swField = document.createElement("div");
        swField.className = "form-field";
        const swLbl = document.createElement("label");
        swLbl.setAttribute("for", "review-switch-state");
        swLbl.textContent = `Initial state of ${swNode.label}`;
        const swSel = document.createElement("select");
        swSel.id = "review-switch-state";
        const currentVal = draft.domain_model.switch_states[swNode.id] || "open";
        for (const st of ["open", "closed"]) {
          const opt = document.createElement("option");
          opt.value = st;
          opt.textContent = st;
          opt.selected = currentVal === st;
          swSel.appendChild(opt);
        }
        swSel.addEventListener("change", () => {
          draft.domain_model.switch_states = { [swNode.id]: swSel.value };
          markDraftDirty();
        });
        swField.appendChild(swLbl);
        swField.appendChild(swSel);
        dom.reviewDomainControls.appendChild(swField);
      }
    } else if (draft.domain === "biology_food_web") {
      const box = document.createElement("div");
      box.className = "consent-box";

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = "review-arrow-confirm";
      checkbox.checked = state.reviewArrowConfirmed;
      checkbox.addEventListener("change", () => {
        state.reviewArrowConfirmed = checkbox.checked;
        updateReviewConfirmButton();
      });

      const label = document.createElement("label");
      label.setAttribute("for", "review-arrow-confirm");
      label.textContent =
        "I confirm that every feeding arrow above points from food/prey (Source) to consumer/predator (Target).";

      box.appendChild(checkbox);
      box.appendChild(label);
      dom.reviewDomainControls.appendChild(box);
    }
  }

  function renderReviewWorkspace() {
    const draft = state.reviewDraft;
    if (!draft) return;

    dom.reviewDomainBadge.textContent = formatDomainLabel(draft.domain);
    dom.reviewTitleInput.value = draft.title;
    renderReviewValidation();
    renderReviewNodes();
    renderReviewEdges();
    renderReviewDomainControls();
  }

  function handleAddReviewNode() {
    const draft = state.reviewDraft;
    if (!draft) return;
    const nextNum = draft.nodes.length + 1;
    let newId =
      draft.domain === "physics_circuit" ? `component_${nextNum}` : `organism_${nextNum}`;
    const existingIds = new Set(draft.nodes.map((n) => n.id));
    let suffix = nextNum;
    while (existingIds.has(newId)) {
      suffix += 1;
      newId =
        draft.domain === "physics_circuit" ? `component_${suffix}` : `organism_${suffix}`;
    }

    draft.nodes.push({
      id: newId,
      kind: draft.domain === "physics_circuit" ? "bulb" : "organism",
      label: draft.domain === "physics_circuit" ? `Component ${suffix}` : `Organism ${suffix}`,
      description: "",
      attributes: {},
    });
    syncDraftPhysicsModel(draft);
    markDraftDirty();
    renderReviewWorkspace();
    announce(`Added ${newId} to draft.`);
  }

  function handleAddReviewEdge() {
    const draft = state.reviewDraft;
    if (!draft || draft.nodes.length < 2) {
      showError("Add at least two objects before creating a connection.");
      return;
    }
    const existingIds = new Set(draft.edges.map((e) => e.id));
    let num = draft.edges.length + 1;
    const prefix = draft.domain === "physics_circuit" ? "wire" : "feeding";
    let newEdgeId = `${prefix}_${num}`;
    while (existingIds.has(newEdgeId)) {
      num += 1;
      newEdgeId = `${prefix}_${num}`;
    }

    draft.edges.push({
      id: newEdgeId,
      source: draft.nodes[0].id,
      target: draft.nodes[1].id,
      relation: draft.domain === "physics_circuit" ? "wire" : "energy_to",
      description: `${draft.nodes[0].label} to ${draft.nodes[1].label}`,
    });
    markDraftDirty();
    renderReviewEdges();
    announce(`Added connection ${newEdgeId}.`);
  }

  async function handleValidateReviewDraft() {
    if (!state.reviewDraft || state.isBusy) return;
    clearError();
    state.reviewDraft.title = dom.reviewTitleInput.value.trim() || "Untitled Diagram";
    syncDraftPhysicsModel(state.reviewDraft);

    state.isBusy = true;
    dom.reviewValidateBtn.disabled = true;

    try {
      state.reviewValidation = await apiRequest("/api/validate", {
        method: "POST",
        body: JSON.stringify(state.reviewDraft),
      });
      state.isBusy = false;
      dom.reviewValidateBtn.disabled = false;
      renderReviewValidation();
      dom.reviewValidateBtn.focus();

      if (state.reviewValidation.valid && state.reviewValidation.simulation_ready) {
        announce("Diagram passed validation and is ready to confirm.");
      } else {
        announce(
          `Validation found ${state.reviewValidation.errors.length} error(s). Please review and fix them.`
        );
      }
    } catch (err) {
      state.isBusy = false;
      dom.reviewValidateBtn.disabled = false;
      showError(`Validation request failed: ${err.message}`);
    }
  }

  async function handleConfirmReviewDraft() {
    if (!state.reviewDraft || state.isBusy) return;
    clearError();
    state.reviewDraft.title = dom.reviewTitleInput.value.trim() || "Untitled Diagram";
    syncDraftPhysicsModel(state.reviewDraft);

    state.isBusy = true;
    dom.reviewConfirmBtn.disabled = true;

    try {
      const confirmed = await apiRequest("/api/confirm", {
        method: "POST",
        body: JSON.stringify(state.reviewDraft),
      });
      const backendState = await fetchBackendState(confirmed);

      state.baselineDiagram = deepClone(confirmed);
      state.currentDiagram = deepClone(confirmed);
      state.backendState = backendState;
      state.selectedNodeId = confirmed.nodes.length > 0 ? confirmed.nodes[0].id : null;
      state.lastSimulation = null;
      state.reviewDraft = null;
      state.reviewValidation = null;
      state.explorerMode = "explore";
      state.tourStep = "overview";
      state.flowchartTrace = null;
      state.flowchartStepIdx = 0;
      state.flowchartInputValues = {};
      state.mathAnalysis = null;
      state.mathPointIdx = 0;
      if (confirmed.domain === "math_plot") {
        state.mathAnalysis = await apiRequest("/api/math/analyze", {
          method: "POST",
          body: JSON.stringify({ diagram: confirmed }),
        });
      }
      stopTts();
      resetLabState();
      await loadLabChallengesForBaseline();
      state.isBusy = false;

      showSection("explorer");
      renderExplorer();
      dom.diagramTitle.focus();
      announce(
        `Confirmed ${confirmed.title}. Ready to explore and run deterministic experiments.`
      );
    } catch (err) {
      state.isBusy = false;
      updateReviewConfirmButton();
      showError(`Could not confirm diagram: ${err.message}`);
      announce(`Confirmation failed: ${err.message}`);
    }
  }

  // --- Phase 5: Guided Learning Lab ---

  function resetLabState() {
    state.labAvailable = false;
    state.labUnavailableReason = null;
    state.labChallenges = [];
    state.labIndex = 0;
    state.labCompletedIds = new Set();
    state.labCorrectIds = new Set();
    state.labCurrentResult = null;
  }

  async function loadLabChallengesForBaseline() {
    if (!state.baselineDiagram) return;
    try {
      const resp = await apiRequest("/api/learning/challenges", {
        method: "POST",
        body: JSON.stringify(state.baselineDiagram),
      });
      state.labAvailable = Boolean(resp.available);
      state.labUnavailableReason = resp.unavailable_reason || null;
      state.labChallenges = Array.isArray(resp.challenges) ? resp.challenges : [];
      state.labIndex = 0;
      state.labCompletedIds = new Set();
      state.labCorrectIds = new Set();
      state.labCurrentResult = null;
    } catch (err) {
      state.labAvailable = false;
      state.labUnavailableReason = `Learning Lab could not be loaded: ${err.message}`;
      state.labChallenges = [];
    }
  }

  function renderModeSwitcher() {
    const isLab = state.explorerMode === "lab";
    dom.modeExploreBtn.setAttribute("aria-pressed", isLab ? "false" : "true");
    dom.modeLabBtn.setAttribute("aria-pressed", isLab ? "true" : "false");
    dom.modeExploreBtn.className = isLab ? "btn btn-secondary" : "btn btn-primary";
    dom.modeLabBtn.className = isLab ? "btn btn-teal" : "btn btn-secondary";
    dom.learningLabPanel.hidden = !isLab;
  }

  function renderLearningLab() {
    renderModeSwitcher();
    if (state.explorerMode !== "lab") return;

    if (!state.labAvailable || state.labChallenges.length === 0) {
      dom.labUnavailableMsg.textContent =
        state.labUnavailableReason ||
        "No guided learning challenges are available for this diagram.";
      dom.labUnavailableMsg.hidden = false;
      dom.labActiveContent.hidden = true;
      dom.labProgressText.textContent = "Unavailable";
      return;
    }

    dom.labUnavailableMsg.hidden = true;
    dom.labActiveContent.hidden = false;

    const total = state.labChallenges.length;
    const challenge = state.labChallenges[state.labIndex] || state.labChallenges[0];
    dom.labProgressText.textContent =
      `Challenge ${state.labIndex + 1} of ${total} · ` +
      `Answered: ${state.labCompletedIds.size}/${total} · ` +
      `Correct: ${state.labCorrectIds.size}`;

    dom.labChallengeTitle.textContent = challenge.title;
    dom.labChallengePrompt.textContent = challenge.prompt;
    dom.labChallengeHint.textContent = `Hint: ${challenge.hint}`;
    dom.labScientificNote.textContent = challenge.scientific_note;

    dom.labOptionsLegend.textContent =
      challenge.input_type === "single_choice"
        ? "Select one prediction"
        : "Select all that apply";

    dom.labOptionsContainer.textContent = "";
    const inputType = challenge.input_type === "single_choice" ? "radio" : "checkbox";
    const answered = Boolean(state.labCurrentResult);
    const prevSelected = new Set(
      (state.labCurrentResult && state.labCurrentResult.selected_option_ids) || []
    );

    challenge.options.forEach((opt, idx) => {
      const row = document.createElement("div");
      row.className = "lab-option-row";

      const input = document.createElement("input");
      input.type = inputType;
      input.id = `lab-opt-${idx}`;
      input.name = "lab-prediction";
      input.value = opt.id;
      input.disabled = answered || state.isBusy;
      if (prevSelected.has(opt.id)) {
        input.checked = true;
      }

      const label = document.createElement("label");
      label.setAttribute("for", input.id);
      label.textContent = opt.label;

      row.appendChild(input);
      row.appendChild(label);
      dom.labOptionsContainer.appendChild(row);
    });

    dom.labSubmitBtn.textContent =
      challenge.action_type === "inspect_only"
        ? "Check Prediction"
        : "Submit Prediction & Run Experiment";
    dom.labSubmitBtn.hidden = answered;
    dom.labSubmitBtn.disabled = state.isBusy;
    dom.labRetryBtn.hidden = !answered;
    dom.labNextBtn.hidden = !answered;
    dom.labNextBtn.textContent =
      state.labIndex + 1 < total ? "Next Challenge" : "Restart First Challenge";
    dom.labSkipBtn.hidden = answered || total <= 1;

    if (state.labCurrentResult) {
      const res = state.labCurrentResult;
      dom.labResultBox.hidden = false;
      dom.labResultBox.className = res.correct
        ? "lab-result-box"
        : "lab-result-box is-review";
      dom.labResultStatus.textContent = res.correct
        ? "Outcome: Prediction matched deterministic result"
        : "Outcome: Compare your prediction with the deterministic result";
      dom.labResultSummary.textContent = res.summary;
      dom.labResultExplanation.textContent = res.explanation;

      dom.labResultEvidence.textContent = "";
      for (const line of res.evidence || []) {
        const li = document.createElement("li");
        li.textContent = line;
        dom.labResultEvidence.appendChild(li);
      }

      dom.labRelatedLinks.textContent = "";
      const nodeMap = getNodeMap(state.currentDiagram);
      const uniqueRelated = Array.from(new Set(res.related_node_ids || []));
      for (const nid of uniqueRelated) {
        const node = nodeMap.get(nid);
        if (!node) continue;
        const jumpBtn = document.createElement("button");
        jumpBtn.type = "button";
        jumpBtn.className = "btn btn-secondary btn-sm";
        jumpBtn.textContent = `Inspect ${node.label}`;
        jumpBtn.addEventListener("click", () => selectNode(nid, "move_to_detail"));
        dom.labRelatedLinks.appendChild(jumpBtn);
      }
    } else {
      dom.labResultBox.hidden = true;
    }
  }

  async function setExplorerMode(mode) {
    if (state.explorerMode === mode) return;
    clearError();
    state.explorerMode = mode;

    if (mode === "lab") {
      if (state.labChallenges.length === 0 && !state.labUnavailableReason) {
        await loadLabChallengesForBaseline();
      }
      renderLearningLab();
      dom.labHeading.focus();
      announce(
        state.labAvailable
          ? `Entered Guided Learning Lab. Challenge 1 of ${state.labChallenges.length}.`
          : state.labUnavailableReason || "Guided Learning Lab is unavailable for this diagram."
      );
    } else {
      renderModeSwitcher();
      dom.modeExploreBtn.focus();
      announce("Switched to Explore Freely mode.");
    }
  }

  async function handleLabSubmit(event) {
    event.preventDefault();
    if (!state.baselineDiagram || !state.labChallenges.length || state.isBusy) return;
    clearError();

    const challenge = state.labChallenges[state.labIndex];
    const checked = Array.from(
      dom.labOptionsContainer.querySelectorAll("input:checked")
    ).map((el) => el.value);

    if (challenge.input_type === "single_choice" && checked.length === 0) {
      showError("Please choose a prediction option before submitting.");
      const firstInput = dom.labOptionsContainer.querySelector("input");
      if (firstInput) firstInput.focus();
      return;
    }

    state.isBusy = true;
    dom.labSubmitBtn.disabled = true;

    try {
      // Evaluate strictly against the confirmed baseline diagram so results are deterministic.
      const evaluation = await apiRequest("/api/learning/evaluate", {
        method: "POST",
        body: JSON.stringify({
          diagram: state.baselineDiagram,
          challenge_id: challenge.id,
          selected_option_ids: checked,
        }),
      });

      state.labCurrentResult = evaluation;
      state.labCompletedIds.add(challenge.id);
      if (evaluation.correct) {
        state.labCorrectIds.add(challenge.id);
      }

      if (evaluation.simulation_result) {
        const updated = evaluation.simulation_result.updated_diagram;
        const backendState = await fetchBackendState(updated);
        state.currentDiagram = updated;
        state.backendState = backendState;
        state.lastSimulation = {
          event: evaluation.simulation_result.event,
          announcement: evaluation.simulation_result.announcement,
          changes: evaluation.simulation_result.changes || [],
        };
        if (!state.currentDiagram.nodes.some((n) => n.id === state.selectedNodeId)) {
          state.selectedNodeId =
            state.currentDiagram.nodes.length > 0
              ? state.currentDiagram.nodes[0].id
              : null;
        }
      }

      state.isBusy = false;
      renderExplorer();
      dom.labNextBtn.focus();
      announce(`${evaluation.summary} ${evaluation.explanation}`);
    } catch (err) {
      state.isBusy = false;
      renderLearningLab();
      showError(`Learning Lab evaluation failed: ${err.message}`);
      announce(`Evaluation failed: ${err.message}`);
    }
  }

  async function restoreBaselineForLab() {
    if (!state.baselineDiagram) return;
    const restored = deepClone(state.baselineDiagram);
    const backendState = await fetchBackendState(restored);
    state.currentDiagram = restored;
    state.backendState = backendState;
    state.lastSimulation = null;
    if (!state.currentDiagram.nodes.some((n) => n.id === state.selectedNodeId)) {
      state.selectedNodeId =
        state.currentDiagram.nodes.length > 0 ? state.currentDiagram.nodes[0].id : null;
    }
  }

  async function handleLabRetry() {
    clearError();
    state.labCurrentResult = null;
    await restoreBaselineForLab();
    renderExplorer();
    dom.labHeading.focus();
    announce("Challenge reset. Make a new prediction.");
  }

  async function handleLabAdvance(wasSkipped) {
    if (!state.labChallenges.length) return;
    clearError();
    state.labIndex = (state.labIndex + 1) % state.labChallenges.length;
    state.labCurrentResult = null;
    await restoreBaselineForLab();
    renderExplorer();
    dom.labHeading.focus();
    announce(
      `${wasSkipped ? "Skipped to" : "Moved to"} challenge ${state.labIndex + 1} of ${state.labChallenges.length}: ${state.labChallenges[state.labIndex].title}.`
    );
  }

  async function handleLabResetSession() {
    clearError();
    state.labIndex = 0;
    state.labCompletedIds = new Set();
    state.labCorrectIds = new Set();
    state.labCurrentResult = null;
    await restoreBaselineForLab();
    renderExplorer();
    dom.labHeading.focus();
    announce("Guided Learning Lab session reset to Challenge 1.");
  }

  // --- Phase 6: Guided Tour, Optional User-Initiated TTS, & Responsive SVG Semantic Graph ---

  const SVG_NS = "http://www.w3.org/2000/svg";

  function createSvgEl(tag, attrs = {}) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      el.setAttribute(k, String(v));
    }
    return el;
  }

  function stopTts() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    state.ttsSpeaking = false;
    state.ttsPaused = false;
    updateTtsControls();
  }

  function updateTtsControls() {
    const supported =
      typeof window !== "undefined" &&
      "speechSynthesis" in window &&
      typeof window.SpeechSynthesisUtterance === "function";

    if (!supported) {
      dom.tourTtsSpeakBtn.disabled = true;
      dom.tourTtsPauseBtn.disabled = true;
      dom.tourTtsStopBtn.disabled = true;
      dom.tourTtsRate.disabled = true;
      dom.tourTtsStatus.textContent = "Browser speech synthesis is unavailable; text tour works normally.";
      return;
    }

    dom.tourTtsSpeakBtn.disabled = !state.tourText;
    dom.tourTtsPauseBtn.disabled = !state.ttsSpeaking;
    dom.tourTtsPauseBtn.textContent = state.ttsPaused ? "Resume" : "Pause";
    dom.tourTtsStopBtn.disabled = !state.ttsSpeaking;
    dom.tourTtsStatus.textContent = state.ttsSpeaking
      ? state.ttsPaused
        ? "Voice paused"
        : "Speaking explanation…"
      : "";
  }

  function speakCurrentTourText() {
    if (
      !state.tourText ||
      typeof window === "undefined" ||
      !("speechSynthesis" in window)
    ) {
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(state.tourText);
    utterance.rate = parseFloat(dom.tourTtsRate.value) || 1.0;
    utterance.onstart = () => {
      state.ttsSpeaking = true;
      state.ttsPaused = false;
      updateTtsControls();
    };
    utterance.onend = () => {
      state.ttsSpeaking = false;
      state.ttsPaused = false;
      updateTtsControls();
    };
    utterance.onerror = () => {
      state.ttsSpeaking = false;
      state.ttsPaused = false;
      updateTtsControls();
    };
    window.speechSynthesis.speak(utterance);
  }

  function togglePauseTts() {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    if (!state.ttsSpeaking) return;
    if (state.ttsPaused) {
      window.speechSynthesis.resume();
      state.ttsPaused = false;
    } else {
      window.speechSynthesis.pause();
      state.ttsPaused = true;
    }
    updateTtsControls();
  }

  function buildTourOverviewText(diagram) {
    const prov = formatSourceLabel(diagram.source);
    if (diagram.domain === "physics_circuit") {
      const switchNode = diagram.nodes.find((n) => n.kind === "switch");
      const swState = switchNode ? getSwitchDisplayState(diagram, switchNode.id) : "unknown";
      const bulbs = diagram.nodes.filter((n) => n.kind === "bulb");
      const bulbSummary = bulbs
        .map((b) => `${b.label} is ${getBulbDisplayState(b.id)}`)
        .join(", ");
      return (
        `Overview of ${diagram.title} (${prov}). ` +
        `This single-loop series circuit has ${diagram.nodes.length} components and ` +
        `${diagram.edges.length} wire connections. ` +
        `${switchNode ? `${switchNode.label} is ${swState}. ` : ""}` +
        `${bulbSummary ? `${bulbSummary}. ` : ""}` +
        `${diagram.summary}`
      );
    }

    return (
      `Overview of ${diagram.title} (${prov}). ` +
      `This directed food web has ${diagram.nodes.length} organisms and ` +
      `${diagram.edges.length} feeding relationships. ` +
      "Arrows point from food or prey to consumer or predator. " +
      `${diagram.summary}`
    );
  }

  function buildTourComponentText(diagram, node) {
    const idx = diagram.nodes.findIndex((n) => n.id === node.id);
    const meta = getComponentMetaText(diagram, node);
    const neighborCount = diagram.edges.filter(
      (e) => e.source === node.id || e.target === node.id
    ).length;
    return (
      `Component ${idx + 1} of ${diagram.nodes.length}: ${node.label}. ` +
      `${meta}. ${node.description} ` +
      `It has ${neighborCount} direct connection${neighborCount === 1 ? "" : "s"} in this diagram.`
    );
  }

  function buildTourConnectionsText(diagram, node) {
    const nodeMap = getNodeMap(diagram);
    if (diagram.domain === "physics_circuit") {
      const neighbors = [];
      for (const edge of diagram.edges) {
        if (edge.source === node.id && nodeMap.has(edge.target)) {
          neighbors.push(nodeMap.get(edge.target).label);
        } else if (edge.target === node.id && nodeMap.has(edge.source)) {
          neighbors.push(nodeMap.get(edge.source).label);
        }
      }
      if (neighbors.length === 0) {
        return `${node.label} currently has no wire connections in this diagram.`;
      }
      return (
        `${node.label} has ${neighbors.length} direct wire connection${neighbors.length === 1 ? "" : "s"}: ` +
        `connected to ${neighbors.join(" and ")}.`
      );
    }

    const incoming = diagram.edges
      .filter((e) => e.target === node.id && nodeMap.has(e.source))
      .map((e) => nodeMap.get(e.source).label);
    const outgoing = diagram.edges
      .filter((e) => e.source === node.id && nodeMap.has(e.target))
      .map((e) => nodeMap.get(e.target).label);

    const inPart =
      incoming.length > 0
        ? `Receives energy from ${incoming.join(", ")} (food to consumer).`
        : "Receives energy from no other organism in this diagram.";
    const outPart =
      outgoing.length > 0
        ? `Provides energy to ${outgoing.join(", ")} (food to consumer).`
        : "Provides energy to no other organism in this diagram.";

    return `Connections for ${node.label}: ${inPart} ${outPart}`;
  }

  function updateTourDisplay(step, shouldAnnounce = false) {
    const diagram = state.currentDiagram;
    if (!diagram) return;
    state.tourStep = step;

    const nodeMap = getNodeMap(diagram);
    const selectedNode = nodeMap.get(state.selectedNodeId) || diagram.nodes[0];

    if (step === "overview" || !selectedNode) {
      state.tourText = buildTourOverviewText(diagram);
      dom.tourStepBadge.textContent = "Overview";
    } else if (step === "connections") {
      state.tourText = buildTourConnectionsText(diagram, selectedNode);
      dom.tourStepBadge.textContent = `Connections: ${selectedNode.label}`;
    } else {
      const idx = diagram.nodes.findIndex((n) => n.id === selectedNode.id);
      state.tourText = buildTourComponentText(diagram, selectedNode);
      dom.tourStepBadge.textContent = `Component ${idx + 1} of ${diagram.nodes.length}: ${selectedNode.label}`;
    }

    dom.tourTextOutput.textContent = state.tourText;
    updateTtsControls();
    if (shouldAnnounce) {
      announce(state.tourText);
    }
  }

  function stepTourComponent(delta) {
    const diagram = state.currentDiagram;
    if (!diagram || diagram.nodes.length === 0) return;
    stopTts();
    const curIdx = diagram.nodes.findIndex((n) => n.id === state.selectedNodeId);
    const startIdx = curIdx >= 0 ? curIdx : 0;
    const nextIdx = (startIdx + delta + diagram.nodes.length) % diagram.nodes.length;
    const nextNode = diagram.nodes[nextIdx];

    state.selectedNodeId = nextNode.id;
    renderComponentList(diagram);
    renderSelectedDetail(diagram);
    renderExperimentControls(diagram);
    renderSemanticSvgGraph(diagram);
    updateTourDisplay("component", true);
  }

  function computeBiologyLayers(diagram) {
    // Topological layering from directed energy_to edges (pure graph structure).
    const incomingCount = new Map();
    const outgoingMap = new Map();
    for (const n of diagram.nodes) {
      incomingCount.set(n.id, 0);
      outgoingMap.set(n.id, []);
    }
    for (const e of diagram.edges) {
      if (incomingCount.has(e.target) && outgoingMap.has(e.source)) {
        incomingCount.set(e.target, incomingCount.get(e.target) + 1);
        outgoingMap.get(e.source).push(e.target);
      }
    }

    const level = new Map();
    const queue = [];
    for (const n of diagram.nodes) {
      if (incomingCount.get(n.id) === 0) {
        level.set(n.id, 0);
        queue.push(n.id);
      }
    }
    let guard = 0;
    while (queue.length > 0 && guard < 100) {
      guard += 1;
      const cur = queue.shift();
      const curLvl = level.get(cur) || 0;
      for (const nxt of outgoingMap.get(cur) || []) {
        const nextLvl = Math.max(level.get(nxt) || 0, curLvl + 1);
        level.set(nxt, nextLvl);
        queue.push(nxt);
      }
    }
    for (const n of diagram.nodes) {
      if (!level.has(n.id)) level.set(n.id, 0);
    }

    const tiers = new Map();
    for (const n of diagram.nodes) {
      const l = level.get(n.id);
      if (!tiers.has(l)) tiers.set(l, []);
      tiers.get(l).push(n);
    }

    const sortedLevels = Array.from(tiers.keys()).sort((a, b) => a - b);
    const colCount = Math.max(sortedLevels.length, 1);
    const positions = new Map();
    const width = 640;
    const height = 300;
    const padX = 95;
    const padY = 55;

    sortedLevels.forEach((lvl, colIdx) => {
      const group = tiers.get(lvl);
      const x =
        colCount === 1
          ? width / 2
          : padX + (colIdx * (width - 2 * padX)) / (colCount - 1);
      group.forEach((node, rowIdx) => {
        const y =
          group.length === 1
            ? height / 2
            : padY + (rowIdx * (height - 2 * padY)) / (group.length - 1);
        positions.set(node.id, { x, y });
      });
    });
    return positions;
  }

  function computePhysicsPositions(diagram) {
    const seq =
      (diagram.domain_model && diagram.domain_model.sequence) ||
      diagram.nodes.map((n) => n.id);
    const positions = new Map();
    if (seq.length === 3) {
      const coords = [
        { x: 140, y: 155 },
        { x: 320, y: 65 },
        { x: 500, y: 155 },
      ];
      seq.forEach((id, i) => positions.set(id, coords[i]));
    } else {
      const coords = [
        { x: 140, y: 85 },
        { x: 500, y: 85 },
        { x: 500, y: 215 },
        { x: 140, y: 215 },
      ];
      seq.forEach((id, i) => positions.set(id, coords[i % coords.length]));
    }
    return positions;
  }

  function updateSvgComparisonBadge(diagram) {
    if (!state.baselineDiagram) {
      dom.svgStateComparison.textContent = "Baseline state";
      return;
    }

    if (diagram.domain === "physics_circuit") {
      const baseSw = Object.values(
        state.baselineDiagram.domain_model.switch_states || {}
      )[0];
      const curSw = Object.values(diagram.domain_model.switch_states || {})[0];
      const bulbsOn = state.backendState && state.backendState.bulbs_on;
      if (baseSw === curSw) {
        dom.svgStateComparison.textContent = `Baseline state · Switch ${curSw} · Bulb ${bulbsOn ? "ON" : "OFF"}`;
      } else {
        dom.svgStateComparison.textContent = `Experiment changed · Baseline: ${baseSw} -> Current: ${curSw} (Bulb ${bulbsOn ? "ON" : "OFF"})`;
      }
      return;
    }

    const baseNodes = state.baselineDiagram.nodes.length;
    const baseEdges = state.baselineDiagram.edges.length;
    const curNodes = diagram.nodes.length;
    const curEdges = diagram.edges.length;
    if (baseNodes === curNodes && baseEdges === curEdges) {
      dom.svgStateComparison.textContent = `Baseline state · ${curNodes} organisms, ${curEdges} relationships`;
    } else {
      dom.svgStateComparison.textContent = `Experiment changed · Baseline: ${baseNodes} organisms / ${baseEdges} edges -> Current: ${curNodes} / ${curEdges}`;
    }
  }

  function renderSemanticSvgGraph(diagram) {
    const svg = dom.semanticGraphSvg;
    if (!svg || !diagram) return;
    svg.textContent = "";
    updateSvgComparisonBadge(diagram);

    // Arrowhead markers for directed Biology edges
    const defs = createSvgEl("defs");
    const markerNormal = createSvgEl("marker", {
      id: "arrow-head",
      viewBox: "0 0 10 10",
      refX: "9",
      refY: "5",
      markerWidth: "7",
      markerHeight: "7",
      orient: "auto-start-reverse",
    });
    markerNormal.appendChild(createSvgEl("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#64748b" }));
    defs.appendChild(markerNormal);

    const markerHighlight = createSvgEl("marker", {
      id: "arrow-head-highlight",
      viewBox: "0 0 10 10",
      refX: "9",
      refY: "5",
      markerWidth: "7",
      markerHeight: "7",
      orient: "auto-start-reverse",
    });
    markerHighlight.appendChild(
      createSvgEl("path", { d: "M 0 0 L 10 5 L 0 10 z", fill: "#1d4ed8" })
    );
    defs.appendChild(markerHighlight);
    svg.appendChild(defs);

    const positions =
      diagram.domain === "physics_circuit"
        ? computePhysicsPositions(diagram)
        : computeBiologyLayers(diagram);

    const connectedToSelected = new Set();
    for (const e of diagram.edges) {
      if (e.source === state.selectedNodeId) connectedToSelected.add(e.target);
      if (e.target === state.selectedNodeId) connectedToSelected.add(e.source);
    }

    const isOpenCircuit =
      diagram.domain === "physics_circuit" &&
      state.backendState &&
      state.backendState.bulbs_on === false;

    // Render edges first
    for (const edge of diagram.edges) {
      const p1 = positions.get(edge.source);
      const p2 = positions.get(edge.target);
      if (!p1 || !p2) continue;

      const isHighlighted =
        edge.source === state.selectedNodeId || edge.target === state.selectedNodeId;
      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const dist = Math.hypot(dx, dy) || 1;
      const padStart = 58;
      const padEnd = diagram.domain === "biology_food_web" ? 64 : 58;
      const x1 = p1.x + (dx / dist) * Math.min(padStart, dist / 3);
      const y1 = p1.y + (dy / dist) * Math.min(padStart, dist / 3);
      const x2 = p2.x - (dx / dist) * Math.min(padEnd, dist / 3);
      const y2 = p2.y - (dy / dist) * Math.min(padEnd, dist / 3);

      const lineClasses = ["svg-edge"];
      if (isHighlighted) lineClasses.push("svg-edge-highlight");
      if (isOpenCircuit) lineClasses.push("svg-edge-open");

      const lineAttrs = {
        x1: x1.toFixed(1),
        y1: y1.toFixed(1),
        x2: x2.toFixed(1),
        y2: y2.toFixed(1),
        class: lineClasses.join(" "),
      };
      if (diagram.domain === "biology_food_web" || diagram.domain === "cs_flowchart") {
        lineAttrs["marker-end"] = isHighlighted
          ? "url(#arrow-head-highlight)"
          : "url(#arrow-head)";
      }
      svg.appendChild(createSvgEl("line", lineAttrs));

      if (
        diagram.domain === "cs_flowchart" &&
        (edge.relation === "branch_true" || edge.relation === "branch_false")
      ) {
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2 - 6;
        const lbl = createSvgEl("text", { x: mx.toFixed(1), y: my.toFixed(1), class: "svg-edge-label" });
        lbl.textContent = edge.relation === "branch_true" ? "TRUE" : "FALSE";
        svg.appendChild(lbl);
      }
    }

    // Render nodes
    for (const node of diagram.nodes) {
      const pos = positions.get(node.id);
      if (!pos) continue;

      const g = createSvgEl("g", {
        class: "svg-node",
        transform: `translate(${pos.x}, ${pos.y})`,
      });

      const classes = ["svg-node"];
      if (node.id === state.selectedNodeId) classes.push("svg-node-selected");
      else if (connectedToSelected.has(node.id)) classes.push("svg-node-connected");

      let subLabel = node.kind.toUpperCase();
      if (diagram.domain === "physics_circuit") {
        if (node.kind === "switch") {
          subLabel = `SWITCH · ${getSwitchDisplayState(diagram, node.id).toUpperCase()}`;
        } else if (node.kind === "bulb") {
          const bState = getBulbDisplayState(node.id);
          subLabel = `BULB · ${bState.toUpperCase()}`;
          if (bState === "on") classes.push("svg-node-bulb-on");
        } else {
          subLabel = "BATTERY (+ / -)";
        }
      } else {
        subLabel = "ORGANISM";
      }
      g.setAttribute("class", classes.join(" "));

      if (node.kind === "bulb") {
        g.appendChild(
          createSvgEl("ellipse", {
            cx: 0,
            cy: 0,
            rx: 56,
            ry: 32,
            class: "svg-node-shape",
          })
        );
      } else {
        g.appendChild(
          createSvgEl("rect", {
            x: -60,
            y: -28,
            width: 120,
            height: 56,
            rx: node.kind === "organism" ? 20 : 8,
            class: "svg-node-shape",
          })
        );
      }

      const titleText = createSvgEl("text", { x: 0, y: -3, class: "svg-node-title" });
      titleText.textContent = node.label;
      g.appendChild(titleText);

      const subText = createSvgEl("text", { x: 0, y: 15, class: "svg-node-sub" });
      subText.textContent = subLabel;
      g.appendChild(subText);

      g.addEventListener("click", () => selectNode(node.id, "move_to_detail"));
      svg.appendChild(g);
    }
  }

  // --- Shared Explorer (Fixtures & Confirmed AI Diagrams) ---

  function renderStats(diagram) {
    dom.diagramStats.textContent = "";

    const stats = [];
    if (diagram.domain === "physics_circuit") {
      stats.push({ label: "Components", value: String(diagram.nodes.length) });
      stats.push({ label: "Wire Connections", value: String(diagram.edges.length) });

      const switchStates =
        (state.backendState && state.backendState.switch_states) ||
        diagram.domain_model.switch_states ||
        {};
      const switchEntries = Object.entries(switchStates);
      if (switchEntries.length > 0) {
        const [, swState] = switchEntries[0];
        stats.push({
          label: "Switch State",
          value: swState.charAt(0).toUpperCase() + swState.slice(1),
        });
      }

      const bulbs = diagram.nodes.filter((n) => n.kind === "bulb");
      for (const bulb of bulbs) {
        const bState = getBulbDisplayState(bulb.id);
        stats.push({
          label: `${bulb.label} State`,
          value: bState.toUpperCase(),
        });
      }
    } else if (diagram.domain === "biology_food_web") {
      stats.push({ label: "Organisms", value: String(diagram.nodes.length) });
      stats.push({ label: "Feeding Relationships", value: String(diagram.edges.length) });
      const removedCount = state.baselineDiagram
        ? state.baselineDiagram.nodes.length - diagram.nodes.length
        : 0;
      stats.push({ label: "Removed in Experiment", value: String(removedCount) });
    } else if (diagram.domain === "cs_flowchart") {
      stats.push({ label: "Flowchart Blocks", value: String(diagram.nodes.length) });
      stats.push({ label: "Connections", value: String(diagram.edges.length) });
      const maxSteps =
        (state.backendState && state.backendState.max_steps) ||
        (diagram.domain_model && diagram.domain_model.max_steps) ||
        100;
      stats.push({ label: "Max Steps Limit", value: String(maxSteps) });
      if (state.flowchartTrace) {
        stats.push({
          label: "Trace Status",
          value: `${state.flowchartTrace.status} (${state.flowchartTrace.steps_executed} steps)`,
        });
      }
    } else if (diagram.domain === "math_plot") {
      const dm = diagram.domain_model;
      stats.push({ label: "Data Points", value: String(dm.points.length) });
      stats.push({ label: "X Axis", value: `${dm.x_label}${dm.x_unit ? ` (${dm.x_unit})` : ""}` });
      stats.push({ label: "Y Axis", value: `${dm.y_label}${dm.y_unit ? ` (${dm.y_unit})` : ""}` });
      if (state.mathAnalysis) {
        stats.push({
          label: "Global Max",
          value: `${state.mathAnalysis.global_max.y} ${dm.y_unit}`.trim(),
        });
      }
    }

    for (const stat of stats) {
      const wrapper = document.createElement("div");
      wrapper.className = "stat-item";

      const dt = document.createElement("dt");
      dt.textContent = stat.label;
      const dd = document.createElement("dd");
      dd.textContent = stat.value;

      wrapper.appendChild(dt);
      wrapper.appendChild(dd);
      dom.diagramStats.appendChild(wrapper);
    }
  }

  function renderFeedback() {
    if (!state.lastSimulation) {
      dom.feedbackPanel.hidden = true;
      return;
    }

    dom.feedbackAnnouncement.textContent = state.lastSimulation.announcement;
    dom.feedbackChanges.textContent = "";

    for (const change of state.lastSimulation.changes || []) {
      const li = document.createElement("li");
      li.textContent = change;
      dom.feedbackChanges.appendChild(li);
    }

    dom.feedbackPanel.hidden = false;
  }

  function getComponentMetaText(diagram, node) {
    if (diagram.domain === "physics_circuit") {
      if (node.kind === "switch") {
        const swState = getSwitchDisplayState(diagram, node.id);
        return `Switch · Currently ${swState}`;
      }
      if (node.kind === "bulb") {
        const bState = getBulbDisplayState(node.id);
        return `Bulb · Currently ${bState}`;
      }
      return "Battery · Electrical energy source";
    }

    if (diagram.domain === "biology_food_web") {
      const incoming = diagram.edges.filter((e) => e.target === node.id).length;
      const outgoing = diagram.edges.filter((e) => e.source === node.id).length;
      return `Organism · Receives from ${incoming}, provides to ${outgoing}`;
    }

    return node.kind;
  }

  function renderComponentList(diagram, restoreFocusNodeId = null) {
    dom.componentList.textContent = "";

    diagram.nodes.forEach((node, index) => {
      const li = document.createElement("li");

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "component-btn";
      btn.dataset.nodeId = node.id;
      const isSelected = node.id === state.selectedNodeId;
      btn.setAttribute("aria-pressed", isSelected ? "true" : "false");

      const header = document.createElement("span");
      header.className = "component-btn-header";

      const title = document.createElement("span");
      title.className = "component-btn-title";
      title.textContent = `${index + 1}. ${node.label}`;
      header.appendChild(title);

      if (isSelected) {
        const selectedTag = document.createElement("span");
        selectedTag.className = "badge badge-domain";
        selectedTag.textContent = "Selected";
        header.appendChild(selectedTag);
      }

      const meta = document.createElement("span");
      meta.className = "component-btn-meta";
      meta.textContent = getComponentMetaText(diagram, node);

      btn.appendChild(header);
      btn.appendChild(meta);

      btn.addEventListener("click", () => selectNode(node.id, "keep_list_focus"));

      li.appendChild(btn);
      dom.componentList.appendChild(li);
    });

    if (restoreFocusNodeId) {
      const targetBtn = dom.componentList.querySelector(
        `button[data-node-id="${CSS.escape(restoreFocusNodeId)}"]`
      );
      if (targetBtn) {
        targetBtn.focus();
      }
    }
  }

  function buildNeighborList(items, emptyMessage) {
    if (items.length === 0) {
      const p = document.createElement("p");
      p.className = "empty-relation";
      p.textContent = emptyMessage;
      return p;
    }

    const ul = document.createElement("ul");
    ul.className = "relation-list";

    for (const item of items) {
      const li = document.createElement("li");
      li.className = "relation-item";

      const text = document.createElement("span");
      text.className = "relation-item-text";
      text.textContent = item.description;

      const jumpBtn = document.createElement("button");
      jumpBtn.type = "button";
      jumpBtn.className = "btn btn-secondary btn-sm";
      jumpBtn.textContent = `Select ${item.neighbor.label}`;
      jumpBtn.addEventListener("click", () =>
        selectNode(item.neighbor.id, "move_to_detail")
      );

      li.appendChild(text);
      li.appendChild(jumpBtn);
      ul.appendChild(li);
    }

    return ul;
  }

  function renderSelectedDetail(diagram) {
    dom.selectedDetail.textContent = "";
    dom.selectedRelationships.textContent = "";

    const nodeMap = getNodeMap(diagram);
    const node = nodeMap.get(state.selectedNodeId) || diagram.nodes[0];
    if (!node) return;
    state.selectedNodeId = node.id;

    const nameEl = document.createElement("p");
    nameEl.className = "selected-name";
    nameEl.textContent = node.label;
    dom.selectedDetail.appendChild(nameEl);

    const kindEl = document.createElement("p");
    kindEl.className = "selected-kind";
    kindEl.textContent = getComponentMetaText(diagram, node);
    dom.selectedDetail.appendChild(kindEl);

    const descEl = document.createElement("p");
    descEl.className = "selected-desc";
    descEl.textContent = node.description;
    dom.selectedDetail.appendChild(descEl);

    const attrEntries = Object.entries(node.attributes || {});
    if (attrEntries.length > 0) {
      const dl = document.createElement("dl");
      dl.className = "attributes-list";
      for (const [key, value] of attrEntries) {
        const dt = document.createElement("dt");
        dt.textContent = key;
        const dd = document.createElement("dd");
        dd.textContent = String(value);
        dl.appendChild(dt);
        dl.appendChild(dd);
      }
      dom.selectedDetail.appendChild(dl);
    }

    if (diagram.domain === "physics_circuit") {
      const neighbors = [];
      for (const edge of diagram.edges) {
        if (edge.source === node.id && nodeMap.has(edge.target)) {
          neighbors.push({
            neighbor: nodeMap.get(edge.target),
            description: `Connected by wire to ${nodeMap.get(edge.target).label}. ${edge.description}`,
          });
        } else if (edge.target === node.id && nodeMap.has(edge.source)) {
          neighbors.push({
            neighbor: nodeMap.get(edge.source),
            description: `Connected by wire to ${nodeMap.get(edge.source).label}. ${edge.description}`,
          });
        }
      }

      const group = document.createElement("div");
      group.className = "relation-group";
      const title = document.createElement("p");
      title.className = "relation-group-title";
      title.textContent = "Wire connections";
      group.appendChild(title);
      group.appendChild(
        buildNeighborList(neighbors, "No wire connections for this component.")
      );
      dom.selectedRelationships.appendChild(group);
    } else if (diagram.domain === "biology_food_web") {
      const incoming = diagram.edges
        .filter((e) => e.target === node.id && nodeMap.has(e.source))
        .map((e) => ({
          neighbor: nodeMap.get(e.source),
          description: `Receives energy from ${nodeMap.get(e.source).label} (${nodeMap.get(e.source).label} -> ${node.label}).`,
        }));

      const outgoing = diagram.edges
        .filter((e) => e.source === node.id && nodeMap.has(e.target))
        .map((e) => ({
          neighbor: nodeMap.get(e.target),
          description: `Provides energy to ${nodeMap.get(e.target).label} (${node.label} -> ${nodeMap.get(e.target).label}).`,
        }));

      const inGroup = document.createElement("div");
      inGroup.className = "relation-group";
      const inTitle = document.createElement("p");
      inTitle.className = "relation-group-title";
      inTitle.textContent = "Receives energy from (food / prey)";
      inGroup.appendChild(inTitle);
      inGroup.appendChild(
        buildNeighborList(
          incoming,
          `${node.label} receives energy from no other organism in this diagram.`
        )
      );

      const outGroup = document.createElement("div");
      outGroup.className = "relation-group";
      const outTitle = document.createElement("p");
      outTitle.className = "relation-group-title";
      outTitle.textContent = "Provides energy to (consumer / predator)";
      outGroup.appendChild(outTitle);
      outGroup.appendChild(
        buildNeighborList(
          outgoing,
          `${node.label} provides energy to no other organism in this diagram.`
        )
      );

      dom.selectedRelationships.appendChild(inGroup);
      dom.selectedRelationships.appendChild(outGroup);
    } else if (diagram.domain === "cs_flowchart") {
      const outgoing = diagram.edges
        .filter((e) => e.source === node.id && nodeMap.has(e.target))
        .map((e) => {
          const branchTag =
            e.relation === "branch_true"
              ? "[TRUE branch] "
              : e.relation === "branch_false"
                ? "[FALSE branch] "
                : "";
          return {
            neighbor: nodeMap.get(e.target),
            description: `${branchTag}Proceeds to ${nodeMap.get(e.target).label}. ${e.description}`,
          };
        });
      const incoming = diagram.edges
        .filter((e) => e.target === node.id && nodeMap.has(e.source))
        .map((e) => ({
          neighbor: nodeMap.get(e.source),
          description: `Reached from ${nodeMap.get(e.source).label} (${e.relation}).`,
        }));

      const outGroup = document.createElement("div");
      outGroup.className = "relation-group";
      const outTitle = document.createElement("p");
      outTitle.className = "relation-group-title";
      outTitle.textContent = "Next step(s) / branches";
      outGroup.appendChild(outTitle);
      outGroup.appendChild(
        buildNeighborList(outgoing, "Terminal block (no outgoing flow).")
      );

      const inGroup = document.createElement("div");
      inGroup.className = "relation-group";
      const inTitle = document.createElement("p");
      inTitle.className = "relation-group-title";
      inTitle.textContent = "Incoming flow from";
      inGroup.appendChild(inTitle);
      inGroup.appendChild(
        buildNeighborList(incoming, "Entry point (no incoming flow).")
      );

      dom.selectedRelationships.appendChild(outGroup);
      dom.selectedRelationships.appendChild(inGroup);
    }
  }

  function renderExperimentControls(diagram, restoreFocusAction = null) {
    dom.experimentActions.textContent = "";
    const nodeMap = getNodeMap(diagram);

    if (diagram.domain === "physics_circuit") {
      const switchNode = diagram.nodes.find((n) => n.kind === "switch");
      const switchState = switchNode
        ? getSwitchDisplayState(diagram, switchNode.id)
        : "open";

      dom.experimentGuidance.textContent = switchNode
        ? `Toggle ${switchNode.label} to test how opening or closing the series loop affects the bulb. All simulation results are computed by the Python backend.`
        : "No switch is available in this circuit.";

      if (switchNode) {
        const toggleBtn = document.createElement("button");
        toggleBtn.type = "button";
        toggleBtn.className = "btn btn-primary";
        toggleBtn.dataset.action = "toggle_switch";
        toggleBtn.disabled = state.isBusy;
        toggleBtn.textContent =
          switchState === "open"
            ? `Close ${switchNode.label}`
            : `Open ${switchNode.label}`;
        toggleBtn.addEventListener("click", () =>
          runSimulation({ type: "toggle_switch", target_id: switchNode.id })
        );
        dom.experimentActions.appendChild(toggleBtn);
      }

      dom.experimentLimitation.textContent =
        "Scope limitation: Qualitative single-loop series model only. Does not calculate voltage, current, resistance, or bulb brightness.";
    } else if (diagram.domain === "biology_food_web") {
      const selectedNode = nodeMap.get(state.selectedNodeId) || diagram.nodes[0];
      const canRemove = diagram.nodes.length > 1;

      dom.experimentGuidance.textContent = selectedNode
        ? `Temporarily remove ${selectedNode.label} from this diagram to inspect which feeding relationships disappear and which remain.`
        : "Select an organism to test removing it from the food web.";

      if (selectedNode) {
        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "btn btn-danger";
        removeBtn.dataset.action = "remove_organism";
        removeBtn.disabled = state.isBusy || !canRemove;
        removeBtn.textContent = canRemove
          ? `Remove ${selectedNode.label}`
          : "Cannot remove final organism";
        removeBtn.addEventListener("click", () =>
          runSimulation({ type: "remove_organism", target_id: selectedNode.id })
        );
        dom.experimentActions.appendChild(removeBtn);
      }

      dom.experimentLimitation.textContent =
        "Scientific note: Removing an organism updates only the feeding relationships shown in this diagram. It does not predict extinction or population changes.";
      dom.flowchartInputsBlock.hidden = true;
      dom.flowchartTracePanel.hidden = true;
    } else if (diagram.domain === "cs_flowchart") {
      dom.experimentGuidance.textContent =
        "Set initial integer or boolean input values and run the safe restricted Python interpreter to step forward and backward through execution.";

      dom.flowchartInputsBlock.textContent = "";
      const inputDefs = (diagram.domain_model && diagram.domain_model.inputs) || {};
      const inputKeys = Object.keys(inputDefs);
      if (inputKeys.length > 0) {
        for (const key of inputKeys) {
          const field = document.createElement("div");
          field.className = "form-field";
          const lbl = document.createElement("label");
          const inputId = `fc-input-${key}`;
          lbl.setAttribute("for", inputId);
          lbl.textContent = `Initial value for ${key}`;
          const inp = document.createElement("input");
          inp.type = "text";
          inp.id = inputId;
          const currentVal =
            key in state.flowchartInputValues
              ? state.flowchartInputValues[key]
              : inputDefs[key];
          inp.value = String(currentVal);
          inp.addEventListener("input", () => {
            state.flowchartInputValues[key] = inp.value;
          });
          field.appendChild(lbl);
          field.appendChild(inp);
          dom.flowchartInputsBlock.appendChild(field);
        }
        dom.flowchartInputsBlock.hidden = false;
      } else {
        dom.flowchartInputsBlock.hidden = true;
      }

      const runBtn = document.createElement("button");
      runBtn.type = "button";
      runBtn.className = "btn btn-primary";
      runBtn.dataset.action = "run_flowchart";
      runBtn.disabled = state.isBusy;
      runBtn.textContent = "Run Trace";
      runBtn.addEventListener("click", runFlowchartTrace);
      dom.experimentActions.appendChild(runBtn);

      renderFlowchartTracePanel();

      dom.experimentLimitation.textContent =
        "Safety boundary: Uses a restricted integer/boolean expression parser (no eval/exec) with bounded step limits to halt infinite loops safely.";
      dom.mathControlsPanel.hidden = true;
    } else if (diagram.domain === "math_plot") {
      dom.flowchartInputsBlock.hidden = true;
      dom.flowchartTracePanel.hidden = true;
      dom.experimentGuidance.textContent =
        "Navigate point-by-point or compare intervals using the deterministic math engine. Optional audio sonification is volume-limited and user-triggered.";
      renderMathControlsPanel(diagram);
      dom.experimentLimitation.textContent =
        "Mathematical boundary: Extrema, intervals, and intercepts are computed strictly over the finite provided dataset. No asymptotes or unseen extrapolations are invented.";
    }

    if (diagram.domain === "physics_circuit" || diagram.domain === "biology_food_web") {
      dom.flowchartInputsBlock.hidden = true;
      dom.flowchartTracePanel.hidden = true;
      dom.mathControlsPanel.hidden = true;
    }

    const resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.className = "btn btn-secondary";
    resetBtn.dataset.action = "reset_experiment";
    resetBtn.disabled = state.isBusy;
    resetBtn.textContent = "Reset Experiment";
    resetBtn.addEventListener("click", resetExperiment);
    dom.experimentActions.appendChild(resetBtn);

    if (restoreFocusAction) {
      const target = dom.experimentActions.querySelector(
        `button[data-action="${CSS.escape(restoreFocusAction)}"]`
      );
      if (target && !target.disabled) {
        target.focus();
      } else {
        resetBtn.focus();
      }
    }
  }

  function renderAllRelationsAndPreview(diagram) {
    dom.allRelationsList.textContent = "";
    const nodeMap = getNodeMap(diagram);

    if (diagram.edges.length === 0) {
      const li = document.createElement("li");
      li.textContent = "No active relationships remain in the current diagram.";
      dom.allRelationsList.appendChild(li);
    } else {
      for (const edge of diagram.edges) {
        const li = document.createElement("li");
        const src = nodeMap.get(edge.source);
        const tgt = nodeMap.get(edge.target);
        const srcLabel = src ? src.label : edge.source;
        const tgtLabel = tgt ? tgt.label : edge.target;

        if (diagram.domain === "biology_food_web") {
          li.textContent = `${srcLabel} provides energy to ${tgtLabel} (${edge.description})`;
        } else {
          li.textContent = `${srcLabel} connected by wire to ${tgtLabel} (${edge.description})`;
        }
        dom.allRelationsList.appendChild(li);
      }
    }

    const filename = diagram.source && diagram.source.filename;
    if (diagram.source && diagram.source.mode === "fixture" && filename) {
      dom.diagramPreviewImg.src = `/fixtures/images/${encodeURIComponent(filename)}`;
      dom.diagramPreviewImg.alt = `${diagram.title} schematic diagram. Full structure is provided in the text overview and component list.`;
      dom.diagramPreviewCaption.textContent = `Reference image (${filename}) for ${diagram.title}. Visual preview shows the original baseline diagram.`;
      dom.visualPreviewSection.hidden = false;
    } else {
      dom.visualPreviewSection.hidden = true;
    }
  }

  function renderExplorer(focusOption = null) {
    const diagram = state.currentDiagram;
    if (!diagram) return;

    showSection("explorer");

    dom.diagramTitle.textContent = diagram.title;
    dom.sourceBadge.textContent = formatSourceLabel(diagram.source);
    dom.sourceBadge.className =
      diagram.source && diagram.source.mode === "ai"
        ? "badge badge-ai-review"
        : "badge badge-demo";
    dom.reviewBadge.textContent =
      diagram.review_status === "confirmed"
        ? "Confirmed diagram — ready to explore"
        : "AI-generated — review required";
    dom.domainBadge.textContent = formatDomainLabel(diagram.domain);

    dom.diagramSummary.textContent = diagram.summary;
    if (diagram.domain === "biology_food_web") {
      dom.domainConvention.textContent =
        "Arrow convention: Each directed arrow points from food/prey to its consumer/predator (energy flow).";
    } else if (diagram.domain === "cs_flowchart") {
      dom.domainConvention.textContent =
        "Flowchart convention: Execution starts at Start, evaluates restricted integer/boolean assignments and True/False decisions, and halts at End or max_steps.";
    } else if (diagram.domain === "math_plot") {
      const dm = diagram.domain_model;
      dom.domainConvention.textContent =
        `Plot convention: ${dm.x_label}${dm.x_unit ? ` (${dm.x_unit})` : ""} on the horizontal axis and ${dm.y_label}${dm.y_unit ? ` (${dm.y_unit})` : ""} on the vertical axis. Exact and estimated points are explicitly labeled.`;
    } else {
      dom.domainConvention.textContent =
        "Circuit convention: Wires connect components in one continuous series loop. Bulbs turn on only when the loop is complete and the switch is closed.";
    }

    renderStats(diagram);
    renderLearningLab();
    renderSemanticSvgGraph(diagram);
    updateTourDisplay(state.tourStep || "overview", false);
    renderFeedback();
    renderComponentList(
      diagram,
      focusOption && focusOption.type === "component" ? focusOption.nodeId : null
    );
    renderSelectedDetail(diagram);
    renderExperimentControls(
      diagram,
      focusOption && focusOption.type === "action" ? focusOption.action : null
    );
    renderAllRelationsAndPreview(diagram);
  }

  function selectNode(nodeId, focusMode) {
    if (!state.currentDiagram) return;
    const nodeMap = getNodeMap(state.currentDiagram);
    const node = nodeMap.get(nodeId);
    if (!node) return;

    state.selectedNodeId = node.id;
    renderComponentList(
      state.currentDiagram,
      focusMode === "keep_list_focus" ? node.id : null
    );
    renderSelectedDetail(state.currentDiagram);
    renderExperimentControls(state.currentDiagram);
    renderSemanticSvgGraph(state.currentDiagram);
    updateTourDisplay("component", false);

    const meta = getComponentMetaText(state.currentDiagram, node);
    announce(`Selected ${node.label}. ${meta}. ${node.description}`);

    if (focusMode === "move_to_detail" && dom.selectedHeading) {
      dom.selectedHeading.focus();
    }
  }

  function renderFlowchartTracePanel() {
    const trace = state.flowchartTrace;
    if (!trace || !trace.steps || trace.steps.length === 0) {
      dom.flowchartTracePanel.hidden = true;
      return;
    }
    dom.flowchartTracePanel.hidden = false;
    const step = trace.steps[state.flowchartStepIdx] || trace.steps[0];
    dom.traceStepCounter.textContent = `Step ${step.step_index} of ${trace.steps.length} (${trace.status})`;
    dom.traceStepAction.textContent = `[${step.node_label}] ${step.action_description}`;

    dom.traceStepVars.textContent = "";
    const entries = Object.entries(step.variables || {});
    if (entries.length === 0) {
      const dt = document.createElement("dt");
      dt.textContent = "Variables";
      const dd = document.createElement("dd");
      dd.textContent = "None initialized yet";
      dom.traceStepVars.appendChild(dt);
      dom.traceStepVars.appendChild(dd);
    } else {
      for (const [k, v] of entries) {
        const dt = document.createElement("dt");
        dt.textContent = k;
        const dd = document.createElement("dd");
        dd.textContent = String(v);
        dom.traceStepVars.appendChild(dt);
        dom.traceStepVars.appendChild(dd);
      }
    }

    dom.tracePrevBtn.disabled = state.flowchartStepIdx <= 0;
    dom.traceNextBtn.disabled = state.flowchartStepIdx >= trace.steps.length - 1;
  }

  function stepFlowchartTrace(delta) {
    if (!state.flowchartTrace || !state.flowchartTrace.steps.length) return;
    const nextIdx = Math.min(
      Math.max(0, state.flowchartStepIdx + delta),
      state.flowchartTrace.steps.length - 1
    );
    state.flowchartStepIdx = nextIdx;
    const step = state.flowchartTrace.steps[nextIdx];
    state.selectedNodeId = step.node_id;
    renderComponentList(state.currentDiagram);
    renderSelectedDetail(state.currentDiagram);
    renderSemanticSvgGraph(state.currentDiagram);
    renderFlowchartTracePanel();
    const varsText = Object.entries(step.variables || {})
      .map(([k, v]) => `${k}=${v}`)
      .join(", ");
    announce(
      `Step ${step.step_index} of ${state.flowchartTrace.steps.length}: ${step.action_description} Variables: ${varsText || "none"}.`
    );
  }

  async function runFlowchartTrace() {
    if (!state.currentDiagram || state.isBusy) return;
    clearError();

    const parsedInputs = {};
    const defaults = (state.currentDiagram.domain_model && state.currentDiagram.domain_model.inputs) || {};
    for (const key of Object.keys(defaults)) {
      const raw = String(
        key in state.flowchartInputValues ? state.flowchartInputValues[key] : defaults[key]
      ).trim();
      if (raw.toLowerCase() === "true") {
        parsedInputs[key] = true;
      } else if (raw.toLowerCase() === "false") {
        parsedInputs[key] = false;
      } else if (/^-?\d+$/.test(raw)) {
        parsedInputs[key] = parseInt(raw, 10);
      } else {
        showError(`Input '${key}' must be an integer or boolean (true/false), got '${raw}'.`);
        return;
      }
    }

    state.isBusy = true;
    renderExperimentControls(state.currentDiagram);

    try {
      const trace = await apiRequest("/api/flowchart/trace", {
        method: "POST",
        body: JSON.stringify({
          diagram: state.currentDiagram,
          inputs: parsedInputs,
        }),
      });
      state.flowchartTrace = trace;
      state.flowchartStepIdx = 0;
      if (trace.steps && trace.steps.length > 0) {
        state.selectedNodeId = trace.steps[0].node_id;
      }
      state.lastSimulation = {
        event: trace.status,
        announcement: trace.announcement,
        changes: trace.steps.slice(0, 6).map((s) => `Step ${s.step_index}: ${s.action_description}`),
      };
      state.isBusy = false;
      renderExplorer({ type: "action", action: "run_flowchart" });
      announce(trace.announcement);
    } catch (err) {
      state.isBusy = false;
      renderExperimentControls(state.currentDiagram, "run_flowchart");
      showError(`Flowchart execution failed: ${err.message}`);
      announce(`Flowchart error: ${err.message}`);
    }
  }

  // --- Phase 9: Mathematics Point/Interval Explorer & Optional Sonification ---

  function playSafeTone(yValue, yMin, yMax, durationMs = 220, delayMs = 0) {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    try {
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const span = yMax - yMin || 1;
      const ratio = Math.min(1, Math.max(0, (yValue - yMin) / span));
      osc.frequency.value = 260 + ratio * 520; // Predictable 260–780 Hz range
      osc.type = "sine";
      gain.gain.value = 0.12; // Strictly volume-limited
      osc.connect(gain);
      gain.connect(ctx.destination);
      const startTime = ctx.currentTime + delayMs / 1000;
      const endTime = startTime + durationMs / 1000;
      osc.start(startTime);
      osc.stop(endTime);
      osc.onended = () => {
        ctx.close().catch(() => {});
      };
    } catch {
      // Ignore audio errors when Web Audio is unavailable.
    }
  }

  function renderMathControlsPanel(diagram) {
    if (!diagram || diagram.domain !== "math_plot") {
      dom.mathControlsPanel.hidden = true;
      return;
    }
    const dm = diagram.domain_model;
    const pts = dm.points || [];
    if (pts.length === 0) {
      dom.mathControlsPanel.hidden = true;
      return;
    }
    dom.mathControlsPanel.hidden = false;
    state.mathPointIdx = Math.min(Math.max(0, state.mathPointIdx), pts.length - 1);
    const pt = pts[state.mathPointIdx];
    const prevPt = state.mathPointIdx > 0 ? pts[state.mathPointIdx - 1] : null;
    const deltaPart = prevPt
      ? ` Change from previous point: ${pt.y - prevPt.y >= 0 ? "+" : ""}${pt.y - prevPt.y} ${dm.y_unit}.`
      : " First point in series.";

    dom.mathPointCounter.textContent = `Point ${state.mathPointIdx + 1} of ${pts.length}`;
    dom.mathPointReadout.textContent =
      `${pt.label} · ${dm.x_label}: ${pt.x} ${dm.x_unit}, ${dm.y_label}: ${pt.y} ${dm.y_unit} ` +
      `(${pt.exact ? "exact" : "estimated"}).${deltaPart}`;

    dom.mathPrevPtBtn.disabled = state.mathPointIdx <= 0;
    dom.mathNextPtBtn.disabled = state.mathPointIdx >= pts.length - 1;

    // Populate interval selectors
    const prevStart = dom.mathIntervalStart.value || "0";
    const prevEnd = dom.mathIntervalEnd.value || String(pts.length - 1);
    dom.mathIntervalStart.textContent = "";
    dom.mathIntervalEnd.textContent = "";
    pts.forEach((p, idx) => {
      const o1 = document.createElement("option");
      o1.value = String(idx);
      o1.textContent = p.label;
      o1.selected = String(idx) === prevStart;
      dom.mathIntervalStart.appendChild(o1);

      const o2 = document.createElement("option");
      o2.value = String(idx);
      o2.textContent = p.label;
      o2.selected = String(idx) === prevEnd;
      dom.mathIntervalEnd.appendChild(o2);
    });

    dom.mathAnalysisList.textContent = "";
    if (state.mathAnalysis) {
      const a = state.mathAnalysis;
      const lines = [
        `Global maximum: ${a.global_max.label}`,
        `Global minimum: ${a.global_min.label}`,
        ...a.monotonic_intervals.map(
          (iv) =>
            `Interval [${iv.start_x}, ${iv.end_x}]: ${iv.trend} (Δy = ${iv.delta_y}, avg rate = ${iv.avg_rate_of_change})`
        ),
        ...a.x_intercepts.map(
          (ic) => `x-intercept at x = ${ic.x} (${ic.exact ? "exact" : "interpolated"}: ${ic.note})`
        ),
      ];
      if (a.y_intercept) {
        lines.push(
          `y-intercept at y = ${a.y_intercept.y} (${a.y_intercept.exact ? "exact" : "interpolated"})`
        );
      }
      for (const line of lines) {
        const li = document.createElement("li");
        li.textContent = line;
        dom.mathAnalysisList.appendChild(li);
      }
      dom.mathIntervalResult.textContent = a.interval_summary
        ? a.interval_summary.announcement
        : "";
    }
  }

  function stepMathPoint(delta) {
    if (!state.currentDiagram || state.currentDiagram.domain !== "math_plot") return;
    const pts = state.currentDiagram.domain_model.points;
    state.mathPointIdx = Math.min(Math.max(0, state.mathPointIdx + delta), pts.length - 1);
    state.selectedNodeId = pts[state.mathPointIdx].id;
    renderComponentList(state.currentDiagram);
    renderSelectedDetail(state.currentDiagram);
    renderSemanticSvgGraph(state.currentDiagram);
    renderMathControlsPanel(state.currentDiagram);
    announce(dom.mathPointReadout.textContent);
  }

  async function runMathIntervalCompare() {
    if (!state.currentDiagram || state.currentDiagram.domain !== "math_plot") return;
    clearError();
    const startIdx = parseInt(dom.mathIntervalStart.value, 10);
    const endIdx = parseInt(dom.mathIntervalEnd.value, 10);
    try {
      const analysis = await apiRequest("/api/math/analyze", {
        method: "POST",
        body: JSON.stringify({
          diagram: state.currentDiagram,
          start_index: startIdx,
          end_index: endIdx,
        }),
      });
      state.mathAnalysis = analysis;
      renderMathControlsPanel(state.currentDiagram);
      if (analysis.interval_summary) {
        announce(analysis.interval_summary.announcement);
      }
    } catch (err) {
      showError(err.message);
    }
  }

  async function loadExample(exampleId) {
    clearError();
    state.isBusy = true;
    announce("Loading example diagram…");

    try {
      const diagram = await apiRequest(`/api/examples/${encodeURIComponent(exampleId)}`);
      const backendState = await fetchBackendState(diagram);

      state.baselineDiagram = deepClone(diagram);
      state.currentDiagram = deepClone(diagram);
      state.backendState = backendState;
      state.selectedNodeId = diagram.nodes.length > 0 ? diagram.nodes[0].id : null;
      state.lastSimulation = null;
      state.explorerMode = "explore";
      state.tourStep = "overview";
      state.flowchartTrace = null;
      state.flowchartStepIdx = 0;
      state.flowchartInputValues = {};
      state.mathAnalysis = null;
      state.mathPointIdx = 0;
      if (diagram.domain === "math_plot") {
        state.mathAnalysis = await apiRequest("/api/math/analyze", {
          method: "POST",
          body: JSON.stringify({ diagram }),
        });
      }
      stopTts();
      resetLabState();
      await loadLabChallengesForBaseline();
      state.isBusy = false;

      renderExplorer();
      dom.diagramTitle.focus();
      announce(
        `Loaded ${diagram.title}. ${formatSourceLabel(diagram.source)}. ${diagram.summary}`
      );
    } catch (err) {
      state.isBusy = false;
      showError(`Could not load example diagram: ${err.message}`);
      announce(`Error loading diagram: ${err.message}`);
    }
  }

  async function runSimulation(action) {
    if (!state.currentDiagram || state.isBusy) return;
    clearError();
    state.isBusy = true;
    renderExperimentControls(state.currentDiagram);

    try {
      const result = await apiRequest("/api/simulate", {
        method: "POST",
        body: JSON.stringify({
          diagram: state.currentDiagram,
          action,
        }),
      });

      const backendState = await fetchBackendState(result.updated_diagram);

      state.currentDiagram = result.updated_diagram;
      state.backendState = backendState;
      state.lastSimulation = {
        event: result.event,
        announcement: result.announcement,
        changes: result.changes || [],
      };

      const stillExists = state.currentDiagram.nodes.some(
        (n) => n.id === state.selectedNodeId
      );
      if (!stillExists) {
        state.selectedNodeId =
          state.currentDiagram.nodes.length > 0
            ? state.currentDiagram.nodes[0].id
            : null;
      }

      state.isBusy = false;
      renderExplorer({ type: "action", action: action.type });
      announce(result.announcement);
    } catch (err) {
      state.isBusy = false;
      renderExperimentControls(state.currentDiagram, action.type);
      showError(`Simulation error: ${err.message}`);
      announce(`Simulation error: ${err.message}`);
    }
  }

  async function resetExperiment() {
    if (!state.baselineDiagram || state.isBusy) return;
    clearError();

    const restored = deepClone(state.baselineDiagram);
    try {
      const backendState = await fetchBackendState(restored);
      state.currentDiagram = restored;
      state.backendState = backendState;
      state.flowchartTrace = null;
      state.flowchartStepIdx = 0;
      state.flowchartInputValues = {};
      state.selectedNodeId =
        state.currentDiagram.nodes.length > 0 ? state.currentDiagram.nodes[0].id : null;
      state.lastSimulation = {
        event: "experiment_reset",
        announcement: `Experiment reset. ${state.currentDiagram.title} restored to its original confirmed baseline.`,
        changes: ["Restored all original components, states, and relationships."],
      };

      renderExplorer({ type: "action", action: "reset_experiment" });
      announce(state.lastSimulation.announcement);
    } catch (err) {
      showError(`Could not reset experiment: ${err.message}`);
    }
  }

  function showWelcome() {
    clearError();
    stopTts();
    state.reviewDraft = null;
    state.reviewValidation = null;
    showSection("welcome");
    const heading = document.getElementById("welcome-heading");
    if (heading) {
      heading.setAttribute("tabindex", "-1");
      heading.focus();
    }
    announce("Returned to SenseGraph home.");
  }

  async function init() {
    dom.errorDismissBtn.addEventListener("click", () => clearError(true));
    dom.backToHomeBtn.addEventListener("click", showWelcome);
    dom.reviewCancelBtn.addEventListener("click", showWelcome);
    dom.brandHomeLink.addEventListener("click", (e) => {
      if (dom.welcomeSection.hidden) {
        e.preventDefault();
        showWelcome();
      }
    });
    dom.switchPhysicsBtn.addEventListener("click", () => loadExample("physics_series"));
    dom.switchBiologyBtn.addEventListener("click", () => loadExample("biology_food_web"));
    dom.switchCsBtn.addEventListener("click", () => loadExample("cs_flowchart"));
    dom.switchMathBtn.addEventListener("click", () => loadExample("math_plot"));
    dom.tracePrevBtn.addEventListener("click", () => stepFlowchartTrace(-1));
    dom.traceNextBtn.addEventListener("click", () => stepFlowchartTrace(1));
    dom.mathPrevPtBtn.addEventListener("click", () => stepMathPoint(-1));
    dom.mathNextPtBtn.addEventListener("click", () => stepMathPoint(1));
    dom.mathCompareBtn.addEventListener("click", runMathIntervalCompare);
    dom.mathSonifyPtBtn.addEventListener("click", () => {
      if (!state.currentDiagram || state.currentDiagram.domain !== "math_plot") return;
      const pts = state.currentDiagram.domain_model.points;
      const ys = pts.map((p) => p.y);
      playSafeTone(pts[state.mathPointIdx].y, Math.min(...ys), Math.max(...ys));
    });
    dom.mathSonifyAllBtn.addEventListener("click", () => {
      if (!state.currentDiagram || state.currentDiagram.domain !== "math_plot") return;
      const pts = state.currentDiagram.domain_model.points;
      const ys = pts.map((p) => p.y);
      const yMin = Math.min(...ys);
      const yMax = Math.max(...ys);
      pts.forEach((p, idx) => playSafeTone(p.y, yMin, yMax, 180, idx * 230));
    });

    dom.modeExploreBtn.addEventListener("click", () => setExplorerMode("explore"));
    dom.modeLabBtn.addEventListener("click", () => setExplorerMode("lab"));
    dom.labPredictionForm.addEventListener("submit", handleLabSubmit);
    dom.labRetryBtn.addEventListener("click", handleLabRetry);
    dom.labSkipBtn.addEventListener("click", () => handleLabAdvance(true));
    dom.labNextBtn.addEventListener("click", () => handleLabAdvance(false));
    dom.labResetBtn.addEventListener("click", handleLabResetSession);

    dom.tourOverviewBtn.addEventListener("click", () => {
      stopTts();
      updateTourDisplay("overview", true);
    });
    dom.tourBackOverviewBtn.addEventListener("click", () => {
      stopTts();
      updateTourDisplay("overview", true);
    });
    dom.tourPrevBtn.addEventListener("click", () => stepTourComponent(-1));
    dom.tourNextBtn.addEventListener("click", () => stepTourComponent(1));
    dom.tourConnectionsBtn.addEventListener("click", () => {
      stopTts();
      updateTourDisplay("connections", true);
    });
    dom.tourRepeatBtn.addEventListener("click", () => {
      if (state.tourText) {
        announce(state.tourText);
      }
    });
    dom.tourTtsSpeakBtn.addEventListener("click", speakCurrentTourText);
    dom.tourTtsPauseBtn.addEventListener("click", togglePauseTts);
    dom.tourTtsStopBtn.addEventListener("click", stopTts);
    updateTtsControls();

    dom.analyzeForm.addEventListener("submit", handleAnalyzeSubmit);
    dom.reviewTitleInput.addEventListener("input", () => {
      if (state.reviewDraft) {
        state.reviewDraft.title = dom.reviewTitleInput.value;
        markDraftDirty();
      }
    });
    dom.reviewAddNodeBtn.addEventListener("click", handleAddReviewNode);
    dom.reviewAddEdgeBtn.addEventListener("click", handleAddReviewEdge);
    dom.reviewValidateBtn.addEventListener("click", handleValidateReviewDraft);
    dom.reviewConfirmBtn.addEventListener("click", handleConfirmReviewDraft);

    try {
      const [health, examples] = await Promise.all([
        apiRequest("/api/health"),
        apiRequest("/api/examples"),
      ]);
      state.health = health;
      state.examples = examples;
      renderHealth();
      renderExamplesGrid();
    } catch (err) {
      dom.examplesLoading.textContent = "Unable to connect to the SenseGraph backend.";
      dom.healthBadge.textContent = "Backend unavailable";
      showError(`Initialization failed: ${err.message}`);
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
