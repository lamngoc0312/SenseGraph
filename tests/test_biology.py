"""Unit tests for the deterministic Biology directed food-web engine."""

from __future__ import annotations

import copy
import json

import pytest

from app.domains import DomainSimulationError
from app.domains.biology import (
    get_energy_paths,
    get_organism_relations,
    remove_organism,
    validate_food_web,
)
from app.models import DiagramDocument
from app.services.description import describe_node
from app.settings import FIXTURES_DIR


def _load_biology_fixture() -> DiagramDocument:
    raw = json.loads((FIXTURES_DIR / "biology_food_web.json").read_text(encoding="utf-8"))
    return DiagramDocument.model_validate(raw)


def test_biology_fixture_validates_and_exposes_directed_relations() -> None:
    doc = _load_biology_fixture()
    validation = validate_food_web(doc)
    assert validation.valid_semantics is True
    assert validation.simulation_ready is True
    assert validation.errors == []

    rabbit_rels = get_organism_relations(doc, "rabbit")
    assert [n.id for _, n in rabbit_rels.receives_energy_from] == ["grass"]
    assert [n.id for _, n in rabbit_rels.provides_energy_to] == ["fox"]

    grass_rels = get_organism_relations(doc, "grass")
    assert grass_rels.receives_energy_from == []
    assert [n.id for _, n in grass_rels.provides_energy_to] == ["rabbit", "mouse"]

    paths = get_energy_paths(doc, "grass")
    assert paths == [["grass", "rabbit", "fox"], ["grass", "mouse", "owl"]]
    assert get_energy_paths(doc, "fox") == []


def test_remove_rabbit_removes_exact_incident_edges_and_preserves_original() -> None:
    original = _load_biology_fixture()
    snapshot = copy.deepcopy(original.model_dump())

    resp = remove_organism(original, "rabbit")
    assert original.model_dump() == snapshot  # strict immutability

    assert resp.event == "organism_removed"
    remaining_node_ids = [n.id for n in resp.updated_diagram.nodes]
    assert "rabbit" not in remaining_node_ids
    assert remaining_node_ids == ["grass", "mouse", "fox", "owl"]

    remaining_pairs = [(e.source, e.target) for e in resp.updated_diagram.edges]
    assert remaining_pairs == [("grass", "mouse"), ("mouse", "owl")]

    assert "Removed organism: Rabbit" in resp.changes
    assert "Removed relationship: Grass -> Rabbit" in resp.changes
    assert "Removed relationship: Rabbit -> Fox" in resp.changes
    assert "does not predict population changes or extinction" in resp.announcement.lower()


def test_remove_isolated_organism_reports_zero_removed_edges() -> None:
    doc = _load_biology_fixture()
    after_rabbit = remove_organism(doc, "rabbit").updated_diagram
    # Fox is now isolated (no incident edges).
    after_fox = remove_organism(after_rabbit, "fox")
    assert "No feeding relationships were connected to Fox" in after_fox.announcement
    assert len(after_fox.updated_diagram.edges) == 2


def test_rejects_removing_last_remaining_organism() -> None:
    doc = _load_biology_fixture()
    doc.nodes = [doc.nodes[0]]
    doc.edges = []

    with pytest.raises(DomainSimulationError) as exc_info:
        remove_organism(doc, "grass")
    assert exc_info.value.status_code == 400


def test_rejects_duplicate_feeding_edge_and_wire_relation() -> None:
    doc = _load_biology_fixture()
    dup = doc.edges[0].model_copy(update={"id": "feeding_dup"})
    doc.edges.append(dup)
    result = validate_food_web(doc)
    assert result.simulation_ready is False
    assert any("Duplicate feeding relationship" in err for err in result.errors)

    doc_wire = _load_biology_fixture()
    doc_wire.edges[0].relation = "wire"
    wire_result = validate_food_web(doc_wire)
    assert wire_result.simulation_ready is False
    assert any("expected 'energy_to'" in err for err in wire_result.errors)


def test_rejects_unreviewed_and_unknown_organism() -> None:
    doc = _load_biology_fixture()
    doc.review_status = "unreviewed"
    with pytest.raises(DomainSimulationError) as exc_unreviewed:
        remove_organism(doc, "rabbit")
    assert exc_unreviewed.value.status_code == 403

    confirmed_doc = _load_biology_fixture()
    with pytest.raises(DomainSimulationError) as exc_unknown:
        remove_organism(confirmed_doc, "wolf")
    assert exc_unknown.value.status_code == 400


def test_describe_node_for_organism() -> None:
    doc = _load_biology_fixture()
    text = describe_node(doc, "rabbit")
    assert "Rabbit" in text
    assert "Receives energy from: Grass." in text
    assert "Provides energy to: Fox." in text
