"""Phase 15 tests: Conversational Voice Interaction, Intent Parser, and Tutor Routing."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"


def _get_fixture(fixture_id: str) -> dict:
    resp = client.get(f"/api/examples/{fixture_id}")
    assert resp.status_code == 200
    return resp.json()


def test_voice_navigation_and_subject_commands():
    cases = [
        ("Start learning", "navigate", "start_learning"),
        ("Show Physics lessons", "select_subject", "select_subject"),
        ("Open Biology", "select_subject", "select_subject"),
        ("Beginner", "select_difficulty", "select_difficulty"),
        ("Next", "navigate", "next"),
        ("Previous", "navigate", "previous"),
        ("Repeat", "navigate", "repeat"),
        ("Help", "navigate", "help"),
        ("Go back", "navigate", "go_back"),
        ("Continue learning", "navigate", "continue_learning"),
    ]
    for transcript, expected_intent, expected_action in cases:
        resp = client.post(
            "/api/voice/interpret",
            json={"transcript": transcript, "step": "subjects"},
        )
        assert resp.status_code == 200, transcript
        data = resp.json()
        assert data["intent"] == expected_intent
        assert data["action"] == expected_action
        assert data["spoken_response"]


def test_voice_exploration_and_experiment_option_selection():
    # Exploration commands
    for transcript, action in (
        ("What is this?", "explain_component"),
        ("Explain the diagram", "explain_diagram"),
        ("Tell me more", "tell_me_more"),
        ("Start experiment", "start_experiment"),
        ("Submit my answer", "submit_answer"),
        ("Try again", "try_again"),
        ("Next lesson", "next_lesson"),
    ):
        resp = client.post(
            "/api/voice/interpret",
            json={"transcript": transcript, "step": "explore"},
        )
        assert resp.status_code == 200
        assert resp.json()["action"] == action

    # Option matching during experiment step (ordinal + natural phrase)
    options = [
        {"id": "bulb_on", "label": "The bulb will turn on"},
        {"id": "bulb_off", "label": "The bulb will stay off"},
    ]
    r_ord = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "Option one",
            "step": "experiment",
            "available_options": options,
        },
    )
    assert r_ord.status_code == 200
    assert r_ord.json()["intent"] == "select_option"
    assert r_ord.json()["parameters"]["option_id"] == "bulb_on"

    r_phrase = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "The bulb will stay off",
            "step": "experiment",
            "available_options": options,
        },
    )
    assert r_phrase.status_code == 200
    assert r_phrase.json()["intent"] == "select_option"
    assert r_phrase.json()["parameters"]["option_id"] == "bulb_off"


def test_voice_scientific_questions_route_to_evidence_grounded_tutor():
    physics = _get_fixture("physics_series")
    resp = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "Why is the bulb off?",
            "step": "explore",
            "domain": "physics_circuit",
            "diagram": physics,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "tutor_question"
    assert data["tutor_response"] is not None
    assert data["tutor_response"]["abstained"] is False
    assert "bulb_1" in data["spoken_response"].lower()
    assert "all_switches_closed=false" in data["spoken_response"].lower()

    # Out-of-scope quantitative question must abstain honestly
    oos = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "What is the voltage of the battery?",
            "step": "explore",
            "domain": "physics_circuit",
            "diagram": physics,
        },
    )
    assert oos.status_code == 200
    assert oos.json()["tutor_response"]["abstained"] is True

    # Biology feeding direction question
    biology = _get_fixture("biology_food_web")
    bio_q = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "What happens if I remove the rabbit?",
            "step": "explore",
            "domain": "biology_food_web",
            "diagram": biology,
        },
    )
    assert bio_q.status_code == 200
    assert bio_q.json()["intent"] == "tutor_question"
    assert bio_q.json()["tutor_response"]["abstained"] is False


def test_voice_uncertain_command_requests_clarification():
    resp = client.post(
        "/api/voice/interpret",
        json={"transcript": "purple elephant sandwich", "step": "welcome"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "clarify"
    assert data["needs_clarification"] is True
    assert data["confidence"] == "low"


def test_phase15_frontend_voice_module_and_push_to_talk_markup():
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    for el_id in (
        "voice-ptt-btn",
        "voice-cancel-btn",
        "voice-mic-status",
        "voice-command-panel",
        "voice-text-form",
        "voice-text-input",
        "voice-transcript-box",
    ):
        assert f'id="{el_id}"' in html
    assert "/static/js/voice.js" in html

    voice_js = (STATIC_DIR / "js" / "voice.js").read_text(encoding="utf-8")
    for cls_name in (
        "class SpeechInputAdapter",
        "class SpeechOutputAdapter",
        "class VoiceCommandInterpreter",
        "class LearningSessionController",
        "class ConversationController",
    ):
        assert cls_name in voice_js
    assert ".innerHTML" not in voice_js
