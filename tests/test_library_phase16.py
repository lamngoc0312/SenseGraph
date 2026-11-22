"""Phase 16 tests: 20-Lesson Validated STEM Learning Library & Educator Package Validation."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"


def test_learning_library_exposes_20_distinct_validated_lessons_across_5_domains():
    resp = client.get("/api/lessons")
    assert resp.status_code == 200
    lessons = resp.json()
    assert len(lessons) >= 20

    by_domain: dict[str, list[dict]] = {}
    diagram_ids: set[str] = set()
    for lesson in lessons:
        by_domain.setdefault(lesson["domain"], []).append(lesson)
        diagram_ids.add(lesson["diagram_id"])
        assert lesson["review_status"] == "confirmed"
        assert lesson["learning_objectives"]
        assert lesson["lesson_steps"]
        assert lesson["difficulty"] in {"beginner", "intermediate", "advanced"}

    # At least 4 distinct lessons per domain across all 5 STEM domains
    for domain in (
        "physics_circuit",
        "biology_food_web",
        "cs_flowchart",
        "math_plot",
        "chemistry_molecule",
    ):
        assert len(by_domain.get(domain, [])) >= 4, f"Domain {domain} has fewer than 4 lessons"

    # Every lesson must have a distinct diagram_id (no title-only duplicates)
    assert len(diagram_ids) == len(lessons)


def test_every_library_lesson_detail_validates_and_generates_deterministic_challenges():
    lessons = client.get("/api/lessons").json()
    for meta in lessons:
        detail_resp = client.get(f"/api/lessons/{meta['lesson_id']}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        diagram = detail["diagram"]

        val_resp = client.post("/api/validate", json=diagram)
        assert val_resp.status_code == 200
        val = val_resp.json()
        assert val["valid"] is True, f"{meta['lesson_id']}: {val['errors']}"
        assert val["simulation_ready"] is True, f"{meta['lesson_id']}: {val['errors']}"

        chal_resp = client.post("/api/learning/challenges", json=diagram)
        assert chal_resp.status_code == 200
        assert chal_resp.json()["available"] is True
        assert len(chal_resp.json()["challenges"]) >= 1


def test_library_filtering_by_domain_difficulty_and_search():
    phy = client.get("/api/lessons?domain=physics_circuit").json()
    assert len(phy) >= 4
    assert all(item["domain"] == "physics_circuit" for item in phy)

    beg = client.get("/api/lessons?difficulty=beginner").json()
    assert len(beg) >= 5
    assert all(item["difficulty"] == "beginner" for item in beg)

    search = client.get("/api/lessons?q=methane").json()
    assert len(search) == 1
    assert search[0]["lesson_id"] == "chem_02_methane"


def test_educator_lesson_package_validation_blocks_unreviewed_and_accepts_confirmed():
    detail = client.get("/api/lessons/phy_01_simple_series").json()
    valid_resp = client.post("/api/lessons/validate-package", json=detail)
    assert valid_resp.status_code == 200
    assert valid_resp.json()["valid"] is True

    # Unreviewed AI diagram MUST be rejected
    unreviewed = {
        "lesson": {**detail["lesson"], "review_status": "confirmed"},
        "diagram": {**detail["diagram"], "review_status": "unreviewed"},
    }
    bad_resp = client.post("/api/lessons/validate-package", json=unreviewed)
    assert bad_resp.status_code == 200
    assert bad_resp.json()["valid"] is False
    assert any("unreviewed" in err.lower() for err in bad_resp.json()["errors"])


def test_phase16_frontend_library_module_and_controls():
    lib_js = (STATIC_DIR / "js" / "library.js").read_text(encoding="utf-8")
    for cls_name in (
        "class ProgressStore",
        "class LessonLibraryController",
        "class EducatorPackageTool",
    ):
        assert cls_name in lib_js
    assert ".innerHTML" not in lib_js
