"""Repeatable scientific & AI extraction benchmark harness for SenseGraph (Phase 12).

Computes node/edge precision & recall with explicit zero-denominator handling
(returning None rather than fabricating 0.0 or 1.0), respecting undirected vs
directed domain edge semantics.

Usage:
    python -m evaluation.benchmark --mode dry-run
    python -m evaluation.benchmark --mode live   # requires GEMINI_API_KEY in .env
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from app.models import DiagramDocument
from app.services.ai_vision import (
    GeminiVisionProvider,
    VisionError,
    validate_uploaded_image,
)
from app.services.validators import validate_diagram
from app.settings import PROJECT_ROOT, load_settings

MANIFEST_PATH = PROJECT_ROOT / "evaluation" / "dataset_manifest.json"
UNDIRECTED_DOMAINS = frozenset({"physics_circuit", "chemistry_molecule"})


@dataclass(frozen=True)
class CaseMetrics:
    case_id: str
    domain: str
    status: str  # "evaluated" | "not_tested" | "rejected_as_expected" | "error"
    node_precision: float | None
    node_recall: float | None
    edge_precision: float | None
    edge_recall: float | None
    kind_accuracy: float | None
    simulation_ready_before_review: bool | None
    notes: str


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    """Return numerator / denominator, or None when denominator is 0."""
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _normalize_label(label: str) -> str:
    return " ".join(label.strip().lower().split())


def _edge_signature(
    doc: DiagramDocument,
) -> set[tuple[str, str, str]] | set[tuple[frozenset[str], str]]:
    id_to_label = {n.id: _normalize_label(n.label) for n in doc.nodes}
    if doc.domain in UNDIRECTED_DOMAINS:
        return {
            (frozenset((id_to_label.get(e.source, e.source), id_to_label.get(e.target, e.target))), e.relation)
            for e in doc.edges
        }
    return {
        (id_to_label.get(e.source, e.source), id_to_label.get(e.target, e.target), e.relation)
        for e in doc.edges
    }


def score_extraction(
    expected: DiagramDocument,
    predicted: DiagramDocument,
    case_id: str,
) -> CaseMetrics:
    """Compute precision, recall, and kind accuracy between expected and predicted graphs."""
    exp_nodes = {_normalize_label(n.label): n.kind for n in expected.nodes}
    pred_nodes = {_normalize_label(n.label): n.kind for n in predicted.nodes}

    matched_labels = set(exp_nodes.keys()) & set(pred_nodes.keys())
    correct_kinds = sum(1 for lbl in matched_labels if exp_nodes[lbl] == pred_nodes[lbl])

    exp_edges = _edge_signature(expected)
    pred_edges = _edge_signature(predicted)
    matched_edges = exp_edges & pred_edges

    val = validate_diagram(predicted)

    return CaseMetrics(
        case_id=case_id,
        domain=expected.domain,
        status="evaluated",
        node_precision=_safe_ratio(len(matched_labels), len(pred_nodes)),
        node_recall=_safe_ratio(len(matched_labels), len(exp_nodes)),
        edge_precision=_safe_ratio(len(matched_edges), len(pred_edges)),
        edge_recall=_safe_ratio(len(matched_edges), len(exp_edges)),
        kind_accuracy=_safe_ratio(correct_kinds, len(matched_labels)),
        simulation_ready_before_review=val.simulation_ready,
        notes=f"warnings={len(predicted.warnings)}, validation_errors={len(val.errors)}",
    )


def run_benchmark(mode: str = "dry-run") -> list[CaseMetrics]:
    """Run dry-run manifest verification or live Gemini extraction benchmark."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    settings = load_settings()
    provider = GeminiVisionProvider(settings) if (mode == "live" and settings.ai_configured) else None
    results: list[CaseMetrics] = []

    for case in manifest.get("cases", []):
        cid = case["case_id"]
        domain = case["domain"]
        img_rel = case.get("image_path")
        exp_rel = case.get("expected_fixture")

        if mode == "dry-run":
            if exp_rel:
                exp_doc = DiagramDocument.model_validate(
                    json.loads((PROJECT_ROOT / exp_rel).read_text(encoding="utf-8"))
                )
                val = validate_diagram(exp_doc)
                results.append(
                    CaseMetrics(
                        case_id=cid,
                        domain=domain,
                        status="not_tested",
                        node_precision=None,
                        node_recall=None,
                        edge_precision=None,
                        edge_recall=None,
                        kind_accuracy=None,
                        simulation_ready_before_review=val.simulation_ready,
                        notes="Dry-run: expected fixture valid; live AI not executed.",
                    )
                )
            else:
                results.append(
                    CaseMetrics(
                        case_id=cid,
                        domain=domain,
                        status="not_tested",
                        node_precision=None,
                        node_recall=None,
                        edge_precision=None,
                        edge_recall=None,
                        kind_accuracy=None,
                        simulation_ready_before_review=None,
                        notes="Dry-run: negative/pending case; live AI not executed.",
                    )
                )
            continue

        # Live mode
        if provider is None:
            results.append(
                CaseMetrics(
                    case_id=cid,
                    domain=domain,
                    status="not_tested",
                    node_precision=None,
                    node_recall=None,
                    edge_precision=None,
                    edge_recall=None,
                    kind_accuracy=None,
                    simulation_ready_before_review=None,
                    notes="Live mode skipped: GEMINI_API_KEY not configured.",
                )
            )
            continue

        if not img_rel or not exp_rel:
            results.append(
                CaseMetrics(
                    case_id=cid,
                    domain=domain,
                    status="not_tested",
                    node_precision=None,
                    node_recall=None,
                    edge_precision=None,
                    edge_recall=None,
                    kind_accuracy=None,
                    simulation_ready_before_review=None,
                    notes="No local image attached for this case yet.",
                )
            )
            continue

        img_path = PROJECT_ROOT / img_rel
        exp_doc = DiagramDocument.model_validate(
            json.loads((PROJECT_ROOT / exp_rel).read_text(encoding="utf-8"))
        )
        raw_bytes = img_path.read_bytes()
        try:
            mime = validate_uploaded_image(raw_bytes, None, settings.max_upload_mb)
            pred_doc = provider.extract(raw_bytes, mime, domain, img_path.name)
            results.append(score_extraction(exp_doc, pred_doc, cid))
        except VisionError as exc:
            results.append(
                CaseMetrics(
                    case_id=cid,
                    domain=domain,
                    status="error",
                    node_precision=None,
                    node_recall=None,
                    edge_precision=None,
                    edge_recall=None,
                    kind_accuracy=None,
                    simulation_ready_before_review=False,
                    notes=f"{exc.code}: {exc.message}",
                )
            )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="SenseGraph evaluation benchmark harness")
    parser.add_argument("--mode", choices=("dry-run", "live"), default="dry-run")
    args = parser.parse_args()
    metrics = run_benchmark(mode=args.mode)
    print(json.dumps([asdict(m) for m in metrics], indent=2))


if __name__ == "__main__":
    main()
