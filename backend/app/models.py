"""SQLAlchemy models mapped to the existing jlpt_quiz schema (built by T1)."""
from __future__ import annotations

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(2), default="N1")
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(Text)

    sections: Mapped[list["Section"]] = relationship(back_populates="exam")
    questions: Mapped[list["Question"]] = relationship(back_populates="exam")


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(32))
    name_jp: Mapped[str] = mapped_column(Text)
    name_zh: Mapped[str] = mapped_column(Text)
    time_limit_min: Mapped[int] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer)

    exam: Mapped["Exam"] = relationship(back_populates="sections")


class QuestionGroup(Base):
    __tablename__ = "question_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    section_code: Mapped[str] = mapped_column(String(32))
    group_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer)

    questions: Mapped[list["Question"]] = relationship(back_populates="group")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("question_groups.id", ondelete="SET NULL"), nullable=True
    )
    section_code: Mapped[str] = mapped_column(String(32))
    qtype_code: Mapped[str] = mapped_column(String(32))
    mondai_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    number_in_section: Mapped[int] = mapped_column(Integer)
    stem: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)  # [{key, text}, ...]
    correct_option: Mapped[str] = mapped_column(String(4))
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam: Mapped["Exam"] = relationship(back_populates="questions")
    group: Mapped["QuestionGroup | None"] = relationship(back_populates="questions")
    explanation: Mapped["Explanation | None"] = relationship(
        back_populates="question", uselist=False
    )


class Explanation(Base):
    __tablename__ = "explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), unique=True
    )
    key_point: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_zh: Mapped[str] = mapped_column(Text)
    distractors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    question: Mapped["Question"] = relationship(back_populates="explanation")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    exam_id: Mapped[int | None] = mapped_column(
        ForeignKey("exams.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(16))  # mock | practice
    section_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    qtype_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    time_limit_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[object | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct: Mapped[int | None] = mapped_column(Integer, nullable=True)

    answers: Mapped[list["AttemptAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("attempts.id", ondelete="CASCADE")
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    selected_option: Mapped[str | None] = mapped_column(String(4), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    attempt: Mapped["Attempt"] = relationship(back_populates="answers")
