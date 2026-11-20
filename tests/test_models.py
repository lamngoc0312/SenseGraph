"""Tests for DiagramDocument JSON schema alignment, Pydantic models, and validators."""

from __future__ import annotations

import copy
import json

import jsonschema
import pytest
from pydantic import ValidationError

from app.models import DiagramDocument
from app.services.fixtures import BUNDLED_FIXTURE_FILES, FixtureRepository
from app.services.validators import validate_diagram, validate_raw_diagram
from app.settings import DIAGRAM_SCHEMA_PATH, FIXTURES_DIR


def _load_fixture_json(filename: str) -> dict:
    return json.loads((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _load_json_schema() -> dict:
    return json.loads(DIAGRAM_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("filename", BUNDLED_FIXTURE_FILES)
def test_bundled_fixtures_match_json_schema_and_validators(filename: str) -> None:
    schema = _load_json_schema()
    raw = _load_fixture_json(filename)

    jsonschema.validate(instance=raw, schema=schema)
    doc = DiagramDocument.model_validate(raw)
    result = validate_diagram(doc)

    assert result.valid is True
    assert result.simulation_ready is True
    assert result.errors == []


def test_fixture_repository_returns_deep_copies() -> None:
    repo = FixtureRepository()
    examples = repo.list_examples()
    assert [e.id for e in examples] == ["physics_series", "biology_food_web"]

    first = repo.get_example("physics_series")
    second = repo.get_example("physics_series")
    assert first is not None and second is not None
    first.title = "Mutated Title"
    assert second.title == "Basic Series Circuit"


def test_rejects_duplicate_node_ids() -> None:
    raw = _load_fixture_json("biology_food_web.json")
    raw["nodes"].append(copy.deepcopy(raw["nodes"][0]))

    doc, result = validate_raw_diagram(raw)
    assert doc is not None
    assert result.valid is False
    assert result.simulation_ready is False
    assert any("Duplicate node ID" in err for err in result.errors)


def test_rejects_duplicate_edge_ids() -> None:
    raw = _load_fixture_json("biology_food_web.json")
    dup_edge = copy.deepcopy(raw["edges"][0])
    dup_edge["source"] = "fox"
    dup_edge["target"] = "owl"
    raw["edges"].append(dup_edge)

    doc, result = validate_raw_diagram(raw)
    assert doc is not None
    assert result.valid is False
    assert result.simulation_ready is False
    assert any("Duplicate edge ID" in err for err in result.errors)


def test_rejects_edge_with_unknown_endpoints() -> None:
    raw = _load_fixture_json("biology_food_web.json")
    raw["edges"][0]["target"] = "nonexistent_species"

    doc, result = validate_raw_diagram(raw)
    assert doc is not None
    assert result.valid is False
    assert result.simulation_ready is False
    assert any("unknown target node" in err for err in result.errors)


def test_rejects_bad_domain_and_mismatched_domain_model() -> None:
    raw = _load_fixture_json("physics_series.json")
    raw["domain"] = "chemistry_molecule"
    with pytest.raises(ValidationError):
        DiagramDocument.model_validate(raw)

    raw_mismatch = _load_fixture_json("physics_series.json")
    raw_mismatch["domain_model"] = {
        "kind": "food_web",
        "arrow_convention": "food_to_consumer",
    }
    with pytest.raises(ValidationError):
        DiagramDocument.model_validate(raw_mismatch)


def test_rejects_ai_source_without_provider() -> None:
    raw = _load_fixture_json("physics_series.json")
    raw["source"] = {"mode": "ai", "filename": "upload.png", "provider": None}
    with pytest.raises(ValidationError):
        DiagramDocument.model_validate(raw)


def test_rejects_extra_fields_on_document() -> None:
    raw = _load_fixture_json("physics_series.json")
    raw["unexpected_field"] = "not allowed"
    with pytest.raises(ValidationError):
        DiagramDocument.model_validate(raw)


def test_rejects_wrong_node_kind_and_edge_relation_for_domain() -> None:
    raw_bio = _load_fixture_json("biology_food_web.json")
    raw_bio["edges"][0]["relation"] = "wire"
    _, bio_result = validate_raw_diagram(raw_bio)
    assert bio_result.valid is False
    assert bio_result.simulation_ready is False

    raw_phys = _load_fixture_json("physics_series.json")
    raw_phys["nodes"][0]["kind"] = "organism"
    _, phys_result = validate_raw_diagram(raw_phys)
    assert phys_result.valid is False
    assert phys_result.simulation_ready is False
