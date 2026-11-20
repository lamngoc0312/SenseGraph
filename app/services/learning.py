"""Deterministic Guided Learning Lab (Predict -> Experiment -> Explain) service.

All scientific outcomes and challenge grading are derived strictly from the
validated semantic graph and the Physics/Biology Python engines. No LLM grading
and no quantitative claims outside P0 scope.
"""

from __future__ import annotations

from app.domains import DomainSimulationError
from app.domains.biology import (
    get_energy_paths,
    get_organism_relations,
    remove_organism,
)
from app.domains.flowchart import execute_flowchart
from app.domains.physics import evaluate_circuit_state, toggle_switch
from app.models import (
    ChallengeOption,
    DiagramDocument,
    FlowchartModel,
    LearningChallenge,
    LearningChallengeSetResponse,
    LearningEvaluationResponse,
    SeriesCircuitModel,
)
from app.services.validators import validate_diagram


def _format_list(items: list[str]) -> str:
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _require_confirmed_valid_diagram(diagram: DiagramDocument) -> None:
    if diagram.review_status != "confirmed":
        raise DomainSimulationError(
            code="UNREVIEWED_DIAGRAM",
            message="Diagram must be confirmed before starting Guided Learning Lab.",
            status_code=403,
        )
    validation = validate_diagram(diagram)
    if not validation.valid or not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_DIAGRAM",
            message="Diagram is not valid for Guided Learning Lab.",
            status_code=422,
            details=validation.errors,
        )


# --- Physics challenge generation & evaluation ---


def _build_physics_challenges(diagram: DiagramDocument) -> list[LearningChallenge]:
    assert isinstance(diagram.domain_model, SeriesCircuitModel)
    switch_node = next((n for n in diagram.nodes if n.kind == "switch"), None)
    bulbs = [n for n in diagram.nodes if n.kind == "bulb"]
    if switch_node is None or not bulbs:
        return []

    state = evaluate_circuit_state(diagram)
    current_sw = state.switch_states[switch_node.id]
    action_verb = "close" if current_sw == "open" else "open"
    reverse_verb = "open" if current_sw == "open" else "close"
    bulb_names = _format_list([b.label for b in bulbs])
    bulb_noun = "bulb" if len(bulbs) == 1 else "bulbs"

    challenges: list[LearningChallenge] = [
        LearningChallenge(
            id=f"physics_toggle:{switch_node.id}",
            template="physics_toggle_switch",
            title="Predict Bulb State After Toggling the Switch",
            prompt=(
                f"{switch_node.label} is currently {current_sw}. "
                f"Before running the experiment, predict: what happens to {bulb_names} "
                f"when you {action_verb} {switch_node.label}?"
            ),
            hint=(
                "Check whether the wire loop is continuous and whether the switch "
                "will complete or break the single series path."
            ),
            input_type="single_choice",
            options=[
                ChallengeOption(id="on", label=f"{bulb_names} will be ON"),
                ChallengeOption(id="off", label=f"{bulb_names} will be OFF"),
            ],
            action_type="toggle_switch",
            target_id=switch_node.id,
            scientific_note=(
                "Qualitative single-loop series model only: predicts ON/OFF state "
                "from loop continuity and switch state, not voltage or current."
            ),
        ),
        LearningChallenge(
            id=f"physics_neighbors:{switch_node.id}",
            template="physics_loop_neighbors",
            title="Trace Direct Wire Connections",
            prompt=(
                f"Which components are directly connected by a wire to "
                f"{switch_node.label} in this series loop?"
            ),
            hint=(
                f"Inspect {switch_node.label} in the component list to check its "
                "direct wire connections before submitting."
            ),
            input_type="multi_choice",
            options=[
                ChallengeOption(id=n.id, label=f"{n.label} ({n.kind})")
                for n in diagram.nodes
                if n.id != switch_node.id
            ],
            action_type="inspect_only",
            target_id=switch_node.id,
            scientific_note=(
                "In a single-loop series circuit, every component connects directly "
                "to two adjacent neighbors along the loop."
            ),
        ),
        LearningChallenge(
            id=f"physics_reverse:{switch_node.id}",
            template="physics_reverse_toggle",
            title="Predict the Reverse Switch Operation",
            prompt=(
                f"Suppose you first {action_verb} {switch_node.label}, and then "
                f"{reverse_verb} {switch_node.label} again. What state will "
                f"{bulb_names} ({bulb_noun}) end up in?"
            ),
            hint=(
                "Think about whether the final switch position leaves the series loop "
                "closed (complete) or open (broken)."
            ),
            input_type="single_choice",
            options=[
                ChallengeOption(id="on", label=f"{bulb_names} will end up ON"),
                ChallengeOption(id="off", label=f"{bulb_names} will end up OFF"),
            ],
            action_type="inspect_only",
            target_id=switch_node.id,
            scientific_note=(
                "Qualitative single-loop series model only: toggling twice returns "
                "the switch to its starting state."
            ),
        ),
    ]
    return challenges


