"""Pydantic data contracts matching contracts/diagram.schema.json and REST API payloads."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ID_PATTERN = r"^[A-Za-z][A-Za-z0-9_-]*$"

DomainType = Literal[
    "physics_circuit",
    "biology_food_web",
    "cs_flowchart",
    "math_plot",
    "chemistry_molecule",
]
SourceMode = Literal["fixture", "ai"]
ReviewStatus = Literal["unreviewed", "confirmed"]
NodeKind = Literal[
    "battery",
    "switch",
    "bulb",
    "organism",
    "start",
    "end",
    "input",
    "assignment",
    "decision",
    "data_point",
    "atom",
]
EdgeRelation = Literal[
    "wire",
    "energy_to",
    "flow",
    "branch_true",
    "branch_false",
    "series_next",
    "single_bond",
    "double_bond",
    "triple_bond",
]
SwitchState = Literal["open", "closed"]

FIXTURE_SOURCE_LABEL = "Pre-annotated demo — no AI used"


class SourceInfo(BaseModel):
    """Provenance information for a diagram document."""

    model_config = ConfigDict(extra="forbid")

    mode: SourceMode
    filename: str
    provider: str | None

    @model_validator(mode="after")
    def validate_provider_for_ai_mode(self) -> SourceInfo:
        if self.mode == "ai" and (self.provider is None or len(self.provider.strip()) == 0):
            raise ValueError("source.provider must be a non-empty string when source.mode is 'ai'.")
        return self


class Node(BaseModel):
    """Semantic graph node representing a STEM diagram entity."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=ID_PATTERN)
    kind: NodeKind
    label: str = Field(..., min_length=1)
    description: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """Semantic graph edge representing a relationship between two nodes."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=ID_PATTERN)
    source: str = Field(..., pattern=ID_PATTERN)
    target: str = Field(..., pattern=ID_PATTERN)
    relation: EdgeRelation
    description: str


class SeriesCircuitModel(BaseModel):
    """Physics domain payload for a qualitative single-loop series circuit."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["series_circuit"]
    sequence: list[str] = Field(..., min_length=3, max_length=4)
    switch_states: dict[str, SwitchState] = Field(..., min_length=1, max_length=1)
    loop_wired: bool

    @model_validator(mode="after")
    def validate_sequence_items(self) -> SeriesCircuitModel:
        import re

        pattern = re.compile(ID_PATTERN)
        for item in self.sequence:
            if not pattern.match(item):
                raise ValueError(f"Invalid component ID '{item}' in domain_model.sequence.")
        if len(set(self.sequence)) != len(self.sequence):
            raise ValueError("domain_model.sequence must contain unique component IDs.")
        return self


class FoodWebModel(BaseModel):
    """Biology domain payload for a directed food web."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["food_web"]
    arrow_convention: Literal["food_to_consumer"]


class FlowchartModel(BaseModel):
    """Computer Science domain payload for a restricted executable flowchart."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["flowchart"]
    entry_node: str = Field(..., pattern=ID_PATTERN)
    inputs: dict[str, int | bool] = Field(default_factory=dict)
    max_steps: int = Field(default=100, ge=1, le=200)


class MathPlotPoint(BaseModel):
    """Single finite (x, y) data point with explicit exact vs estimated flag."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., pattern=ID_PATTERN)
    x: float
    y: float
    label: str = Field(..., min_length=1)
    exact: bool = True


class MathPlotModel(BaseModel):
    """Mathematics domain payload for explicit XY line plots and sample functions."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["math_plot"]
    x_label: str = Field(..., min_length=1)
    x_unit: str = ""
    y_label: str = Field(..., min_length=1)
    y_unit: str = ""
    function_label: str | None = None
    points: list[MathPlotPoint] = Field(..., min_length=2)


