"""Phase 17 End-to-End Acceptance Tests: Complete Voice & Keyboard Student Journeys."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"


def test_e2e_voice_guided_physics_learning_journey():
    """Complete voice-guided journey: Welcome -> Physics -> Beginner -> Explore -> Q&A -> Experiment -> Next."""
    # 1. Student opens SenseGraph
    home = client.get("/")
    assert home.status_code == 200
    assert 'id="student-context-guide"' in home.text
    assert 'id="guide-where"' in home.text
    assert 'id="student-visual-details"' in home.text
    assert "/static/js/guidance.js" in home.text

    # 2. Student says "Start learning"
    r_start = client.post(
        "/api/voice/interpret",
        json={"transcript": "Start learning", "step": "welcome"},
    )
    assert r_start.status_code == 200
    assert r_start.json()["action"] == "start_learning"

    # 3. Student says "Physics"
    r_phy = client.post(
        "/api/voice/interpret",
        json={"transcript": "Physics", "step": "subjects"},
    )
    assert r_phy.status_code == 200
    assert r_phy.json()["action"] == "select_subject"
    assert r_phy.json()["parameters"]["domain"] == "physics_circuit"

    # 4. Student says "Beginner" -> loads first Physics beginner lesson
    r_beg = client.post(
        "/api/voice/interpret",
        json={"transcript": "Beginner", "step": "subjects", "domain": "physics_circuit"},
    )
    assert r_beg.status_code == 200
    assert r_beg.json()["parameters"]["difficulty"] == "beginner"

    lessons = client.get("/api/lessons?domain=physics_circuit&difficulty=beginner").json()
    assert len(lessons) >= 2
    first_lesson = lessons[0]
    detail = client.get(f"/api/lessons/{first_lesson['lesson_id']}").json()
    diagram = detail["diagram"]

    # 5. Student asks a scientific question verbally -> Evidence-Grounded Tutor
    r_qa = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "Why is the bulb off?",
            "step": "explore",
            "domain": "physics_circuit",
            "diagram": diagram,
        },
    )
    assert r_qa.status_code == 200
    assert r_qa.json()["intent"] == "tutor_question"
    assert r_qa.json()["tutor_response"]["abstained"] is False

    # 6. Student starts experiment, selects option verbally, and submits to real Python engine
    challenges = client.post("/api/learning/challenges", json=diagram).json()["challenges"]
    challenge = challenges[0]
    options = [{"id": o["id"], "label": o["label"]} for o in challenge["options"]]

    r_opt = client.post(
        "/api/voice/interpret",
        json={
            "transcript": "Option one",
            "step": "experiment",
            "domain": "physics_circuit",
            "challenge_id": challenge["id"],
            "available_options": options,
        },
    )
    assert r_opt.status_code == 200
    chosen_id = r_opt.json()["parameters"]["option_id"]

    r_sub = client.post(
        "/api/voice/interpret",
        json={"transcript": "Submit my answer", "step": "experiment"},
    )
    assert r_sub.status_code == 200
    assert r_sub.json()["action"] == "submit_answer"

    eval_resp = client.post(
        "/api/learning/evaluate",
        json={
            "diagram": diagram,
            "challenge_id": challenge["id"],
            "selected_option_ids": [chosen_id],
        },
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["summary"]
    assert eval_data["explanation"]
    assert eval_data["evidence"]

    # 7. Student says "Next lesson" -> advances to second Physics lesson (closed switch)
    r_next = client.post(
        "/api/voice/interpret",
        json={"transcript": "Next lesson", "step": "summary"},
    )
    assert r_next.status_code == 200
    assert r_next.json()["action"] == "next_lesson"

    second_detail = client.get(f"/api/lessons/{lessons[1]['lesson_id']}").json()
    second_state = client.post("/api/state", json=second_detail["diagram"]).json()
    assert second_state["bulbs_on"] is True


def test_e2e_keyboard_only_journey_without_voice_biology_and_chemistry():
    """Verify full non-voice workflow works identically across Biology and Chemistry."""
    for lesson_id in ("bio_01_simple_chain", "chem_01_water"):
        detail = client.get(f"/api/lessons/{lesson_id}").json()
        diagram = detail["diagram"]
        state = client.post("/api/state", json=diagram).json()
        assert state["domain"] == diagram["domain"]

        chals = client.post("/api/learning/challenges", json=diagram).json()
        assert chals["available"] is True
        first = chals["challenges"][0]
        eval_resp = client.post(
            "/api/learning/evaluate",
            json={
                "diagram": diagram,
                "challenge_id": first["id"],
                "selected_option_ids": [first["options"][0]["id"]],
            },
        )
        assert eval_resp.status_code == 200
        assert eval_resp.json()["explanation"]


def test_phase17_guidance_module_is_safe_and_modular():
    guidance_js = (STATIC_DIR / "js" / "guidance.js").read_text(encoding="utf-8")
    assert "buildContextualGuidance" in guidance_js
    assert ".innerHTML" not in guidance_js
