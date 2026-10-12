"""Serialization helpers shared by routers.

Security: question serializers MUST NEVER include `correct_option`.
"""
from __future__ import annotations

from . import models, schemas


def group_to_out(g: models.QuestionGroup | None) -> schemas.GroupOut | None:
    if g is None:
        return None
    return schemas.GroupOut(
        id=g.id,
        group_type=g.group_type,
        title=g.title,
        content=g.content,
        sort_order=g.sort_order,
    )


def vocabulary_to_out(v: models.Vocabulary) -> schemas.VocabularyOut:
    return schemas.VocabularyOut(
        word=v.word,
        reading=v.reading,
        meaning_zh=v.meaning_zh,
        etymology_en=v.etymology_en,
    )


def question_to_out(q: models.Question) -> schemas.QuestionOut:
    """Build the answering-view of a question (no answer included)."""
    return schemas.QuestionOut(
        id=q.id,
        exam_id=q.exam_id,
        section_code=q.section_code,
        qtype_code=q.qtype_code,
        mondai_no=q.mondai_no,
        number_in_section=q.number_in_section,
        stem=q.stem,
        target_text=q.target_text,
        options=[
            schemas.OptionItem(key=o.get("key"), text=o.get("text"))
            for o in (q.options or [])
        ],
        audio_url=q.audio_url,
        group=group_to_out(q.group),
    )


def explanation_to_out(
    e: models.Explanation | None,
    vocab: list[models.Vocabulary] | None = None,
) -> schemas.ExplanationOut:
    if e is None:
        return schemas.ExplanationOut(analysis_zh="")
    return schemas.ExplanationOut(
        key_point=e.key_point,
        analysis_zh=e.analysis_zh,
        distractors=e.distractors,
        evidence=e.evidence,
        option_readings=e.option_readings,
        option_meanings=e.option_meanings,
        vocabulary=[
            vocabulary_to_out(v) for v in sorted(vocab or [], key=lambda x: x.id)
        ],
    )