class MoleculeModel(BaseModel):
    """Chemistry domain payload for beginner-level validated covalent molecules."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["molecule"]
    smiles: str = Field(..., min_length=1)
    formula: str = Field(..., min_length=1)
    supported_scope_note: str = (
        "Beginner-level explicit covalent graph only; does not infer toxicity, "
        "reaction yields, medical properties, or lab safety."
    )


DomainModel = Annotated[
    SeriesCircuitModel | FoodWebModel | FlowchartModel | MathPlotModel | MoleculeModel,
    Field(discriminator="kind"),
]


class DiagramDocument(BaseModel):
    """Authoritative SenseGraph DiagramDocument v1."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"] = "1.0"
    id: str = Field(..., pattern=ID_PATTERN)
    title: str = Field(..., min_length=1)
    domain: DomainType
    summary: str = Field(..., min_length=1)
    source: SourceInfo
    review_status: ReviewStatus
    nodes: list[Node] = Field(..., min_length=1)
    edges: list[Edge]
    domain_model: DomainModel
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_domain_matches_model(self) -> DiagramDocument:
        if self.domain == "physics_circuit" and self.domain_model.kind != "series_circuit":
            raise ValueError(
                "domain_model.kind must be 'series_circuit' when domain is 'physics_circuit'."
            )
        if self.domain == "biology_food_web" and self.domain_model.kind != "food_web":
            raise ValueError(
                "domain_model.kind must be 'food_web' when domain is 'biology_food_web'."
            )
        if self.domain == "cs_flowchart" and self.domain_model.kind != "flowchart":
            raise ValueError(
                "domain_model.kind must be 'flowchart' when domain is 'cs_flowchart'."
            )
        if self.domain == "math_plot" and self.domain_model.kind != "math_plot":
            raise ValueError(
                "domain_model.kind must be 'math_plot' when domain is 'math_plot'."
            )
        if self.domain == "chemistry_molecule" and self.domain_model.kind != "molecule":
            raise ValueError(
                "domain_model.kind must be 'molecule' when domain is 'chemistry_molecule'."
            )
        return self


# --- REST API request/response models ---


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    ai_configured: bool
    supported_domains: list[str]


class ExampleSummary(BaseModel):
    id: str
    title: str
    domain: DomainType
    source_label: str = FIXTURE_SOURCE_LABEL


class ValidationResponse(BaseModel):
    valid: bool
    simulation_ready: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class SimulationAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., min_length=1)
    target_id: str = Field(..., pattern=ID_PATTERN)


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagram: DiagramDocument
    action: SimulationAction


class SimulationResponse(BaseModel):
    updated_diagram: DiagramDocument
    event: str
    announcement: str
    changes: list[str]


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[str] = Field(default_factory=list)


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class DiagramStateResponse(BaseModel):
    """Explicit backend-calculated state data for accessible frontend rendering."""

    domain: DomainType
    loop_wired: bool | None = None
    all_switches_closed: bool | None = None
    bulbs_on: bool | None = None
    switch_states: dict[str, SwitchState] = Field(default_factory=dict)
    bulb_states: dict[str, Literal["on", "off"]] = Field(default_factory=dict)
    organism_count: int | None = None
    relationship_count: int | None = None
    entry_node: str | None = None
    flowchart_inputs: dict[str, int | bool] = Field(default_factory=dict)
    max_steps: int | None = None
    point_count: int | None = None
    x_label: str | None = None
    y_label: str | None = None
    smiles: str | None = None
    formula: str | None = None
    atom_counts: dict[str, int] = Field(default_factory=dict)


class SmilesParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    smiles: str = Field(..., min_length=1, max_length=80)
    title: str | None = None


# --- Phase 11: Evidence-Grounded STEM Tutor contracts ---


TutorResponseMode = Literal["hint", "explanation", "direct"]


class TutorToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    summary: str
    cited_node_ids: list[str] = Field(default_factory=list)
    cited_edge_ids: list[str] = Field(default_factory=list)


class TutorAskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagram: DiagramDocument
    question: str = Field(..., min_length=1, max_length=500)
    response_mode: TutorResponseMode = "explanation"
    learn_mode: bool = False


class TutorAskResponse(BaseModel):
    grounded: bool
    abstained: bool
    provenance: Literal["deterministic_tools", "ai_grounded_narrator"]
    response_mode: TutorResponseMode
    answer: str
    follow_up: str | None = None
    cited_node_ids: list[str] = Field(default_factory=list)
    cited_edge_ids: list[str] = Field(default_factory=list)
    tool_calls: list[TutorToolCallRecord] = Field(default_factory=list)


class MathIntercept(BaseModel):
    axis: Literal["x", "y"]
    x: float
    y: float
    exact: bool
    note: str


class MathMonotonicInterval(BaseModel):
    start_id: str
    end_id: str
    start_x: float
    end_x: float
    trend: Literal["increasing", "decreasing", "constant"]
    delta_x: float
    delta_y: float
    avg_rate_of_change: float


