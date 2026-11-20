"""Tests for Phase 12 evaluation benchmark metrics, feature flags, and rate limiting."""

from __future__ import annotations

import io
import json

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.models import DiagramDocument
from app.settings import FIXTURES_DIR, Settings
from evaluation.benchmark import _safe_ratio, run_benchmark, score_extraction


def _make_png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (16, 16), color=(255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


def test_benchmark_metrics_handle_zero_denominators_and_directed_vs_undirected_edges() -> None:
    assert _safe_ratio(0, 0) is None
    assert _safe_ratio(2, 4) == 0.5

    phys = DiagramDocument.model_validate(
        json.loads((FIXTURES_DIR / "physics_series.json").read_text(encoding="utf-8"))
    )
    # Reverse a physics wire direction -> undirected matching still scores 1.0
    phys_pred = phys.model_copy(deep=True)
    phys_pred.edges[0].source, phys_pred.edges[0].target = (
        phys_pred.edges[0].target,
        phys_pred.edges[0].source,
    )
    m_phys = score_extraction(phys, phys_pred, "PHY-TEST")
    assert m_phys.node_precision == 1.0
    assert m_phys.node_recall == 1.0
    assert m_phys.edge_precision == 1.0
    assert m_phys.edge_recall == 1.0

    # Reverse a biology arrow -> directed matching penalizes reversed direction
    bio = DiagramDocument.model_validate(
        json.loads((FIXTURES_DIR / "biology_food_web.json").read_text(encoding="utf-8"))
    )
    bio_pred = bio.model_copy(deep=True)
    bio_pred.edges[0].source, bio_pred.edges[0].target = (
        bio_pred.edges[0].target,
        bio_pred.edges[0].source,
    )
    m_bio = score_extraction(bio, bio_pred, "BIO-TEST")
    assert m_bio.node_precision == 1.0
    assert m_bio.edge_precision == 0.75
    assert m_bio.edge_recall == 0.75


def test_benchmark_dry_run_validates_manifest_without_live_api() -> None:
    results = run_benchmark(mode="dry-run")
    assert len(results) == 6
    assert all(r.status == "not_tested" for r in results)


def test_feature_flag_disables_experimental_domains_cleanly() -> None:
    app = create_app(settings=Settings(enable_experimental_domains=False))
    with TestClient(app) as client:
        health = client.get("/api/health").json()
        assert health["supported_domains"] == ["physics_circuit", "biology_food_web"]

        examples = client.get("/api/examples").json()
        assert {e["id"] for e in examples} == {"physics_series", "biology_food_web"}


def test_analyze_rate_limit_returns_429_when_exceeded() -> None:
    app = create_app(
        settings=Settings(
            ai_provider="none",
            gemini_api_key="",
            analyze_rate_limit_per_min=2,
        )
    )
    png = _make_png()
    with TestClient(app) as client:
        for _ in range(2):
            resp = client.post(
                "/api/analyze",
                files={"file": ("c.png", png, "image/png")},
                data={"domain": "physics_circuit", "consent": "true"},
            )
            assert resp.status_code == 503  # Allowed through rate limit, fails on no key

        resp_limited = client.post(
            "/api/analyze",
            files={"file": ("c.png", png, "image/png")},
            data={"domain": "physics_circuit", "consent": "true"},
        )
        assert resp_limited.status_code == 429
        assert resp_limited.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
