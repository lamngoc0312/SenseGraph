"""Deterministic qualitative single-loop series circuit engine (Physics P0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.domains import DomainSimulationError
from app.models import (
    DiagramDocument,
    Node,
    SeriesCircuitModel,
    SimulationResponse,
    SwitchState,
)

ALLOWED_PHYSICS_NODE_KINDS = frozenset({"battery", "switch", "bulb"})


@dataclass(frozen=True)
class PhysicsValidationResult:
    """Result of physics-specific semantic and topology validation."""

    valid_semantics: bool
    simulation_ready: bool
    derived_loop_wired: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CircuitState:
    """Deterministic qualitative state of a validated single-loop series circuit."""

    loop_wired: bool
    all_switches_closed: bool
    bulbs_on: bool
    switch_states: dict[str, SwitchState]
    bulb_states: dict[str, Literal["on", "off"]]


def _format_list(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def validate_series_circuit(diagram: DiagramDocument) -> PhysicsValidationResult:
    """Validate P0 single-loop series circuit invariants and derive loop_wired from edges."""
    errors: list[str] = []
    warnings: list[str] = []

    if diagram.domain != "physics_circuit":
        errors.append("Expected domain 'physics_circuit'.")
    if not isinstance(diagram.domain_model, SeriesCircuitModel):
        errors.append("Expected domain_model.kind to be 'series_circuit'.")
        return PhysicsValidationResult(
            valid_semantics=False,
            simulation_ready=False,
            derived_loop_wired=False,
            errors=errors,
            warnings=warnings,
        )

    node_by_id: dict[str, Node] = {node.id: node for node in diagram.nodes}
    if len(node_by_id) != len(diagram.nodes):
        errors.append("Duplicate node IDs detected in circuit diagram.")

    for node in diagram.nodes:
        if node.kind not in ALLOWED_PHYSICS_NODE_KINDS:
            errors.append(
                f"Node '{node.id}' has kind '{node.kind}', which is not allowed in physics_circuit."
            )

    for edge in diagram.edges:
        if edge.relation != "wire":
            errors.append(
                f"Edge '{edge.id}' has relation '{edge.relation}', expected 'wire' in physics_circuit."
            )
        if edge.source not in node_by_id:
            errors.append(f"Edge '{edge.id}' references unknown source node '{edge.source}'.")
        if edge.target not in node_by_id:
            errors.append(f"Edge '{edge.id}' references unknown target node '{edge.target}'.")
        if edge.source == edge.target:
            errors.append(f"Edge '{edge.id}' cannot connect node '{edge.source}' to itself.")

    batteries = [n for n in diagram.nodes if n.kind == "battery"]
    switches = [n for n in diagram.nodes if n.kind == "switch"]
    bulbs = [n for n in diagram.nodes if n.kind == "bulb"]

    if len(batteries) != 1:
        errors.append(
            f"Physics P0 requires exactly 1 battery, found {len(batteries)}."
        )
    if len(switches) != 1:
        errors.append(
            f"Physics P0 requires exactly 1 switch, found {len(switches)}."
        )
    if not (1 <= len(bulbs) <= 2):
        errors.append(
            f"Physics P0 requires 1 or 2 bulbs, found {len(bulbs)}."
        )

    sequence = diagram.domain_model.sequence
    sequence_set = set(sequence)
    node_id_set = set(node_by_id.keys())

    missing_in_sequence = sorted(node_id_set - sequence_set)
    unknown_in_sequence = sorted(sequence_set - node_id_set)
    if missing_in_sequence:
        errors.append(
            f"domain_model.sequence is missing node(s): {', '.join(missing_in_sequence)}."
        )
    if unknown_in_sequence:
        errors.append(
            f"domain_model.sequence references unknown node(s): {', '.join(unknown_in_sequence)}."
        )

    switch_ids = {s.id for s in switches}
    state_keys = set(diagram.domain_model.switch_states.keys())
    if switch_ids and state_keys != switch_ids:
        errors.append(
            "domain_model.switch_states keys must match the circuit's switch node IDs "
            f"(expected {sorted(switch_ids)}, got {sorted(state_keys)})."
        )

    # Derive ring connectivity from wire edges (undirected).
    derived_loop_wired = False
    if not errors:
        n = len(sequence)
        expected_pairs: list[frozenset[str]] = [
            frozenset((sequence[i], sequence[(i + 1) % n])) for i in range(n)
        ]
        expected_set = set(expected_pairs)

        actual_pairs: list[frozenset[str]] = []
        seen_pairs: set[frozenset[str]] = set()
        duplicate_pairs: list[frozenset[str]] = []
        for edge in diagram.edges:
            pair = frozenset((edge.source, edge.target))
            actual_pairs.append(pair)
            if pair in seen_pairs:
                duplicate_pairs.append(pair)
            else:
                seen_pairs.add(pair)

        missing_wires = expected_set - seen_pairs
        extra_wires = seen_pairs - expected_set

        if duplicate_pairs:
            dup_desc = ", ".join(sorted(" - ".join(sorted(p)) for p in duplicate_pairs))
            errors.append(
                f"Unsupported topology: duplicate wire connection(s) found between {dup_desc}."
            )
        if missing_wires:
            miss_desc = ", ".join(sorted(" - ".join(sorted(p)) for p in missing_wires))
            errors.append(
                f"Incomplete series loop: missing wire connection(s) between {miss_desc}."
            )
        if extra_wires:
            extra_desc = ", ".join(sorted(" - ".join(sorted(p)) for p in extra_wires))
            errors.append(
                f"Unsupported non-series topology: extra wire connection(s) between {extra_desc}."
            )

        derived_loop_wired = not duplicate_pairs and not missing_wires and not extra_wires

        if diagram.domain_model.loop_wired != derived_loop_wired:
            warnings.append(
                f"Reported loop_wired={diagram.domain_model.loop_wired} disagreed with "
                f"wire topology; derived loop_wired={derived_loop_wired}."
            )

    simulation_ready = len(errors) == 0 and derived_loop_wired
    return PhysicsValidationResult(
        valid_semantics=len(errors) == 0,
        simulation_ready=simulation_ready,
        derived_loop_wired=derived_loop_wired,
        errors=errors,
        warnings=warnings,
    )


def evaluate_circuit_state(diagram: DiagramDocument) -> CircuitState:
    """Compute qualitative switch and bulb states for a single-loop series circuit."""
    validation = validate_series_circuit(diagram)
    if not isinstance(diagram.domain_model, SeriesCircuitModel):
        raise DomainSimulationError(
            code="INVALID_DIAGRAM",
            message="Circuit evaluation requires a series_circuit domain model.",
            status_code=422,
        )

    switch_states = dict(diagram.domain_model.switch_states)
    all_switches_closed = bool(switch_states) and all(
        state == "closed" for state in switch_states.values()
    )
    bulbs_on = validation.derived_loop_wired and all_switches_closed

    node_by_id = {n.id: n for n in diagram.nodes}
    bulb_states: dict[str, Literal["on", "off"]] = {}
    for comp_id in diagram.domain_model.sequence:
        node = node_by_id.get(comp_id)
        if node is not None and node.kind == "bulb":
            bulb_states[node.id] = "on" if bulbs_on else "off"

    return CircuitState(
        loop_wired=validation.derived_loop_wired,
        all_switches_closed=all_switches_closed,
        bulbs_on=bulbs_on,
        switch_states=switch_states,
        bulb_states=bulb_states,
    )


def build_circuit_summary(diagram: DiagramDocument) -> str:
    """Generate a deterministic plain-language summary for a validated series circuit."""
    if not isinstance(diagram.domain_model, SeriesCircuitModel):
        return diagram.summary

    node_by_id = {n.id: n for n in diagram.nodes}
    ordered_labels = [
        node_by_id[cid].label for cid in diagram.domain_model.sequence if cid in node_by_id
    ]
    state = evaluate_circuit_state(diagram)

    switch_parts = [
        f"{node_by_id[sid].label} is {s_state}"
        for sid, s_state in state.switch_states.items()
        if sid in node_by_id
    ]
    bulb_labels = [node_by_id[bid].label for bid in state.bulb_states if bid in node_by_id]

    if state.bulbs_on:
        bulb_verb = "is" if len(bulb_labels) == 1 else "are"
        outcome = (
            f"The series loop is complete and {_format_list(bulb_labels)} {bulb_verb} on."
        )
    elif not state.loop_wired:
        bulb_verb = "is" if len(bulb_labels) == 1 else "are"
        outcome = (
            f"The series loop is not completely wired, so {_format_list(bulb_labels)} "
            f"{bulb_verb} off."
        )
    else:
        bulb_verb = "is" if len(bulb_labels) == 1 else "are"
        outcome = (
            f"The series loop is open, so {_format_list(bulb_labels)} {bulb_verb} off."
        )

    return (
        f"A simple series circuit connects {_format_list(ordered_labels)} in one loop. "
        f"{', '.join(switch_parts)}. {outcome}"
    )


def toggle_switch(diagram: DiagramDocument, switch_id: str) -> SimulationResponse:
    """Toggle the specified switch in a confirmed, validated series circuit without mutating input."""
    if diagram.domain != "physics_circuit" or not isinstance(
        diagram.domain_model, SeriesCircuitModel
    ):
        raise DomainSimulationError(
            code="INVALID_ACTION",
            message="toggle_switch is only supported for physics_circuit diagrams.",
            status_code=400,
        )

    if diagram.review_status != "confirmed":
        raise DomainSimulationError(
            code="UNREVIEWED_DIAGRAM",
            message="Diagram must be confirmed before running simulation actions.",
            status_code=403,
        )

    validation = validate_series_circuit(diagram)
    if not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_DIAGRAM",
            message="Circuit topology is not valid for P0 single-loop series simulation.",
            status_code=422,
            details=validation.errors,
        )

    if switch_id not in diagram.domain_model.switch_states:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Switch '{switch_id}' was not found in this circuit.",
            status_code=400,
        )

    old_state = evaluate_circuit_state(diagram)
    old_switch_state = old_state.switch_states[switch_id]
    new_switch_state: SwitchState = "closed" if old_switch_state == "open" else "open"

    updated = diagram.model_copy(deep=True)
    assert isinstance(updated.domain_model, SeriesCircuitModel)
    updated.domain_model.switch_states[switch_id] = new_switch_state
    updated.domain_model.loop_wired = True

    new_state = evaluate_circuit_state(updated)
    updated.summary = build_circuit_summary(updated)

    node_by_id = {n.id: n for n in updated.nodes}
    switch_label = node_by_id[switch_id].label

    changes: list[str] = [f"{switch_label}: {old_switch_state} -> {new_switch_state}"]
    bulb_labels: list[str] = []
    for bulb_id, new_bulb_state in new_state.bulb_states.items():
        bulb_label = node_by_id[bulb_id].label
        bulb_labels.append(bulb_label)
        old_bulb_state = old_state.bulb_states[bulb_id]
        changes.append(f"{bulb_label}: {old_bulb_state} -> {new_bulb_state}")

    bulb_verb = "is" if len(bulb_labels) == 1 else "are"
    if new_switch_state == "closed":
        event = "switch_closed"
        announcement = (
            f"{switch_label} closed. The series loop is complete. "
            f"{_format_list(bulb_labels)} {bulb_verb} now on."
        )
    else:
        event = "switch_opened"
        announcement = (
            f"{switch_label} opened. The series loop is broken. "
            f"{_format_list(bulb_labels)} {bulb_verb} now off."
        )

    return SimulationResponse(
        updated_diagram=updated,
        event=event,
        announcement=announcement,
        changes=changes,
    )
