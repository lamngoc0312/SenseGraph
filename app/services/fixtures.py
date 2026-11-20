"""Load and validate bundled pre-annotated demo fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from app.models import DiagramDocument, ExampleSummary
from app.services.validators import validate_diagram
from app.settings import FIXTURES_DIR

BUNDLED_FIXTURE_FILES: tuple[str, ...] = (
    "physics_series.json",
    "biology_food_web.json",
    "cs_flowchart.json",
)


class FixtureRepository:
    """Read-only repository of validated pre-annotated fixture diagrams."""

    def __init__(self, fixtures_dir: Path = FIXTURES_DIR) -> None:
        self._fixtures_dir = fixtures_dir
        self._diagrams: dict[str, DiagramDocument] = {}
        self._load_all()

    def _load_all(self) -> None:
        for filename in BUNDLED_FIXTURE_FILES:
            path = self._fixtures_dir / filename
            if not path.is_file():
                raise FileNotFoundError(f"Bundled fixture file not found: {path}")

            raw = json.loads(path.read_text(encoding="utf-8"))
            diagram = DiagramDocument.model_validate(raw)

            if diagram.source.mode != "fixture":
                raise ValueError(
                    f"Fixture '{filename}' must have source.mode='fixture'."
                )
            if diagram.review_status != "confirmed":
                raise ValueError(
                    f"Fixture '{filename}' must have review_status='confirmed'."
                )

            validation = validate_diagram(diagram)
            if not validation.valid or not validation.simulation_ready:
                raise ValueError(
                    f"Fixture '{filename}' failed validation: {validation.errors}"
                )

            self._diagrams[diagram.id] = diagram

    def list_examples(self) -> list[ExampleSummary]:
        """Return metadata summaries for all bundled fixtures."""
        return [
            ExampleSummary(
                id=doc.id,
                title=doc.title,
                domain=doc.domain,
            )
            for doc in self._diagrams.values()
        ]

    def get_example(self, example_id: str) -> DiagramDocument | None:
        """Return a deep copy of the requested fixture, or None if not found."""
        doc = self._diagrams.get(example_id)
        if doc is None:
            return None
        return doc.model_copy(deep=True)
