"""Exam / question listing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..db import get_db
from ..serializers import question_to_out

router = APIRouter()


@router.get("/exams", response_model=list[schemas.ExamListItem])
def list_exams(db: Session = Depends(get_db)):
    exams = (
        db.query(models.Exam)
        .order_by(models.Exam.year.desc(), models.Exam.month.desc())
        .all()
    )
    out: list[schemas.ExamListItem] = []
    for e in exams:
        sections = (
            db.query(models.Section)
            .filter_by(exam_id=e.id)
            .order_by(models.Section.sort_order)
            .all()
        )
        sec_out = []
        for s in sections:
            cnt = (
                db.query(func.count(models.Question.id))
                .filter(
                    models.Question.exam_id == e.id,
                    models.Question.section_code == s.code,
                )
                .scalar()
            )
            sec_out.append(
                schemas.SectionSummary(
                    code=s.code,
                    name_zh=s.name_zh,
                    time_limit_min=s.time_limit_min,
                    question_count=cnt or 0,
                )
            )
        out.append(
            schemas.ExamListItem(
                id=e.id,
                level=e.level,
                year=e.year,
                month=e.month,
                title=e.title,
                sections=sec_out,
            )
        )
    return out


@router.get("/exams/{exam_id}", response_model=schemas.ExamDetail)
def exam_detail(exam_id: int, db: Session = Depends(get_db)):
    e = db.get(models.Exam, exam_id)
    if e is None:
        raise HTTPException(status_code=404, detail="exam not found")
    sections = (
        db.query(models.Section)
        .filter_by(exam_id=e.id)
        .order_by(models.Section.sort_order)
        .all()
    )
    sec_out = []
    for s in sections:
        stats = (
            db.query(models.Question.qtype_code, func.count(models.Question.id))
            .filter(
                models.Question.exam_id == e.id,
                models.Question.section_code == s.code,
            )
            .group_by(models.Question.qtype_code)
            .order_by(func.count(models.Question.id).desc())
            .all()
        )
        qcount = sum(c for _, c in stats)
        sec_out.append(
            schemas.SectionDetail(
                code=s.code,
                name_jp=s.name_jp,
                name_zh=s.name_zh,
                time_limit_min=s.time_limit_min,
                question_count=qcount,
                qtype_stats=[
                    schemas.QTypeStat(qtype_code=code, count=c) for code, c in stats
                ],
            )
        )
    return schemas.ExamDetail(
        id=e.id,
        level=e.level,
        year=e.year,
        month=e.month,
        title=e.title,
        sections=sec_out,
    )


@router.get("/exams/{exam_id}/questions", response_model=list[schemas.QuestionOut])
def exam_questions(
    exam_id: int,
    section: str | None = Query(default=None, description="section code filter"),
    db: Session = Depends(get_db),
):
    """Questions for answering — never includes correct_option."""
    e = db.get(models.Exam, exam_id)
    if e is None:
        raise HTTPException(status_code=404, detail="exam not found")
    q = (
        db.query(models.Question)
        .join(
            models.Section,
            (models.Section.exam_id == models.Question.exam_id)
            & (models.Section.code == models.Question.section_code),
        )
        .options(joinedload(models.Question.group))
        .filter(models.Question.exam_id == exam_id)
    )
    if section:
        q = q.filter(models.Question.section_code == section)
    questions = q.order_by(
        models.Section.sort_order, models.Question.number_in_section
    ).all()
    return [question_to_out(x) for x in questions]
