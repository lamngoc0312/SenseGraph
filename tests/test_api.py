"""Integration tests for SenseGraph Phase 1 FastAPI REST endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import Settings


def _make_client(settings: Settings | None = None) -> TestClient:
    return TestClient(create_app(settings=settings))


def test_health_endpoint_default_and_configured_without_leaking_key() -> None:
    with _make_client(Settings(ai_provider="none", gemini_api_key="")) as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {
            "status": "ok",
            "ai_configured": False,
            "supported_domains": ["physics_circuit", "biology_food_web"],
        }

    secret_key = "SUPER_SECRET_DO_NOT_EXPOSE"
    with _make_client(
        Settings(ai_provider="gemini", gemini_api_key=secret_key)
    ) as configured_client:
        resp_cfg = configured_client.get("/api/health")
        assert resp_cfg.status_code == 200
        assert resp_cfg.json()["ai_configured"] is True
        assert secret_key not in resp_cfg.text


def test_examples_list_and_detail_endpoints() -> None:
    with _make_client() as client:
        list_resp = client.get("/api/examples")
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) == 2
        assert {item["id"] for item in items} == {"physics_series", "biology_food_web"}
        assert all(
            item["source_label"] == "Pre-annotated demo — no AI used" for item in items
        )

        for example_id in ("physics_series", "biology_food_web"):
            detail_resp = client.get(f"/api/examples/{example_id}")
            assert detail_resp.status_code == 200
            body = detail_resp.json()
            assert body["id"] == example_id
            assert body["source"]["mode"] == "fixture"
            assert body["review_status"] == "confirmed"

        missing_resp = client.get("/api/examples/does_not_exist")
        assert missing_resp.status_code == 404
        assert missing_resp.json()["error"]["code"] == "NOT_FOUND"


def test_validate_endpoint_distinguishes_structural_and_simulation_readiness() -> None:
    with _make_client() as client:
        physics_doc = client.get("/api/examples/physics_series").json()

        ok_resp = client.post("/api/validate", json=physics_doc)
        assert ok_resp.status_code == 200
        assert ok_resp.json() == {
            "valid": True,
            "simulation_ready": True,
            "warnings": [],
            "errors": [],
        }

        # Structurally valid nodes/edges, but missing a wire breaks series ring.
        broken_ring = dict(physics_doc)
        broken_ring["edges"] = physics_doc["edges"][:-1]
        ring_resp = client.post("/api/validate", json=broken_ring)
        assert ring_resp.status_code == 200
        ring_body = ring_resp.json()
        assert ring_body["valid"] is True
        assert ring_body["simulation_ready"] is False
        assert len(ring_body["errors"]) >= 1

        # Malformed schema returns valid=False without crashing.
        bad_resp = client.post("/api/validate", json={"domain": "unknown"})
        assert bad_resp.status_code == 200
        assert bad_resp.json()["valid"] is False
        assert bad_resp.json()["simulation_ready"] is False


def test_confirm_endpoint_confirms_valid_and_rejects_invalid() -> None:
    with _make_client() as client:
        physics_doc = client.get("/api/examples/physics_series").json()
        physics_doc["review_status"] = "unreviewed"

        confirm_resp = client.post("/api/confirm", json=physics_doc)
        assert confirm_resp.status_code == 200
        confirmed = confirm_resp.json()
        assert confirmed["review_status"] == "confirmed"
        assert confirmed["domain_model"]["loop_wired"] is True

        # Broken topology cannot be confirmed.
        invalid_doc = dict(physics_doc)
        invalid_doc["edges"] = physics_doc["edges"][:-1]
        fail_resp = client.post("/api/confirm", json=invalid_doc)
        assert fail_resp.status_code == 422
        assert fail_resp.json()["error"]["code"] == "CONFIRMATION_FAILED"


def test_simulate_physics_and_biology_stateless_flow() -> None:
    with _make_client() as client:
        # Physics toggle open -> closed -> open
        physics_doc = client.get("/api/examples/physics_series").json()
        sim_close = client.post(
            "/api/simulate",
            json={
                "diagram": physics_doc,
                "action": {"type": "toggle_switch", "target_id": "switch_1"},
            },
        )
        assert sim_close.status_code == 200
        close_body = sim_close.json()
        assert close_body["event"] == "switch_closed"
        assert (
            close_body["updated_diagram"]["domain_model"]["switch_states"]["switch_1"]
            == "closed"
        )

        # Server remains stateless: original fixture is still open.
        refetched = client.get("/api/examples/physics_series").json()
        assert refetched["domain_model"]["switch_states"]["switch_1"] == "open"

        # Biology remove_organism
        bio_doc = client.get("/api/examples/biology_food_web").json()
        sim_remove = client.post(
            "/api/simulate",
            json={
                "diagram": bio_doc,
                "action": {"type": "remove_organism", "target_id": "rabbit"},
            },
        )
        assert sim_remove.status_code == 200
        rem_body = sim_remove.json()
        assert rem_body["event"] == "organism_removed"
        assert len(rem_body["updated_diagram"]["nodes"]) == 4
        assert len(rem_body["updated_diagram"]["edges"]) == 2


def test_simulate_error_handling() -> None:
    with _make_client() as client:
        physics_doc = client.get("/api/examples/physics_series").json()

        # Unreviewed -> 403
        unreviewed = dict(physics_doc)
        unreviewed["review_status"] = "unreviewed"
        resp_403 = client.post(
            "/api/simulate",
            json={
                "diagram": unreviewed,
                "action": {"type": "toggle_switch", "target_id": "switch_1"},
            },
        )
        assert resp_403.status_code == 403
        assert resp_403.json()["error"]["code"] == "UNREVIEWED_DIAGRAM"

        # Unknown action -> 400
        resp_bad_action = client.post(
            "/api/simulate",
            json={
                "diagram": physics_doc,
                "action": {"type": "eval_code", "target_id": "switch_1"},
            },
        )
        assert resp_bad_action.status_code == 400
        assert resp_bad_action.json()["error"]["code"] == "INVALID_ACTION"

        # Unknown target -> 400
        resp_bad_target = client.post(
            "/api/simulate",
            json={
                "diagram": physics_doc,
                "action": {"type": "toggle_switch", "target_id": "switch_999"},
            },
        )
        assert resp_bad_target.status_code == 400
        assert resp_bad_target.json()["error"]["code"] == "UNKNOWN_TARGET"
