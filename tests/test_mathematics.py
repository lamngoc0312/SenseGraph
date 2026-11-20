"""Automated tests for Phase 9 Mathematics Data & Function Graph Explorer."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.domains import DomainSimulationError
from app.domains.mathematics import (
    analyze_interval,
    analyze_math_plot,
    parse_csv_to_math_plot,
    validate_math_plot,
)
from app.main import create_app
from app.models import DiagramDocument
from app.services.learning import evaluate_challenge, generate_challenges
from app.settings import FIXTURES_DIR


def _load_math_fixture() -> DiagramDocument:
    raw = json.loads((FIXTURES_DIR / "math_plot.json").read_text(encoding="utf-8"))
    return DiagramDocument.model_validate(raw)


def test_math_fixture_analysis_extrema_intervals_and_intercepts() -> None:
    doc = _load_math_fixture()
    assert validate_math_plot(doc).simulation_ready is True

    analysis = analyze_math_plot(doc)
    assert analysis.point_count == 5
    assert analysis.global_max.id == "pt_3"
    assert analysis.global_max.y == 4
    assert analysis.global_min.y == 0
    assert [p.id for p in analysis.local_maxima] == ["pt_3"]
    assert analysis.local_minima == []

    # Increasing on [0, 2], decreasing on [2, 4]
    assert len(analysis.monotonic_intervals) == 2
    assert analysis.monotonic_intervals[0].trend == "increasing"
    assert analysis.monotonic_intervals[0].start_x == 0
    assert analysis.monotonic_intervals[0].end_x == 2
    assert analysis.monotonic_intervals[1].trend == "decreasing"
    assert analysis.monotonic_intervals[1].start_x == 2
    assert analysis.monotonic_intervals[1].end_x == 4

    # Exact x-intercepts at 0 and 4; exact y-intercept at (0, 0)
    assert [(ic.x, ic.exact) for ic in analysis.x_intercepts] == [(0.0, True), (4.0, True)]
    assert analysis.y_intercept is not None
    assert analysis.y_intercept.y == 0.0
    assert analysis.y_intercept.exact is True


def test_interval_behavior_and_interpolated_intercept_distinction() -> None:
    doc = parse_csv_to_math_plot(
        "Time,Temp\n-1,-2,true\n1,2,false\n3,2,true\n",
        title="Temperature Crossing Zero",
        x_unit="h",
        y_unit="C",
    )
    analysis = analyze_math_plot(doc)
    # Sign change between (-1, -2) and (1, 2) -> interpolated crossing at x = 0, exact = False
    assert len(analysis.x_intercepts) == 1
    assert analysis.x_intercepts[0].x == 0.0
    assert analysis.x_intercepts[0].exact is False
    assert analysis.y_intercept is not None
    assert analysis.y_intercept.exact is False

    iv = analyze_interval(doc, 0, 2)
    assert iv.trend == "mixed"
    assert iv.contains_estimated_points is True
    assert "estimated/interpolated" in iv.announcement.lower()


def test_rejects_duplicate_x_unsorted_x_non_finite_and_missing_csv_data() -> None:
    # Duplicate x
    doc_dup = _load_math_fixture()
    doc_dup.domain_model.points[2].x = doc_dup.domain_model.points[1].x
    res_dup = validate_math_plot(doc_dup)
    assert res_dup.simulation_ready is False
    assert any("duplicate x" in err.lower() for err in res_dup.errors)

    # Unsorted x
    doc_unsorted = _load_math_fixture()
    doc_unsorted.domain_model.points[1].x = 3.5
    res_unsorted = validate_math_plot(doc_unsorted)
    assert res_unsorted.simulation_ready is False
    assert any("strictly increasing" in err.lower() for err in res_unsorted.errors)

    # Non-finite number
    doc_nan = _load_math_fixture()
    doc_nan.domain_model.points[0].y = float("nan")
    res_nan = validate_math_plot(doc_nan)
    assert res_nan.simulation_ready is False
    assert any("non-finite" in err.lower() for err in res_nan.errors)

    # Missing CSV value
    with pytest.raises(DomainSimulationError) as exc_missing:
        parse_csv_to_math_plot("x,y\n1,2\n2,\n")
    assert exc_missing.value.status_code == 400


def test_math_guided_learning_quizzes() -> None:
    doc = _load_math_fixture()
    ch_set = generate_challenges(doc)
    assert ch_set.available is True
    assert len(ch_set.challenges) == 2

    res_max = evaluate_challenge(doc, ch_set.challenges[0].id, ["pt_3"])
    assert res_max.correct is True

    res_trend = evaluate_challenge(doc, ch_set.challenges[1].id, ["increasing"])
    assert res_trend.correct is True


def test_math_api_endpoints_and_frontend_controls() -> None:
    app = create_app()
    with TestClient(app) as client:
        doc = client.get("/api/examples/math_plot").json()
        assert doc["domain"] == "math_plot"

        analyze_resp = client.post(
            "/api/math/analyze",
            json={"diagram": doc, "start_index": 0, "end_index": 2},
        )
        assert analyze_resp.status_code == 200
        body = analyze_resp.json()
        assert body["global_max"]["id"] == "pt_3"
        assert body["interval_summary"]["trend"] == "increasing"
        assert body["interval_summary"]["delta_y"] == 4.0

        csv_resp = client.post(
            "/api/math/import-csv",
            json={
                "csv_text": "x,y\n0,1\n2,5\n4,9\n",
                "title": "Linear Growth",
                "x_label": "Hours",
                "y_label": "Distance",
            },
        )
        assert csv_resp.status_code == 200
        assert csv_resp.json()["domain"] == "math_plot"
        assert len(csv_resp.json()["domain_model"]["points"]) == 3

        html = client.get("/").text
        assert 'id="switch-math-btn"' in html
        assert 'id="math-controls-panel"' in html
        assert 'id="math-prev-pt-btn"' in html
        assert 'id="math-next-pt-btn"' in html
        assert 'id="math-sonify-pt-btn"' in html
