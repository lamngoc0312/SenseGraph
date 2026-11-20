"""Automated tests for Phase 3 AI vision upload, normalization, review, and error handling.

Note: Never calls the real Gemini API in automated tests; uses mocked VisionProvider
implementations and in-memory PIL test images.
"""

from __future__ import annotations

import io
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.models import DiagramDocument, DomainType
from app.services.ai_vision import (
    ExtractionInvalidError,
    ProviderQuotaError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    VisionProvider,
    normalize_extraction_proposal,
)
from app.settings import Settings


def _make_image_bytes(fmt: str = "PNG", size: tuple[int, int] = (32, 32)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(240, 245, 255))
    img.save(buf, format=fmt)
    return buf.getvalue()


class _MockVisionProvider(VisionProvider):
    provider_name = "gemini"

    def __init__(self, proposal: dict[str, Any] | Exception) -> None:
        self._proposal = proposal
        self.calls: list[tuple[str, str, str]] = []

    def extract(
        self,
        image_bytes: bytes,
        mime_type: str,
        domain: DomainType,
        filename: str,
    ) -> DiagramDocument:
        self.calls.append((mime_type, domain, filename))
        if isinstance(self._proposal, Exception):
            raise self._proposal
        return normalize_extraction_proposal(
            raw_proposal=self._proposal,
            domain=domain,
            filename=filename,
            provider_name=self.provider_name,
        )


def _valid_physics_proposal() -> dict[str, Any]:
    return {
        "title": "Uploaded Series Circuit",
        "summary": "A circuit with Battery B1, Switch S1, and Bulb L1.",
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
                "description": "Control switch.",
                "attributes": {},
            },
            {
                "id": "bulb_1",
                "kind": "bulb",
                "label": "Bulb L1",
                "description": "Light bulb.",
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
                "target": "battery_1",
                "relation": "wire",
                "description": "Bulb L1 to Battery B1.",
            },
        ],
        "domain_model": {
            "kind": "series_circuit",
            "sequence": ["battery_1", "switch_1", "bulb_1"],
            "switch_states": {"switch_1": "open"},
            "loop_wired": True,
        },
        "warnings": [],
    }


def _valid_biology_proposal() -> dict[str, Any]:
    return {
        "title": "Uploaded Meadow Food Web",
        "summary": "Energy flows from Clover to Hare and from Hare to Hawk.",
        "nodes": [
            {
                "id": "clover",
                "kind": "organism",
                "label": "Clover",
                "description": "Producer plant.",
                "attributes": {},
            },
            {
                "id": "hare",
                "kind": "organism",
                "label": "Hare",
                "description": "Herbivore.",
                "attributes": {},
            },
            {
                "id": "hawk",
                "kind": "organism",
                "label": "Hawk",
                "description": "Predator.",
                "attributes": {},
            },
        ],
        "edges": [
            {
                "id": "feeding_1",
                "source": "clover",
                "target": "hare",
                "relation": "energy_to",
                "description": "Clover provides energy to Hare.",
            },
            {
                "id": "feeding_2",
                "source": "hare",
                "target": "hawk",
                "relation": "energy_to",
                "description": "Hare provides energy to Hawk.",
            },
        ],
        "domain_model": {
            "kind": "food_web",
            "arrow_convention": "food_to_consumer",
        },
        "warnings": [],
    }


