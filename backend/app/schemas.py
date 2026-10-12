"""Pydantic response/request schemas for the JLPT quiz API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ---------- shared ----------

class OptionItem(BaseModel):
    key: str
    text: str


class GroupOut(BaseModel):
    id: int
    group_type: str
    title: str | None = None
    content: str
    sort_order: int


class QuestionOut(BaseModel):
    """Question for answering — NEVER includes correct_option."""

    id: int
    exam_id: int
    section_code: str
    qtype_code: str
    mondai_no: int | None = None
    number_in_section: int
    stem: str
    target_text: str | None = None
    options: list[OptionItem]
    audio_url: str | None = None
    group: GroupOut | None = None


# ---------- exams ----------

class SectionSummary(BaseModel):
    code: str
    name_zh: str
    time_limit_min: int
    question_count: int
    has_audio: bool = False


class ExamListItem(BaseModel):
    id: int
    level: str
    year: int
    month: int
    title: str
    sections: list[SectionSummary]


class QTypeStat(BaseModel):
    qtype_code: str
    count: int


class SectionDetail(BaseModel):
    code: str
    name_jp: str
    name_zh: str
    time_limit_min: int
    question_count: int
    qtype_stats: list[QTypeStat]


class ExamDetail(BaseModel):
    id: int
    level: str
    year: int
    month: int
    title: str
    sections: list[SectionDetail]


# ---------- attempts ----------

class AttemptCreate(BaseModel):
    exam_id: int | None = None
    mode: str = Field(pattern="^(mock|practice)$")
    section_code: str | None = None
    qtype_code: str | None = None
    question_ids: list[int] | None = None


class AttemptCreated(BaseModel):
    attempt_id: int
    time_limit_min: int | None = None


class AnswerIn(BaseModel):
    question_id: int
    selected_option: str | None = None


class SubmitIn(BaseModel):
    answers: list[AnswerIn]


class VocabularyOut(BaseModel):
    word: str
    reading: str | None = None
    meaning_zh: str | None = None
    etymology_en: str | None = None


class ExplanationOut(BaseModel):
    key_point: str | None = None
    analysis_zh: str
    distractors: list[Any] | None = None
    evidence: str | None = None
    option_readings: dict[str, str] | None = None
    vocabulary: list[VocabularyOut] = []


class PerQuestionResult(BaseModel):
    question_id: int
    selected_option: str | None = None
    correct_option: str
    is_correct: bool
    explanation: ExplanationOut


class SubmitResult(BaseModel):
    total: int
    correct: int
    accuracy: float  # percentage, 0-100, 1 decimal
    per_question: list[PerQuestionResult]
    wrong_question_ids: list[int]
    overtime: bool = False


class AttemptDetail(BaseModel):
    attempt_id: int
    exam_id: int | None = None
    mode: str
    section_code: str | None = None
    qtype_code: str | None = None
    time_limit_min: int | None = None
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    submitted: bool = False
    total: int | None = None
    correct: int | None = None
    accuracy: float | None = None
    overtime: bool = False
    per_question: list[PerQuestionResult] = []
    wrong_question_ids: list[int] = []


# ---------- auth ----------

class AuthIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    id: int
    username: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


# ---------- wrong answers （錯題本） ----------

class WrongAnswerItem(BaseModel):
    id: int
    question: QuestionOut
    correct_option: str
    explanation: ExplanationOut
    wrong_count: int
    mastered: bool
    mastered_at: datetime | None = None
    review_count: int
    last_reviewed_at: datetime | None = None
    created_at: datetime | None = None


class WrongPracticeIn(BaseModel):
    question_ids: list[int] = Field(min_length=1, max_length=100)


class WrongPracticeOut(BaseModel):
    attempt_id: int
    questions: list[QuestionOut]
