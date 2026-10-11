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


def test_auth_placeholders_return_501():
    for path in ("/api/auth/register", "/api/auth/login"):
        r = client.post(path, json={})
        assert r.status_code == 501
        assert r.json() == {"detail": "auth not enabled yet"}
