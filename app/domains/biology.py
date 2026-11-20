"""Deterministic directed food-web relationship engine (Biology P0)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domains import DomainSimulationError
from app.models import DiagramDocument, Edge, FoodWebModel, Node, SimulationResponse


@dataclass(frozen=True)
class BiologyValidationResult:
    """Result of biology-specific semantic and graph validation."""

    valid_semantics: bool
    simulation_ready: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class OrganismRelations:
    """Direct incoming (food/prey) and outgoing (consumer/predator) relationships."""

    organism: Node
    receives_energy_from: list[tuple[Edge, Node]]
    provides_energy_to: list[tuple[Edge, Node]]


def validate_food_web(diagram: DiagramDocument) -> BiologyValidationResult:
    """Validate P0 directed food-web invariants (food/prey -> consumer/predator)."""
    errors: list[str] = []
    warnings: list[str] = []

    if diagram.domain != "biology_food_web":
        errors.append("Expected domain 'biology_food_web'.")
    if not isinstance(diagram.domain_model, FoodWebModel):
        errors.append("Expected domain_model.kind to be 'food_web'.")
        return BiologyValidationResult(
            valid_semantics=False,
            simulation_ready=False,
            errors=errors,
            warnings=warnings,
        )

    if diagram.domain_model.arrow_convention != "food_to_consumer":
        errors.append("arrow_convention must be 'food_to_consumer'.")

    node_by_id: dict[str, Node] = {}
    for node in diagram.nodes:
        if node.id in node_by_id:
            errors.append(f"Duplicate node ID '{node.id}' in food web.")
        node_by_id[node.id] = node
        if node.kind != "organism":
            errors.append(
                f"Node '{node.id}' has kind '{node.kind}', expected 'organism' in biology_food_web."
            )

    seen_directed_pairs: set[tuple[str, str]] = set()
    for edge in diagram.edges:
        if edge.relation != "energy_to":
            errors.append(
                f"Edge '{edge.id}' has relation '{edge.relation}', "
                "expected 'energy_to' in biology_food_web."
            )
        if edge.source not in node_by_id:
            errors.append(f"Edge '{edge.id}' references unknown source organism '{edge.source}'.")
        if edge.target not in node_by_id:
            errors.append(f"Edge '{edge.id}' references unknown target organism '{edge.target}'.")
        if edge.source == edge.target:
            errors.append(
                f"Edge '{edge.id}' cannot point organism '{edge.source}' to itself."
            )
        pair = (edge.source, edge.target)
        if pair in seen_directed_pairs:
            errors.append(
                f"Duplicate feeding relationship from '{edge.source}' to '{edge.target}'."
            )
        seen_directed_pairs.add(pair)

    if not errors and len(diagram.edges) == 0:
        warnings.append("This food web currently has no feeding relationships.")

    valid = len(errors) == 0
    return BiologyValidationResult(
        valid_semantics=valid,
        simulation_ready=valid,
        errors=errors,
        warnings=warnings,
    )


def get_organism_relations(diagram: DiagramDocument, organism_id: str) -> OrganismRelations:
    """Return direct incoming (food) and outgoing (consumer) relations for an organism."""
    node_by_id = {n.id: n for n in diagram.nodes}
    organism = node_by_id.get(organism_id)
    if organism is None or organism.kind != "organism":
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Organism '{organism_id}' was not found in this food web.",
            status_code=400,
        )

    incoming: list[tuple[Edge, Node]] = []
    outgoing: list[tuple[Edge, Node]] = []
    for edge in diagram.edges:
        if edge.target == organism_id and edge.source in node_by_id:
            incoming.append((edge, node_by_id[edge.source]))
        if edge.source == organism_id and edge.target in node_by_id:
            outgoing.append((edge, node_by_id[edge.target]))

    return OrganismRelations(
        organism=organism,
        receives_energy_from=incoming,
        provides_energy_to=outgoing,
    )


def get_energy_paths(
    diagram: DiagramDocument, start_id: str, max_depth: int = 10
) -> list[list[str]]:
    """Return maximal cycle-free directed energy paths starting from start_id."""
    node_by_id = {n.id: n for n in diagram.nodes}
    if start_id not in node_by_id:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Organism '{start_id}' was not found in this food web.",
            status_code=400,
        )

    adjacency: dict[str, list[str]] = {n.id: [] for n in diagram.nodes}
    for edge in diagram.edges:
        if edge.source in adjacency and edge.target in node_by_id:
            adjacency[edge.source].append(edge.target)

    paths: list[list[str]] = []

    def dfs(current: str, path: list[str]) -> None:
        next_nodes = [nxt for nxt in adjacency[current] if nxt not in path]
        if not next_nodes or len(path) >= max_depth:
            if len(path) >= 2:
                paths.append(list(path))
            return
        for nxt in next_nodes:
            path.append(nxt)
            dfs(nxt, path)
            path.pop()

    dfs(start_id, [start_id])
    return paths


def build_food_web_summary(diagram: DiagramDocument) -> str:
    """Generate a deterministic plain-language summary of confirmed food-web relationships."""
    node_by_id = {n.id: n for n in diagram.nodes}
    org_count = len(diagram.nodes)
    edge_count = len(diagram.edges)
    org_word = "organism" if org_count == 1 else "organisms"
    rel_word = "feeding relationship" if edge_count == 1 else "feeding relationships"

    if edge_count == 0:
        return (
            f"This food web contains {org_count} {org_word} and 0 feeding relationships. "
            "Arrows represent energy flow from food to consumer."
        )

    rel_phrases = [
        f"{node_by_id[e.source].label} to {node_by_id[e.target].label}"
        for e in diagram.edges
        if e.source in node_by_id and e.target in node_by_id
    ]
    return (
        f"This food web contains {org_count} {org_word} and {edge_count} {rel_word}: "
        f"{'; '.join(rel_phrases)}. Arrows indicate energy flow from food to consumer."
    )


def remove_organism(diagram: DiagramDocument, organism_id: str) -> SimulationResponse:
    """Remove an organism and all incident feeding edges without mutating the input diagram."""
    if diagram.domain != "biology_food_web" or not isinstance(
        diagram.domain_model, FoodWebModel
    ):
        raise DomainSimulationError(
            code="INVALID_ACTION",
            message="remove_organism is only supported for biology_food_web diagrams.",
            status_code=400,
        )

    if diagram.review_status != "confirmed":
        raise DomainSimulationError(
            code="UNREVIEWED_DIAGRAM",
            message="Diagram must be confirmed before running simulation actions.",
            status_code=403,
        )

    validation = validate_food_web(diagram)
    if not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_DIAGRAM",
            message="Food web structure is not valid for simulation.",
            status_code=422,
            details=validation.errors,
        )

    node_by_id = {n.id: n for n in diagram.nodes}
    target_node = node_by_id.get(organism_id)
    if target_node is None or target_node.kind != "organism":
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Organism '{organism_id}' was not found in this food web.",
            status_code=400,
        )

    if len(diagram.nodes) <= 1:
        raise DomainSimulationError(
            code="INVALID_ACTION",
            message="Cannot remove the last remaining organism in the diagram.",
            status_code=400,
        )

    updated = diagram.model_copy(deep=True)
    removed_edges = [
        e for e in updated.edges if organism_id in (e.source, e.target)
    ]
    removed_edge_ids = {e.id for e in removed_edges}

    updated.edges = [e for e in updated.edges if e.id not in removed_edge_ids]
    updated.nodes = [n for n in updated.nodes if n.id != organism_id]
    updated.summary = build_food_web_summary(updated)

    changes: list[str] = [f"Removed organism: {target_node.label}"]
    removed_descriptions: list[str] = []
    for edge in removed_edges:
        src_label = node_by_id[edge.source].label
        tgt_label = node_by_id[edge.target].label
        changes.append(f"Removed relationship: {src_label} -> {tgt_label}")
        removed_descriptions.append(f"{src_label} to {tgt_label}")

    remaining_count = len(updated.edges)
    rem_word = "relationship remains" if remaining_count == 1 else "relationships remain"

    if removed_edges:
        rel_count = len(removed_edges)
        rel_word = "relationship" if rel_count == 1 else "relationships"
        announcement = (
            f"{target_node.label} removed from this diagram. "
            f"Removed {rel_count} {rel_word}: {'; '.join(removed_descriptions)}. "
            f"{remaining_count} {rem_word}. "
            "This shows graph relationship changes only and does not predict population changes or extinction."
        )
    else:
        announcement = (
            f"{target_node.label} removed from this diagram. "
            f"No feeding relationships were connected to {target_node.label}. "
            f"{remaining_count} {rem_word}. "
            "This shows graph relationship changes only and does not predict population changes or extinction."
        )

    return SimulationResponse(
        updated_diagram=updated,
        event="organism_removed",
        announcement=announcement,
        changes=changes,
    )
