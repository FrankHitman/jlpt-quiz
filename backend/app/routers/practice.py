"""Practice (by question type) endpoints — no countdown, no answers."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..db import get_db
from ..serializers import question_to_out

router = APIRouter()


@router.get("/practice/questions", response_model=list[schemas.QuestionOut])
def practice_questions(
    qtype_code: str | None = Query(default=None),
    exam_id: int | None = Query(default=None),
    section: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Filter questions by type/exam/section — never includes correct_option."""
    q = db.query(models.Question).options(joinedload(models.Question.group))
    if qtype_code:
        q = q.filter(models.Question.qtype_code == qtype_code)
    if exam_id is not None:
        q = q.filter(models.Question.exam_id == exam_id)
    if section:
        q = q.filter(models.Question.section_code == section)
    questions = (
        q.order_by(models.Question.exam_id, models.Question.number_in_section)
        .limit(limit)
        .all()
    )
    return [question_to_out(x) for x in questions]
