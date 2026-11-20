"""Automated tests for Phase 8 Computer Science Flowchart Explorer."""

from __future__ import annotations

import copy
import json

import pytest
from fastapi.testclient import TestClient

from app.domains import DomainSimulationError
from app.domains.flowchart import (
    ExpressionError,
    execute_flowchart,
    safe_eval_expr,
    validate_flowchart,
)
from app.main import create_app
from app.models import DiagramDocument
from app.services.ai_vision import ExtractionInvalidError, normalize_extraction_proposal
from app.services.learning import evaluate_challenge, generate_challenges
from app.settings import FIXTURES_DIR


def _load_flowchart_fixture() -> DiagramDocument:
    raw = json.loads((FIXTURES_DIR / "cs_flowchart.json").read_text(encoding="utf-8"))
    return DiagramDocument.model_validate(raw)


def test_safe_expression_evaluator_supports_int_and_bool_and_rejects_code_injection() -> None:
    env = {"n": 3, "total": 4, "flag": True}
    assert safe_eval_expr("total + n * 2", env) == 10
    assert safe_eval_expr("(total + n) // 2", env) == 3
    assert safe_eval_expr("n > 0 and flag", env) is True
    assert safe_eval_expr("not (n == 0)", env) is True

    # Rejects function calls, attribute access, strings, imports, division by zero.
    for bad_expr in (
        "__import__('os').system('echo hi')",
        "eval('1+1')",
        "n.bit_length()",
        "10 // 0",
        "undefined_var + 1",
        "flag + 1",
    ):
        with pytest.raises(ExpressionError):
            safe_eval_expr(bad_expr, env)


def test_flowchart_fixture_executes_finite_loop_deterministically() -> None:
    doc = _load_flowchart_fixture()
    assert validate_flowchart(doc).simulation_ready is True

    # Default n=3 -> total = 3 + 2 + 1 = 6
    trace = execute_flowchart(doc)
    assert trace.status == "completed"
    assert trace.final_variables == {"n": 0, "total": 6}
    assert trace.steps[0].node_id == "start_1"
    assert trace.steps[-1].node_id == "end_1"

    # Custom input n=0 -> skips loop body directly
    trace_zero = execute_flowchart(doc, initial_inputs={"n": 0})
    assert trace_zero.status == "completed"
    assert trace_zero.final_variables == {"n": 0, "total": 0}
    assert trace_zero.steps_executed < trace.steps_executed


def test_flowchart_infinite_loop_halts_safely_at_max_steps() -> None:
    doc = _load_flowchart_fixture()
    # Change decrement to increment -> infinite loop when n=3
    for node in doc.nodes:
        if node.id == "dec_n":
            node.attributes["expression"] = "n + 1"

    trace = execute_flowchart(doc, initial_inputs={"n": 3}, max_steps=15)
    assert trace.status == "max_steps_exceeded"
    assert trace.steps_executed == 15
    assert "maximum limit of 15 steps" in trace.announcement.lower()


def test_flowchart_validation_rejects_missing_branch_invalid_expr_and_unsupported_node() -> None:
    # Missing false branch on decision
    doc_missing_branch = _load_flowchart_fixture()
    doc_missing_branch.edges = [
        e for e in doc_missing_branch.edges if e.relation != "branch_false"
    ]
    res_branch = validate_flowchart(doc_missing_branch)
    assert res_branch.simulation_ready is False
    assert any("branch_true" in err and "branch_false" in err for err in res_branch.errors)

    # Invalid expression in assignment
    doc_bad_expr = _load_flowchart_fixture()
    for n in doc_bad_expr.nodes:
        if n.id == "add_total":
            n.attributes["expression"] = "__import__('os')"
    res_expr = validate_flowchart(doc_bad_expr)
    assert res_expr.simulation_ready is False
    assert any("invalid expression" in err.lower() for err in res_expr.errors)

    # Unreviewed flowchart cannot execute
    doc_unreviewed = _load_flowchart_fixture()
    doc_unreviewed.review_status = "unreviewed"
    with pytest.raises(DomainSimulationError) as exc:
        execute_flowchart(doc_unreviewed)
    assert exc.value.status_code == 403


def test_flowchart_guided_learning_branch_and_final_value_challenges() -> None:
    doc = _load_flowchart_fixture()
    ch_set = generate_challenges(doc)
    assert ch_set.available is True
    assert len(ch_set.challenges) == 2
    assert ch_set.challenges[0].template == "flowchart_predict_branch"
    assert ch_set.challenges[1].template == "flowchart_predict_final_value"

    res_branch = evaluate_challenge(doc, ch_set.challenges[0].id, ["true"])
    assert res_branch.correct is True
    assert "true branch" in res_branch.summary.lower()

    res_final = evaluate_challenge(doc, ch_set.challenges[1].id, ["6"])
    assert res_final.correct is True


def test_flowchart_ai_normalization_flags_ambiguous_branches_and_rejects_unsupported_shapes() -> None:
    raw_valid = copy.deepcopy(_load_flowchart_fixture().model_dump())
    normalized = normalize_extraction_proposal(
        raw_proposal=raw_valid,
        domain="cs_flowchart",
        filename="algo.png",
        provider_name="gemini",
    )
    assert normalized.source.mode == "ai"
    assert normalized.review_status == "unreviewed"
    assert any("branch labels" in w.lower() for w in normalized.warnings)

    raw_unsupported = copy.deepcopy(raw_valid)
    raw_unsupported["nodes"].append(
        {
            "id": "sub_1",
            "kind": "subroutine_call",
            "label": "Call External API",
            "description": "Unsupported shape",
            "attributes": {},
        }
    )
    with pytest.raises(ExtractionInvalidError):
        normalize_extraction_proposal(
            raw_proposal=raw_unsupported,
            domain="cs_flowchart",
            filename="bad_algo.png",
            provider_name="gemini",
        )


def test_flowchart_api_trace_and_frontend_controls() -> None:
    app = create_app()
    with TestClient(app) as client:
        fc_doc = client.get("/api/examples/cs_flowchart").json()
        assert fc_doc["domain"] == "cs_flowchart"

        state_resp = client.post("/api/state", json=fc_doc)
        assert state_resp.status_code == 200
        assert state_resp.json()["entry_node"] == "start_1"
        assert state_resp.json()["flowchart_inputs"] == {"n": 3}

        trace_resp = client.post(
            "/api/flowchart/trace",
            json={"diagram": fc_doc, "inputs": {"n": 4}},
        )
        assert trace_resp.status_code == 200
        body = trace_resp.json()
        assert body["status"] == "completed"
        assert body["final_variables"] == {"n": 0, "total": 10}

        html = client.get("/").text
        assert 'value="cs_flowchart"' in html
        assert 'id="switch-cs-btn"' in html
        assert 'id="flowchart-trace-panel"' in html
        assert 'id="trace-prev-btn"' in html
        assert 'id="trace-next-btn"' in html
