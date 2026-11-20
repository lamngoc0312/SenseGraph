"""Unit tests for the deterministic Physics single-loop series circuit engine."""

from __future__ import annotations

import copy
import json

import pytest

from app.domains import DomainSimulationError
from app.domains.physics import (
    evaluate_circuit_state,
    toggle_switch,
    validate_series_circuit,
)
from app.models import DiagramDocument
from app.services.description import describe_node
from app.settings import FIXTURES_DIR


def _load_physics_fixture() -> DiagramDocument:
    raw = json.loads((FIXTURES_DIR / "physics_series.json").read_text(encoding="utf-8"))
    return DiagramDocument.model_validate(raw)


def _make_two_bulb_circuit() -> DiagramDocument:
    raw = {
        "schema_version": "1.0",
        "id": "physics_two_bulbs",
        "title": "Two-Bulb Series Circuit",
        "domain": "physics_circuit",
        "summary": "A series circuit with Battery B1, Switch S1, Bulb L1, and Bulb L2.",
        "source": {"mode": "fixture", "filename": "two_bulbs.png", "provider": None},
        "review_status": "confirmed",
        "nodes": [
            {
                "id": "battery_1",
                "kind": "battery",
                "label": "Battery B1",
                "description": "Power source.",
                "attributes": {},
            },
            {
                "id": "switch_1",
                "kind": "switch",
                "label": "Switch S1",
                "description": "Series switch.",
                "attributes": {},
            },
            {
                "id": "bulb_1",
                "kind": "bulb",
                "label": "Bulb L1",
                "description": "First bulb.",
                "attributes": {},
            },
            {
                "id": "bulb_2",
                "kind": "bulb",
                "label": "Bulb L2",
                "description": "Second bulb.",
                "attributes": {},
            },
        ],
        "edges": [
            {
                "id": "wire_1",
                "source": "battery_1",
                "target": "switch_1",
                "relation": "wire",
                "description": "Battery B1 to Switch S1.",
            },
            {
                "id": "wire_2",
                "source": "switch_1",
                "target": "bulb_1",
                "relation": "wire",
                "description": "Switch S1 to Bulb L1.",
            },
            {
                "id": "wire_3",
                "source": "bulb_1",
                "target": "bulb_2",
                "relation": "wire",
                "description": "Bulb L1 to Bulb L2.",
            },
            {
                "id": "wire_4",
                "source": "bulb_2",
                "target": "battery_1",
                "relation": "wire",
                "description": "Bulb L2 to Battery B1.",
            },
        ],
        "domain_model": {
            "kind": "series_circuit",
            "sequence": ["battery_1", "switch_1", "bulb_1", "bulb_2"],
            "switch_states": {"switch_1": "open"},
            "loop_wired": True,
        },
        "warnings": [],
    }
    return DiagramDocument.model_validate(raw)


def test_default_fixture_switch_open_means_bulb_off() -> None:
    doc = _load_physics_fixture()
    validation = validate_series_circuit(doc)
    assert validation.simulation_ready is True
    assert validation.derived_loop_wired is True

    state = evaluate_circuit_state(doc)
    assert state.loop_wired is True
    assert state.all_switches_closed is False
    assert state.bulbs_on is False
    assert state.bulb_states == {"bulb_1": "off"}


def test_toggle_switch_cycles_bulb_on_and_off_without_mutating_input() -> None:
    original = _load_physics_fixture()
    snapshot = copy.deepcopy(original.model_dump())

    closed_resp = toggle_switch(original, "switch_1")
    assert original.model_dump() == snapshot  # strict immutability
    assert closed_resp.event == "switch_closed"
    assert closed_resp.updated_diagram.domain_model.switch_states["switch_1"] == "closed"
    assert evaluate_circuit_state(closed_resp.updated_diagram).bulb_states == {"bulb_1": "on"}
    assert "Bulb L1: off -> on" in closed_resp.changes
    assert "now on" in closed_resp.announcement.lower()

    reopened_resp = toggle_switch(closed_resp.updated_diagram, "switch_1")
    assert reopened_resp.event == "switch_opened"
    assert reopened_resp.updated_diagram.domain_model.switch_states["switch_1"] == "open"
    assert evaluate_circuit_state(reopened_resp.updated_diagram).bulb_states == {"bulb_1": "off"}
    assert "Bulb L1: on -> off" in reopened_resp.changes
    assert "now off" in reopened_resp.announcement.lower()


