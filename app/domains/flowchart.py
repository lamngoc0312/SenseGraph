"""Safe restricted Computer Science Flowchart validator and interpreter (Phase 8).

Uses an explicit recursive-descent expression parser for integer/boolean
assignments and comparisons. NEVER uses Python eval(), exec(), or compile().
Enforces step limits and wall-clock timeouts to guard against infinite loops.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from app.domains import DomainSimulationError
from app.models import (
    DiagramDocument,
    Edge,
    FlowchartModel,
    FlowchartTraceResponse,
    FlowchartTraceStep,
    Node,
)

ALLOWED_FLOWCHART_NODE_KINDS = frozenset(
    {"start", "end", "input", "assignment", "decision"}
)
ALLOWED_FLOWCHART_RELATIONS = frozenset({"flow", "branch_true", "branch_false"})
VAR_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RESERVED_WORDS = frozenset({"true", "false", "and", "or", "not"})

MAX_EXECUTION_SECONDS = 0.5
MAX_ALLOWED_STEPS = 200


class ExpressionError(ValueError):
    """Raised when a flowchart expression has unsupported syntax or runtime error."""


# --- Safe Recursive-Descent Expression Parser (no eval/exec) ---

_TOKEN_SPEC = re.compile(
    r"\s*(?:"
    r"(?P<NUMBER>\d+)"
    r"|(?P<OP>==|!=|<=|>=|//|[+\-*%<>()])"
    r"|(?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)"
    r"|(?P<MISMATCH>.)"
    r")"
)


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


def _tokenize(expr: str) -> list[_Token]:
    if not isinstance(expr, str) or not expr.strip():
        raise ExpressionError("Expression cannot be empty.")
    if len(expr) > 200:
        raise ExpressionError("Expression exceeds maximum length (200 characters).")

    tokens: list[_Token] = []
    for match in _TOKEN_SPEC.finditer(expr):
        kind = match.lastgroup
        if kind is None:
            continue
        val = match.group(kind)
        if kind == "MISMATCH":
            raise ExpressionError(f"Unsupported character '{val.strip()}' in expression '{expr}'.")
        if kind == "IDENT":
            lower = val.lower()
            if lower in {"true", "false"}:
                tokens.append(_Token("BOOL", lower))
            elif lower in {"and", "or", "not"}:
                tokens.append(_Token("LOGIC", lower))
            else:
                tokens.append(_Token("IDENT", val))
        elif kind in {"NUMBER", "OP"}:
            tokens.append(_Token(kind, val.strip()))
    if not tokens:
        raise ExpressionError("Expression contains no valid tokens.")
    return tokens


class _ExprParser:
    """Recursive-descent parser/evaluator for safe integer & boolean expressions.

    Grammar:
        expr       := or_expr
        or_expr    := and_expr ( 'or' and_expr )*
        and_expr   := not_expr ( 'and' not_expr )*
        not_expr   := 'not' not_expr | cmp_expr
        cmp_expr   := add_expr ( ('==' | '!=' | '<' | '<=' | '>' | '>=') add_expr )?
        add_expr   := mul_expr ( ('+' | '-') mul_expr )*
        mul_expr   := unary_expr ( ('*' | '//' | '%') unary_expr )*
        unary_expr := '-' unary_expr | primary
        primary    := NUMBER | BOOL | IDENT | '(' expr ')'
    """

    def __init__(
        self,
        tokens: list[_Token],
        env: dict[str, int | bool] | None,
        syntax_only: bool = False,
    ) -> None:
        self._tokens = tokens
        self._pos = 0
        self._env = env or {}
        self._syntax_only = syntax_only

    def _peek(self) -> _Token | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _consume(self) -> _Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def parse(self) -> int | bool:
        value = self._parse_or()
        if self._peek() is not None:
            raise ExpressionError(
                f"Unexpected token '{self._peek().value}' in expression."  # type: ignore[union-attr]
            )
        return value

    def _parse_or(self) -> int | bool:
        left = self._parse_and()
        while (tok := self._peek()) is not None and tok.kind == "LOGIC" and tok.value == "or":
            self._consume()
            right = self._parse_and()
            if self._syntax_only:
                left = False
            else:
                if not isinstance(left, bool) or not isinstance(right, bool):
                    raise ExpressionError("Operator 'or' requires boolean operands.")
                left = left or right
        return left

    def _parse_and(self) -> int | bool:
        left = self._parse_not()
        while (tok := self._peek()) is not None and tok.kind == "LOGIC" and tok.value == "and":
            self._consume()
            right = self._parse_not()
            if self._syntax_only:
                left = False
            else:
                if not isinstance(left, bool) or not isinstance(right, bool):
                    raise ExpressionError("Operator 'and' requires boolean operands.")
                left = left and right
        return left

    def _parse_not(self) -> int | bool:
        tok = self._peek()
        if tok is not None and tok.kind == "LOGIC" and tok.value == "not":
            self._consume()
            val = self._parse_not()
            if self._syntax_only:
                return False
            if not isinstance(val, bool):
                raise ExpressionError("Operator 'not' requires a boolean operand.")
            return not val
        return self._parse_cmp()

    def _parse_cmp(self) -> int | bool:
        left = self._parse_add()
        tok = self._peek()
        if tok is not None and tok.kind == "OP" and tok.value in {"==", "!=", "<", "<=", ">", ">="}:
            op = self._consume().value
            right = self._parse_add()
            if self._syntax_only:
                return False
            if op in {"<", "<=", ">", ">="}:
                if type(left) is not int or type(right) is not int:
                    raise ExpressionError(f"Comparison '{op}' requires integer operands.")
                if op == "<":
                    return left < right
                if op == "<=":
                    return left <= right
                if op == ">":
                    return left > right
                return left >= right
            if type(left) is not type(right):
                raise ExpressionError(f"Comparison '{op}' requires matching operand types.")
            return (left == right) if op == "==" else (left != right)
        return left

    def _parse_add(self) -> int | bool:
        left = self._parse_mul()
        while (tok := self._peek()) is not None and tok.kind == "OP" and tok.value in {"+", "-"}:
            op = self._consume().value
            right = self._parse_mul()
            if self._syntax_only:
                left = 0
            else:
                if type(left) is not int or type(right) is not int:
                    raise ExpressionError(f"Arithmetic operator '{op}' requires integers.")
                left = (left + right) if op == "+" else (left - right)
        return left

    def _parse_mul(self) -> int | bool:
        left = self._parse_unary()
        while (tok := self._peek()) is not None and tok.kind == "OP" and tok.value in {"*", "//", "%"}:
            op = self._consume().value
            right = self._parse_unary()
            if self._syntax_only:
                left = 0
            else:
                if type(left) is not int or type(right) is not int:
                    raise ExpressionError(f"Arithmetic operator '{op}' requires integers.")
                if op == "*":
                    left = left * right
                elif op == "//":
                    if right == 0:
                        raise ExpressionError("Division by zero is not allowed.")
                    left = left // right
                else:
                    if right == 0:
                        raise ExpressionError("Modulo by zero is not allowed.")
                    left = left % right
        return left

    def _parse_unary(self) -> int | bool:
        tok = self._peek()
        if tok is not None and tok.kind == "OP" and tok.value == "-":
            self._consume()
            val = self._parse_unary()
            if self._syntax_only:
                return 0
            if type(val) is not int:
                raise ExpressionError("Unary '-' requires an integer operand.")
            return -val
        return self._parse_primary()

    def _parse_primary(self) -> int | bool:
        tok = self._peek()
        if tok is None:
            raise ExpressionError("Unexpected end of expression.")

        if tok.kind == "NUMBER":
            self._consume()
            return int(tok.value)
        if tok.kind == "BOOL":
            self._consume()
            return tok.value == "true"
        if tok.kind == "IDENT":
            self._consume()
            if self._syntax_only:
                return 0
            if tok.value not in self._env:
                raise ExpressionError(f"Undefined variable '{tok.value}'.")
            return self._env[tok.value]
        if tok.kind == "OP" and tok.value == "(":
            self._consume()
            val = self._parse_or()
            closing = self._peek()
            if closing is None or closing.kind != "OP" or closing.value != ")":
                raise ExpressionError("Missing closing parenthesis ')'.")
            self._consume()
            return val

        raise ExpressionError(f"Unexpected token '{tok.value}' in expression.")


def validate_expression_syntax(expr: str) -> None:
    """Validate expression grammar without executing or requiring variable values."""
    tokens = _tokenize(expr)
    _ExprParser(tokens, env=None, syntax_only=True).parse()


def safe_eval_expr(expr: str, env: dict[str, int | bool]) -> int | bool:
    """Safely evaluate a restricted integer/boolean expression against env."""
    tokens = _tokenize(expr)
    return _ExprParser(tokens, env=env, syntax_only=False).parse()


# --- Flowchart Validation & Execution ---


@dataclass(frozen=True)
class FlowchartValidationResult:
    valid_semantics: bool
    simulation_ready: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _is_valid_var_name(name: object) -> bool:
    return (
        isinstance(name, str)
        and bool(VAR_NAME_RE.match(name))
        and name.lower() not in RESERVED_WORDS
    )


def validate_flowchart(diagram: DiagramDocument) -> FlowchartValidationResult:
    """Validate Computer Science flowchart structure, branching, and expression syntax."""
    errors: list[str] = []
    warnings: list[str] = []

    if diagram.domain != "cs_flowchart":
        errors.append("Expected domain 'cs_flowchart'.")
    if not isinstance(diagram.domain_model, FlowchartModel):
        errors.append("Expected domain_model.kind to be 'flowchart'.")
        return FlowchartValidationResult(
            valid_semantics=False,
            simulation_ready=False,
            errors=errors,
            warnings=warnings,
        )

    node_by_id: dict[str, Node] = {}
    for node in diagram.nodes:
        if node.id in node_by_id:
            errors.append(f"Duplicate node ID '{node.id}' in flowchart.")
        node_by_id[node.id] = node
        if node.kind not in ALLOWED_FLOWCHART_NODE_KINDS:
            errors.append(
                f"Node '{node.id}' has kind '{node.kind}', not allowed in cs_flowchart."
            )

    outgoing_by_node: dict[str, list[Edge]] = {n.id: [] for n in diagram.nodes}
    seen_edges: set[tuple[str, str, str]] = set()
    for edge in diagram.edges:
        if edge.relation not in ALLOWED_FLOWCHART_RELATIONS:
            errors.append(
                f"Edge '{edge.id}' has relation '{edge.relation}', "
                "expected 'flow', 'branch_true', or 'branch_false'."
            )
        if edge.source not in node_by_id:
            errors.append(f"Edge '{edge.id}' references unknown source node '{edge.source}'.")
        if edge.target not in node_by_id:
            errors.append(f"Edge '{edge.id}' references unknown target node '{edge.target}'.")
        key = (edge.source, edge.target, edge.relation)
        if key in seen_edges:
            errors.append(
                f"Duplicate flowchart edge from '{edge.source}' to '{edge.target}' ({edge.relation})."
            )
        seen_edges.add(key)
        if edge.source in outgoing_by_node:
            outgoing_by_node[edge.source].append(edge)

    starts = [n for n in diagram.nodes if n.kind == "start"]
    ends = [n for n in diagram.nodes if n.kind == "end"]
    if len(starts) != 1:
        errors.append(f"Flowchart requires exactly 1 'start' node, found {len(starts)}.")
    if len(ends) < 1:
        errors.append("Flowchart requires at least 1 'end' node.")

    entry = diagram.domain_model.entry_node
    if entry not in node_by_id or node_by_id[entry].kind != "start":
        errors.append(
            f"domain_model.entry_node '{entry}' must reference the flowchart's 'start' node."
        )

    for node in diagram.nodes:
        out_edges = outgoing_by_node.get(node.id, [])
        if node.kind in {"start", "input", "assignment"}:
            flow_edges = [e for e in out_edges if e.relation == "flow"]
            non_flow = [e for e in out_edges if e.relation != "flow"]
            if len(flow_edges) != 1 or non_flow:
                errors.append(
                    f"Node '{node.id}' ({node.kind}) must have exactly 1 outgoing 'flow' edge."
                )
        elif node.kind == "decision":
            true_edges = [e for e in out_edges if e.relation == "branch_true"]
            false_edges = [e for e in out_edges if e.relation == "branch_false"]
            other = [e for e in out_edges if e.relation not in {"branch_true", "branch_false"}]
            if len(true_edges) != 1 or len(false_edges) != 1 or other:
                errors.append(
                    f"Decision node '{node.id}' must have exactly 1 'branch_true' edge "
                    "and 1 'branch_false' edge."
                )
        elif node.kind == "end" and out_edges:
            errors.append(f"End node '{node.id}' cannot have outgoing edges.")

        # Validate node-specific safe instruction attributes.
        attrs = node.attributes or {}
        if node.kind == "input":
            var = attrs.get("variable")
            if not _is_valid_var_name(var):
                errors.append(
                    f"Input node '{node.id}' requires a valid attributes.variable identifier."
                )
        elif node.kind == "assignment":
            var = attrs.get("variable")
            expr = attrs.get("expression")
            if not _is_valid_var_name(var):
                errors.append(
                    f"Assignment node '{node.id}' requires a valid attributes.variable identifier."
                )
            if not isinstance(expr, str) or not expr.strip():
                errors.append(
                    f"Assignment node '{node.id}' requires a non-empty attributes.expression."
                )
            else:
                try:
                    validate_expression_syntax(expr)
                except ExpressionError as exc:
                    errors.append(
                        f"Assignment node '{node.id}' has invalid expression '{expr}': {exc}"
                    )
        elif node.kind == "decision":
            cond = attrs.get("condition")
            if not isinstance(cond, str) or not cond.strip():
                errors.append(
                    f"Decision node '{node.id}' requires a non-empty attributes.condition."
                )
            else:
                try:
                    validate_expression_syntax(cond)
                except ExpressionError as exc:
                    errors.append(
                        f"Decision node '{node.id}' has invalid condition '{cond}': {exc}"
                    )

    valid = len(errors) == 0
    return FlowchartValidationResult(
        valid_semantics=valid,
        simulation_ready=valid,
        errors=errors,
        warnings=warnings,
    )


def build_flowchart_summary(diagram: DiagramDocument) -> str:
    """Generate a deterministic plain-language summary of a flowchart."""
    if not isinstance(diagram.domain_model, FlowchartModel):
        return diagram.summary

    decisions = sum(1 for n in diagram.nodes if n.kind == "decision")
    assignments = sum(1 for n in diagram.nodes if n.kind == "assignment")
    inputs_str = (
        ", ".join(f"{k}={v}" for k, v in diagram.domain_model.inputs.items())
        or "none"
    )
    return (
        f"This flowchart contains {len(diagram.nodes)} blocks "
        f"({decisions} decision(s), {assignments} assignment(s)) and "
        f"{len(diagram.edges)} directed connections. "
        f"Default initial inputs: {inputs_str}. Maximum execution limit: "
        f"{diagram.domain_model.max_steps} steps."
    )


def execute_flowchart(
    diagram: DiagramDocument,
    initial_inputs: dict[str, int | bool] | None = None,
    max_steps: int | None = None,
) -> FlowchartTraceResponse:
    """Execute a confirmed, validated flowchart deterministically with bounded steps."""
    if diagram.domain != "cs_flowchart" or not isinstance(
        diagram.domain_model, FlowchartModel
    ):
        raise DomainSimulationError(
            code="INVALID_ACTION",
            message="Flowchart execution is only supported for cs_flowchart diagrams.",
            status_code=400,
        )

    if diagram.review_status != "confirmed":
        raise DomainSimulationError(
            code="UNREVIEWED_DIAGRAM",
            message="Flowchart must be confirmed before executing a trace.",
            status_code=403,
        )

    validation = validate_flowchart(diagram)
    if not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_DIAGRAM",
            message="Flowchart failed structural or expression validation.",
            status_code=422,
            details=validation.errors,
        )

    step_limit = min(
        max(1, max_steps if max_steps is not None else diagram.domain_model.max_steps),
        MAX_ALLOWED_STEPS,
    )
    provided_inputs = dict(diagram.domain_model.inputs)
    if initial_inputs is not None:
        for k, v in initial_inputs.items():
            if not isinstance(v, (int, bool)):
                raise DomainSimulationError(
                    code="INVALID_INPUT",
                    message=f"Initial input '{k}' must be an integer or boolean.",
                    status_code=400,
                )
            provided_inputs[k] = v

    node_by_id = {n.id: n for n in diagram.nodes}
    outgoing: dict[str, list[Edge]] = {n.id: [] for n in diagram.nodes}
    for edge in diagram.edges:
        outgoing[edge.source].append(edge)

    env: dict[str, int | bool] = {}
    steps: list[FlowchartTraceStep] = []
    current_id: str | None = diagram.domain_model.entry_node
    started_at = time.monotonic()

    while current_id is not None:
        if len(steps) >= step_limit:
            return FlowchartTraceResponse(
                status="max_steps_exceeded",
                steps_executed=len(steps),
                max_steps=step_limit,
                final_variables=dict(env),
                announcement=(
                    f"Execution stopped after reaching the maximum limit of {step_limit} steps. "
                    "This usually indicates an infinite loop or a loop requiring more steps."
                ),
                steps=steps,
            )

        if (time.monotonic() - started_at) > MAX_EXECUTION_SECONDS:
            return FlowchartTraceResponse(
                status="max_steps_exceeded",
                steps_executed=len(steps),
                max_steps=step_limit,
                final_variables=dict(env),
                announcement="Execution stopped due to safety timeout.",
                steps=steps,
            )

        node = node_by_id[current_id]
        step_num = len(steps) + 1
        out_edges = outgoing[current_id]
        branch_taken: str | None = None
        next_id: str | None = None

        if node.kind == "start":
            next_id = out_edges[0].target
            desc = f"Started execution at '{node.label}'. Proceeding to '{node_by_id[next_id].label}'."

        elif node.kind == "input":
            var_name = str(node.attributes["variable"])
            val = provided_inputs.get(var_name, 0)
            env[var_name] = val
            next_id = out_edges[0].target
            desc = f"Read input {var_name} = {val}."

        elif node.kind == "assignment":
            var_name = str(node.attributes["variable"])
            expr = str(node.attributes["expression"])
            try:
                val = safe_eval_expr(expr, env)
            except ExpressionError as exc:
                raise DomainSimulationError(
                    code="EXECUTION_ERROR",
                    message=f"Error evaluating assignment '{var_name} = {expr}' at '{node.label}': {exc}",
                    status_code=422,
                ) from exc
            env[var_name] = val
            next_id = out_edges[0].target
            desc = f"Assigned {var_name} = {val} (from '{expr}')."

        elif node.kind == "decision":
            cond = str(node.attributes["condition"])
            try:
                result = safe_eval_expr(cond, env)
            except ExpressionError as exc:
                raise DomainSimulationError(
                    code="EXECUTION_ERROR",
                    message=f"Error evaluating condition '{cond}' at '{node.label}': {exc}",
                    status_code=422,
                ) from exc
            if not isinstance(result, bool):
                raise DomainSimulationError(
                    code="EXECUTION_ERROR",
                    message=f"Decision condition '{cond}' at '{node.label}' must evaluate to a boolean.",
                    status_code=422,
                )
            branch_taken = "true" if result else "false"
            chosen_rel = "branch_true" if result else "branch_false"
            chosen_edge = next(e for e in out_edges if e.relation == chosen_rel)
            next_id = chosen_edge.target
            desc = (
                f"Evaluated '{cond}' -> {result}. "
                f"Took {branch_taken.upper()} branch to '{node_by_id[next_id].label}'."
            )

        else:  # end
            next_id = None
            desc = f"Reached '{node.label}'. Execution completed."

        steps.append(
            FlowchartTraceStep(
                step_index=step_num,
                node_id=node.id,
                node_label=node.label,
                node_kind=node.kind,
                action_description=desc,
                branch_taken=branch_taken,  # type: ignore[arg-type]
                variables=dict(env),
                next_node_id=next_id,
            )
        )
        current_id = next_id

    final_vars_str = ", ".join(f"{k} = {v}" for k, v in env.items()) or "none"
    return FlowchartTraceResponse(
        status="completed",
        steps_executed=len(steps),
        max_steps=step_limit,
        final_variables=dict(env),
        announcement=(
            f"Flowchart completed in {len(steps)} steps. Final variables: {final_vars_str}."
        ),
        steps=steps,
    )