def _evaluate_physics_challenge(
    diagram: DiagramDocument,
    challenge_id: str,
    selected_option_ids: list[str],
) -> LearningEvaluationResponse:
    node_by_id = {n.id: n for n in diagram.nodes}
    parts = challenge_id.split(":", 1)
    if len(parts) != 2:
        raise DomainSimulationError(
            code="INVALID_CHALLENGE",
            message=f"Unknown learning challenge '{challenge_id}'.",
            status_code=400,
        )
    kind_key, target_id = parts
    target_node = node_by_id.get(target_id)
    if target_node is None:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Challenge target '{target_id}' was not found in this diagram.",
            status_code=400,
        )

    bulbs = [n for n in diagram.nodes if n.kind == "bulb"]
    bulb_names = _format_list([b.label for b in bulbs])

    if kind_key == "physics_toggle":
        sim_result = toggle_switch(diagram, target_id)
        after_state = evaluate_circuit_state(sim_result.updated_diagram)
        expected = "on" if after_state.bulbs_on else "off"
        selected_clean = [s.strip().lower() for s in selected_option_ids if s.strip()]
        correct = selected_clean == [expected]
        new_sw_state = after_state.switch_states[target_id]

        expected_label = f"{bulb_names} {'ON' if expected == 'on' else 'OFF'}"
        if correct:
            summary = f"Correct prediction! {sim_result.announcement}"
        else:
            summary = (
                f"Not quite. You predicted {_format_list(selected_clean) or 'nothing'}, "
                f"but the experiment showed: {sim_result.announcement}"
            )

        explanation = (
            f"Because this is a verified single-loop series circuit (loop_wired=true) "
            f"and {target_node.label} is now {new_sw_state}, "
            + (
                f"there is one complete closed path through {_format_list([node_by_id[c].label for c in diagram.domain_model.sequence])}, so {bulb_names} turn(s) ON."
                if after_state.bulbs_on
                else f"the single series path is broken at {target_node.label}, so {bulb_names} stay(s) OFF."
            )
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=selected_clean,
            expected_option_ids=[expected],
            expected_labels=[expected_label],
            summary=summary,
            explanation=explanation,
            evidence=[
                f"Verified single-loop wire continuity: {after_state.loop_wired}",
                f"{target_node.label} state after action: {new_sw_state}",
                *sim_result.changes,
            ],
            related_node_ids=[target_id, *[b.id for b in bulbs]],
            simulation_result=sim_result,
        )

    if kind_key == "physics_neighbors":
        neighbor_ids: list[str] = []
        for edge in diagram.edges:
            if edge.source == target_id and edge.target in node_by_id:
                neighbor_ids.append(edge.target)
            elif edge.target == target_id and edge.source in node_by_id:
                neighbor_ids.append(edge.source)
        expected_set = set(neighbor_ids)
        selected_set = set(selected_option_ids)
        correct = selected_set == expected_set
        expected_labels = [node_by_id[nid].label for nid in neighbor_ids]

        summary = (
            f"Correct! {target_node.label} connects directly to {_format_list(expected_labels)}."
            if correct
            else f"Check the wires: {target_node.label} connects directly to {_format_list(expected_labels)}."
        )
        explanation = (
            f"In this verified single-loop series circuit, {target_node.label} has direct wire "
            f"connections to {_format_list(expected_labels)}. Every component in a simple series "
            "loop sits between two neighbors so electricity has only one path around the loop."
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=sorted(selected_set),
            expected_option_ids=neighbor_ids,
            expected_labels=expected_labels,
            summary=summary,
            explanation=explanation,
            evidence=[
                f"Wire: {node_by_id[e.source].label} — {node_by_id[e.target].label}"
                for e in diagram.edges
                if target_id in (e.source, e.target)
            ],
            related_node_ids=[target_id, *neighbor_ids],
            simulation_result=None,
        )

    if kind_key == "physics_reverse":
        step1 = toggle_switch(diagram, target_id)
        step2 = toggle_switch(step1.updated_diagram, target_id)
        final_state = evaluate_circuit_state(step2.updated_diagram)
        expected = "on" if final_state.bulbs_on else "off"
        selected_clean = [s.strip().lower() for s in selected_option_ids if s.strip()]
        correct = selected_clean == [expected]
        final_sw_state = final_state.switch_states[target_id]
        expected_label = f"{bulb_names} {'ON' if expected == 'on' else 'OFF'}"

        summary = (
            f"Correct! After toggling twice, {target_node.label} is {final_sw_state} and {bulb_names} is/are {expected.upper()}."
            if correct
            else f"Not quite. After toggling twice, {target_node.label} returns to {final_sw_state}, so {bulb_names} is/are {expected.upper()}."
        )
        explanation = (
            f"Toggling {target_node.label} once changes it to "
            f"{step1.updated_diagram.domain_model.switch_states[target_id]}, and toggling it a "
            f"second time returns it to {final_sw_state}. Because the series loop is "
            f"{'complete' if final_state.bulbs_on else 'open'}, {bulb_names} end(s) up {expected.upper()}."
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=selected_clean,
            expected_option_ids=[expected],
            expected_labels=[expected_label],
            summary=summary,
            explanation=explanation,
            evidence=[
                f"Step 1: {step1.announcement}",
                f"Step 2: {step2.announcement}",
            ],
            related_node_ids=[target_id, *[b.id for b in bulbs]],
            simulation_result=None,
        )

    raise DomainSimulationError(
        code="INVALID_CHALLENGE",
        message=f"Unsupported physics challenge '{challenge_id}'.",
        status_code=400,
    )


