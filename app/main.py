"""FastAPI backend application for SenseGraph (Phase 1: Core Backend)."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domains import DomainSimulationError
from app.domains.biology import remove_organism
from app.domains.chemistry import get_atom_counts, parse_smiles_to_molecule
from app.domains.flowchart import execute_flowchart
from app.domains.mathematics import analyze_math_plot, parse_csv_to_math_plot
from app.domains.physics import evaluate_circuit_state, toggle_switch
from app.models import (
    DiagramDocument,
    DiagramStateResponse,
    ErrorDetail,
    ErrorEnvelope,
    ExampleSummary,
    FlowchartModel,
    FlowchartTraceRequest,
    FlowchartTraceResponse,
    HealthResponse,
    LearningChallengeSetResponse,
    LearningEvaluateRequest,
    LearningEvaluationResponse,
    LessonDetailResponse,
    LessonMetadata,
    LessonPackagePayload,
    LessonPackageValidationResponse,
    MathAnalysisRequest,
    MathAnalysisResponse,
    MathCsvImportRequest,
    MathPlotModel,
    MoleculeModel,
    SeriesCircuitModel,
    SimulationRequest,
    SimulationResponse,
    SmilesParseRequest,
    TutorAskRequest,
    TutorAskResponse,
    ValidationResponse,
    VoiceInterpretRequest,
    VoiceInterpretResponse,
)
from app.services.ai_vision import (
    GeminiVisionProvider,
    ProviderNotConfiguredError,
    VisionError,
    VisionProvider,
    sanitize_filename,
    validate_uploaded_image,
)
from app.services.description import describe_diagram
from app.services.fixtures import FixtureRepository
from app.services.learning import evaluate_challenge, generate_challenges
from app.services.library import LessonLibrary
from app.services.tutor import TutorNarrator, answer_grounded_question
from app.services.validators import validate_diagram, validate_raw_diagram
from app.services.voice import interpret_voice_command
from app.settings import PROJECT_ROOT, Settings, load_settings


class APIError(Exception):
    """Application-level HTTP error rendered with the standard error envelope."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[str] | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorDetail(code=code, message=message, details=details or [])
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