def test_two_bulbs_in_series_both_turn_on_and_off_together() -> None:
    doc = _make_two_bulb_circuit()
    assert validate_series_circuit(doc).simulation_ready is True
    assert evaluate_circuit_state(doc).bulb_states == {"bulb_1": "off", "bulb_2": "off"}

    closed = toggle_switch(doc, "switch_1")
    assert evaluate_circuit_state(closed.updated_diagram).bulb_states == {
        "bulb_1": "on",
        "bulb_2": "on",
    }
    assert "Bulb L1: off -> on" in closed.changes
    assert "Bulb L2: off -> on" in closed.changes


def test_rejects_missing_wire_even_if_input_claims_loop_wired() -> None:
    doc = _load_physics_fixture()
    doc.edges.pop()  # remove return wire

    result = validate_series_circuit(doc)
    assert result.derived_loop_wired is False
    assert result.simulation_ready is False
    assert any("missing wire" in err.lower() for err in result.errors)
    assert any("disagreed" in warn.lower() for warn in result.warnings)

    with pytest.raises(DomainSimulationError) as exc_info:
        toggle_switch(doc, "switch_1")
    assert exc_info.value.status_code == 422


def test_rejects_extra_non_series_branch_wire() -> None:
    doc = _make_two_bulb_circuit()
    doc.edges.append(
        doc.edges[0].model_copy(
            update={
                "id": "wire_extra",
                "source": "battery_1",
                "target": "bulb_1",
                "description": "Extra parallel branch wire.",
            }
        )
    )

    result = validate_series_circuit(doc)
    assert result.derived_loop_wired is False
    assert result.simulation_ready is False
    assert any("extra wire" in err.lower() for err in result.errors)


def test_rejects_two_batteries() -> None:
    doc = _make_two_bulb_circuit()
    doc.nodes[3].kind = "battery"

    result = validate_series_circuit(doc)
    assert result.simulation_ready is False
    assert any("exactly 1 battery" in err for err in result.errors)


def test_rejects_unknown_switch_id_in_switch_states() -> None:
    doc = _load_physics_fixture()
    doc.domain_model.switch_states = {"wrong_switch": "open"}

    result = validate_series_circuit(doc)
    assert result.simulation_ready is False
    assert any("switch_states" in err for err in result.errors)


def test_rejects_dangling_node_missing_from_sequence() -> None:
    doc = _load_physics_fixture()
    doc.nodes.append(
        doc.nodes[2].model_copy(update={"id": "bulb_extra", "label": "Dangling Bulb"})
    )

    result = validate_series_circuit(doc)
    assert result.simulation_ready is False
    assert any("missing node" in err.lower() for err in result.errors)


def test_rejects_unreviewed_diagram_and_unknown_target() -> None:
    doc = _load_physics_fixture()
    doc.review_status = "unreviewed"
    with pytest.raises(DomainSimulationError) as exc_unreviewed:
        toggle_switch(doc, "switch_1")
    assert exc_unreviewed.value.status_code == 403

    confirmed_doc = _load_physics_fixture()
    with pytest.raises(DomainSimulationError) as exc_target:
        toggle_switch(confirmed_doc, "battery_1")
    assert exc_target.value.status_code == 400


def test_describe_node_includes_state_and_neighbors() -> None:
    doc = _load_physics_fixture()
    text = describe_node(doc, "switch_1")
    assert "Switch S1" in text
    assert "open" in text
    assert "Battery B1" in text
    assert "Bulb L1" in text
