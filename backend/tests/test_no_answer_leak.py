"""Security test: answering endpoints must never leak correct_option."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _exam_id() -> int:
    r = client.get("/api/exams")
    assert r.status_code == 200
    exams = r.json()
    assert exams, "no exams in DB"
    return exams[0]["id"]


def test_exam_questions_never_leak_answer():
    eid = _exam_id()
    r = client.get(f"/api/exams/{eid}/questions", params={"section": "lang_reading"})
    assert r.status_code == 200
    questions = r.json()
    assert questions, "expected questions for section lang_reading"
    for q in questions:
        assert "correct_option" not in q, f"answer leaked in question {q['id']}"
        assert "correct_option" not in q.get("stem", "")
        group = q.get("group")
        if group:
            assert "correct_option" not in str(group)


def test_exam_questions_all_sections_never_leak_answer():
    eid = _exam_id()
    r = client.get(f"/api/exams/{eid}/questions")  # no section filter
    assert r.status_code == 200
    for q in r.json():
        assert "correct_option" not in q, f"answer leaked in question {q['id']}"


def test_practice_questions_never_leak_answer():
    r = client.get(
        "/api/practice/questions", params={"qtype_code": "grammar_fill", "limit": 5}
    )
    assert r.status_code == 200
    for q in r.json():
        assert "correct_option" not in q, f"answer leaked in question {q['id']}"


def test_auth_register_login_flow():
    uname = "pytest_user_auth"
    # 註冊成功回 token
    r = client.post(
        "/api/auth/register", json={"username": uname, "password": "pytest123"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token"] and body["user"]["username"] == uname
    token = body["token"]
    # 重複註冊 400
    r = client.post(
        "/api/auth/register", json={"username": uname, "password": "pytest123"}
    )
    assert r.status_code == 400
    # 錯誤密碼 401
    r = client.post(
        "/api/auth/login", json={"username": uname, "password": "wrongpass"}
    )
    assert r.status_code == 401
    # 登入成功
    r = client.post(
        "/api/auth/login", json={"username": uname, "password": "pytest123"}
    )
    assert r.status_code == 200
    # me 需 token
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == uname
    # 錯題本未登入 401
    assert client.get("/api/wrong-answers").status_code == 401
