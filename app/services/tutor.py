"""Evidence-Grounded STEM Tutor backed strictly by confirmed graphs & deterministic tools (Phase 11).

All factual claims are derived from validated domain tools and cite exact node/edge IDs.
Unanswerable, out-of-scope, or adversarial questions return an explicit abstention
('Not established by this diagram.') with a clarifying follow-up rather than hallucinating.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque

from app.domains import DomainSimulationError
from app.domains.biology import (
    get_energy_paths,
    get_organism_relations,
    remove_organism,
)
from app.domains.chemistry import get_atom_counts
from app.domains.flowchart import execute_flowchart
from app.domains.mathematics import analyze_math_plot
from app.domains.physics import evaluate_circuit_state, toggle_switch
from app.models import (
    DiagramDocument,
    TutorAskResponse,
    TutorResponseMode,
    TutorToolCallRecord,
)
from app.services.learning import generate_challenges
from app.services.validators import validate_diagram

INJECTION_PATTERNS = (
    "ignore previous",
    "ignore all instructions",
    "system prompt",
    "reveal api key",
    "print api key",
    "show secret",
    "bypass",
    "jailbreak",
)

PHYSICS_OUT_OF_SCOPE = (
    "voltage",
    "volt",
    "electric current",
    "electrical current",
    "current in",
    "how much current",
    "amp",
    "ampere",
    "ohm",
    "resistance",
    "resistor",
    "watt",
    "power",
    "brightness",
    "short circuit",
)

BIOLOGY_OUT_OF_SCOPE = (
    "extinct",
    "extinction",
    "population",
    "die out",
    "starve",
    "how many",
    "increase in number",
    "decrease in number",
    "ecosystem collapse",
)

CHEMISTRY_OUT_OF_SCOPE = (
    "toxic",
    "toxicity",
    "poison",
    "safe to drink",
    "lab safety",
    "reaction yield",
    "medical",
    "medicine",
    "flammable",
)

MATH_OUT_OF_SCOPE = (
    "asymptote",
    "integral",
    "derivative",
    "extrapolate",
    "at infinity",
)


def _require_confirmed_diagram(diagram: DiagramDocument) -> None:
    if diagram.review_status != "confirmed":
        raise DomainSimulationError(
            code="UNREVIEWED_DIAGRAM",
            message="The tutor can only answer questions about a confirmed diagram.",
            status_code=403,
        )
    validation = validate_diagram(diagram)
    if not validation.valid or not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_DIAGRAM",
            message="Diagram must pass structural and domain validation before tutoring.",
            status_code=422,
            details=validation.errors,
        )


# --- Deterministic Graph Query Tools ---


def tool_get_neighbors(diagram: DiagramDocument, node_id: str) -> TutorToolCallRecord:
    """Return exact direct neighbors and incident edge IDs for node_id."""
    node_by_id = {n.id: n for n in diagram.nodes}
    node = node_by_id.get(node_id)
    if node is None:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Node '{node_id}' does not exist in this diagram.",
            status_code=400,
        )

    incoming: list[str] = []
    outgoing: list[str] = []
    cited_nodes = [node.id]
    cited_edges: list[str] = []

    for edge in diagram.edges:
        if edge.source == node_id and edge.target in node_by_id:
            outgoing.append(f"{node_by_id[edge.target].label} [{edge.target}] ({edge.relation})")
            cited_nodes.append(edge.target)
            cited_edges.append(edge.id)
        elif edge.target == node_id and edge.source in node_by_id:
            incoming.append(f"{node_by_id[edge.source].label} [{edge.source}] ({edge.relation})")
            cited_nodes.append(edge.source)
            cited_edges.append(edge.id)

    if diagram.domain in {"physics_circuit", "chemistry_molecule"}:
        all_n = incoming + outgoing
        summary = (
            f"{node.label} [{node.id}] is directly connected to: {', '.join(all_n)}."
            if all_n
            else f"{node.label} [{node.id}] has no direct connections."
        )
    else:
        in_str = ", ".join(incoming) if incoming else "none"
        out_str = ", ".join(outgoing) if outgoing else "none"
        summary = (
            f"{node.label} [{node.id}] — incoming from: {in_str}; outgoing to: {out_str}."
        )

    return TutorToolCallRecord(
        tool_name="get_neighbors",
        arguments={"node_id": node_id},
        summary=summary,
        cited_node_ids=list(dict.fromkeys(cited_nodes)),
        cited_edge_ids=list(dict.fromkeys(cited_edges)),
    )


def tool_shortest_path(
    diagram: DiagramDocument, start_id: str, target_id: str
) -> TutorToolCallRecord:
    """Find shortest valid path between start_id and target_id respecting domain directionality."""
    node_by_id = {n.id: n for n in diagram.nodes}
    if start_id not in node_by_id or target_id not in node_by_id:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message="Both start_id and target_id must exist in this diagram.",
            status_code=400,
        )

    undirected = diagram.domain in {"physics_circuit", "chemistry_molecule"}
    adj: dict[str, list[tuple[str, str]]] = {nid: [] for nid in node_by_id}
    for e in diagram.edges:
        if e.source in adj and e.target in adj:
            adj[e.source].append((e.target, e.id))
            if undirected:
                adj[e.target].append((e.source, e.id))

    queue: deque[tuple[list[str], list[str]]] = deque([([start_id], [])])
    visited = {start_id}
    found_nodes: list[str] = []
    found_edges: list[str] = []

    while queue:
        n_path, e_path = queue.popleft()
        cur = n_path[-1]
        if cur == target_id:
            found_nodes, found_edges = n_path, e_path
            break
        for nxt, eid in adj[cur]:
            if nxt not in visited:
                visited.add(nxt)
                queue.append(([*n_path, nxt], [*e_path, eid]))

    if not found_nodes:
        return TutorToolCallRecord(
            tool_name="shortest_path",
            arguments={"start_id": start_id, "target_id": target_id},
            summary=(
                f"No valid path exists from {node_by_id[start_id].label} [{start_id}] "
                f"to {node_by_id[target_id].label} [{target_id}] in this diagram."
            ),
            cited_node_ids=[start_id, target_id],
            cited_edge_ids=[],
        )

    labels = " -> ".join(f"{node_by_id[nid].label} [{nid}]" for nid in found_nodes)
    return TutorToolCallRecord(
        tool_name="shortest_path",
        arguments={"start_id": start_id, "target_id": target_id},
        summary=f"Verified path ({len(found_edges)} step(s)): {labels}.",
        cited_node_ids=found_nodes,
        cited_edge_ids=found_edges,
    )


def tool_component_state(
    diagram: DiagramDocument, node_id: str | None = None
) -> TutorToolCallRecord:
    """Return explicit deterministic state of a component or diagram."""
    node_by_id = {n.id: n for n in diagram.nodes}
    if node_id is not None and node_id not in node_by_id:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Component '{node_id}' does not exist in this diagram.",
            status_code=400,
        )

    if diagram.domain == "physics_circuit":
        st = evaluate_circuit_state(diagram)
        if node_id is not None:
            node = node_by_id[node_id]
            if node.kind == "switch":
                desc = f"{node.label} [{node.id}] is currently {st.switch_states[node.id]}."
            elif node.kind == "bulb":
                desc = (
                    f"{node.label} [{node.id}] is currently {st.bulb_states[node.id].upper()} "
                    f"(loop_wired={st.loop_wired}, all_switches_closed={st.all_switches_closed})."
                )
            else:
                desc = f"{node.label} [{node.id}] is the circuit battery (loop_wired={st.loop_wired})."
            cited = [node.id]
        else:
            sw_part = ", ".join(f"{node_by_id[k].label}={v}" for k, v in st.switch_states.items())
            b_part = ", ".join(f"{node_by_id[k].label}={v.upper()}" for k, v in st.bulb_states.items())
            desc = f"Circuit state: loop_wired={st.loop_wired}; {sw_part}; {b_part}."
            cited = [n.id for n in diagram.nodes]
        return TutorToolCallRecord(
            tool_name="component_state",
            arguments={"node_id": node_id},
            summary=desc,
            cited_node_ids=cited,
            cited_edge_ids=[e.id for e in diagram.edges],
        )

    if diagram.domain == "math_plot":
        analysis = analyze_math_plot(diagram)
        desc = (
            f"Math plot has {analysis.point_count} points. "
            f"Global max: {analysis.global_max.label} [{analysis.global_max.id}]; "
            f"Global min: {analysis.global_min.label} [{analysis.global_min.id}]."
        )
        return TutorToolCallRecord(
            tool_name="component_state",
            arguments={"node_id": node_id},
            summary=desc,
            cited_node_ids=[analysis.global_max.id, analysis.global_min.id],
            cited_edge_ids=[],
        )

    if diagram.domain == "chemistry_molecule":
        counts = get_atom_counts(diagram)
        desc = (
            f"Molecule {diagram.title} (formula {diagram.domain_model.formula}, "  # type: ignore[union-attr]
            f"SMILES: {diagram.domain_model.smiles}): atom counts {counts}."  # type: ignore[union-attr]
        )
        return TutorToolCallRecord(
            tool_name="component_state",
            arguments={"node_id": node_id},
            summary=desc,
            cited_node_ids=[n.id for n in diagram.nodes],
            cited_edge_ids=[e.id for e in diagram.edges],
        )

    if diagram.domain == "cs_flowchart":
        trace = execute_flowchart(diagram)
        return TutorToolCallRecord(
            tool_name="component_state",
            arguments={"node_id": node_id},
            summary=trace.announcement,
            cited_node_ids=[s.node_id for s in trace.steps[:5]],
            cited_edge_ids=[],
        )

    # Biology fallback
    return TutorToolCallRecord(
        tool_name="component_state",
        arguments={"node_id": node_id},
        summary=(
            f"Food web contains {len(diagram.nodes)} organisms and "
            f"{len(diagram.edges)} directed feeding relationships."
        ),
        cited_node_ids=[n.id for n in diagram.nodes],
        cited_edge_ids=[e.id for e in diagram.edges],
    )


def tool_energy_flow(diagram: DiagramDocument, organism_id: str) -> TutorToolCallRecord:
    """Biology-only tool reporting exact incoming/outgoing energy links and paths."""
    if diagram.domain != "biology_food_web":
        raise DomainSimulationError(
            code="INVALID_DOMAIN_TOOL",
            message="energy_flow tool is only valid for biology_food_web diagrams.",
            status_code=400,
        )
    rels = get_organism_relations(diagram, organism_id)
    paths = get_energy_paths(diagram, organism_id)
    node_by_id = {n.id: n for n in diagram.nodes}

    in_labels = [f"{n.label} [{n.id}]" for _, n in rels.receives_energy_from]
    out_labels = [f"{n.label} [{n.id}]" for _, n in rels.provides_energy_to]
    path_strs = [" -> ".join(node_by_id[nid].label for nid in p) for p in paths]

    cited_nodes = [organism_id] + [n.id for _, n in rels.receives_energy_from] + [
        n.id for _, n in rels.provides_energy_to
    ]
    cited_edges = [e.id for e, _ in rels.receives_energy_from] + [
        e.id for e, _ in rels.provides_energy_to
    ]

    summary = (
        f"Energy flow for {rels.organism.label} [{organism_id}] (food -> consumer): "
        f"receives energy from {', '.join(in_labels) or 'none'}; "
        f"provides energy to {', '.join(out_labels) or 'none'}. "
        f"Downstream paths: {'; '.join(path_strs) or 'none'}."
    )
    return TutorToolCallRecord(
        tool_name="energy_flow",
        arguments={"organism_id": organism_id},
        summary=summary,
        cited_node_ids=list(dict.fromkeys(cited_nodes)),
        cited_edge_ids=list(dict.fromkeys(cited_edges)),
    )


def tool_run_verified_simulation(
    diagram: DiagramDocument, action_type: str, target_id: str
) -> TutorToolCallRecord:
    """Execute a verified domain simulation on a deep copy without mutating input."""
    if action_type == "toggle_switch":
        sim = toggle_switch(diagram, target_id)
        return TutorToolCallRecord(
            tool_name="run_verified_simulation",
            arguments={"action_type": action_type, "target_id": target_id},
            summary=f"{sim.announcement} Changes: {'; '.join(sim.changes)}.",
            cited_node_ids=[target_id, *[n.id for n in diagram.nodes if n.kind == "bulb"]],
            cited_edge_ids=[e.id for e in diagram.edges],
        )
    if action_type == "remove_organism":
        sim = remove_organism(diagram, target_id)
        removed_edge_ids = [
            e.id for e in diagram.edges if target_id in (e.source, e.target)
        ]
        return TutorToolCallRecord(
            tool_name="run_verified_simulation",
            arguments={"action_type": action_type, "target_id": target_id},
            summary=sim.announcement,
            cited_node_ids=[target_id],
            cited_edge_ids=removed_edge_ids,
        )
    raise DomainSimulationError(
        code="INVALID_ACTION",
        message=f"Unsupported simulation tool action '{action_type}'.",
        status_code=400,
    )


def tool_get_learning_feedback(diagram: DiagramDocument) -> TutorToolCallRecord:
    """Return available verified Guided Learning Lab challenges for the diagram."""
    ch_set = generate_challenges(diagram)
    if not ch_set.available:
        summary = ch_set.unavailable_reason or "No learning challenges available."
    else:
        titles = "; ".join(c.title for c in ch_set.challenges)
        summary = f"Available guided challenges ({len(ch_set.challenges)}): {titles}."
    return TutorToolCallRecord(
        tool_name="get_learning_feedback",
        arguments={},
        summary=summary,
        cited_node_ids=[n.id for n in diagram.nodes[:3]],
        cited_edge_ids=[],
    )


# --- Optional External Narrator Interface (Strictly Grounded) ---


class TutorNarrator(ABC):
    """Optional natural-language rephraser layered over verified tool outputs."""

    @abstractmethod
    def narrate(
        self,
        question: str,
        tool_calls: list[TutorToolCallRecord],
        response_mode: TutorResponseMode,
    ) -> str:
        """Rephrase verified tool outputs without adding ungrounded facts."""


# --- Grounded Question Router ---


def _find_mentioned_nodes(diagram: DiagramDocument, question_lower: str) -> list[str]:
    matched: list[str] = []
    for node in diagram.nodes:
        if (
            node.id.lower() in question_lower
            or node.label.lower() in question_lower
            or any(
                part in question_lower
                for part in node.label.lower().split()
                if len(part) >= 3 and part not in {"the", "and", "for", "set"}
            )
        ):
            matched.append(node.id)
    return matched


def _is_out_of_scope(diagram: DiagramDocument, q_lower: str) -> tuple[bool, str | None]:
    if any(p in q_lower for p in INJECTION_PATTERNS):
        return (
            True,
            "I only answer questions grounded in the confirmed diagram using verified tools.",
        )

    if diagram.domain == "physics_circuit" and any(k in q_lower for k in PHYSICS_OUT_OF_SCOPE):
        return (
            True,
            "This qualitative single-loop series model does not establish voltage, current, resistance, power, or brightness. Ask about switch state, bulb ON/OFF, or wire connections.",
        )

    if diagram.domain == "biology_food_web" and any(k in q_lower for k in BIOLOGY_OUT_OF_SCOPE):
        return (
            True,
            "This food web diagram does not establish extinction or population size changes. Ask which feeding relationships connect to an organism or disappear when it is removed.",
        )

    if diagram.domain == "chemistry_molecule" and any(k in q_lower for k in CHEMISTRY_OUT_OF_SCOPE):
        return (
            True,
            "This beginner molecular graph does not establish toxicity, reaction yields, medical properties, or lab safety. Ask about atom counts, covalent bonds, or neighbors.",
        )

    if diagram.domain == "math_plot" and any(k in q_lower for k in MATH_OUT_OF_SCOPE):
        return (
            True,
            "This finite XY plot does not establish asymptotes, derivatives, or values outside the given points. Ask about extrema, intervals, or computable intercepts.",
        )

    return False, None


def answer_grounded_question(
    diagram: DiagramDocument,
    question: str,
    response_mode: TutorResponseMode = "explanation",
    learn_mode: bool = False,
    narrator: TutorNarrator | None = None,
) -> TutorAskResponse:
    """Answer a learner question strictly from confirmed graph tools, or abstain honestly."""
    _require_confirmed_diagram(diagram)

    q_clean = question.strip()
    q_lower = q_clean.lower()

    out_of_scope, follow_up = _is_out_of_scope(diagram, q_lower)
    if out_of_scope:
        return TutorAskResponse(
            grounded=False,
            abstained=True,
            provenance="deterministic_tools",
            response_mode=response_mode,
            answer="Not established by this diagram.",
            follow_up=follow_up,
            cited_node_ids=[],
            cited_edge_ids=[],
            tool_calls=[],
        )

    mentioned = _find_mentioned_nodes(diagram, q_lower)
    tool_calls: list[TutorToolCallRecord] = []

    # 1. Verified simulation queries ("what happens if I close/open switch / remove organism")
    if diagram.domain == "physics_circuit" and any(
        k in q_lower for k in ("toggle", "close", "open", "what happens", "turn on", "turn off")
    ):
        sw = next((n.id for n in diagram.nodes if n.kind == "switch"), None)
        if sw:
            tool_calls.append(tool_run_verified_simulation(diagram, "toggle_switch", sw))

    elif diagram.domain == "biology_food_web" and any(
        k in q_lower for k in ("remove", "delete", "disappear", "what happens")
    ):
        if mentioned:
            tool_calls.append(
                tool_run_verified_simulation(diagram, "remove_organism", mentioned[0])
            )

    # 2. Path queries ("path", "reach", "from X to Y")
    elif any(k in q_lower for k in ("path", "reach", "route")) and len(mentioned) >= 2:
        tool_calls.append(tool_shortest_path(diagram, mentioned[0], mentioned[1]))

    # 3. Energy flow / neighbor queries
    elif diagram.domain == "biology_food_web" and mentioned and any(
        k in q_lower for k in ("energy", "eat", "eats", "eaten", "prey", "predator", "neighbor", "connect", "arrow")
    ):
        tool_calls.append(tool_energy_flow(diagram, mentioned[0]))

    elif mentioned and any(
        k in q_lower for k in ("neighbor", "connect", "wire", "bond", "attached", "next", "branch")
    ):
        tool_calls.append(tool_get_neighbors(diagram, mentioned[0]))

    # 4. State / summary / extrema / formula queries
    elif any(
        k in q_lower
        for k in ("state", "status", "on", "off", "max", "min", "formula", "smiles", "count", "how many atoms", "trace", "result", "value")
    ):
        target = mentioned[0] if mentioned else None
        tool_calls.append(tool_component_state(diagram, target))

    # 5. Learning challenge / hint queries
    elif any(k in q_lower for k in ("challenge", "quiz", "practice", "learn")):
        tool_calls.append(tool_get_learning_feedback(diagram))

    # 6. Fallback when a single valid node is mentioned
    elif len(mentioned) == 1:
        tool_calls.append(tool_get_neighbors(diagram, mentioned[0]))

    if not tool_calls:
        return TutorAskResponse(
            grounded=False,
            abstained=True,
            provenance="deterministic_tools",
            response_mode=response_mode,
            answer="Not established by this diagram.",
            follow_up=(
                "Could you name a specific object in this diagram (for example: "
                + ", ".join(n.label for n in diagram.nodes[:3])
                + ") and ask about its connections, path, or verified state?"
            ),
            cited_node_ids=[],
            cited_edge_ids=[],
            tool_calls=[],
        )

    cited_nodes = list(
        dict.fromkeys(nid for tc in tool_calls for nid in tc.cited_node_ids)
    )
    cited_edges = list(
        dict.fromkeys(eid for tc in tool_calls for eid in tc.cited_edge_ids)
    )

    # Learn-mode prediction scaffold when response_mode is "hint"
    if learn_mode and response_mode == "hint":
        node_by_id = {n.id: n for n in diagram.nodes}
        ref_labels = ", ".join(
            f"{node_by_id[nid].label} [{nid}]" for nid in cited_nodes[:3] if nid in node_by_id
        )
        answer = (
            f"Prediction prompt: Before revealing the verified result, check {ref_labels or 'the diagram'} "
            "and predict the outcome yourself. Switch Response style to 'Full explanation' or 'Direct answer' "
            "when you are ready to compare with the deterministic tool output."
        )
        return TutorAskResponse(
            grounded=True,
            abstained=False,
            provenance="deterministic_tools",
            response_mode="hint",
            answer=answer,
            follow_up="What do you predict will happen based on the cited components?",
            cited_node_ids=cited_nodes,
            cited_edge_ids=cited_edges,
            tool_calls=tool_calls,
        )

    if narrator is not None:
        answer = narrator.narrate(q_clean, tool_calls, response_mode)
        provenance = "ai_grounded_narrator"
    else:
        combined = " ".join(tc.summary for tc in tool_calls)
        if response_mode == "direct":
            answer = combined
        else:
            tools_used = ", ".join(tc.tool_name for tc in tool_calls)
            answer = f"Verified via {tools_used}: {combined}"
        provenance = "deterministic_tools"

    return TutorAskResponse(
        grounded=True,
        abstained=False,
        provenance=provenance,  # type: ignore[arg-type]
        response_mode=response_mode,
        answer=answer,
        follow_up=None,
        cited_node_ids=cited_nodes,
        cited_edge_ids=cited_edges,
        tool_calls=tool_calls,
    )
