#!/usr/bin/env python3
"""組裝 2021-07 N1 exam.json + manifest.json。

題目數據見 data_ql.py / data_reading.py / data_listening.py，
解析見 data_exp_ql.py / data_exp_rd.py / data_exp_li.py，生詞見 data_vocab.py。
答案以 PDF p.24 答案表（樹先生日語編制）為最終依據，逐題核對原圖。
本卷題數非標準：言語知識・讀解 69 題、聽解 35 題。
"""
import json
import os
import sys

SEED = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SEED)

from data_ql import QUESTIONS_QL, TEXT_PASSAGE          # noqa: E402
from data_reading import GROUPS, QUESTIONS_RD            # noqa: E402
from data_listening import QUESTIONS_LI                 # noqa: E402
from data_exp_ql import EXP_QL                          # noqa: E402
from data_exp_rd import EXP_RD                          # noqa: E402
from data_exp_li import EXP_LI                          # noqa: E402
from data_vocab import VOCAB                           # noqa: E402

# ---------- 答案表（PDF p.24，以此為最終依據） ----------
ANSWERS = {
    # 言語知識・讀解 Q1–69
    ("lang_reading", 1): "2", ("lang_reading", 2): "4", ("lang_reading", 3): "2",
    ("lang_reading", 4): "3", ("lang_reading", 5): "3", ("lang_reading", 6): "1",
    ("lang_reading", 7): "3", ("lang_reading", 8): "2", ("lang_reading", 9): "4",
    ("lang_reading", 10): "4", ("lang_reading", 11): "1", ("lang_reading", 12): "2",
    ("lang_reading", 13): "1", ("lang_reading", 14): "1", ("lang_reading", 15): "4",
    ("lang_reading", 16): "3", ("lang_reading", 17): "2", ("lang_reading", 18): "2",
    ("lang_reading", 19): "1", ("lang_reading", 20): "2", ("lang_reading", 21): "1",
    ("lang_reading", 22): "3", ("lang_reading", 23): "4", ("lang_reading", 24): "3",
    ("lang_reading", 25): "4", ("lang_reading", 26): "2", ("lang_reading", 27): "1",
    ("lang_reading", 28): "1", ("lang_reading", 29): "4", ("lang_reading", 30): "3",
    ("lang_reading", 31): "1", ("lang_reading", 32): "4", ("lang_reading", 33): "3",
    ("lang_reading", 34): "2", ("lang_reading", 35): "2", ("lang_reading", 36): "4",
    ("lang_reading", 37): "1", ("lang_reading", 38): "2", ("lang_reading", 39): "3",
    ("lang_reading", 40): "2", ("lang_reading", 41): "4", ("lang_reading", 42): "2",
    ("lang_reading", 43): "3", ("lang_reading", 44): "1", ("lang_reading", 45): "2",
    ("lang_reading", 46): "4", ("lang_reading", 47): "3", ("lang_reading", 48): "2",
    ("lang_reading", 49): "1", ("lang_reading", 50): "3", ("lang_reading", 51): "4",
    ("lang_reading", 52): "1", ("lang_reading", 53): "4", ("lang_reading", 54): "1",
    ("lang_reading", 55): "4", ("lang_reading", 56): "2", ("lang_reading", 57): "3",
    ("lang_reading", 58): "3", ("lang_reading", 59): "1", ("lang_reading", 60): "4",
    ("lang_reading", 61): "3", ("lang_reading", 62): "3", ("lang_reading", 63): "4",
    ("lang_reading", 64): "2", ("lang_reading", 65): "4", ("lang_reading", 66): "4",
    ("lang_reading", 67): "1", ("lang_reading", 68): "2", ("lang_reading", 69): "1",
    # 聽解 L1–35
    ("listening", 1): "3", ("listening", 2): "1", ("listening", 3): "3",
    ("listening", 4): "2", ("listening", 5): "4", ("listening", 6): "3",
    ("listening", 7): "4", ("listening", 8): "3", ("listening", 9): "3",
    ("listening", 10): "2", ("listening", 11): "2", ("listening", 12): "4",
    ("listening", 13): "1", ("listening", 14): "1", ("listening", 15): "4",
    ("listening", 16): "3", ("listening", 17): "2", ("listening", 18): "3",
    ("listening", 19): "3", ("listening", 20): "3", ("listening", 21): "1",
    ("listening", 22): "3", ("listening", 23): "1", ("listening", 24): "3",
    ("listening", 25): "2", ("listening", 26): "2", ("listening", 27): "3",
    ("listening", 28): "2", ("listening", 29): "2", ("listening", 30): "2",
    ("listening", 31): "1", ("listening", 32): "1", ("listening", 33): "3",
    ("listening", 34): "2", ("listening", 35): "4",
}


