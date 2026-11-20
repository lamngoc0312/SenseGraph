"""FastAPI backend application for SenseGraph (Phase 1: Core Backend)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domains import DomainSimulationError
from app.domains.biology import remove_organism
from app.domains.physics import toggle_switch
from app.models import (
    DiagramDocument,
    ErrorDetail,
    ErrorEnvelope,
    ExampleSummary,
    HealthResponse,
    SeriesCircuitModel,
    SimulationRequest,
    SimulationResponse,
    ValidationResponse,
)
from app.services.description import describe_diagram
from app.services.fixtures import FixtureRepository
from app.services.validators import validate_diagram, validate_raw_diagram
from app.settings import PROJECT_ROOT, SUPPORTED_DOMAINS, Settings, load_settings


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


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the SenseGraph FastAPI application."""
    active_settings = settings or load_settings()
    fixture_repo = FixtureRepository(active_settings.fixtures_dir)

    application = FastAPI(
        title="SenseGraph API",
        version="0.1.0",
        description=(
            "Accessible interactive STEM diagram semantic graph and deterministic "
            "simulation backend (Phase 1: Physics P0 and Biology P0)."
        ),
    )

    application.state.settings = active_settings
    application.state.fixture_repo = fixture_repo

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
            ai_configured=active_settings.ai_configured,
            supported_domains=list(SUPPORTED_DOMAINS),
        )

    @application.get("/api/examples", response_model=list[ExampleSummary])
    def list_examples() -> list[ExampleSummary]:
        return fixture_repo.list_examples()

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

    return application


app = create_app()
