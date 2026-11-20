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
    diagramTitle: document.getElementById("diagram-title"),
    sourceBadge: document.getElementById("source-badge"),
    reviewBadge: document.getElementById("review-badge"),
    domainBadge: document.getElementById("domain-badge"),

    diagramSummary: document.getElementById("diagram-summary"),
    domainConvention: document.getElementById("domain-convention"),
    diagramStats: document.getElementById("diagram-stats"),

    feedbackPanel: document.getElementById("feedback-panel"),
    feedbackAnnouncement: document.getElementById("feedback-announcement"),
    feedbackChanges: document.getElementById("feedback-changes"),

    componentList: document.getElementById("component-list"),
    selectedHeading: document.getElementById("selected-heading"),
    selectedDetail: document.getElementById("selected-detail"),
    selectedRelationships: document.getElementById("selected-relationships"),

    experimentGuidance: document.getElementById("experiment-guidance"),
    experimentActions: document.getElementById("experiment-actions"),
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

  function clearError() {
    dom.errorBanner.hidden = true;
    dom.errorBannerText.textContent = "";
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
          announce(`Swapped arrow direction for connection ${index + 1}.`);
        });
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
    } else {
      dom.domainConvention.textContent =
        "Circuit convention: Wires connect components in one continuous series loop. Bulbs turn on only when the loop is complete and the switch is closed.";
    }

    renderStats(diagram);
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

    const meta = getComponentMetaText(state.currentDiagram, node);
    announce(`Selected ${node.label}. ${meta}. ${node.description}`);

    if (focusMode === "move_to_detail" && dom.selectedHeading) {
      dom.selectedHeading.focus();
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
    dom.errorDismissBtn.addEventListener("click", clearError);
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
