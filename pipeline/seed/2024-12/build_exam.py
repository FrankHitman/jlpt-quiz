#!/usr/bin/env python3
"""從 data_*.py 組裝 exam.json + manifest.json（2024-12 N1）。

數據直接以 Python 字面量記錄（依 transcription.md 轉錄）；本腳本只做
合併、校驗與輸出，不改寫內容。答案以 PDF p.45 答案表為準（見 transcription.md）。
本卷無聽解音頻，listening 題不帶 audio_url。
"""
import json
import os
import sys

SEED = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SEED)

from data_q1 import QUESTIONS as Q1
from data_q2 import QUESTIONS as Q2
from data_q3 import QUESTIONS as Q3
from data_ql import QUESTIONS as QL
from data_groups import GROUPS
from data_e1 import EXPLANATIONS as E1
from data_e2 import EXPLANATIONS as E2
from data_e3 import EXPLANATIONS as E3
from data_el import EXPLANATIONS as EL
from data_v1 import VOCABULARY as V1
from data_v2 import VOCABULARY as V2

questions = Q1 + Q2 + Q3 + QL
explanations = E1 + E2 + E3 + EL
vocabulary = V1 + V2

errors = []

# 1. 題數
if len(questions) != 96:
    errors.append(f"questions={len(questions)}，應為96")
lang = [q for q in questions if q["section_code"] == "lang_reading"]
lis = [q for q in questions if q["section_code"] == "listening"]
if len(lang) != 66:
    errors.append(f"lang_reading={len(lang)}，應為66")
if len(lis) != 30:
    errors.append(f"listening={len(lis)}，應為30")

# 2. number_in_section 連續性
for sec, qs, total in [("lang_reading", lang, 66), ("listening", lis, 30)]:
    nis = sorted(q["number_in_section"] for q in qs)
    if nis != list(range(1, total + 1)):
        errors.append(f"{sec} number_in_section 不連續: {nis[:5]}...{nis[-3:]}")

# 3. 每題：選項4個（聽解12–28除外；29–30有印刷選項）、correct_option 在 1–4 內
for q in questions:
    n, sec = q["number_in_section"], q["section_code"]
    opts = q["options"]
    if sec == "listening" and 12 <= n <= 28:
        if opts:
            errors.append(f"listening {n}: 無印刷選項應為空，實際{len(opts)}個")
    elif len(opts) != 4:
        errors.append(f"{sec} {n}: 選項{len(opts)}個，應為4個")
    if q["correct_option"] not in ("1", "2", "3", "4"):
        errors.append(f"{sec} {n}: correct_option={q['correct_option']} 非法")

# 4. explanations 覆蓋率＋distractors 非空
for sec, total in [("lang_reading", 66), ("listening", 30)]:
    have = {e["number_in_section"] for e in explanations if e["section_code"] == sec}
    missing = [i for i in range(1, total + 1) if i not in have]
    if missing:
        errors.append(f"{sec} explanations 缺: {missing}")
    for e in explanations:
        if e["section_code"] == sec and not e["distractors"]:
            errors.append(f"{sec} {e['number_in_section']}: distractors 為空")

# 5. vocabulary 每題 ≥1 ＋欄位完整
for sec, total in [("lang_reading", 66), ("listening", 30)]:
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