# --- Biology challenge generation & evaluation ---


def _pick_removal_target(diagram: DiagramDocument) -> str | None:
    if len(diagram.nodes) < 2 or not diagram.edges:
        return None
    # Prefer an intermediate organism with both incoming and outgoing feeding edges.
    for node in diagram.nodes:
        rels = get_organism_relations(diagram, node.id)
        if rels.receives_energy_from and rels.provides_energy_to:
            return node.id
    # Fallback to any organism with at least one incident edge.
    for node in diagram.nodes:
        rels = get_organism_relations(diagram, node.id)
        if rels.receives_energy_from or rels.provides_energy_to:
            return node.id
    return None


def _pick_neighbor_target(diagram: DiagramDocument) -> tuple[str, str] | None:
    # Prefer an organism that provides energy to at least one consumer.
    for node in diagram.nodes:
        rels = get_organism_relations(diagram, node.id)
        if rels.provides_energy_to:
            return node.id, "outgoing"
    for node in diagram.nodes:
        rels = get_organism_relations(diagram, node.id)
        if rels.receives_energy_from:
            return node.id, "incoming"
    return None


def _pick_path_start(diagram: DiagramDocument) -> str | None:
    # Prefer a producer (0 incoming) with at least one path of length >= 3, else >= 2.
    best_id: str | None = None
    best_len = 0
    for node in diagram.nodes:
        paths = get_energy_paths(diagram, node.id)
        max_len = max((len(p) for p in paths), default=0)
        if max_len > best_len:
            best_len = max_len
            best_id = node.id
    return best_id if best_len >= 2 else None


