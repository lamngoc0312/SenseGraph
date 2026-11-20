/* SenseGraph — Phase 2 Accessible Frontend Application
 * Strictly uses backend REST APIs for all simulation logic.
 * Renders all diagram/API strings with textContent (no unsanitized HTML).
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
    baselineDiagram: null,
    currentDiagram: null,
    selectedNodeId: null,
    lastSimulation: null,
    // Tracks bulb state labels reported directly by backend simulation changes (never computed in JS).
    reportedBulbStates: {},
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
    // Clear then set on next frame so repeated identical messages are still announced.
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
    const response = await fetch(url, {
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.headers || {}),
      },
      ...options,
    });

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
      return `AI-generated (${source.provider || "provider"})`;
    }
    return "Unknown source";
  }

  function extractBulbStatesFromChanges(diagram, changes) {
    // Parse exact bulb state strings returned by Python backend (e.g. "Bulb L1: off -> on").
    const updated = { ...state.reportedBulbStates };
    if (!Array.isArray(changes)) return updated;

    const bulbNodes = diagram.nodes.filter((n) => n.kind === "bulb");
    for (const changeLine of changes) {
      for (const bulb of bulbNodes) {
        const prefix = `${bulb.label}:`;
        if (changeLine.startsWith(prefix) && changeLine.includes("->")) {
          const parts = changeLine.split("->");
          const newState = parts[parts.length - 1].trim().toLowerCase();
          if (newState === "on" || newState === "off") {
            updated[bulb.id] = newState;
          }
        }
      }
    }
    return updated;
  }

  function getInitialBulbStateLabel(diagram) {
    // Do not compute physics in JS; reflect only the backend summary text for initial fixture state.
    const summaryLower = (diagram.summary || "").toLowerCase();
    if (summaryLower.includes("bulb is off") || summaryLower.includes("bulbs are off")) {
      return "off";
    }
    if (summaryLower.includes("bulb is on") || summaryLower.includes("bulbs are on")) {
      return "on";
    }
    return "see overview";
  }

  function getBulbDisplayState(diagram, bulbId) {
    if (state.reportedBulbStates[bulbId]) {
      return state.reportedBulbStates[bulbId];
    }
    return getInitialBulbStateLabel(diagram);
  }

  function renderHealth() {
    if (!state.health) return;
    if (state.health.ai_configured) {
      dom.healthBadge.textContent = "Backend ready · AI key configured";
      dom.aiStatusText.textContent =
        "An AI provider key is configured on the server. Live image upload and AI review UI will be added in Phase 3. Pre-annotated examples below do not call AI.";
    } else {
      dom.healthBadge.textContent = "Backend ready · Fixture demo mode (no AI)";
      dom.aiStatusText.textContent =
        "No AI provider key is active. SenseGraph is running in Pre-annotated demo mode with deterministic Python simulation engines. Live image upload will be added in Phase 3.";
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

  function renderStats(diagram) {
    dom.diagramStats.textContent = "";

    const stats = [];
    if (diagram.domain === "physics_circuit") {
      stats.push({ label: "Components", value: String(diagram.nodes.length) });
      stats.push({ label: "Wire Connections", value: String(diagram.edges.length) });

      const switchStates = diagram.domain_model.switch_states || {};
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
        const bState = getBulbDisplayState(diagram, bulb.id);
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
        const swState = diagram.domain_model.switch_states[node.id] || "unknown";
        return `Switch · Currently ${swState}`;
      }
      if (node.kind === "bulb") {
        const bState = getBulbDisplayState(diagram, node.id);
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

  function renderComponentList(diagram) {
    dom.componentList.textContent = "";

    diagram.nodes.forEach((node, index) => {
      const li = document.createElement("li");

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "component-btn";
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

      btn.addEventListener("click", () => selectNode(node.id, false));

      li.appendChild(btn);
      dom.componentList.appendChild(li);
    });
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
      jumpBtn.addEventListener("click", () => selectNode(item.neighbor.id, true));

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

  function renderExperimentControls(diagram) {
    dom.experimentActions.textContent = "";
    const nodeMap = getNodeMap(diagram);

    if (diagram.domain === "physics_circuit") {
      const switchNode = diagram.nodes.find((n) => n.kind === "switch");
      const switchId = switchNode ? switchNode.id : null;
      const switchState =
        switchId && diagram.domain_model.switch_states
          ? diagram.domain_model.switch_states[switchId]
          : "open";

      dom.experimentGuidance.textContent = switchNode
        ? `Toggle ${switchNode.label} to test how opening or closing the series loop affects the bulb. All simulation results are computed by the Python backend.`
        : "No switch is available in this circuit.";

      if (switchNode) {
        const toggleBtn = document.createElement("button");
        toggleBtn.type = "button";
        toggleBtn.className = "btn btn-primary";
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
    resetBtn.disabled = state.isBusy;
    resetBtn.textContent = "Reset Experiment";
    resetBtn.addEventListener("click", resetExperiment);
    dom.experimentActions.appendChild(resetBtn);
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

  function renderExplorer() {
    const diagram = state.currentDiagram;
    if (!diagram) return;

    dom.welcomeSection.hidden = true;
    dom.explorerSection.hidden = false;

    dom.diagramTitle.textContent = diagram.title;
    dom.sourceBadge.textContent = formatSourceLabel(diagram.source);
    dom.reviewBadge.textContent =
      diagram.review_status === "confirmed" ? "Confirmed" : "Review required";
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
    renderComponentList(diagram);
    renderSelectedDetail(diagram);
    renderExperimentControls(diagram);
    renderAllRelationsAndPreview(diagram);
  }

  function selectNode(nodeId, moveFocusToDetail) {
    if (!state.currentDiagram) return;
    const nodeMap = getNodeMap(state.currentDiagram);
    const node = nodeMap.get(nodeId);
    if (!node) return;

    state.selectedNodeId = node.id;
    renderComponentList(state.currentDiagram);
    renderSelectedDetail(state.currentDiagram);
    renderExperimentControls(state.currentDiagram);

    const meta = getComponentMetaText(state.currentDiagram, node);
    announce(`Selected ${node.label}. ${meta}. ${node.description}`);

    if (moveFocusToDetail && dom.selectedHeading) {
      dom.selectedHeading.focus();
    }
  }

  async function loadExample(exampleId) {
    clearError();
    state.isBusy = true;
    announce("Loading example diagram…");

    try {
      const diagram = await apiRequest(`/api/examples/${encodeURIComponent(exampleId)}`);
      state.baselineDiagram = deepClone(diagram);
      state.currentDiagram = deepClone(diagram);
      state.selectedNodeId = diagram.nodes.length > 0 ? diagram.nodes[0].id : null;
      state.lastSimulation = null;
      state.reportedBulbStates = {};
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

      state.currentDiagram = result.updated_diagram;
      state.lastSimulation = {
        event: result.event,
        announcement: result.announcement,
        changes: result.changes || [],
      };

      if (state.currentDiagram.domain === "physics_circuit") {
        state.reportedBulbStates = extractBulbStatesFromChanges(
          state.currentDiagram,
          result.changes
        );
      }

      // If the selected node was removed (e.g. Biology remove_organism), select first remaining node.
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
      renderExplorer();
      announce(result.announcement);
    } catch (err) {
      state.isBusy = false;
      renderExperimentControls(state.currentDiagram);
      showError(`Simulation error: ${err.message}`);
      announce(`Simulation error: ${err.message}`);
    }
  }

  function resetExperiment() {
    if (!state.baselineDiagram) return;
    clearError();

    state.currentDiagram = deepClone(state.baselineDiagram);
    state.selectedNodeId =
      state.currentDiagram.nodes.length > 0 ? state.currentDiagram.nodes[0].id : null;
    state.reportedBulbStates = {};
    state.lastSimulation = {
      event: "experiment_reset",
      announcement: `Experiment reset. ${state.currentDiagram.title} restored to its original confirmed baseline.`,
      changes: ["Restored all original components, states, and relationships."],
    };

    renderExplorer();
    announce(state.lastSimulation.announcement);
  }

  function showWelcome() {
    clearError();
    dom.explorerSection.hidden = true;
    dom.welcomeSection.hidden = false;
    const heading = document.getElementById("welcome-heading");
    if (heading) {
      heading.setAttribute("tabindex", "-1");
      heading.focus();
    }
    announce("Returned to SenseGraph module selection.");
  }

  async function init() {
    dom.errorDismissBtn.addEventListener("click", clearError);
    dom.backToHomeBtn.addEventListener("click", showWelcome);
    dom.brandHomeLink.addEventListener("click", (e) => {
      if (!dom.explorerSection.hidden) {
        e.preventDefault();
        showWelcome();
      }
    });
    dom.switchPhysicsBtn.addEventListener("click", () => loadExample("physics_series"));
    dom.switchBiologyBtn.addEventListener("click", () => loadExample("biology_food_web"));

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