def create_app(
    settings: Settings | None = None,
    vision_provider: VisionProvider | None = None,
    tutor_narrator: TutorNarrator | None = None,
) -> FastAPI:
    """Create and configure the SenseGraph FastAPI application."""
    active_settings = settings or load_settings()
    fixture_repo = FixtureRepository(active_settings.fixtures_dir)
    lesson_library = LessonLibrary(fixture_repo)
    active_provider: VisionProvider | None = (
        vision_provider
        if vision_provider is not None
        else (GeminiVisionProvider(active_settings) if active_settings.ai_configured else None)
    )

    application = FastAPI(
        title="SenseGraph API",
        version="0.3.0",
        description=(
            "Accessible interactive STEM diagram semantic graph, deterministic "
            "simulation engines, and Gemini Vision extraction backend."
        ),
    )

    application.state.settings = active_settings
    application.state.fixture_repo = fixture_repo
    application.state.vision_provider = active_provider
    logger = logging.getLogger("sensegraph.telemetry")
    analyze_hits: dict[str, deque[float]] = defaultdict(deque)

    def _check_analyze_rate_limit(client_ip: str) -> None:
        now = time.monotonic()
        window = analyze_hits[client_ip]
        while window and (now - window[0]) > 60.0:
            window.popleft()
        if len(window) >= active_settings.analyze_rate_limit_per_min:
            logger.warning("rate_limit_exceeded route=/api/analyze")
            raise APIError(
                status_code=429,
                code="RATE_LIMIT_EXCEEDED",
                message="Too many image analysis requests. Please wait a minute and try again.",
            )
        window.append(now)

    static_dir = PROJECT_ROOT / "app" / "static"
    fixture_images_dir = active_settings.fixtures_dir / "images"
    if static_dir.is_dir():
        application.mount(
            "/static", StaticFiles(directory=str(static_dir)), name="static"
        )
    if fixture_images_dir.is_dir():
        application.mount(
            "/fixtures/images",
            StaticFiles(directory=str(fixture_images_dir)),
            name="fixture-images",
        )

    @application.get("/", include_in_schema=False)
    def serve_index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @application.exception_handler(APIError)
    async def handle_api_error(_request: Request, exc: APIError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message, exc.details)

    @application.exception_handler(DomainSimulationError)
    async def handle_domain_error(
        _request: Request, exc: DomainSimulationError
    ) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message, exc.details)

    @application.exception_handler(VisionError)
    async def handle_vision_error(
        _request: Request, exc: VisionError
    ) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message, exc.details)

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            f"{'.'.join(str(p) for p in err.get('loc', ()))}: {err.get('msg', 'Invalid input')}"
            for err in exc.errors()
        ]
        return _error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request payload failed schema validation.",
            details=details,
        )

    @application.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return _error_response(
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
        )

    @application.get("/api/health", response_model=HealthResponse)
    def get_health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            ai_configured=active_provider is not None,
            supported_domains=list(active_settings.active_domains),
        )

    @application.post("/api/analyze", response_model=DiagramDocument)
    async def post_analyze(
        request: Request,
        file: Annotated[UploadFile, File(...)],
        domain: Annotated[str, Form(...)],
        consent: Annotated[str, Form()] = "false",
    ) -> DiagramDocument:
        client_ip = request.client.host if request.client else "unknown"
        _check_analyze_rate_limit(client_ip)
        allowed_domains = active_settings.active_domains
        if domain not in allowed_domains:
            raise APIError(
                status_code=400,
                code="INVALID_DOMAIN",
                message=(
                    f"Unsupported domain '{domain}'. "
                    f"Choose one of: {', '.join(allowed_domains)}."
                ),
            )

        consent_accepted = consent.strip().lower() in {"true", "1", "yes"}
        if not consent_accepted:
            raise APIError(
                status_code=400,
                code="CONSENT_REQUIRED",
                message=(
                    "Explicit user consent is required before sending an uploaded "
                    "image to an external AI provider."
                ),
            )

        max_bytes = active_settings.max_upload_mb * 1024 * 1024
        # Read at most max_bytes + 1 so oversized uploads are rejected safely without buffering huge files.
        image_bytes = await file.read(max_bytes + 1)
        await file.close()

        canonical_mime = validate_uploaded_image(
            image_bytes=image_bytes,
            declared_mime=file.content_type,
            max_upload_mb=active_settings.max_upload_mb,
        )

        if active_provider is None:
            raise ProviderNotConfiguredError()

        safe_name = sanitize_filename(file.filename)
        return active_provider.extract(
            image_bytes=image_bytes,
            mime_type=canonical_mime,
            domain=domain,  # type: ignore[arg-type]
            filename=safe_name,
        )

    @application.post("/api/state", response_model=DiagramStateResponse)
    def post_state(diagram: DiagramDocument) -> DiagramStateResponse:
        if diagram.domain == "physics_circuit":
            circuit_state = evaluate_circuit_state(diagram)
            return DiagramStateResponse(
                domain="physics_circuit",
                loop_wired=circuit_state.loop_wired,
                all_switches_closed=circuit_state.all_switches_closed,
                bulbs_on=circuit_state.bulbs_on,
                switch_states=circuit_state.switch_states,
                bulb_states=circuit_state.bulb_states,
            )
        if diagram.domain == "biology_food_web":
            return DiagramStateResponse(
                domain="biology_food_web",
                organism_count=len(diagram.nodes),
                relationship_count=len(diagram.edges),
            )
        if diagram.domain == "cs_flowchart":
            assert isinstance(diagram.domain_model, FlowchartModel)
            return DiagramStateResponse(
                domain="cs_flowchart",
                entry_node=diagram.domain_model.entry_node,
                flowchart_inputs=dict(diagram.domain_model.inputs),
                max_steps=diagram.domain_model.max_steps,
            )
        if diagram.domain == "math_plot":
            assert isinstance(diagram.domain_model, MathPlotModel)
            return DiagramStateResponse(
                domain="math_plot",
                point_count=len(diagram.domain_model.points),
                x_label=diagram.domain_model.x_label,
                y_label=diagram.domain_model.y_label,
            )
        assert isinstance(diagram.domain_model, MoleculeModel)
        return DiagramStateResponse(
            domain="chemistry_molecule",
            smiles=diagram.domain_model.smiles,
            formula=diagram.domain_model.formula,
            atom_counts=get_atom_counts(diagram),
        )

    @application.post("/api/chemistry/parse-smiles", response_model=DiagramDocument)
    def post_chemistry_parse_smiles(request: SmilesParseRequest) -> DiagramDocument:
        return parse_smiles_to_molecule(smiles=request.smiles, title=request.title)

    @application.post("/api/flowchart/trace", response_model=FlowchartTraceResponse)
    def post_flowchart_trace(request: FlowchartTraceRequest) -> FlowchartTraceResponse:
        return execute_flowchart(
            diagram=request.diagram,
            initial_inputs=request.inputs,
            max_steps=request.max_steps,
        )

    @application.post("/api/math/analyze", response_model=MathAnalysisResponse)
    def post_math_analyze(request: MathAnalysisRequest) -> MathAnalysisResponse:
        return analyze_math_plot(
            diagram=request.diagram,
            start_index=request.start_index,
            end_index=request.end_index,
        )

    @application.post("/api/math/import-csv", response_model=DiagramDocument)
    def post_math_import_csv(request: MathCsvImportRequest) -> DiagramDocument:
        return parse_csv_to_math_plot(
            csv_text=request.csv_text,
            title=request.title,
            x_label=request.x_label,
            x_unit=request.x_unit,
            y_label=request.y_label,
            y_unit=request.y_unit,
        )

    @application.get("/api/examples", response_model=list[ExampleSummary])
    def list_examples() -> list[ExampleSummary]:
        enabled = set(active_settings.active_domains)
        return [ex for ex in fixture_repo.list_examples() if ex.domain in enabled]

    @application.get("/api/examples/{example_id}", response_model=DiagramDocument)
    def get_example(example_id: str) -> DiagramDocument:
        example = fixture_repo.get_example(example_id)
        if example is None:
            raise APIError(
                status_code=404,
                code="NOT_FOUND",
                message=f"Example diagram '{example_id}' was not found.",
            )
        return example

    @application.post("/api/validate", response_model=ValidationResponse)
    def post_validate(payload: dict[str, Any]) -> ValidationResponse:
        _, result = validate_raw_diagram(payload)
        return result

    @application.post("/api/confirm", response_model=DiagramDocument)
    def post_confirm(diagram: DiagramDocument) -> DiagramDocument:
        validation = validate_diagram(diagram)
        if not validation.valid or not validation.simulation_ready:
            raise APIError(
                status_code=422,
                code="CONFIRMATION_FAILED",
                message="Diagram cannot be confirmed because it failed structural or domain validation.",
                details=validation.errors,
            )

        confirmed = diagram.model_copy(deep=True)
        confirmed.review_status = "confirmed"
        if isinstance(confirmed.domain_model, SeriesCircuitModel):
            confirmed.domain_model.loop_wired = True
        confirmed.summary = describe_diagram(confirmed)
        return confirmed

    @application.post("/api/simulate", response_model=SimulationResponse)
    def post_simulate(request: SimulationRequest) -> SimulationResponse:
        action_type = request.action.type
        target_id = request.action.target_id

        if action_type == "toggle_switch":
            return toggle_switch(request.diagram, target_id)
        if action_type == "remove_organism":
            return remove_organism(request.diagram, target_id)

        raise APIError(
            status_code=400,
            code="INVALID_ACTION",
            message=(
                f"Unsupported action type '{action_type}'. "
                "Supported actions are 'toggle_switch' and 'remove_organism'."
            ),
        )

    @application.post(
        "/api/learning/challenges", response_model=LearningChallengeSetResponse
    )
    def post_learning_challenges(
        diagram: DiagramDocument,
    ) -> LearningChallengeSetResponse:
        return generate_challenges(diagram)

    @application.post(
        "/api/learning/evaluate", response_model=LearningEvaluationResponse
    )
    def post_learning_evaluate(
        request: LearningEvaluateRequest,
    ) -> LearningEvaluationResponse:
        return evaluate_challenge(
            diagram=request.diagram,
            challenge_id=request.challenge_id,
            selected_option_ids=request.selected_option_ids,
        )

    @application.post("/api/tutor/ask", response_model=TutorAskResponse)
    def post_tutor_ask(request: TutorAskRequest) -> TutorAskResponse:
        return answer_grounded_question(
            diagram=request.diagram,
            question=request.question,
            response_mode=request.response_mode,
            learn_mode=request.learn_mode,
            narrator=tutor_narrator,
        )

    @application.post("/api/voice/interpret", response_model=VoiceInterpretResponse)
    def post_voice_interpret(request: VoiceInterpretRequest) -> VoiceInterpretResponse:
        return interpret_voice_command(request, narrator=tutor_narrator)

    @application.get("/api/lessons", response_model=list[LessonMetadata])
    def list_lessons(
        domain: str | None = None,
        difficulty: str | None = None,
        q: str | None = None,
    ) -> list[LessonMetadata]:
        enabled = set(active_settings.active_domains)
        return lesson_library.list_lessons(
            domain=domain,
            difficulty=difficulty,
            query=q,
            enabled_domains=enabled,
        )

    @application.get("/api/lessons/{lesson_id}", response_model=LessonDetailResponse)
    def get_lesson(lesson_id: str) -> LessonDetailResponse:
        detail = lesson_library.get_lesson(lesson_id)
        if detail is None:
            raise APIError(
                status_code=404,
                code="NOT_FOUND",
                message=f"Lesson '{lesson_id}' was not found in the Learning Library.",
            )
        return detail

    @application.post(
        "/api/lessons/validate-package", response_model=LessonPackageValidationResponse
    )
    def post_validate_lesson_package(
        payload: LessonPackagePayload,
    ) -> LessonPackageValidationResponse:
        return lesson_library.validate_lesson_package(payload)

    return application


app = create_app()