def _build_biology_challenges(diagram: DiagramDocument) -> list[LearningChallenge]:
    node_by_id = {n.id: n for n in diagram.nodes}
    challenges: list[LearningChallenge] = []

    removal_target = _pick_removal_target(diagram)
    if removal_target is not None:
        target_label = node_by_id[removal_target].label
        challenges.append(
            LearningChallenge(
                id=f"biology_remove:{removal_target}",
                template="biology_remove_impact",
                title=f"Predict Relationship Changes When Removing {target_label}",
                prompt=(
                    f"If you temporarily remove {target_label} from this food web diagram, "
                    "which feeding relationships will disappear?"
                ),
                hint=(
                    f"Select every arrow where {target_label} is either the food/prey (source) "
                    "or the consumer/predator (target)."
                ),
                input_type="multi_choice",
                options=[
                    ChallengeOption(
                        id=e.id,
                        label=f"{node_by_id[e.source].label} -> {node_by_id[e.target].label}",
                    )
                    for e in diagram.edges
                    if e.source in node_by_id and e.target in node_by_id
                ],
                action_type="remove_organism",
                target_id=removal_target,
                scientific_note=(
                    "Removing an organism shows only which graph relationships disappear or remain. "
                    "It does NOT predict extinction or population changes."
                ),
            )
        )

    neighbor_choice = _pick_neighbor_target(diagram)
    if neighbor_choice is not None:
        target_id, direction = neighbor_choice
        target_label = node_by_id[target_id].label
        if direction == "outgoing":
            prompt = (
                f"Following the food-to-consumer arrow convention, which organism(s) "
                f"directly receive energy from {target_label}?"
            )
            hint = f"Look for arrows pointing outward from {target_label} to its direct consumers."
        else:
            prompt = (
                f"Following the food-to-consumer arrow convention, which organism(s) "
                f"directly provide energy to {target_label}?"
            )
            hint = f"Look for arrows pointing into {target_label} from its food sources."

        challenges.append(
            LearningChallenge(
                id=f"biology_neighbors_{direction}:{target_id}",
                template="biology_direct_neighbors",
                title=f"Identify Direct Feeding Neighbors of {target_label}",
                prompt=prompt,
                hint=hint,
                input_type="multi_choice",
                options=[
                    ChallengeOption(id=n.id, label=n.label)
                    for n in diagram.nodes
                    if n.id != target_id
                ],
                action_type="inspect_only",
                target_id=target_id,
                scientific_note=(
                    "Arrows in this food web always point from food/prey to consumer/predator."
                ),
            )
        )

    path_start = _pick_path_start(diagram)
    if path_start is not None:
        start_label = node_by_id[path_start].label
        challenges.append(
            LearningChallenge(
                id=f"biology_downstream:{path_start}",
                template="biology_energy_path",
                title=f"Trace Downstream Energy Paths from {start_label}",
                prompt=(
                    f"Starting at {start_label} and following directed food-to-consumer arrows "
                    "one or more steps, which organism(s) can energy reach in this diagram?"
                ),
                hint=(
                    f"Include both direct consumers of {start_label} and consumers further "
                    "along the directed arrow paths."
                ),
                input_type="multi_choice",
                options=[
                    ChallengeOption(id=n.id, label=n.label)
                    for n in diagram.nodes
                    if n.id != path_start
                ],
                action_type="inspect_only",
                target_id=path_start,
                scientific_note=(
                    "Energy paths show confirmed directed feeding links only, not quantitative "
                    "energy transfer or population dynamics."
                ),
            )
        )

    return challenges