class MathIntervalSummary(BaseModel):
    start_index: int
    end_index: int
    start_x: float
    end_x: float
    start_y: float
    end_y: float
    delta_x: float
    delta_y: float
    avg_rate_of_change: float
    trend: Literal["increasing", "decreasing", "constant", "mixed"]
    contains_estimated_points: bool
    announcement: str


class MathAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagram: DiagramDocument
    start_index: int | None = Field(default=None, ge=0)
    end_index: int | None = Field(default=None, ge=0)


class MathAnalysisResponse(BaseModel):
    point_count: int
    x_label: str
    x_unit: str
    y_label: str
    y_unit: str
    global_min: MathPlotPoint
    global_max: MathPlotPoint
    local_maxima: list[MathPlotPoint] = Field(default_factory=list)
    local_minima: list[MathPlotPoint] = Field(default_factory=list)
    monotonic_intervals: list[MathMonotonicInterval] = Field(default_factory=list)
    x_intercepts: list[MathIntercept] = Field(default_factory=list)
    y_intercept: MathIntercept | None = None
    interval_summary: MathIntervalSummary | None = None
    summary: str


class MathCsvImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv_text: str = Field(..., min_length=3)
    title: str = Field(default="Imported XY Data Plot", min_length=1)
    x_label: str = Field(default="x", min_length=1)
    x_unit: str = ""
    y_label: str = Field(default="y", min_length=1)
    y_unit: str = ""


class FlowchartTraceStep(BaseModel):
    step_index: int
    node_id: str
    node_label: str
    node_kind: str
    action_description: str
    branch_taken: Literal["true", "false"] | None = None
    variables: dict[str, int | bool] = Field(default_factory=dict)
    next_node_id: str | None = None


class FlowchartTraceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagram: DiagramDocument
    inputs: dict[str, int | bool] | None = None
    max_steps: int | None = Field(default=None, ge=1, le=200)


class FlowchartTraceResponse(BaseModel):
    status: Literal["completed", "max_steps_exceeded"]
    steps_executed: int
    max_steps: int
    final_variables: dict[str, int | bool] = Field(default_factory=dict)
    announcement: str
    steps: list[FlowchartTraceStep] = Field(default_factory=list)


# --- Guided Learning Lab (Phase 5) contracts ---


class ChallengeOption(BaseModel):
    id: str
    label: str


class LearningChallenge(BaseModel):
    id: str
    template: str
    title: str
    prompt: str
    hint: str
    input_type: Literal["single_choice", "multi_choice"]
    options: list[ChallengeOption]
    action_type: Literal["toggle_switch", "remove_organism", "inspect_only"]
    target_id: str | None = None
    scientific_note: str


class LearningChallengeSetResponse(BaseModel):
    available: bool
    unavailable_reason: str | None = None
    domain: DomainType
    challenges: list[LearningChallenge] = Field(default_factory=list)


class LearningEvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagram: DiagramDocument
    challenge_id: str = Field(..., min_length=1)
    selected_option_ids: list[str] = Field(default_factory=list)


class LearningEvaluationResponse(BaseModel):
    challenge_id: str
    correct: bool
    selected_option_ids: list[str]
    expected_option_ids: list[str]
    expected_labels: list[str]
    summary: str
    explanation: str
    evidence: list[str] = Field(default_factory=list)
    related_node_ids: list[str] = Field(default_factory=list)
    simulation_result: SimulationResponse | None = None


# --- Phase 15: Conversational Voice Interaction ---


VoiceIntentType = Literal[
    "navigate",
    "select_subject",
    "select_difficulty",
    "select_lesson",
    "explore_action",
    "experiment_action",
    "select_option",
    "submit_answer",
    "tutor_question",
    "confirm_yes",
    "confirm_no",
    "clarify",
]


class VoiceOptionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str


class VoiceInterpretRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript: str = Field(..., min_length=1, max_length=400)
    step: str = Field(default="welcome", max_length=40)
    domain: str | None = None
    selected_node_id: str | None = None
    challenge_id: str | None = None
    available_options: list[VoiceOptionSummary] = Field(default_factory=list)
    diagram: DiagramDocument | None = None


class VoiceInterpretResponse(BaseModel):
    transcript: str
    intent: VoiceIntentType
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    spoken_response: str
    needs_clarification: bool = False
    confidence: Literal["high", "medium", "low"] = "high"
    tutor_response: TutorAskResponse | None = None
