"""Structural and domain semantic validation for DiagramDocument instances."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.domains.biology import validate_food_web
from app.domains.physics import validate_series_circuit
from app.models import DiagramDocument, ValidationResponse


def _format_pydantic_errors(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", ()))
        msg = err.get("msg", "Invalid value")
        messages.append(f"{loc}: {msg}" if loc else msg)
    return messages


def validate_diagram(diagram: DiagramDocument) -> ValidationResponse:
    """Validate structural graph integrity and domain simulation readiness separately.

    - `valid`: schema and graph structural checks pass (unique IDs, valid endpoints,
      no self-loops, domain-appropriate node kinds and edge relations).
    - `simulation_ready`: diagram also satisfies all P0 domain invariants required to
      run deterministic simulation actions safely.
    """
    structural_errors: list[str] = []
    warnings: list[str] = list(diagram.warnings)

    seen_node_ids: set[str] = set()
    for node in diagram.nodes:
        if node.id in seen_node_ids:
            structural_errors.append(f"Duplicate node ID '{node.id}'.")
        seen_node_ids.add(node.id)

    seen_edge_ids: set[str] = set()
    for edge in diagram.edges:
        if edge.id in seen_edge_ids:
            structural_errors.append(f"Duplicate edge ID '{edge.id}'.")
        seen_edge_ids.add(edge.id)
        if edge.source not in seen_node_ids:
            structural_errors.append(
                f"Edge '{edge.id}' references unknown source node '{edge.source}'."
            )
        if edge.target not in seen_node_ids:
            structural_errors.append(
                f"Edge '{edge.id}' references unknown target node '{edge.target}'."
            )
        if edge.source == edge.target:
            structural_errors.append(
                f"Edge '{edge.id}' cannot connect node '{edge.source}' to itself."
            )

    if diagram.domain == "physics_circuit":
        for node in diagram.nodes:
            if node.kind not in {"battery", "switch", "bulb"}:
                structural_errors.append(
                    f"Node '{node.id}' has kind '{node.kind}', not allowed in physics_circuit."
                )
        for edge in diagram.edges:
            if edge.relation != "wire":
                structural_errors.append(
                    f"Edge '{edge.id}' has relation '{edge.relation}', expected 'wire'."
                )
    elif diagram.domain == "biology_food_web":
        for node in diagram.nodes:
            if node.kind != "organism":
                structural_errors.append(
                    f"Node '{node.id}' has kind '{node.kind}', expected 'organism'."
                )
        for edge in diagram.edges:
            if edge.relation != "energy_to":
                structural_errors.append(
                    f"Edge '{edge.id}' has relation '{edge.relation}', expected 'energy_to'."
                )

    if structural_errors:
        return ValidationResponse(
            valid=False,
            simulation_ready=False,
            warnings=warnings,
            errors=structural_errors,
        )

    if diagram.domain == "physics_circuit":
        physics_result = validate_series_circuit(diagram)
        warnings.extend(physics_result.warnings)
        return ValidationResponse(
            valid=True,
            simulation_ready=physics_result.simulation_ready,
            warnings=warnings,
            errors=physics_result.errors,
        )

    biology_result = validate_food_web(diagram)
    warnings.extend(biology_result.warnings)
    return ValidationResponse(
        valid=True,
        simulation_ready=biology_result.simulation_ready,
        warnings=warnings,
        errors=biology_result.errors,
    )


def validate_raw_diagram(payload: Any) -> tuple[DiagramDocument | None, ValidationResponse]:
    """Parse raw JSON dict into DiagramDocument and run structural + domain validation."""
    try:
        diagram = DiagramDocument.model_validate(payload)
    except ValidationError as exc:
        return None, ValidationResponse(
            valid=False,
            simulation_ready=False,
            warnings=[],
            errors=_format_pydantic_errors(exc),
        )

    return diagram, validate_diagram(diagram)
