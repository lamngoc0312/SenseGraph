"""Automated tests for Phase 10 Chemistry Molecular Structure Explorer."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.domains import DomainSimulationError
from app.domains.chemistry import (
    find_shortest_bond_path,
    get_atom_counts,
    get_atom_neighbors,
    parse_smiles_to_molecule,
    validate_molecule,
)
from app.main import create_app
from app.models import DiagramDocument
from app.services.learning import evaluate_challenge, generate_challenges
from app.settings import FIXTURES_DIR


def _load_chem_fixture() -> DiagramDocument:
    raw = json.loads((FIXTURES_DIR / "chemistry_molecule.json").read_text(encoding="utf-8"))
    return DiagramDocument.model_validate(raw)


def test_chemistry_fixture_validates_counts_neighbors_and_paths() -> None:
    doc = _load_chem_fixture()
    assert validate_molecule(doc).simulation_ready is True
    assert get_atom_counts(doc) == {"C": 1, "H": 2, "O": 1}

    c_neighbors = get_atom_neighbors(doc, "C_1")
    assert len(c_neighbors) == 3
    assert {n.id: order for _, n, order in c_neighbors} == {
        "O_1": 2,
        "H_1": 1,
        "H_2": 1,
    }
    assert find_shortest_bond_path(doc, "H_1", "O_1") == ["H_1", "C_1", "O_1"]


def test_smiles_parser_builds_water_co2_and_ethanol_with_exact_valences() -> None:
    water = parse_smiles_to_molecule("O", title="Water")
    assert water.domain_model.formula == "H2O"
    assert get_atom_counts(water) == {"H": 2, "O": 1}

    co2 = parse_smiles_to_molecule("O=C=O", title="Carbon Dioxide")
    assert co2.domain_model.formula == "CO2"
    assert get_atom_counts(co2) == {"C": 1, "O": 2}

    ethanol = parse_smiles_to_molecule("CCO", title="Ethanol")
    assert ethanol.domain_model.formula == "C2H6O"
    assert get_atom_counts(ethanol) == {"C": 2, "H": 6, "O": 1}


def test_rejects_aromaticity_stereochemistry_invalid_valence_and_duplicate_bonds() -> None:
    # Aromatic benzene rejected (outside beginner scope)
    with pytest.raises(DomainSimulationError) as exc_arom:
        parse_smiles_to_molecule("c1ccccc1")
    assert exc_arom.value.code == "UNSUPPORTED_CHEMISTRY"

    # Stereochemistry rejected
    with pytest.raises(DomainSimulationError) as exc_stereo:
        parse_smiles_to_molecule("C/C=C/C")
    assert exc_stereo.value.code == "UNSUPPORTED_CHEMISTRY"

    # Pentavalent carbon (C with triple + double bond = 5) rejected
    with pytest.raises(DomainSimulationError) as exc_val:
        parse_smiles_to_molecule("C#C=C=C")
    assert exc_val.value.code == "INVALID_VALENCE"

    # Duplicate undirected bond rejected in graph validation
    doc_dup = _load_chem_fixture()
    doc_dup.edges.append(doc_dup.edges[0].model_copy(update={"id": "bond_dup"}))
    res_dup = validate_molecule(doc_dup)
    assert res_dup.simulation_ready is False
    assert any("duplicate bond" in err.lower() for err in res_dup.errors)


def test_chemistry_guided_learning_challenges() -> None:
    doc = _load_chem_fixture()
    ch_set = generate_challenges(doc)
    assert ch_set.available is True
    assert len(ch_set.challenges) == 2

    res_count = evaluate_challenge(doc, ch_set.challenges[0].id, ["2"])
    assert res_count.correct is True
    assert "does not infer lab safety" in res_count.explanation.lower()

    res_neighbors = evaluate_challenge(
        doc, ch_set.challenges[1].id, ["O_1", "H_1", "H_2"]
    )
    assert res_neighbors.correct is True


def test_chemistry_api_and_frontend_controls() -> None:
    app = create_app()
    with TestClient(app) as client:
        doc = client.get("/api/examples/chemistry_molecule").json()
        assert doc["domain"] == "chemistry_molecule"

        state_resp = client.post("/api/state", json=doc)
        assert state_resp.status_code == 200
        assert state_resp.json()["formula"] == "CH2O"
        assert state_resp.json()["atom_counts"] == {"C": 1, "H": 2, "O": 1}

        smiles_resp = client.post(
            "/api/chemistry/parse-smiles",
            json={"smiles": "O=C=O", "title": "Carbon Dioxide"},
        )
        assert smiles_resp.status_code == 200
        assert smiles_resp.json()["domain_model"]["formula"] == "CO2"

        bad_resp = client.post(
            "/api/chemistry/parse-smiles",
            json={"smiles": "c1ccccc1"},
        )
        assert bad_resp.status_code == 422
        assert bad_resp.json()["error"]["code"] == "UNSUPPORTED_CHEMISTRY"

        html = client.get("/").text
        assert 'id="switch-chem-btn"' in html
        assert 'id="chem-controls-panel"' in html
        assert 'id="chem-smiles-input"' in html