# 8. 答案表交叉核對
ANSWERS = {
    ("lang_reading", 1): "2", ("lang_reading", 2): "1", ("lang_reading", 3): "1",
    ("lang_reading", 4): "3", ("lang_reading", 5): "4", ("lang_reading", 6): "3",
    ("lang_reading", 7): "1", ("lang_reading", 8): "4", ("lang_reading", 9): "3",
    ("lang_reading", 10): "4", ("lang_reading", 11): "2", ("lang_reading", 12): "1",
    ("lang_reading", 13): "3", ("lang_reading", 14): "2", ("lang_reading", 15): "2",
    ("lang_reading", 16): "4", ("lang_reading", 17): "3", ("lang_reading", 18): "1",
    ("lang_reading", 19): "1", ("lang_reading", 20): "2", ("lang_reading", 21): "4",
    ("lang_reading", 22): "4", ("lang_reading", 23): "3", ("lang_reading", 24): "2",
    ("lang_reading", 25): "1", ("lang_reading", 26): "4", ("lang_reading", 27): "3",
    ("lang_reading", 28): "2", ("lang_reading", 29): "3", ("lang_reading", 30): "1",
    ("lang_reading", 31): "4", ("lang_reading", 32): "4", ("lang_reading", 33): "1",
    ("lang_reading", 34): "2", ("lang_reading", 35): "2", ("lang_reading", 36): "1",
    ("lang_reading", 37): "2", ("lang_reading", 38): "4", ("lang_reading", 39): "1",
    ("lang_reading", 40): "3", ("lang_reading", 41): "3", ("lang_reading", 42): "4",
    ("lang_reading", 43): "1", ("lang_reading", 44): "2", ("lang_reading", 45): "3",
    ("lang_reading", 46): "4", ("lang_reading", 47): "1", ("lang_reading", 48): "2",
    ("lang_reading", 49): "4", ("lang_reading", 50): "2", ("lang_reading", 51): "2",
    ("lang_reading", 52): "4", ("lang_reading", 53): "2", ("lang_reading", 54): "3",
    ("lang_reading", 55): "3", ("lang_reading", 56): "1", ("lang_reading", 57): "2",
    ("lang_reading", 58): "3", ("lang_reading", 59): "1", ("lang_reading", 60): "4",
    ("lang_reading", 61): "3", ("lang_reading", 62): "2", ("lang_reading", 63): "3",
    ("lang_reading", 64): "4", ("lang_reading", 65): "1", ("lang_reading", 66): "1",
    ("listening", 1): "3", ("listening", 2): "2", ("listening", 3): "3",
    ("listening", 4): "2", ("listening", 5): "1", ("listening", 6): "1",
    ("listening", 7): "4", ("listening", 8): "4", ("listening", 9): "1",
    ("listening", 10): "2", ("listening", 11): "2", ("listening", 12): "4",
    ("listening", 13): "2", ("listening", 14): "3", ("listening", 15): "2",
    ("listening", 16): "4", ("listening", 17): "3", ("listening", 18): "1",
    ("listening", 19): "3", ("listening", 20): "2", ("listening", 21): "2",
    ("listening", 22): "1", ("listening", 23): "3", ("listening", 24): "3",
    ("listening", 25): "1", ("listening", 26): "2", ("listening", 27): "2",
    ("listening", 28): "4", ("listening", 29): "1", ("listening", 30): "3",
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
    "exam": {"level": "N1", "year": 2024, "month": 12, "title": "2024年12月 JLPT N1 真題"},
    "groups": GROUPS,
    "questions": questions,
    "explanations": explanations,
    "vocabulary": vocabulary,
}
with open(os.path.join(SEED, "exam.json"), "w", encoding="utf-8") as f:
    json.dump(exam, f, ensure_ascii=False, indent=1)

manifest = {
    "level": "N1",
    "year": 2024,
    "month": 12,
    "total_questions": 96,
    "by_section": {"lang_reading": 66, "listening": 30},
    "missing": [],
    "listening_without_printed_options": list(range(12, 29)),
    "answer_verified": True,
    "answer_source": "試卷 PDF p.45 答案表「2024年12月日语能力考试 N1真题答案」（2026-10-11 逐題提取）；96 題全部核對一致，無存疑題號",
    "notes": "2026-10-11 轉錄。PDF 無聽解台本、無聽解音頻，聽解 stem 為場景說明（問題1/2/5-2番有印刷選項已轉錄；問題3/4/5-1番無印刷選項，options 記[]）。p.33/p.37 兩組無番號選項判定為問題1/2例題殘頁，未入庫。questions.target_text 用於 Q1–6（漢字讀音）與 Q14–19（近義詞）；vocabulary.etymology_en 用於片假名詞源（如ロス←loss、トレードオフ←trade-off）。",
}
with open(os.path.join(SEED, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print(f"OK: questions=96 (lang={len(lang)}, listening={len(lis)}), "
      f"groups={len(GROUPS)}, explanations={len(explanations)}, vocabulary={len(vocabulary)}")
