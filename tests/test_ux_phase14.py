"""Phase 14 tests: Audio-First Student Experience, Experience Switcher, and Accessibility."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"


def test_student_experience_is_default_and_educator_is_preserved():
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text

    # Student Experience visible by default; Educator welcome hidden by default
    assert 'id="student-section"' in html
    assert 'id="welcome-section" class="welcome-section" aria-labelledby="welcome-heading" hidden' in html

    # Experience Switcher
    assert 'id="exp-student-btn"' in html
    assert 'id="exp-educator-btn"' in html

    # All 5 Student Experience stages + stepper + help dialog
    for element_id in (
        "student-stepper",
        "student-help-dialog",
        "student-step-welcome",
        "student-step-subjects",
        "student-step-explore",
        "student-step-experiment",
        "student-step-summary",
        "student-mini-svg",
        "student-start-sr-btn",
        "student-start-voice-btn",
        "student-prev-comp-btn",
        "student-next-comp-btn",
        "student-go-experiment-btn",
        "student-exp-form",
        "student-sum-next-lesson-btn",
    ):
        assert f'id="{element_id}"' in html, f"Missing Phase 14 element: {element_id}"

    # Existing Educator / Advanced DOM IDs preserved without regression
    for legacy_id in (
        "analyze-form",
        "review-section",
        "explorer-section",
        "learning-lab-panel",
        "semantic-graph-svg",
        "tutor-form",
        "math-csv-input",
        "chem-smiles-input",
    ):
        assert f'id="{legacy_id}"' in html, f"Missing preserved Educator element: {legacy_id}"


def test_audio_guidance_bar_is_off_by_default_and_never_autoplays():
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text

    assert 'id="audio-start-btn" class="btn btn-teal btn-sm" aria-pressed="false"' in html
    for audio_id in (
        "audio-pause-btn",
        "audio-stop-btn",
        "audio-repeat-btn",
        "audio-rate-select",
        "audio-voice-select",
        "audio-mode-status",
    ):
        assert f'id="{audio_id}"' in html

    js_source = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "spokenGuidanceEnabled: false" in js_source
    assert "beforeunload" in js_source
    assert ".innerHTML" not in js_source
    assert "setExperience(" in js_source
    assert "startStudentLesson(" in js_source
    assert "handleStudentExperimentSubmit(" in js_source


def test_phase14_css_preserves_accessibility_primitives():
    css = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")
    assert "[hidden]" in css
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert ".student-card" in css
    assert ".audio-bar" in css
    assert ".experience-switcher" in css