def test_analyze_accepts_valid_png_jpeg_webp_and_returns_unreviewed_ai_doc() -> None:
    provider = _MockVisionProvider(_valid_physics_proposal())
    app = create_app(settings=Settings(ai_provider="gemini", gemini_api_key=""), vision_provider=provider)

    with TestClient(app) as client:
        for fmt, mime, ext in (
            ("PNG", "image/png", "png"),
            ("JPEG", "image/jpeg", "jpg"),
            ("WEBP", "image/webp", "webp"),
        ):
            img_bytes = _make_image_bytes(fmt)
            resp = client.post(
                "/api/analyze",
                files={"file": (f"circuit.{ext}", img_bytes, mime)},
                data={"domain": "physics_circuit", "consent": "true"},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["source"]["mode"] == "ai"
            assert body["source"]["provider"] == "gemini"
            assert body["review_status"] == "unreviewed"
            assert body["domain"] == "physics_circuit"


def test_analyze_rejects_missing_consent_and_invalid_domain() -> None:
    provider = _MockVisionProvider(_valid_physics_proposal())
    app = create_app(vision_provider=provider)
    png_bytes = _make_image_bytes("PNG")

    with TestClient(app) as client:
        resp_no_consent = client.post(
            "/api/analyze",
            files={"file": ("circuit.png", png_bytes, "image/png")},
            data={"domain": "physics_circuit", "consent": "false"},
        )
        assert resp_no_consent.status_code == 400
        assert resp_no_consent.json()["error"]["code"] == "CONSENT_REQUIRED"

        resp_bad_domain = client.post(
            "/api/analyze",
            files={"file": ("circuit.png", png_bytes, "image/png")},
            data={"domain": "chemistry", "consent": "true"},
        )
        assert resp_bad_domain.status_code == 400
        assert resp_bad_domain.json()["error"]["code"] == "INVALID_DOMAIN"
        assert provider.calls == []


def test_analyze_rejects_unsupported_format_corrupt_bytes_and_oversized_file() -> None:
    provider = _MockVisionProvider(_valid_physics_proposal())
    app = create_app(settings=Settings(max_upload_mb=1), vision_provider=provider)

    with TestClient(app) as client:
        # Unsupported SVG
        resp_svg = client.post(
            "/api/analyze",
            files={"file": ("diagram.svg", b"<svg></svg>", "image/svg+xml")},
            data={"domain": "physics_circuit", "consent": "true"},
        )
        assert resp_svg.status_code == 415
        assert resp_svg.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"

        # Corrupted PNG bytes
        resp_corrupt = client.post(
            "/api/analyze",
            files={"file": ("broken.png", b"\x89PNG\r\n\x1a\ncorrupt-payload", "image/png")},
            data={"domain": "physics_circuit", "consent": "true"},
        )
        assert resp_corrupt.status_code == 415
        assert resp_corrupt.json()["error"]["code"] == "INVALID_IMAGE"

        # Oversized (> 1 MB configured above)
        oversized = b"\x00" * (1 * 1024 * 1024 + 10)
        resp_big = client.post(
            "/api/analyze",
            files={"file": ("huge.png", oversized, "image/png")},
            data={"domain": "physics_circuit", "consent": "true"},
        )
        assert resp_big.status_code == 413
        assert resp_big.json()["error"]["code"] == "FILE_TOO_LARGE"
        assert provider.calls == []


def test_analyze_without_api_key_returns_503_and_never_fakes_fixture() -> None:
    app = create_app(settings=Settings(ai_provider="none", gemini_api_key=""))
    png_bytes = _make_image_bytes("PNG")

    with TestClient(app) as client:
        resp = client.post(
            "/api/analyze",
            files={"file": ("circuit.png", png_bytes, "image/png")},
            data={"domain": "physics_circuit", "consent": "true"},
        )
        assert resp.status_code == 503
        assert resp.json()["error"]["code"] == "AI_NOT_CONFIGURED"

        # Fixtures remain fully functional when no key is configured.
        ex_resp = client.get("/api/examples/physics_series")
        assert ex_resp.status_code == 200
        assert ex_resp.json()["source"]["mode"] == "fixture"


def test_analyze_maps_provider_timeout_quota_unavailable_and_invalid_output() -> None:
    png_bytes = _make_image_bytes("PNG")
    cases = [
        (ProviderTimeoutError(), 504, "AI_TIMEOUT"),
        (ProviderQuotaError(), 503, "AI_QUOTA_EXCEEDED"),
        (ProviderUnavailableError(), 503, "AI_PROVIDER_ERROR"),
        (ExtractionInvalidError("Malformed AI JSON."), 422, "AI_EXTRACTION_INVALID"),
    ]

    for exc, expected_status, expected_code in cases:
        app = create_app(vision_provider=_MockVisionProvider(exc))
        with TestClient(app) as client:
            resp = client.post(
                "/api/analyze",
                files={"file": ("diagram.png", png_bytes, "image/png")},
                data={"domain": "physics_circuit", "consent": "true"},
            )
            assert resp.status_code == expected_status
            assert resp.json()["error"]["code"] == expected_code


def test_human_correction_validate_confirm_state_and_simulate_physics_flow() -> None:
    # AI missed the return wire between bulb_1 and battery_1.
    incomplete_proposal = _valid_physics_proposal()
    incomplete_proposal["edges"] = incomplete_proposal["edges"][:-1]

    app = create_app(vision_provider=_MockVisionProvider(incomplete_proposal))
    png_bytes = _make_image_bytes("PNG")

    with TestClient(app) as client:
        analyze_resp = client.post(
            "/api/analyze",
            files={"file": ("circuit.png", png_bytes, "image/png")},
            data={"domain": "physics_circuit", "consent": "true"},
        )
        assert analyze_resp.status_code == 200
        draft = analyze_resp.json()
        assert draft["review_status"] == "unreviewed"
        assert draft["domain_model"]["loop_wired"] is False
        assert len(draft["warnings"]) >= 1

        # Simulation blocked for unreviewed diagram (403).
        sim_blocked = client.post(
            "/api/simulate",
            json={
                "diagram": draft,
                "action": {"type": "toggle_switch", "target_id": "switch_1"},
            },
        )
        assert sim_blocked.status_code == 403

        # Confirmation blocked while wire is missing (422).
        confirm_blocked = client.post("/api/confirm", json=draft)
        assert confirm_blocked.status_code == 422

        # Human adds missing return wire during review.
        draft["edges"].append(
            {
                "id": "wire_3",
                "source": "bulb_1",
                "target": "battery_1",
                "relation": "wire",
                "description": "Return wire added during human review.",
            }
        )

        val_resp = client.post("/api/validate", json=draft)
        assert val_resp.status_code == 200
        assert val_resp.json()["valid"] is True
        assert val_resp.json()["simulation_ready"] is True

        confirm_resp = client.post("/api/confirm", json=draft)
        assert confirm_resp.status_code == 200
        confirmed = confirm_resp.json()
        assert confirmed["review_status"] == "confirmed"
        assert confirmed["domain_model"]["loop_wired"] is True

        # Explicit backend state endpoint reports bulb off initially.
        state_before = client.post("/api/state", json=confirmed)
        assert state_before.status_code == 200
        assert state_before.json()["bulb_states"] == {"bulb_1": "off"}

        # Simulation succeeds on confirmed AI diagram.
        sim_resp = client.post(
            "/api/simulate",
            json={
                "diagram": confirmed,
                "action": {"type": "toggle_switch", "target_id": "switch_1"},
            },
        )
        assert sim_resp.status_code == 200
        updated = sim_resp.json()["updated_diagram"]

        state_after = client.post("/api/state", json=updated)
        assert state_after.status_code == 200
        assert state_after.json()["bulb_states"] == {"bulb_1": "on"}


def test_biology_ai_extraction_and_review_confirmation() -> None:
    app = create_app(vision_provider=_MockVisionProvider(_valid_biology_proposal()))
    png_bytes = _make_image_bytes("PNG")

    with TestClient(app) as client:
        resp = client.post(
            "/api/analyze",
            files={"file": ("meadow.png", png_bytes, "image/png")},
            data={"domain": "biology_food_web", "consent": "true"},
        )
        assert resp.status_code == 200
        draft = resp.json()
        assert draft["source"]["mode"] == "ai"
        assert draft["review_status"] == "unreviewed"
        assert any("arrow direction" in w.lower() for w in draft["warnings"])

        confirm_resp = client.post("/api/confirm", json=draft)
        assert confirm_resp.status_code == 200
        confirmed = confirm_resp.json()
        assert confirmed["review_status"] == "confirmed"

        sim_resp = client.post(
            "/api/simulate",
            json={
                "diagram": confirmed,
                "action": {"type": "remove_organism", "target_id": "hare"},
            },
        )
        assert sim_resp.status_code == 200
        assert len(sim_resp.json()["updated_diagram"]["nodes"]) == 2
        assert len(sim_resp.json()["updated_diagram"]["edges"]) == 0


def test_frontend_includes_phase3_analyze_and_review_markup() -> None:
    app = create_app()
    with TestClient(app) as client:
        html = client.get("/").text
        assert 'id="analyze-form"' in html
        assert 'id="analyze-consent-checkbox"' in html
        assert 'id="review-section"' in html
        assert "AI-generated — review required" in html

        js = client.get("/static/app.js").text
        assert "/api/analyze" in js
        assert "/api/state" in js
        assert "/api/confirm" in js
