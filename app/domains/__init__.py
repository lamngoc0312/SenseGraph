"""Domain-specific deterministic simulation engines."""


class DomainSimulationError(Exception):
    """Structured error raised when a domain simulation action cannot proceed."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 422,
        details: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