def build():
    errors = []

    # ---- groups ----
    groups = []
    for g in GROUPS:
        groups.append({
            "local_id": g["local_id"],
            "section_code": "lang_reading",
            "group_type": g["group_type"],
            "title": g["title"],
            "content": g["content"],
            "sort_order": g["sort_order"],
        })

    # ---- questions ----
    questions = []
    for q in QUESTIONS_QL:
        n = q["n"]
        key = ("lang_reading", n)
        questions.append({
            "group_local_id": q.get("group"),
            "section_code": "lang_reading",
            "qtype_code": q["qtype"],
            "mondai_no": q["mondai"],
            "number_in_section": n,
            "stem": q["stem"],
            "options": [{"key": k, "text": t} for k, t in q["options"]],
            "target_text": q.get("target"),
            "correct_option": ANSWERS[key],
        })
    for q in QUESTIONS_RD:
        n = q["n"]
        key = ("lang_reading", n)
        questions.append({
            "group_local_id": q["group"],
            "section_code": "lang_reading",
            "qtype_code": q["qtype"],
            "mondai_no": q["mondai"],
            "number_in_section": n,
            "stem": q["stem"],
            "options": [{"key": k, "text": t} for k, t in q["options"]],
            "target_text": None,
            "correct_option": ANSWERS[key],
        })
    for q in QUESTIONS_LI:
        n = q["n"]
        key = ("listening", n)
        questions.append({
            "group_local_id": None,
            "section_code": "listening",
            "qtype_code": q["qtype"],
            "mondai_no": q["mondai"],
            "number_in_section": n,
            "stem": q["stem"],
            "options": [{"key": k, "text": t} for k, t in q["options"]],
            "target_text": None,
            "correct_option": ANSWERS[key],
        })

    # ---- explanations ----
    explanations = []
    for (sec, n), e in sorted(EXP_QL.items()):
        explanations.append({
            "section_code": "lang_reading", "number_in_section": n,
            "key_point": e["key_point"], "analysis_zh": e["analysis_zh"],
            "distractors": [{"option": d["option"], "why_wrong": d["why_wrong"]}
                            for d in e["distractors"]],
            "evidence": e["evidence"],
        })
    for (sec, n), e in sorted(EXP_RD.items()):
        explanations.append({
            "section_code": "lang_reading", "number_in_section": n,
            "key_point": e["key_point"], "analysis_zh": e["analysis_zh"],
            "distractors": [{"option": d["option"], "why_wrong": d["why_wrong"]}
                            for d in e["distractors"]],
            "evidence": e["evidence"],
        })
    for (sec, n), e in sorted(EXP_LI.items()):
        explanations.append({
            "section_code": sec, "number_in_section": n,
            "key_point": e["key_point"], "analysis_zh": e["analysis_zh"],
            "distractors": [{"option": d["option"], "why_wrong": d["why_wrong"]}
                            for d in e["distractors"]],
            "evidence": e["evidence"],
        })

    # ---- vocabulary ----
    vocabulary = []
    for (sec, n), entries in sorted(VOCAB.items()):
        for v in entries:
            vocabulary.append({
                "section_code": sec, "number_in_section": n,
                "word": v["word"], "reading": v.get("reading"),
                "meaning_zh": v["meaning_zh"],
                "etymology_en": v.get("etymology_en"),
            })

    # ============ 驗證 ============
    # 1. 題數
    lang = [q for q in questions if q["section_code"] == "lang_reading"]
    lis = [q for q in questions if q["section_code"] == "listening"]
    if len(lang) != 69:
        errors.append(f"lang_reading 題數={len(lang)}（期望69）")
    if len(lis) != 35:
        errors.append(f"listening 題數={len(lis)}（期望35）")

    # 2. 題號連續
    if sorted(q["number_in_section"] for q in lang) != list(range(1, 70)):
        errors.append("lang_reading 題號不連續")
    if sorted(q["number_in_section"] for q in lis) != list(range(1, 36)):
        errors.append("listening 題號不連續")

    # 3. 選項數：有印刷選項的必須4個
    for q in questions:
        nopts = len(q["options"])
        if q["section_code"] == "lang_reading" and nopts != 4:
            errors.append(f"lang {q['number_in_section']}: 選項數={nopts}")
        if q["section_code"] == "listening" and nopts not in (0, 4):
            errors.append(f"listening {q['number_in_section']}: 選項數={nopts}")

    # 4. explanations 覆蓋率＋distractors 非空
    for sec, total in [("lang_reading", 69), ("listening", 35)]:
        have = {e["number_in_section"] for e in explanations if e["section_code"] == sec}
        missing = [i for i in range(1, total + 1) if i not in have]
        if missing:
            errors.append(f"{sec} explanations 缺: {missing}")
        for e in explanations:
            if e["section_code"] == sec and not e["distractors"]:
                errors.append(f"{sec} {e['number_in_section']}: distractors 為空")

    # 5. vocabulary 每題 ≥1 ＋欄位完整
    for sec, total in [("lang_reading", 69), ("listening", 35)]:
        have = {}
        for x in vocabulary:
            if x["section_code"] == sec:
                have.setdefault(x["number_in_section"], 0)
                have[x["number_in_section"]] += 1
        missing = [i for i in range(1, total + 1) if i not in have]
        if missing:
            errors.append(f"{sec} vocabulary 缺題: {missing}")
        for x in vocabulary:
            if not x["word"] or not x["reading"] or not x["meaning_zh"]:
                errors.append(f"vocab 缺欄位: {x}")

    # 6. group_local_id 引用有效
    gids = {g["local_id"] for g in groups}
    for q in questions:
        if q["group_local_id"] and q["group_local_id"] not in gids:
            errors.append(f"{q['section_code']} {q['number_in_section']}: group={q['group_local_id']} 不存在")

    # 7. target_text 與 stem 一致性（Q1–6、Q14–19 必須有）
    for q in lang:
        n = q["number_in_section"]
        if n <= 6 or 14 <= n <= 19:
            if not q["target_text"]:
                errors.append(f"lang {n}: 缺 target_text")
            elif q["target_text"] not in q["stem"]:
                errors.append(f"lang {n}: target_text 不在 stem 中: {q['target_text']}")

    # 8. 答案表交叉核對
    for q in questions:
        key = (q["section_code"], q["number_in_section"])
        if q["correct_option"] != ANSWERS[key]:
            errors.append(f"{key}: correct_option={q['correct_option']}，答案表={ANSWERS[key]}")

    # 9. 每題答案必須在選項中（有印刷選項的題目）
    for q in questions:
        if q["options"] and q["correct_option"] not in {o["key"] for o in q["options"]}:
            errors.append(f"{q['section_code']} {q['number_in_section']}: 答案不在選項中")

    # 10. 無答案洩露檢查：stem/options 不含答案標記
    for q in questions:
        for field in ("stem",):
            if "正解" in q[field] or "答案" in q[field]:
                errors.append(f"{q['section_code']} {q['number_in_section']}: stem 含答案洩露詞")

    if errors:
        print("驗證失敗：")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    exam = {
        "exam": {"level": "N1", "year": 2021, "month": 7, "title": "2021年7月 JLPT N1"},
        "groups": groups,
        "questions": questions,
        "explanations": explanations,
        "vocabulary": vocabulary,
    }
    with open(os.path.join(SEED, "exam.json"), "w", encoding="utf-8") as f:
        json.dump(exam, f, ensure_ascii=False, indent=1)

    manifest = {
        "level": "N1",
        "year": 2021,
        "month": 7,
        "total_questions": len(questions),
        "by_section": {"lang_reading": len(lang), "listening": len(lis)},
        "missing": [],
        "listening_without_printed_options": sorted(
            q["number_in_section"] for q in lis if not q["options"]),
        "answer_verified": True,
        "answer_source": "PDF p.24 答案表（樹先生日語編制），逐題核對原圖；聽解問題5(2)子格放大確認為 2/4",
        "notes": ("本卷題數非標準：言語知識・讀解69題（問題11僅2題、問題12有4題）、聽解35題（問題4有13題）。"
                  "問題13（資訊檢索）的表格頁為圖片形式，文章組以條件摘要記錄。"
                  "聽解問題3/4、問題5-1番無印刷選項，options記[]，解析為應對策略、不臆造台本。"
                  "Q38 排序題按答案表（★=のみならず）入庫。"),
    }
    with open(os.path.join(SEED, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print(f"exam.json: {len(questions)} questions, {len(groups)} groups, "
          f"{len(explanations)} explanations, {len(vocabulary)} vocabulary")
    print(f"manifest.json: total={manifest['total_questions']}, "
          f"missing={manifest['missing']}, "
          f"no_print_opts={manifest['listening_without_printed_options']}")


if __name__ == "__main__":
    build()
