"""Automated tests for Phase 5 Guided Learning Lab (Predict -> Experiment -> Explain)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import DiagramDocument
from app.services.learning import evaluate_challenge, generate_challenges
from app.settings import FIXTURES_DIR


def _load_fixture(name: str) -> DiagramDocument:
    raw = json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))
    return DiagramDocument.model_validate(raw)


def test_physics_learning_challenges_and_toggle_evaluation() -> None:
    doc = _load_fixture("physics_series.json")
    challenge_set = generate_challenges(doc)

    assert challenge_set.available is True
    assert len(challenge_set.challenges) == 3
    templates = [c.template for c in challenge_set.challenges]
    assert templates == [
        "physics_toggle_switch",
        "physics_loop_neighbors",
        "physics_reverse_toggle",
    ]

    # Correct prediction: closing Switch S1 turns Bulb L1 ON.
    toggle_id = challenge_set.challenges[0].id
    correct_res = evaluate_challenge(doc, toggle_id, ["on"])
    assert correct_res.correct is True
    assert correct_res.expected_option_ids == ["on"]
    assert correct_res.simulation_result is not None
    assert (
        correct_res.simulation_result.updated_diagram.domain_model.switch_states["switch_1"]
        == "closed"
    )
    assert "loop_wired=true" in correct_res.explanation
    assert "voltage" not in correct_res.explanation.lower()

    # Incorrect prediction receives constructive comparison.
    wrong_res = evaluate_challenge(doc, toggle_id, ["off"])
    assert wrong_res.correct is False
    assert "not quite" in wrong_res.summary.lower()


def test_physics_neighbors_and_reverse_toggle_challenges() -> None:
    doc = _load_fixture("physics_series.json")
    challenge_set = generate_challenges(doc)

    neighbors_id = challenge_set.challenges[1].id
    res_neighbors = evaluate_challenge(doc, neighbors_id, ["battery_1", "bulb_1"])
    assert res_neighbors.correct is True
    assert res_neighbors.simulation_result is None

    reverse_id = challenge_set.challenges[2].id
    res_reverse = evaluate_challenge(doc, reverse_id, ["off"])
    assert res_reverse.correct is True
    assert res_reverse.expected_option_ids == ["off"]


def test_biology_learning_challenges_and_removal_evaluation() -> None:
    doc = _load_fixture("biology_food_web.json")
    challenge_set = generate_challenges(doc)

    assert challenge_set.available is True
    assert len(challenge_set.challenges) == 3
    templates = [c.template for c in challenge_set.challenges]
    assert templates == [
        "biology_remove_impact",
        "biology_direct_neighbors",
        "biology_energy_path",
    ]

    # Removing Rabbit removes feeding_1 (grass->rabbit) and feeding_3 (rabbit->fox).
    remove_id = challenge_set.challenges[0].id
    assert remove_id == "biology_remove:rabbit"

    res_ok = evaluate_challenge(doc, remove_id, ["feeding_1", "feeding_3"])
    assert res_ok.correct is True
    assert res_ok.simulation_result is not None
    assert len(res_ok.simulation_result.updated_diagram.nodes) == 4
    assert len(res_ok.simulation_result.updated_diagram.edges) == 2
    assert "does not predict extinction or population changes" in res_ok.explanation.lower()

    # Partial prediction reports exact missed relationship.
    res_partial = evaluate_challenge(doc, remove_id, ["feeding_1"])
    assert res_partial.correct is False
    assert "missed" in res_partial.summary.lower()


def test_biology_direct_neighbors_and_downstream_paths() -> None:
    doc = _load_fixture("biology_food_web.json")
    challenge_set = generate_challenges(doc)

    neighbors_id = challenge_set.challenges[1].id
    res_neighbors = evaluate_challenge(doc, neighbors_id, ["rabbit", "mouse"])
    assert res_neighbors.correct is True

    downstream_id = challenge_set.challenges[2].id
    res_downstream = evaluate_challenge(
        doc, downstream_id, ["rabbit", "mouse", "fox", "owl"]
    )
    assert res_downstream.correct is True
    assert any("Grass -> Rabbit -> Fox" in line for line in res_downstream.evidence)


def test_isolated_food_web_returns_honest_unavailable_state() -> None:
    doc = _load_fixture("biology_food_web.json")
    doc.edges = []
    challenge_set = generate_challenges(doc)
    assert challenge_set.available is False
    assert challenge_set.challenges == []
    assert challenge_set.unavailable_reason is not None


def test_learning_api_endpoints_and_error_guards() -> None:
    app = create_app()
    with TestClient(app) as client:
        phys = client.get("/api/examples/physics_series").json()

        ch_resp = client.post("/api/learning/challenges", json=phys)
        assert ch_resp.status_code == 200
        challenges = ch_resp.json()["challenges"]
        assert len(challenges) == 3

        eval_resp = client.post(
            "/api/learning/evaluate",
            json={
                "diagram": phys,
                "challenge_id": challenges[0]["id"],
                "selected_option_ids": ["on"],
            },
        )
        assert eval_resp.status_code == 200
        assert eval_resp.json()["correct"] is True

        # Unreviewed diagram rejected with 403.
        unreviewed = dict(phys)
        unreviewed["review_status"] = "unreviewed"
        resp_403 = client.post("/api/learning/challenges", json=unreviewed)
        assert resp_403.status_code == 403

        # Unknown challenge ID rejected with 400.
        resp_400 = client.post(
            "/api/learning/evaluate",
            json={
                "diagram": phys,
                "challenge_id": "unknown_template:switch_1",
                "selected_option_ids": ["on"],
            },
        )
        assert resp_400.status_code == 400

        # Frontend includes mode switcher and Learning Lab controls.
        html = client.get("/").text
        assert 'id="mode-explore-btn"' in html
        assert 'id="mode-lab-btn"' in html
        assert 'id="learning-lab-panel"' in html
        assert 'id="lab-prediction-form"' in html

        js = client.get("/static/app.js").text
        assert "/api/learning/challenges" in js
        assert "/api/learning/evaluate" in js
