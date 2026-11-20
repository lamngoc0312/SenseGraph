"""Deterministic plain-language diagram and node descriptions."""

from __future__ import annotations

from app.domains.biology import build_food_web_summary, get_organism_relations
from app.domains.chemistry import build_molecule_summary
from app.domains.flowchart import build_flowchart_summary
from app.domains.mathematics import build_math_plot_summary
from app.domains.physics import build_circuit_summary, evaluate_circuit_state
from app.models import DiagramDocument


def describe_diagram(diagram: DiagramDocument) -> str:
    """Generate a deterministic plain-language overview of a confirmed or validated diagram."""
    if diagram.domain == "physics_circuit":
        return build_circuit_summary(diagram)
    if diagram.domain == "biology_food_web":
        return build_food_web_summary(diagram)
    if diagram.domain == "cs_flowchart":
        return build_flowchart_summary(diagram)
    if diagram.domain == "math_plot":
        return build_math_plot_summary(diagram)
    if diagram.domain == "chemistry_molecule":
        return build_molecule_summary(diagram)
    return diagram.summary


def describe_node(diagram: DiagramDocument, node_id: str) -> str:
    """Generate an accessible plain-language description of a node and its direct relationships."""
    node_by_id = {n.id: n for n in diagram.nodes}
    node = node_by_id.get(node_id)
    if node is None:
        raise KeyError(f"Node '{node_id}' was not found in diagram '{diagram.id}'.")

    if diagram.domain == "physics_circuit":
        neighbors = []
        for edge in diagram.edges:
            if edge.source == node_id and edge.target in node_by_id:
                neighbors.append(node_by_id[edge.target].label)
            elif edge.target == node_id and edge.source in node_by_id:
                neighbors.append(node_by_id[edge.source].label)

        state = evaluate_circuit_state(diagram)
        state_text = ""
        if node.kind == "switch" and node.id in state.switch_states:
            state_text = f" Current state: {state.switch_states[node.id]}."
        elif node.kind == "bulb" and node.id in state.bulb_states:
            state_text = f" Current state: {state.bulb_states[node.id]}."

        conn_text = (
            f" Connected by wire to: {', '.join(neighbors)}."
            if neighbors
            else " No wire connections."
        )
        return f"{node.label} ({node.kind}). {node.description}{state_text}{conn_text}"

    if diagram.domain == "biology_food_web":
        rels = get_organism_relations(diagram, node_id)
        incoming = [src.label for _, src in rels.receives_energy_from]
        outgoing = [tgt.label for _, tgt in rels.provides_energy_to]

        in_text = (
            f" Receives energy from: {', '.join(incoming)}."
            if incoming
            else " Receives energy from no other organism in this diagram."
        )
        out_text = (
            f" Provides energy to: {', '.join(outgoing)}."
            if outgoing
            else " Provides energy to no other organism in this diagram."
        )
        return f"{node.label} (organism). {node.description}{in_text}{out_text}"

    return f"{node.label} ({node.kind}). {node.description}"
