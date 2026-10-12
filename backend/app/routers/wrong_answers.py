"""錯題本（需登錄）：列表 / 標記掌握 / 刪除 / 錯題重練。"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..auth import get_current_user
from ..db import get_db
from ..serializers import explanation_to_out, question_to_out

router = APIRouter()


def _wrong_answer_to_out(wa: models.WrongAnswer) -> schemas.WrongAnswerItem:
    q = wa.question
    return schemas.WrongAnswerItem(
        id=wa.id,
        question=question_to_out(q),
        correct_option=q.correct_option,
        explanation=explanation_to_out(q.explanation, q.vocabulary),
        wrong_count=wa.wrong_count,
        mastered=wa.mastered,
        mastered_at=wa.mastered_at,
        review_count=wa.review_count,
        last_reviewed_at=wa.last_reviewed_at,
        created_at=wa.created_at,
    )


def _get_owned(wa_id: int, user: models.User, db: Session) -> models.WrongAnswer:
    wa = (
        db.query(models.WrongAnswer)
        .options(
            joinedload(models.WrongAnswer.question).joinedload(models.Question.explanation),
            joinedload(models.WrongAnswer.question).joinedload(models.Question.vocabulary),
            joinedload(models.WrongAnswer.question).joinedload(models.Question.group),
        )
        .filter_by(id=wa_id, user_id=user.id)
        .first()
    )
    if wa is None:
        raise HTTPException(status_code=404, detail="錯題不存在")
    return wa


@router.get("/wrong-answers", response_model=list[schemas.WrongAnswerItem])
def list_wrong_answers(
    mastered: bool | None = None,
    qtype_code: str | None = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.WrongAnswer)
        .options(
            joinedload(models.WrongAnswer.question).joinedload(models.Question.explanation),
            joinedload(models.WrongAnswer.question).joinedload(models.Question.vocabulary),
            joinedload(models.WrongAnswer.question).joinedload(models.Question.group),
        )
        .filter_by(user_id=user.id)
    )
    if mastered is not None:
        q = q.filter(models.WrongAnswer.mastered == mastered)
    if qtype_code:
        q = q.join(models.Question, models.WrongAnswer.question_id == models.Question.id).filter(
            models.Question.qtype_code == qtype_code
        )
    rows = q.order_by(models.WrongAnswer.created_at.desc()).all()
    return [_wrong_answer_to_out(wa) for wa in rows]


@router.post("/wrong-answers/{wa_id}/master", response_model=schemas.WrongAnswerItem)
def mark_mastered(
    wa_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wa = _get_owned(wa_id, user, db)
    wa.mastered = True
    wa.mastered_at = datetime.now(timezone.utc)
    db.commit()
    return _wrong_answer_to_out(wa)


@router.post("/wrong-answers/{wa_id}/unmaster", response_model=schemas.WrongAnswerItem)
def mark_unmastered(
    wa_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wa = _get_owned(wa_id, user, db)
    wa.mastered = False
    wa.mastered_at = None
    db.commit()
    return _wrong_answer_to_out(wa)


@router.delete("/wrong-answers/{wa_id}")
def delete_wrong_answer(
    wa_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wa = _get_owned(wa_id, user, db)
    db.delete(wa)
    db.commit()
    return {"deleted": True, "id": wa_id}


@router.post("/wrong-answers/practice", response_model=schemas.WrongPracticeOut)
def start_wrong_practice(
    payload: schemas.WrongPracticeIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qids = list(dict.fromkeys(payload.question_ids))  # 去重保序
    owned = {
        r[0]
        for r in db.query(models.WrongAnswer.question_id)
        .filter(
            models.WrongAnswer.user_id == user.id,
            models.WrongAnswer.question_id.in_(qids),
        )
        .all()
    }
    missing = [i for i in qids if i not in owned]
    if missing:
        raise HTTPException(
            status_code=400, detail=f"以下題目不在你的錯題本中：{missing}"
        )
    questions = (
        db.query(models.Question)
        .options(
            joinedload(models.Question.explanation),
            joinedload(models.Question.vocabulary),
            joinedload(models.Question.group),
        )
        .filter(models.Question.id.in_(qids))
        .all()
    )
    by_id = {q.id: q for q in questions}
    ordered = [by_id[i] for i in qids if i in by_id]

    att = models.Attempt(
        user_id=user.id,
        exam_id=None,  # 錯題可跨卷；submit 時跳過 exam 一致性校驗
        mode="practice",
        section_code="wrong_review",
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return schemas.WrongPracticeOut(
        attempt_id=att.id,
        questions=[question_to_out(q) for q in ordered],
    )