def _evaluate_biology_challenge(
    diagram: DiagramDocument,
    challenge_id: str,
    selected_option_ids: list[str],
) -> LearningEvaluationResponse:
    node_by_id = {n.id: n for n in diagram.nodes}
    edge_by_id = {e.id: e for e in diagram.edges}
    parts = challenge_id.split(":", 1)
    if len(parts) != 2:
        raise DomainSimulationError(
            code="INVALID_CHALLENGE",
            message=f"Unknown learning challenge '{challenge_id}'.",
            status_code=400,
        )
    kind_key, target_id = parts
    target_node = node_by_id.get(target_id)
    if target_node is None:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Organism '{target_id}' was not found in this food web.",
            status_code=400,
        )

    if kind_key == "biology_remove":
        sim_result = remove_organism(diagram, target_id)
        remaining_ids = {e.id for e in sim_result.updated_diagram.edges}
        removed_edges = [e for e in diagram.edges if e.id not in remaining_ids]
        remaining_edges = [e for e in diagram.edges if e.id in remaining_ids]

        expected_ids = [e.id for e in removed_edges]
        expected_set = set(expected_ids)
        selected_set = set(selected_option_ids)
        correct = selected_set == expected_set

        expected_labels = [
            f"{node_by_id[e.source].label} -> {node_by_id[e.target].label}"
            for e in removed_edges
        ]
        remaining_labels = [
            f"{node_by_id[e.source].label} -> {node_by_id[e.target].label}"
            for e in remaining_edges
        ]

        missed = [
            f"{node_by_id[edge_by_id[eid].source].label} -> {node_by_id[edge_by_id[eid].target].label}"
            for eid in expected_ids
            if eid not in selected_set
        ]
        extra = [
            f"{node_by_id[edge_by_id[eid].source].label} -> {node_by_id[edge_by_id[eid].target].label}"
            for eid in selected_option_ids
            if eid in edge_by_id and eid not in expected_set
        ]

        if correct:
            summary = (
                f"Correct prediction! Removing {target_node.label} removed exactly "
                f"{len(removed_edges)} feeding relationship(s): {_format_list(expected_labels)}."
            )
        else:
            diff_parts: list[str] = []
            if missed:
                diff_parts.append(f"missed {_format_list(missed)}")
            if extra:
                diff_parts.append(f"selected unaffected {_format_list(extra)}")
            summary = (
                f"Compare with the graph result: you {', '.join(diff_parts) or 'did not match'}. "
                f"Removing {target_node.label} removed {_format_list(expected_labels)}."
            )

        explanation = (
            f"When {target_node.label} is removed from the diagram, only edges directly attached to "
            f"{target_node.label} disappear ({_format_list(expected_labels)}). "
            f"Unrelated feeding relationships remain intact ({_format_list(remaining_labels)}). "
            "Important: this graph operation does NOT predict extinction or population changes."
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=sorted(selected_set),
            expected_option_ids=expected_ids,
            expected_labels=expected_labels,
            summary=summary,
            explanation=explanation,
            evidence=[
                f"Removed relationships ({len(removed_edges)}): {_format_list(expected_labels)}",
                f"Remaining relationships ({len(remaining_edges)}): {_format_list(remaining_labels)}",
                "Scope note: graph relationship change only; no extinction or population prediction.",
            ],
            related_node_ids=[
                n_id
                for e in removed_edges
                for n_id in (e.source, e.target)
                if n_id != target_id
            ],
            simulation_result=sim_result,
        )

    if kind_key in {"biology_neighbors_outgoing", "biology_neighbors_incoming"}:
        rels = get_organism_relations(diagram, target_id)
        if kind_key == "biology_neighbors_outgoing":
            expected_nodes = [tgt for _, tgt in rels.provides_energy_to]
            verb_phrase = f"directly receive energy from {target_node.label}"
        else:
            expected_nodes = [src for _, src in rels.receives_energy_from]
            verb_phrase = f"directly provide energy to {target_node.label}"

        expected_ids = [n.id for n in expected_nodes]
        expected_labels = [n.label for n in expected_nodes]
        selected_set = set(selected_option_ids)
        correct = selected_set == set(expected_ids)

        summary = (
            f"Correct! {_format_list(expected_labels)} {verb_phrase}."
            if correct
            else f"Not quite. In this diagram, {_format_list(expected_labels)} {verb_phrase}."
        )
        explanation = (
            f"Using the food-to-consumer convention (food/prey -> consumer/predator), "
            f"the direct matches for {target_node.label} are: {_format_list(expected_labels)}."
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=sorted(selected_set),
            expected_option_ids=expected_ids,
            expected_labels=expected_labels,
            summary=summary,
            explanation=explanation,
            evidence=[
                f"{node_by_id[e.source].label} -> {node_by_id[e.target].label}"
                for e in diagram.edges
                if (
                    (kind_key == "biology_neighbors_outgoing" and e.source == target_id)
                    or (kind_key == "biology_neighbors_incoming" and e.target == target_id)
                )
            ],
            related_node_ids=[target_id, *expected_ids],
            simulation_result=None,
        )

    if kind_key == "biology_downstream":
        paths = get_energy_paths(diagram, target_id)
        downstream_ids: list[str] = []
        for path in paths:
            for nid in path[1:]:
                if nid not in downstream_ids:
                    downstream_ids.append(nid)
        expected_labels = [node_by_id[nid].label for nid in downstream_ids]
        selected_set = set(selected_option_ids)
        correct = selected_set == set(downstream_ids)

        path_strings = [
            " -> ".join(node_by_id[nid].label for nid in path) for path in paths
        ]
        summary = (
            f"Correct! Downstream organisms from {target_node.label} are {_format_list(expected_labels)}."
            if correct
            else f"Review the paths: downstream organisms from {target_node.label} are {_format_list(expected_labels)}."
        )
        explanation = (
            f"Following directed food-to-consumer arrows from {target_node.label} produces "
            f"{len(paths)} verified energy path(s): {'; '.join(path_strings) or 'none'}. "
            "This traces diagram connections only and does not model population dynamics."
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=sorted(selected_set),
            expected_option_ids=downstream_ids,
            expected_labels=expected_labels,
            summary=summary,
            explanation=explanation,
            evidence=path_strings or ["No downstream paths exist from this organism."],
            related_node_ids=[target_id, *downstream_ids],
            simulation_result=None,
        )

    raise DomainSimulationError(
        code="INVALID_CHALLENGE",
        message=f"Unsupported biology challenge '{challenge_id}'.",
        status_code=400,
    )


