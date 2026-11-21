"""Tests for Non-Visual Student Experience Redesign & Guided Voice Turn-Taking."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"


def test_default_student_ui_declutters_header_into_settings_drawer():
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text

    # Advanced audio settings & Educator switch are tucked inside a collapsed <details> drawer
    assert '<details id="student-settings-drawer" class="settings-drawer">' in html
    assert 'id="voice-guided-turn-btn"' in html
    assert 'id="voice-shortcut-checkbox"' in html
    # Voice command bar starts hidden on Welcome screen so H1 & 2 choices come first
    assert 'id="voice-command-panel"\n        class="voice-command-panel"\n        aria-label="Spoken conversation and keyboard command bar"\n        hidden' in html


def test_voice_module_enforces_guided_turn_taking_safety_and_bounded_timeout():
    voice_js = (STATIC_DIR / "js" / "voice.js").read_text(encoding="utf-8")
    assert "guidedTurnTaking = false" in voice_js
    assert "listeningTimeoutMs" in voice_js
    assert "playListeningCue" in voice_js
    assert "startGuidedConversation" in voice_js
    assert "stopGuidedConversation" in voice_js
    assert ".innerHTML" not in voice_js

    guidance_js = (STATIC_DIR / "js" / "guidance.js").read_text(encoding="utf-8")
    assert "buildSpokenDialogue" in guidance_js
    assert ".innerHTML" not in guidance_js


def test_voice_stop_listening_and_where_am_i_commands():
    r_stop = client.post(
        "/api/voice/interpret",
        json={"transcript": "Stop listening", "step": "explore"},
    )
    assert r_stop.status_code == 200
    assert r_stop.json()["action"] == "stop_guided_voice"

    r_where = client.post(
        "/api/voice/interpret",
        json={"transcript": "Where am I?", "step": "explore"},
    )
    assert r_where.status_code == 200
    assert r_where.json()["action"] == "where_am_i"


def test_complete_nonvisual_physics_and_biology_conversations():
    """Verify full spoken Physics & Biology lessons using real backend state & engines."""
    # --- Physics complete conversation ---
    phy_detail = client.get("/api/lessons/phy_01_simple_series").json()
    phy_diag = phy_detail["diagram"]

    assert client.post("/api/voice/interpret", json={"transcript": "Next", "step": "explore"}).json()["action"] == "next"
    assert client.post("/api/voice/interpret", json={"transcript": "Explain more", "step": "explore"}).json()["action"] == "tell_me_more"

    qa_phy = client.post(
        "/api/voice/interpret",
        json={"transcript": "Why is the bulb off?", "step": "explore", "domain": "physics_circuit", "diagram": phy_diag},
    ).json()
    assert qa_phy["intent"] == "tutor_question"
    assert qa_phy["tutor_response"]["abstained"] is False

    phy_chals = client.post("/api/learning/challenges", json=phy_diag).json()["challenges"]
    phy_eval = client.post(
        "/api/learning/evaluate",
        json={
            "diagram": phy_diag,
            "challenge_id": phy_chals[0]["id"],
            "selected_option_ids": [phy_chals[0]["options"][0]["id"]],
        },
    ).json()
    assert phy_eval["explanation"]
    assert phy_eval["simulation_result"] is not None

    # --- Biology complete conversation ---
    bio_detail = client.get("/api/lessons/bio_01_simple_chain").json()
    bio_diag = bio_detail["diagram"]

    qa_bio = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "What happens if I remove the deer?",
            "step": "explore",
            "domain": "biology_food_web",
            "diagram": bio_diag,
        },
    ).json()
    assert qa_bio["intent"] == "tutor_question"
    assert qa_bio["tutor_response"]["abstained"] is False

    bio_chals = client.post("/api/learning/challenges", json=bio_diag).json()["challenges"]
    bio_eval = client.post(
        "/api/learning/evaluate",
        json={
            "diagram": bio_diag,
            "challenge_id": bio_chals[0]["id"],
            "selected_option_ids": [bio_chals[0]["options"][0]["id"]],
        },
    ).json()
    assert bio_eval["explanation"]
    assert bio_eval["evidence"]
