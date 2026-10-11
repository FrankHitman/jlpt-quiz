"""Attempt lifecycle: create -> submit -> view result."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..auth import get_current_user_optional
from ..db import get_db
from ..serializers import explanation_to_out

router = APIRouter()


def _is_overtime(att: models.Attempt) -> bool:
    """True when submitted after the time limit (grading still applies)."""
    if not att.time_limit_min or att.started_at is None or att.submitted_at is None:
        return False
    started = att.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    submitted = att.submitted_at
    if submitted.tzinfo is None:
        submitted = submitted.replace(tzinfo=timezone.utc)
    return (submitted - started).total_seconds() > att.time_limit_min * 60


@router.post("/attempts", response_model=schemas.AttemptCreated)
def create_attempt(
    payload: schemas.AttemptCreate,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_current_user_optional),
):
    time_limit: int | None = None
    if payload.exam_id is not None:
        exam = db.get(models.Exam, payload.exam_id)
        if exam is None:
            raise HTTPException(status_code=404, detail="exam not found")
        if payload.mode == "mock" and payload.section_code:
            sec = (
                db.query(models.Section)
                .filter_by(exam_id=payload.exam_id, code=payload.section_code)
                .first()
            )
            if sec is None:
                raise HTTPException(
                    status_code=400, detail=f"unknown section: {payload.section_code}"
                )
            time_limit = sec.time_limit_min

    att = models.Attempt(
        user_id=user_id,  # None until auth is enabled
        exam_id=payload.exam_id,
        mode=payload.mode,
        section_code=payload.section_code,
        qtype_code=payload.qtype_code,
        time_limit_min=time_limit,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return schemas.AttemptCreated(
        attempt_id=att.id, time_limit_min=att.time_limit_min
    )


@router.post("/attempts/{attempt_id}/submit", response_model=schemas.SubmitResult)
def submit_attempt(
    attempt_id: int,
    payload: schemas.SubmitIn,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_current_user_optional),
):
    att = db.get(models.Attempt, attempt_id)
    if att is None:
        raise HTTPException(status_code=404, detail="attempt not found")
    if att.submitted_at is not None:
        raise HTTPException(status_code=400, detail="attempt already submitted")
    if not payload.answers:
        raise HTTPException(status_code=400, detail="no answers submitted")

    now = datetime.now(timezone.utc)
    per: list[schemas.PerQuestionResult] = []
    correct = 0

    for ans in payload.answers:
        q = (
            db.query(models.Question)
            .options(joinedload(models.Question.explanation))
            .filter(models.Question.id == ans.question_id)
            .first()
        )
        if q is None:
            raise HTTPException(
                status_code=404, detail=f"question not found: {ans.question_id}"
            )
        if att.exam_id is not None and q.exam_id != att.exam_id:
            raise HTTPException(
                status_code=400,
                detail=f"question {ans.question_id} does not belong to this attempt",
            )
        is_ok = ans.selected_option is not None and ans.selected_option == q.correct_option
        if is_ok:
            correct += 1
        aa = (
            db.query(models.AttemptAnswer)
            .filter_by(attempt_id=att.id, question_id=q.id)
            .first()
        )
        if aa is None:
            db.add(
                models.AttemptAnswer(
                    attempt_id=att.id,
                    question_id=q.id,
                    selected_option=ans.selected_option,
                    is_correct=is_ok,
                )
            )
        else:
            aa.selected_option = ans.selected_option
            aa.is_correct = is_ok
        per.append(
            schemas.PerQuestionResult(
                question_id=q.id,
                selected_option=ans.selected_option,
                correct_option=q.correct_option,
                is_correct=is_ok,
                explanation=explanation_to_out(q.explanation),
            )
        )

    total = len(payload.answers)
    accuracy = round(correct / total * 100, 1) if total else 0.0
    att.submitted_at = now
    att.total = total
    att.correct = correct
    db.commit()

    wrong_ids = [p.question_id for p in per if not p.is_correct]
    return schemas.SubmitResult(
        total=total,
        correct=correct,
        accuracy=accuracy,
        per_question=per,
        wrong_question_ids=wrong_ids,
        overtime=_is_overtime(att),
    )


@router.get("/attempts/{attempt_id}", response_model=schemas.AttemptDetail)
def get_attempt(attempt_id: int, db: Session = Depends(get_db)):
    att = db.get(models.Attempt, attempt_id)
    if att is None:
        raise HTTPException(status_code=404, detail="attempt not found")

    detail = schemas.AttemptDetail(
        attempt_id=att.id,
        exam_id=att.exam_id,
        mode=att.mode,
        section_code=att.section_code,
        qtype_code=att.qtype_code,
        time_limit_min=att.time_limit_min,
        started_at=att.started_at,
        submitted_at=att.submitted_at,
        submitted=att.submitted_at is not None,
        total=att.total,
        correct=att.correct,
    )
    if att.submitted_at is None:
        # Not submitted yet: do not reveal answers or explanations.
        return detail

    rows = (
        db.query(models.AttemptAnswer, models.Question)
        .join(models.Question, models.AttemptAnswer.question_id == models.Question.id)
        .options(joinedload(models.Question.explanation))
        .filter(models.AttemptAnswer.attempt_id == att.id)
        .order_by(models.Question.number_in_section)
        .all()
    )
    per = [
        schemas.PerQuestionResult(
            question_id=q.id,
            selected_option=aa.selected_option,
            correct_option=q.correct_option,
            is_correct=bool(aa.is_correct),
            explanation=explanation_to_out(q.explanation),
        )
        for aa, q in rows
    ]
    detail.per_question = per
    detail.wrong_question_ids = [p.question_id for p in per if not p.is_correct]
    detail.accuracy = round(att.correct / att.total * 100, 1) if att.total else 0.0
    detail.overtime = _is_overtime(att)
    return detail