# --- Flowchart challenge generation & evaluation (Phase 8) ---


def _build_flowchart_challenges(diagram: DiagramDocument) -> list[LearningChallenge]:
    if not isinstance(diagram.domain_model, FlowchartModel):
        return []
    trace = execute_flowchart(diagram)
    inputs_str = (
        ", ".join(f"{k} = {v}" for k, v in diagram.domain_model.inputs.items()) or "default values"
    )
    challenges: list[LearningChallenge] = []

    first_decision = next((s for s in trace.steps if s.node_kind == "decision"), None)
    if first_decision is not None:
        challenges.append(
            LearningChallenge(
                id=f"flowchart_branch:{first_decision.node_id}",
                template="flowchart_predict_branch",
                title=f"Predict Branch at '{first_decision.node_label}'",
                prompt=(
                    f"With initial inputs ({inputs_str}), when execution first reaches "
                    f"decision '{first_decision.node_label}', which branch will it take?"
                ),
                hint=(
                    "Trace the variable values up to this decision block and evaluate "
                    "its condition using the restricted comparison rules."
                ),
                input_type="single_choice",
                options=[
                    ChallengeOption(id="true", label="TRUE branch"),
                    ChallengeOption(id="false", label="FALSE branch"),
                ],
                action_type="inspect_only",
                target_id=first_decision.node_id,
                scientific_note=(
                    "Evaluated strictly by the safe restricted flowchart interpreter "
                    "(no eval/exec, bounded steps)."
                ),
            )
        )

    if trace.status == "completed" and trace.final_variables:
        last_var = list(trace.final_variables.keys())[-1]
        final_val = trace.final_variables[last_var]
        if type(final_val) is int:
            candidate_vals = sorted({final_val, final_val + 1, max(0, final_val - 1)})
            options = [
                ChallengeOption(id=str(v), label=f"{last_var} = {v}")
                for v in candidate_vals
            ]
        else:
            options = [
                ChallengeOption(id="True", label=f"{last_var} = True"),
                ChallengeOption(id="False", label=f"{last_var} = False"),
            ]
        challenges.append(
            LearningChallenge(
                id=f"flowchart_final:{last_var}",
                template="flowchart_predict_final_value",
                title=f"Predict Final Value of '{last_var}'",
                prompt=(
                    f"When this flowchart runs to completion with initial inputs ({inputs_str}), "
                    f"what is the final value of variable '{last_var}'?"
                ),
                hint="Step through each assignment and loop condition carefully.",
                input_type="single_choice",
                options=options,
                action_type="inspect_only",
                target_id=diagram.domain_model.entry_node,
                scientific_note=(
                    "Computed deterministically from the traced execution environment."
                ),
            )
        )

    return challenges


