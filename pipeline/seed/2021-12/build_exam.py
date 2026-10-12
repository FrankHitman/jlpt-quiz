#!/usr/bin/env python3
"""從 data_*.py 組裝 exam.json + manifest.json（2021-12 N1）。

題目與解析由逐頁讀圖轉錄；答案以 PDF p.21 答案表為最終依據（data_answers.py）。
"""
import json
import os
import sys

SEED = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SEED)

from data_answers import ANSWERS, ANSWERS_L
from data_q1 import QUESTIONS_LR_1
from data_q2 import QUESTIONS_LR_2, GROUP_Q7
from data_q3 import QUESTIONS_LR_3, GROUPS_Q8_Q9
from data_q4 import QUESTIONS_LR_4, GROUPS_Q10_Q13
from data_ql import QUESTIONS_L
from data_e1 import EXPL_1
from data_e2 import EXPL_2
from data_e3 import EXPL_3
from data_el import EXPL_L
from data_v1 import VOCAB_1
from data_v2 import VOCAB_2
from data_vl import VOCAB_L

QTYPE_LABEL = {
    "kanji_reading": "漢字読み", "vocab_fill": "語彙・文脈規定", "synonym": "言い換え類義",
    "word_usage": "語の使い方", "grammar_fill": "文法形式の判断", "sentence_order": "文の組み立て",
    "text_grammar": "文章の文法", "short_reading": "短文読解", "mid_reading": "中文読解",
    "long_reading": "長文読解", "comparison_reading": "対比読解", "info_retrieval": "情報検索",
    "listening_task": "課題理解", "listening_point": "ポイント理解", "listening_summary": "概要理解",
    "listening_response": "即時応答", "listening_comprehensive": "統合理解",
}


def build():
    lr = QUESTIONS_LR_1 + QUESTIONS_LR_2 + QUESTIONS_LR_3 + QUESTIONS_LR_4
    assert len(lr) == 69, f"lang_reading count {len(lr)}"
    assert len(QUESTIONS_L) == 35, f"listening count {len(QUESTIONS_L)}"

    questions = []
    for q in lr:
        n = q["n"]
        correct = ANSWERS[n]
        opts = [{"key": k, "text": t} for k, t in q["options"]]
        assert any(o["key"] == correct for o in opts), f"Q{n} correct {correct} not in options"
        if q.get("target"):
            assert q["target"] in q["stem"], f"Q{n} target_text not in stem"
        questions.append({
            "section_code": "lang_reading",
            "qtype_code": q["qtype"],
            "mondai_no": q["mondai"],
            "number_in_section": n,
            "stem": q["stem"],
            "options": opts,
            "correct_option": correct,
            "target_text": q.get("target"),
            "group_local_id": q.get("group"),
            "audio_url": None,
        })
    for q in QUESTIONS_L:
        n = q["n"]
        correct = ANSWERS_L[n]
        opts = [{"key": k, "text": t} for k, t in q["options"]]
        if opts:
            assert any(o["key"] == correct for o in opts), f"L{n} correct {correct} not in options"
        questions.append({
            "section_code": "listening",
            "qtype_code": q["qtype"],
            "mondai_no": q["mondai"],
            "number_in_section": n,
            "stem": q["stem"],
            "options": opts,
            "correct_option": correct,
            "target_text": None,
            "group_local_id": None,
            "audio_url": None,
        })

    expls = EXPL_1 + EXPL_2 + EXPL_3
    expl_l = EXPL_L
    assert len(expls) == 69 and len(expl_l) == 35
    explanations = []
    for e in expls:
        q = next(x for x in lr if x["n"] == e["n"])
        explanations.append({
            "section_code": "lang_reading",
            "number_in_section": e["n"],
            "key_point": e["key_point"],
            "analysis_zh": e.get("analysis_zh") or e.get("analysis"),
            "distractors": [{"option": o, "why_wrong": w} for o, w in e["distractors"]],
            "evidence": e["evidence"],
        })
        _ = q
    for e in expl_l:
        explanations.append({
            "section_code": "listening",
            "number_in_section": e["n"],
            "key_point": e["key_point"],
            "analysis_zh": e.get("analysis_zh") or e.get("analysis"),
            "distractors": [{"option": o, "why_wrong": w} for o, w in e["distractors"]],
            "evidence": e["evidence"],
        })

    vocabs = VOCAB_1 + VOCAB_2 + VOCAB_L
    covered = {v["n"] for v in vocabs}
    missing_v = [n for n in range(1, 70) if n not in covered] + [n for n in range(1, 36) if n not in {v["n"] for v in VOCAB_L}]
    assert not missing_v, f"vocab missing: {missing_v}"
    vocabulary = []
    for v in vocabs:
        sec = "lang_reading" if v["n"] <= 69 and v in (VOCAB_1 + VOCAB_2) else "listening"
        if v in VOCAB_L:
            sec = "listening"
        else:
            sec = "lang_reading"
        entry = {
            "section_code": sec,
            "number_in_section": v["n"],
            "word": v["word"],
            "reading": v["reading"],
            "meaning_zh": v["meaning_zh"],
        }
        if v.get("etymology_en"):
            entry["etymology_en"] = v["etymology_en"]
        vocabulary.append(entry)

    groups = [GROUP_Q7] + GROUPS_Q8_Q9 + GROUPS_Q10_Q13
    assert len(groups) == 12, f"groups {len(groups)}"

    exam = {
        "exam": {"level": "N1", "year": 2021, "month": 12, "title": "2021年12月 JLPT N1"},
        "groups": groups,
        "questions": questions,
        "explanations": explanations,
        "vocabulary": vocabulary,
    }
    with open(os.path.join(SEED, "exam.json"), "w", encoding="utf-8") as f:
        json.dump(exam, f, ensure_ascii=False, indent=1)

    no_print = [q["n"] for q in QUESTIONS_L if not q["options"]]
    manifest = {
        "level": "N1", "year": 2021, "month": 12,
        "total_questions": 104,
        "by_section": {"lang_reading": 69, "listening": 35},
        "missing": [],
        "listening_without_printed_options": no_print,
        "answer_verified": True,
        "answer_source": "PDF p.21 答案表（逐格核對，以此為最終依據）",
        "notes": [
            "本卷為69題言語知識・読解＋35題聴解＝104題，與他年份的66+30不同，答案表欄數與題數完全自洽",
            "問題7題目說明寫41–45但實際只有41–44（考試頁碼12/21缺第5小題欄位，與2024-07同類異常）",
            "問題13題頭誤寫「オーケストラの年間セット券」，實際內容為正南大学施設使用案内",
            "聴解問題2・4番選項2/3印刷文字相同（運営費用の確保が困難なこと），按原圖照錄",
            "聽解無音頻，audio_url均為null",
        ],
    }
    with open(os.path.join(SEED, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print(f"questions: {len(questions)} (lr={len(lr)}, l={len(QUESTIONS_L)})")
    print(f"explanations: {len(explanations)}, vocabulary: {len(vocabulary)}, groups: {len(groups)}")
    print(f"listening without printed options: {no_print}")
    # target_text 覆蓋
    tt = sum(1 for q in questions if q["target_text"])
    print(f"target_text coverage: {tt} (Q1-6 + Q14-19 = 12 expected)")


if __name__ == "__main__":
    build()
