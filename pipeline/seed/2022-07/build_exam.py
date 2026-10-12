#!/usr/bin/env python3
"""從 data_*.py 組裝 exam.json + manifest.json（2022-07 N1）。

數據直接以 Python 字面量記錄（依 transcription.md 轉錄）；本腳本只做
合併、校驗與輸出，不改寫內容。答案以 PDF p.22 答案表為最終依據。
本卷無聽解音頻，listening 題不帶 audio_url。

題數：言語知識・読解 68（問題1–13）、聴解 35（問題1:6、問題2:7、問題3:6、問題4:13、問題5:3）。
聴解問題5：1番 1 題＋2番 質問1/質問2（答案表「2|1」）。
"""
import json
import os
import sys

SEED = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SEED)

from data_q1 import QUESTIONS as Q1
from data_q2 import QUESTIONS as Q2
from data_ql import QUESTIONS as QL
from data_groups import GROUPS
from data_e1 import E as E1
from data_e2 import E as E2
from data_el import E as EL
from data_v1 import V as V1
from data_v2 import V as V2

questions = Q1 + Q2 + QL
explanations = E1 + E2 + EL
vocabulary = V1 + V2

errors = []

# 1. 題數
if len(questions) != 103:
    errors.append(f"questions={len(questions)}，應為103")
lang = [q for q in questions if q["section_code"] == "lang_reading"]
lis = [q for q in questions if q["section_code"] == "listening"]
if len(lang) != 68:
    errors.append(f"lang_reading={len(lang)}，應為68")
if len(lis) != 35:
    errors.append(f"listening={len(lis)}，應為35")

# 2. number_in_section 連續性
for sec, qs, total in [("lang_reading", lang, 68), ("listening", lis, 35)]:
    nis = sorted(q["number_in_section"] for q in qs)
    if nis != list(range(1, total + 1)):
        errors.append(f"{sec} number_in_section 不連續: {nis[:5]}...{nis[-3:]}")

# 3. 每題：選項4個（聽解無印刷選項除外）、correct_option 在 1–4 內
#    無印刷選項：L14–33（問題3、問題4、問題5-1番）
for q in questions:
    n, sec = q["number_in_section"], q["section_code"]
    opts = q["options"]
    if sec == "listening" and 14 <= n <= 33:
        if opts:
            errors.append(f"listening {n}: 無印刷選項應為空，實際{len(opts)}個")
    elif len(opts) != 4:
        errors.append(f"{sec} {n}: 選項{len(opts)}個，應為4個")
    if q["correct_option"] not in ("1", "2", "3", "4"):
        errors.append(f"{sec} {n}: correct_option={q['correct_option']} 非法")

# 4. explanations 覆蓋率（聽解無印刷題 distractors 可空，沿用 2025-12 前例）
for sec, total in [("lang_reading", 68), ("listening", 35)]:
    have = {e["number_in_section"] for e in explanations if e["section_code"] == sec}
    missing = [i for i in range(1, total + 1) if i not in have]
    if missing:
        errors.append(f"{sec} explanations 缺: {missing}")
    for e in explanations:
        if e["section_code"] == sec and sec == "lang_reading" and not e["distractors"]:
            errors.append(f"{sec} {e['number_in_section']}: distractors 為空")

# 5. vocabulary 每題 ≥1 ＋欄位完整
for sec, total in [("lang_reading", 68), ("listening", 35)]:
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
gids = {g["local_id"] for g in GROUPS}
for q in questions:
    if q["group_local_id"] and q["group_local_id"] not in gids:
        errors.append(f"{q['section_code']} {q['number_in_section']}: group_local_id={q['group_local_id']} 不存在")

# 7. target_text 與 stem 一致性（Q1–6、Q14–19 必須有）
for q in lang:
    n = q["number_in_section"]
    if n <= 6 or 14 <= n <= 19:
        if not q["target_text"]:
            errors.append(f"lang {n}: 缺 target_text")
        elif q["target_text"] not in q["stem"]:
            errors.append(f"lang {n}: target_text 不在 stem 中: {q['target_text']}")

