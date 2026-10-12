#!/usr/bin/env python3
"""從 data_*.py 組裝 exam.json + manifest.json（2025-07 N1）。

數據直接以 Python 字面量記錄（依 transcription.md 轉錄）；本腳本只做
合併、校驗與輸出，不改寫內容。答案以 PDF p.46 答案表為準（見 transcription.md）。
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

# 3. 每題：選項4個（聽解12–30除外）、correct_option 在 1–4 內
for q in questions:
    n, sec = q["number_in_section"], q["section_code"]
    opts = q["options"]
    if sec == "listening" and n >= 12:
        if opts:
            errors.append(f"listening {n}: 無印刷選項應為空，實際{len(opts)}個")
    elif len(opts) != 4:
        errors.append(f"{sec} {n}: 選項{len(opts)}個，應為4個")
    if q["correct_option"] not in ("1", "2", "3", "4"):
        errors.append(f"{sec} {n}: correct_option={q['correct_option']} 非法")

# 4. explanations 覆蓋率
for sec, total in [("lang_reading", 66), ("listening", 30)]:
    have = {e["number_in_section"] for e in explanations if e["section_code"] == sec}
    missing = [i for i in range(1, total + 1) if i not in have]
    if missing:
        errors.append(f"{sec} explanations 缺: {missing}")
    for e in explanations:
        if e["section_code"] == sec and not e["distractors"]:
            errors.append(f"{sec} {e['number_in_section']}: distractors 為空")

# 5. vocabulary 每題 ≥1
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

# 8. 聽解 audio_url
for q in lis:
    if q.get("audio_url") != "/static/audio/2025-07-listening.mp3":
        errors.append(f"listening {q['number_in_section']}: audio_url 錯誤")

if errors:
    print("校驗失敗：")
    for er in errors:
        print(" -", er)
    sys.exit(1)

exam = {
    "exam": {"level": "N1", "year": 2025, "month": 7, "title": "2025年7月 JLPT N1 真題"},
    "groups": GROUPS,
    "questions": questions,
    "explanations": explanations,
    "vocabulary": vocabulary,
}
with open(os.path.join(SEED, "exam.json"), "w", encoding="utf-8") as f:
    json.dump(exam, f, ensure_ascii=False, indent=1)

manifest = {
    "level": "N1",
    "year": 2025,
    "month": 7,
    "total_questions": 96,
    "by_section": {"lang_reading": 66, "listening": 30},
    "missing": [],
    "listening_without_printed_options": list(range(12, 31)),
    "answer_verified": True,
    "answer_source": "試卷 PDF p.46 答案表（2026-10-11 逐題提取）；Q8=2、Q36=3 存疑但按答案表入庫，詳見 transcription.md「答案存疑」",
    "notes": "2026-10-11 轉錄。PDF 無聽解台本，聽解 stem 為場景說明（問題1/2 有印刷選項已轉錄；問題3–5 無印刷選項，options 記[]）。questions.target_text 用於 Q1–6（漢字讀音）與 Q14–19（近義詞）題干加粗；vocabulary.etymology_en 用於片假名詞源（如ブランク←blank）。",
}
with open(os.path.join(SEED, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print(f"OK: questions=96 (lang={len(lang)}, listening={len(lis)}), "
      f"groups={len(GROUPS)}, explanations={len(explanations)}, vocabulary={len(vocabulary)}")