def _evaluate_flowchart_challenge(
    diagram: DiagramDocument,
    challenge_id: str,
    selected_option_ids: list[str],
) -> LearningEvaluationResponse:
    parts = challenge_id.split(":", 1)
    if len(parts) != 2:
        raise DomainSimulationError(
            code="INVALID_CHALLENGE",
            message=f"Unknown flowchart challenge '{challenge_id}'.",
            status_code=400,
        )
    kind_key, target = parts
    trace = execute_flowchart(diagram)

    if kind_key == "flowchart_branch":
        step = next(
            (s for s in trace.steps if s.node_id == target and s.node_kind == "decision"),
            None,
        )
        if step is None or step.branch_taken is None:
            raise DomainSimulationError(
                code="UNKNOWN_TARGET",
                message=f"Decision '{target}' was not reached during execution.",
                status_code=400,
            )
        expected = step.branch_taken
        selected_clean = [s.strip().lower() for s in selected_option_ids if s.strip()]
        correct = selected_clean == [expected]
        vars_desc = ", ".join(f"{k}={v}" for k, v in step.variables.items()) or "none"

        summary = (
            f"Correct! At step {step.step_index}, '{step.node_label}' took the {expected.upper()} branch."
            if correct
            else f"Not quite. At step {step.step_index}, '{step.node_label}' took the {expected.upper()} branch."
        )
        explanation = (
            f"At step {step.step_index}, the variable environment was ({vars_desc}). "
            f"{step.action_description}"
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=selected_clean,
            expected_option_ids=[expected],
            expected_labels=[f"{expected.upper()} branch"],
            summary=summary,
            explanation=explanation,
            evidence=[
                f"Step {step.step_index}: {step.action_description}",
                f"Variables at decision: {vars_desc}",
                f"Trace outcome: {trace.announcement}",
            ],
            related_node_ids=[step.node_id] + ([step.next_node_id] if step.next_node_id else []),
            simulation_result=None,
        )

    if kind_key == "flowchart_final":
        if target not in trace.final_variables:
            raise DomainSimulationError(
                code="UNKNOWN_TARGET",
                message=f"Variable '{target}' was not found in final execution state.",
                status_code=400,
            )
        expected = str(trace.final_variables[target])
        selected_clean = [s.strip() for s in selected_option_ids if s.strip()]
        correct = selected_clean == [expected]
        summary = (
            f"Correct! After {trace.steps_executed} steps, {target} = {expected}."
            if correct
            else f"Not quite. After {trace.steps_executed} steps, {target} = {expected}."
        )
        explanation = (
            f"{trace.announcement} Inspect the execution trace to verify each assignment and branch."
        )
        return LearningEvaluationResponse(
            challenge_id=challenge_id,
            correct=correct,
            selected_option_ids=selected_clean,
            expected_option_ids=[expected],
            expected_labels=[f"{target} = {expected}"],
            summary=summary,
            explanation=explanation,
            evidence=[s.action_description for s in trace.steps[-4:]],
            related_node_ids=[diagram.domain_model.entry_node],  # type: ignore[union-attr]
            simulation_result=None,
        )

    raise DomainSimulationError(
        code="INVALID_CHALLENGE",
        message=f"Unsupported flowchart challenge '{challenge_id}'.",
        status_code=400,
    )


# --- Public API ---


def generate_challenges(diagram: DiagramDocument) -> LearningChallengeSetResponse:
    """Generate deterministic Guided Learning Lab challenges for a confirmed diagram."""
    _require_confirmed_valid_diagram(diagram)

    if diagram.domain == "physics_circuit":
        challenges = _build_physics_challenges(diagram)
    elif diagram.domain == "biology_food_web":
        challenges = _build_biology_challenges(diagram)
    else:
        challenges = _build_flowchart_challenges(diagram)

    if not challenges:
        return LearningChallengeSetResponse(
            available=False,
            unavailable_reason=(
                "No guided learning challenges can be generated for this diagram "
                "(for example, a food web with no feeding relationships yet)."
            ),
            domain=diagram.domain,
            challenges=[],
        )

    return LearningChallengeSetResponse(
        available=True,
        unavailable_reason=None,
        domain=diagram.domain,
        challenges=challenges,
    )


def evaluate_challenge(
    diagram: DiagramDocument,
    challenge_id: str,
    selected_option_ids: list[str],
) -> LearningEvaluationResponse:
    """Evaluate a learner's prediction against deterministic domain engine outcomes."""
    _require_confirmed_valid_diagram(diagram)

    if diagram.domain == "physics_circuit":
        return _evaluate_physics_challenge(diagram, challenge_id, selected_option_ids)
    if diagram.domain == "biology_food_web":
        return _evaluate_biology_challenge(diagram, challenge_id, selected_option_ids)
    return _evaluate_flowchart_challenge(diagram, challenge_id, selected_option_ids)
