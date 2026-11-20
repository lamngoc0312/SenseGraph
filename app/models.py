"""Pydantic data contracts matching contracts/diagram.schema.json and REST API payloads."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ID_PATTERN = r"^[A-Za-z][A-Za-z0-9_-]*$"

DomainType = Literal["physics_circuit", "biology_food_web"]
SourceMode = Literal["fixture", "ai"]
ReviewStatus = Literal["unreviewed", "confirmed"]
NodeKind = Literal["battery", "switch", "bulb", "organism"]
EdgeRelation = Literal["wire", "energy_to"]
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


DomainModel = Annotated[
    SeriesCircuitModel | FoodWebModel,
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