# 8. 答案表交叉核對（PDF p.22）
ANSWERS = {
    ("lang_reading", 1): "1", ("lang_reading", 2): "3", ("lang_reading", 3): "3",
    ("lang_reading", 4): "4", ("lang_reading", 5): "2", ("lang_reading", 6): "4",
    ("lang_reading", 7): "4", ("lang_reading", 8): "2", ("lang_reading", 9): "2",
    ("lang_reading", 10): "1", ("lang_reading", 11): "1", ("lang_reading", 12): "3",
    ("lang_reading", 13): "3", ("lang_reading", 14): "4", ("lang_reading", 15): "2",
    ("lang_reading", 16): "4", ("lang_reading", 17): "3", ("lang_reading", 18): "3",
    ("lang_reading", 19): "1", ("lang_reading", 20): "2", ("lang_reading", 21): "3",
    ("lang_reading", 22): "1", ("lang_reading", 23): "2", ("lang_reading", 24): "1",
    ("lang_reading", 25): "4", ("lang_reading", 26): "2", ("lang_reading", 27): "3",
    ("lang_reading", 28): "1", ("lang_reading", 29): "4", ("lang_reading", 30): "1",
    ("lang_reading", 31): "2", ("lang_reading", 32): "3", ("lang_reading", 33): "4",
    ("lang_reading", 34): "2", ("lang_reading", 35): "2", ("lang_reading", 36): "4",
    ("lang_reading", 37): "1", ("lang_reading", 38): "3", ("lang_reading", 39): "2",
    ("lang_reading", 40): "4", ("lang_reading", 41): "3", ("lang_reading", 42): "2",
    ("lang_reading", 43): "4", ("lang_reading", 44): "1", ("lang_reading", 45): "3",
    ("lang_reading", 46): "1", ("lang_reading", 47): "4", ("lang_reading", 48): "3",
    ("lang_reading", 49): "3", ("lang_reading", 50): "3", ("lang_reading", 51): "1",
    ("lang_reading", 52): "3", ("lang_reading", 53): "2", ("lang_reading", 54): "2",
    ("lang_reading", 55): "1", ("lang_reading", 56): "4", ("lang_reading", 57): "4",
    ("lang_reading", 58): "1", ("lang_reading", 59): "4", ("lang_reading", 60): "3",
    ("lang_reading", 61): "2", ("lang_reading", 62): "3", ("lang_reading", 63): "4",
    ("lang_reading", 64): "1", ("lang_reading", 65): "2", ("lang_reading", 66): "4",
    ("lang_reading", 67): "1", ("lang_reading", 68): "2",
    ("listening", 1): "3", ("listening", 2): "2", ("listening", 3): "1",
    ("listening", 4): "2", ("listening", 5): "3", ("listening", 6): "2",
    ("listening", 7): "2", ("listening", 8): "3", ("listening", 9): "2",
    ("listening", 10): "2", ("listening", 11): "3", ("listening", 12): "1",
    ("listening", 13): "3", ("listening", 14): "4", ("listening", 15): "4",
    ("listening", 16): "1", ("listening", 17): "4", ("listening", 18): "1",
    ("listening", 19): "3", ("listening", 20): "3", ("listening", 21): "3",
    ("listening", 22): "1", ("listening", 23): "2", ("listening", 24): "2",
    ("listening", 25): "3", ("listening", 26): "3", ("listening", 27): "1",
    ("listening", 28): "1", ("listening", 29): "1", ("listening", 30): "3",
    ("listening", 31): "1", ("listening", 32): "2", ("listening", 33): "4",
    ("listening", 34): "2", ("listening", 35): "1",
}
for q in questions:
    key = (q["section_code"], q["number_in_section"])
    if q["correct_option"] != ANSWERS[key]:
        errors.append(f"{key}: correct_option={q['correct_option']}，答案表={ANSWERS[key]}")

if errors:
    print("校驗失敗：")
    for er in errors:
        print(" -", er)
    sys.exit(1)

exam = {
    "exam": {
        "level": "N1",
        "year": 2022,
        "month": 7,
        "title": "2022年7月 JLPT N1 真題",
    },
    "groups": GROUPS,
    "questions": questions,
    "explanations": explanations,
    "vocabulary": vocabulary,
}

with open(os.path.join(SEED, "exam.json"), "w", encoding="utf-8") as f:
    json.dump(exam, f, ensure_ascii=False, indent=2)

manifest = {
    "title": "2022年7月 JLPT N1 真題",
    "level": "N1",
    "year": 2022,
    "month": 7,
    "source_pdf": "2022.07.N1.pdf",
    "answer_verified": True,
    "answer_source": "PDF p.22「2022年7月日语能力考试 N1真题答案」（逐題核對，全題一致）",
    "question_counts": {"lang_reading": 68, "listening": 35, "total": 103},
    "listening_without_printed_options": list(range(14, 34)),
    "listening_has_printed_options": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 34, 35],
    "notes": [
        "言語知識・読解 68 題：問題9 為（三）篇×3 題=9 題（49–57）。",
        "聴解 35 題：問題4（即時応答）13 題；問題5 3 題（1番＋2番 質問1/質問2，答案表「2|1」）。",
        "問題13 指示文寫「オーケストラの年間セット券」但實際文件為「外部講座の受講料補助」，按實際文件轉錄。",
        "Q3 下劃線在「慕って」下（したって），target_text=慕って。",
        "無聽解音頻、無聽解台本；聴解 stem 為場景描述。",
    ],
}
with open(os.path.join(SEED, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f"OK: questions={len(questions)} (lang={len(lang)}, listening={len(lis)}), "
      f"explanations={len(explanations)}, vocabulary={len(vocabulary)}, groups={len(GROUPS)}")
