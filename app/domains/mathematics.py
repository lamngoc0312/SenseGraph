"""Deterministic Mathematics XY Data & Function Graph Engine (Phase 9).

Operates strictly on finite, validated (x, y) data points. Computes global/local
extrema, monotonic intervals, average rates of change, and exact vs interpolated
intercepts. Never invents asymptotes or unseen data beyond the provided domain.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field

from app.domains import DomainSimulationError
from app.models import (
    DiagramDocument,
    Edge,
    MathAnalysisResponse,
    MathIntercept,
    MathIntervalSummary,
    MathMonotonicInterval,
    MathPlotModel,
    MathPlotPoint,
    Node,
    SourceInfo,
)


@dataclass(frozen=True)
class MathValidationResult:
    valid_semantics: bool
    simulation_ready: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _fmt_num(val: float) -> str:
    if float(val).is_integer():
        return str(int(val))
    return f"{val:.4g}"


def _unit_suffix(unit: str) -> str:
    return f" {unit.strip()}" if unit.strip() else ""


def validate_math_plot(diagram: DiagramDocument) -> MathValidationResult:
    """Validate finite numeric bounds, strictly increasing unique x, and labeled axes."""
    errors: list[str] = []
    warnings: list[str] = []

    if diagram.domain != "math_plot":
        errors.append("Expected domain 'math_plot'.")
    if not isinstance(diagram.domain_model, MathPlotModel):
        errors.append("Expected domain_model.kind to be 'math_plot'.")
        return MathValidationResult(
            valid_semantics=False,
            simulation_ready=False,
            errors=errors,
            warnings=warnings,
        )

    dm = diagram.domain_model
    if not dm.x_label.strip():
        errors.append("x_label must be a non-empty axis title.")
    if not dm.y_label.strip():
        errors.append("y_label must be a non-empty axis title.")

    if len(dm.points) < 2:
        errors.append("Math plot requires at least 2 finite data points.")

    seen_x: set[float] = set()
    seen_ids: set[str] = set()
    prev_x: float | None = None
    has_estimated = False

    for idx, pt in enumerate(dm.points):
        if pt.id in seen_ids:
            errors.append(f"Duplicate point ID '{pt.id}' in math_plot.")
        seen_ids.add(pt.id)

        if not math.isfinite(pt.x) or not math.isfinite(pt.y):
            errors.append(
                f"Point '{pt.id}' at index {idx} contains non-finite numeric values."
            )
            continue

        if pt.x in seen_x:
            errors.append(
                f"Duplicate x value ({_fmt_num(pt.x)}) at point '{pt.id}'; "
                "a single-valued function plot requires unique x coordinates."
            )
        seen_x.add(pt.x)

        if prev_x is not None and pt.x < prev_x:
            errors.append(
                f"Points must be sorted in strictly increasing x order "
                f"(found x={_fmt_num(pt.x)} after x={_fmt_num(prev_x)})."
            )
        prev_x = pt.x

        if not pt.exact:
            has_estimated = True

    if has_estimated:
        warnings.append(
            "One or more points are marked as estimated/interpolated rather than exact measurements."
        )

    valid = len(errors) == 0
    return MathValidationResult(
        valid_semantics=valid,
        simulation_ready=valid,
        errors=errors,
        warnings=warnings,
    )


def build_math_plot_summary(diagram: DiagramDocument) -> str:
    """Generate a deterministic plain-language summary of a validated math plot."""
    if not isinstance(diagram.domain_model, MathPlotModel):
        return diagram.summary
    dm = diagram.domain_model
    pts = dm.points
    if len(pts) < 2:
        return diagram.summary

    xu = _unit_suffix(dm.x_unit)
    yu = _unit_suffix(dm.y_unit)
    min_pt = min(pts, key=lambda p: p.y)
    max_pt = max(pts, key=lambda p: p.y)
    fn_part = f" ({dm.function_label})" if dm.function_label else ""
    return (
        f"Line plot of {dm.y_label}{yu} versus {dm.x_label}{xu}{fn_part} across "
        f"{len(pts)} data points from {_fmt_num(pts[0].x)}{xu} to {_fmt_num(pts[-1].x)}{xu}. "
        f"Minimum {dm.y_label} is {_fmt_num(min_pt.y)}{yu} at {_fmt_num(min_pt.x)}{xu}; "
        f"maximum {dm.y_label} is {_fmt_num(max_pt.y)}{yu} at {_fmt_num(max_pt.x)}{xu}."
    )


def analyze_interval(
    diagram: DiagramDocument, start_index: int, end_index: int
) -> MathIntervalSummary:
    """Compute exact change, average rate of change, and trend on [start_index, end_index]."""
    if not isinstance(diagram.domain_model, MathPlotModel):
        raise DomainSimulationError(
            code="INVALID_ACTION",
            message="Interval analysis is only supported for math_plot diagrams.",
            status_code=400,
        )

    dm = diagram.domain_model
    pts = dm.points
    if not (0 <= start_index < end_index < len(pts)):
        raise DomainSimulationError(
            code="INVALID_INTERVAL",
            message=(
                f"Interval indices must satisfy 0 <= start_index < end_index < {len(pts)}."
            ),
            status_code=400,
        )

    sub = pts[start_index : end_index + 1]
    dx = sub[-1].x - sub[0].x
    dy = sub[-1].y - sub[0].y
    rate = dy / dx

    step_trends: set[str] = set()
    for i in range(len(sub) - 1):
        d = sub[i + 1].y - sub[i].y
        if d > 0:
            step_trends.add("increasing")
        elif d < 0:
            step_trends.add("decreasing")
        else:
            step_trends.add("constant")

    trend = next(iter(step_trends)) if len(step_trends) == 1 else "mixed"
    has_estimated = any(not p.exact for p in sub)

    xu = _unit_suffix(dm.x_unit)
    yu = _unit_suffix(dm.y_unit)
    est_note = (
        " Note: includes estimated/interpolated point(s)."
        if has_estimated
        else " All points in this interval are exact."
    )
    announcement = (
        f"From {dm.x_label} = {_fmt_num(sub[0].x)}{xu} to {_fmt_num(sub[-1].x)}{xu}: "
        f"{dm.y_label} changes from {_fmt_num(sub[0].y)}{yu} to {_fmt_num(sub[-1].y)}{yu} "
        f"(change {_fmt_num(dy)}{yu}, average rate {_fmt_num(rate)}{yu} per {dm.x_unit or dm.x_label}). "
        f"Overall trend: {trend}.{est_note}"
    )

    return MathIntervalSummary(
        start_index=start_index,
        end_index=end_index,
        start_x=sub[0].x,
        end_x=sub[-1].x,
        start_y=sub[0].y,
        end_y=sub[-1].y,
        delta_x=dx,
        delta_y=dy,
        avg_rate_of_change=rate,
        trend=trend,  # type: ignore[arg-type]
        contains_estimated_points=has_estimated,
        announcement=announcement,
    )


def analyze_math_plot(
    diagram: DiagramDocument,
    start_index: int | None = None,
    end_index: int | None = None,
) -> MathAnalysisResponse:
    """Compute global/local extrema, monotonic intervals, and computable intercepts."""
    if diagram.domain != "math_plot" or not isinstance(
        diagram.domain_model, MathPlotModel
    ):
        raise DomainSimulationError(
            code="INVALID_ACTION",
            message="Math analysis is only supported for math_plot diagrams.",
            status_code=400,
        )
    if diagram.review_status != "confirmed":
        raise DomainSimulationError(
            code="UNREVIEWED_DIAGRAM",
            message="Math plot must be confirmed before running analysis.",
            status_code=403,
        )

    validation = validate_math_plot(diagram)
    if not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_DIAGRAM",
            message="Math plot failed validation.",
            status_code=422,
            details=validation.errors,
        )

    dm = diagram.domain_model
    pts = dm.points
    global_min = min(pts, key=lambda p: p.y)
    global_max = max(pts, key=lambda p: p.y)

    local_maxima: list[MathPlotPoint] = []
    local_minima: list[MathPlotPoint] = []
    for i in range(1, len(pts) - 1):
        if pts[i].y > pts[i - 1].y and pts[i].y > pts[i + 1].y:
            local_maxima.append(pts[i])
        elif pts[i].y < pts[i - 1].y and pts[i].y < pts[i + 1].y:
            local_minima.append(pts[i])

    # Group consecutive segments sharing the same monotonic direction.
    intervals: list[MathMonotonicInterval] = []
    seg_start = 0

    def _dir(a: MathPlotPoint, b: MathPlotPoint) -> str:
        if b.y > a.y:
            return "increasing"
        if b.y < a.y:
            return "decreasing"
        return "constant"

    cur_dir = _dir(pts[0], pts[1])
    for i in range(1, len(pts) - 1):
        nxt_dir = _dir(pts[i], pts[i + 1])
        if nxt_dir != cur_dir:
            dx = pts[i].x - pts[seg_start].x
            dy = pts[i].y - pts[seg_start].y
            intervals.append(
                MathMonotonicInterval(
                    start_id=pts[seg_start].id,
                    end_id=pts[i].id,
                    start_x=pts[seg_start].x,
                    end_x=pts[i].x,
                    trend=cur_dir,  # type: ignore[arg-type]
                    delta_x=dx,
                    delta_y=dy,
                    avg_rate_of_change=dy / dx,
                )
            )
            seg_start = i
            cur_dir = nxt_dir

    dx_last = pts[-1].x - pts[seg_start].x
    dy_last = pts[-1].y - pts[seg_start].y
    intervals.append(
        MathMonotonicInterval(
            start_id=pts[seg_start].id,
            end_id=pts[-1].id,
            start_x=pts[seg_start].x,
            end_x=pts[-1].x,
            trend=cur_dir,  # type: ignore[arg-type]
            delta_x=dx_last,
            delta_y=dy_last,
            avg_rate_of_change=dy_last / dx_last,
        )
    )

    # Computable intercepts within the given data domain only (never extrapolating).
    x_intercepts: list[MathIntercept] = []
    for pt in pts:
        if pt.y == 0:
            x_intercepts.append(
                MathIntercept(
                    axis="x",
                    x=pt.x,
                    y=0.0,
                    exact=pt.exact,
                    note=f"Exact data point {pt.id}" if pt.exact else f"Estimated point {pt.id}",
                )
            )
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if (a.y < 0 < b.y) or (a.y > 0 > b.y):
            t = -a.y / (b.y - a.y)
            x_cross = a.x + t * (b.x - a.x)
            x_intercepts.append(
                MathIntercept(
                    axis="x",
                    x=round(x_cross, 6),
                    y=0.0,
                    exact=False,
                    note=f"Linearly interpolated crossing between {a.id} and {b.id}",
                )
            )

    y_intercept: MathIntercept | None = None
    for pt in pts:
        if pt.x == 0:
            y_intercept = MathIntercept(
                axis="y",
                x=0.0,
                y=pt.y,
                exact=pt.exact,
                note=f"Exact data point {pt.id}" if pt.exact else f"Estimated point {pt.id}",
            )
            break
    if y_intercept is None:
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if a.x < 0 < b.x:
                t = (0.0 - a.x) / (b.x - a.x)
                y_cross = a.y + t * (b.y - a.y)
                y_intercept = MathIntercept(
                    axis="y",
                    x=0.0,
                    y=round(y_cross, 6),
                    exact=False,
                    note=f"Linearly interpolated at x=0 between {a.id} and {b.id}",
                )
                break

    interval_summary: MathIntervalSummary | None = None
    if start_index is not None and end_index is not None:
        interval_summary = analyze_interval(diagram, start_index, end_index)

    return MathAnalysisResponse(
        point_count=len(pts),
        x_label=dm.x_label,
        x_unit=dm.x_unit,
        y_label=dm.y_label,
        y_unit=dm.y_unit,
        global_min=global_min,
        global_max=global_max,
        local_maxima=local_maxima,
        local_minima=local_minima,
        monotonic_intervals=intervals,
        x_intercepts=x_intercepts,
        y_intercept=y_intercept,
        interval_summary=interval_summary,
        summary=build_math_plot_summary(diagram),
    )


def parse_csv_to_math_plot(
    csv_text: str,
    title: str = "Imported XY Data Plot",
    x_label: str = "x",
    x_unit: str = "",
    y_label: str = "y",
    y_unit: str = "",
) -> DiagramDocument:
    """Parse simple 2-column (x,y) or 3-column (x,y,exact) CSV into a validated DiagramDocument."""
    reader = csv.reader(io.StringIO(csv_text.strip()))
    raw_rows = [row for row in reader if any(cell.strip() for cell in row)]
    if len(raw_rows) < 2:
        raise DomainSimulationError(
            code="INVALID_CSV",
            message="CSV must contain at least 2 numeric (x, y) data rows.",
            status_code=400,
        )

    # Detect optional header row if first row is non-numeric.
    start_row = 0
    try:
        float(raw_rows[0][0].strip())
        float(raw_rows[0][1].strip())
    except (ValueError, IndexError):
        if len(raw_rows[0]) >= 2:
            if x_label == "x" and raw_rows[0][0].strip():
                x_label = raw_rows[0][0].strip()
            if y_label == "y" and raw_rows[0][1].strip():
                y_label = raw_rows[0][1].strip()
        start_row = 1

    data_rows = raw_rows[start_row:]
    if len(data_rows) < 2:
        raise DomainSimulationError(
            code="INVALID_CSV",
            message="CSV must contain at least 2 numeric (x, y) data rows after the header.",
            status_code=400,
        )
    if len(data_rows) > 100:
        raise DomainSimulationError(
            code="INVALID_CSV",
            message="CSV import supports up to 100 data points.",
            status_code=400,
        )

    points: list[MathPlotPoint] = []
    xu = _unit_suffix(x_unit)
    yu = _unit_suffix(y_unit)
    for idx, row in enumerate(data_rows, start=1):
        if len(row) < 2 or not row[0].strip() or not row[1].strip():
            raise DomainSimulationError(
                code="INVALID_CSV",
                message=f"Row {idx} is missing x or y data.",
                status_code=400,
            )
        try:
            x_val = float(row[0].strip())
            y_val = float(row[1].strip())
        except ValueError as exc:
            raise DomainSimulationError(
                code="INVALID_CSV",
                message=f"Row {idx} contains non-numeric values: {row[:2]}",
                status_code=400,
            ) from exc

        exact = True
        if len(row) >= 3 and row[2].strip().lower() in {"false", "0", "estimated", "interpolated"}:
            exact = False

        points.append(
            MathPlotPoint(
                id=f"pt_{idx}",
                x=x_val,
                y=y_val,
                label=f"Point {idx} ({_fmt_num(x_val)}{xu}, {_fmt_num(y_val)}{yu})",
                exact=exact,
            )
        )

    nodes = [
        Node(
            id=p.id,
            kind="data_point",
            label=p.label,
            description=(
                f"{x_label} = {_fmt_num(p.x)}{xu}, {y_label} = {_fmt_num(p.y)}{yu} "
                f"({'exact' if p.exact else 'estimated'})."
            ),
            attributes={"x": p.x, "y": p.y, "exact": p.exact},
        )
        for p in points
    ]
    edges = [
        Edge(
            id=f"seg_{i + 1}",
            source=points[i].id,
            target=points[i + 1].id,
            relation="series_next",
            description=(
                f"From ({_fmt_num(points[i].x)}{xu}, {_fmt_num(points[i].y)}{yu}) "
                f"to ({_fmt_num(points[i + 1].x)}{xu}, {_fmt_num(points[i + 1].y)}{yu})."
            ),
        )
        for i in range(len(points) - 1)
    ]

    doc = DiagramDocument(
        schema_version="1.0",
        id="csv_math_plot",
        title=title.strip() or "Imported XY Data Plot",
        domain="math_plot",
        summary="Imported XY data plot.",
        source=SourceInfo(mode="fixture", filename="imported.csv", provider=None),
        review_status="confirmed",
        nodes=nodes,
        edges=edges,
        domain_model=MathPlotModel(
            kind="math_plot",
            x_label=x_label,
            x_unit=x_unit,
            y_label=y_label,
            y_unit=y_unit,
            points=points,
        ),
        warnings=[],
    )

    validation = validate_math_plot(doc)
    if not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_CSV",
            message="Imported CSV data failed mathematical plot validation.",
            status_code=422,
            details=validation.errors,
        )

    doc.summary = build_math_plot_summary(doc)
    doc.warnings = list(validation.warnings)
    return doc
