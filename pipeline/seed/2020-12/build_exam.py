#!/usr/bin/env python3
"""從數據模塊組裝 exam.json + manifest.json（2020-12 N1）。

數據來源：pipeline/seed/2020-12/transcription.md（逐頁轉錄）；
答案以 PDF p.15 答案表為最終依據。
"""
import json
import os
import sys

SEED = os.path.expanduser("~/workspace/jlpt-quiz/pipeline/seed/2020-12")
sys.path.insert(0, SEED)

from data_q1 import Q  # noqa: E402  (Q1-40)
import data_q2  # noqa: E402  (Q41-68 + L1-35，append 進 Q)
from data_g import GROUPS  # noqa: E402
from data_exp1 import EXP  # noqa: E402  (Q1-40)
import data_exp3  # noqa: E402  (L1-35 append 進 EXP；Q41-68 在 data_exp2)
from data_vocab1 import VOCAB  # noqa: E402  (Q1-40)
import data_vocab2  # noqa: E402  (Q41-68 + L1-35，更新 VOCAB)


def main():
    # ---- 校驗題數 ----
    lr = [q for q in Q if q["section_code"] == "lang_reading"]
    li = [q for q in Q if q["section_code"] == "listening"]
    assert len(lr) == 68, f"lang_reading={len(lr)}"
    assert len(li) == 35, f"listening={len(li)}"
    assert sorted(q["number_in_section"] for q in lr) == list(range(1, 69))
    assert sorted(q["number_in_section"] for q in li) == list(range(1, 36))

    for q in Q:
        if q["qtype_code"] not in ("listening_summary", "listening_response",
                                   "listening_comprehensive") or q["number_in_section"] in (34, 35):
            pass
        # 問題3/4/5-1番允許空選項；其餘必須4個選項
        n = q["number_in_section"]
        if q["section_code"] == "listening" and q["qtype_code"] in (
                "listening_summary", "listening_response") or (q["qtype_code"] == "listening_comprehensive" and n == 33):
            assert q["options"] == [], f"L{n} 應為空選項"
        else:
            assert len(q["options"]) == 4, f"Q{q['number_in_section']} 選項數={len(q['options'])}"
        # target_text 必須在 stem 中原樣出現
        if q.get("target_text"):
            assert q["target_text"] in q["stem"], f"target_text 不在 stem 中: {q['number_in_section']}"

    questions = []
    for q in Q:
        questions.append({
            "group_local_id": q.get("group_local_id"),
            "section_code": q["section_code"],
            "qtype_code": q["qtype_code"],
            "mondai_no": q["mondai_no"],
            "number_in_section": q["number_in_section"],
            "stem": q["stem"],
            "options": q["options"],
            "correct_option": q["correct_option"],
            "target_text": q.get("target_text"),
        })

    # ---- 解析 ----
    exp_keys = {(e["section_code"], e["number_in_section"]) for e in EXP}
    assert len(exp_keys) == 103, f"explanations={len(exp_keys)}"
    explanations = []
    for e_ in EXP:
        explanations.append({
            "section_code": e_["section_code"],
            "number_in_section": e_["number_in_section"],
            "key_point": e_["key_point"],
            "analysis_zh": e_["analysis_zh"],
            "distractors": e_["distractors"],
            "evidence": e_.get("evidence"),
        })

    # ---- 生詞 ----
    assert len(VOCAB) == 103, f"vocabulary 覆蓋題數={len(VOCAB)}"
    vocabulary = []
    for (sc, n), entries in sorted(VOCAB.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        for en in entries:
            vocabulary.append({
                "section_code": sc,
                "number_in_section": n,
                "word": en["word"],
                "reading": en.get("reading") or None,
                "pos": None,
                "meaning_zh": en.get("meaning_zh"),
                "example_sentence": None,
                "note": None,
                "etymology_en": en.get("etymology_en"),
            })

    groups = []
    for g in GROUPS:
        groups.append({
            "local_id": g["local_id"],
            "section_code": g["section_code"],
            "group_type": g["group_type"],
            "title": g["title"],
            "content": g["content"],
            "sort_order": g["sort_order"],
        })

    exam = {
        "exam": {"level": "N1", "year": 2020, "month": 12, "title": "2020年12月 JLPT N1"},
        "groups": groups,
        "questions": questions,
        "explanations": explanations,
        "vocabulary": vocabulary,
    }
    with open(os.path.join(SEED, "exam.json"), "w", encoding="utf-8") as f:
        json.dump(exam, f, ensure_ascii=False, indent=1)

    no_print = [q["number_in_section"] for q in li
                if q["qtype_code"] in ("listening_summary", "listening_response")
                or (q["qtype_code"] == "listening_comprehensive" and q["number_in_section"] == 33)]
    manifest = {
        "level": "N1",
        "year": 2020,
        "month": 12,
        "total_questions": len(questions),
        "by_section": {
            "lang_reading": len(lr),
            "listening": len(li),
        },
        "missing": [],
        "listening_without_printed_options": sorted(no_print),
        "answer_verified": True,
        "answer_source": "PDF p.15「2020年12月日语能力考试 N1真题答案」答案表（逐題核對，全數一致）",
        "notes": ("本卷言語知識・読解 68 題（2022 改制前題量）、聴解 35 題。聴解問題3（L14–19）・問題4（L20–32）・問題5-1番（L33）無印刷選項，"
                  "options 記 []。聴解問題5-2番（L34/L35）印刷選項中的教室編號因原 PDF 字體缺失無法判讀，選項暫記為「＿番教室」×4。"
                  "聴解考試時間原標註 60 分鐘（2022 改制前），section 統一按 55 分鐘建。本卷無聽解音頻，audio_url 留空。"),
    }
    with open(os.path.join(SEED, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print(f"exam.json: {len(questions)} questions, {len(groups)} groups, "
          f"{len(explanations)} explanations, {len(vocabulary)} vocabulary entries")


if __name__ == "__main__":
    main()
