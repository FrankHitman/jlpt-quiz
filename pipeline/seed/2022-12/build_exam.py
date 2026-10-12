#!/usr/bin/env python3
"""從 exam_data.py 組裝 exam.json + manifest.json（2022-12 N1）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exam_data import EXAM, ANSWERS, GROUPS, QDATA_1_7, QDATA_8_13, QDATA_LISTENING, EXPLANATIONS, VOCABULARY

SEED = os.path.dirname(os.path.abspath(__file__))


def build():
    questions = []
    # 問題1–7（無文章組）
    for n, qtype, mondai, stem, opts, target in QDATA_1_7:
        questions.append({
            "group_local_id": None,
            "section_code": "lang_reading",
            "qtype_code": qtype,
            "mondai_no": mondai,
            "number_in_section": n,
            "stem": stem,
            "options": [{"key": k, "text": t} for k, t in opts],
            "correct_option": ANSWERS[("lang_reading", n)],
            "target_text": target,
            "audio_url": None,
        })
    # 問題8–13（有文章組）
    for n, qtype, mondai, gid, stem, opts in QDATA_8_13:
        questions.append({
            "group_local_id": gid,
            "section_code": "lang_reading",
            "qtype_code": qtype,
            "mondai_no": mondai,
            "number_in_section": n,
            "stem": stem,
            "options": [{"key": k, "text": t} for k, t in opts],
            "correct_option": ANSWERS[("lang_reading", n)],
            "target_text": None,
            "audio_url": None,
        })
    # 聽解
    for n, qtype, mondai, stem, opts in QDATA_LISTENING:
        questions.append({
            "group_local_id": None,
            "section_code": "listening",
            "qtype_code": qtype,
            "mondai_no": mondai,
            "number_in_section": n,
            "stem": stem,
            "options": [{"key": k, "text": t} for k, t in opts],
            "correct_option": ANSWERS[("listening", n)],
            "target_text": None,
            "audio_url": None,
        })

    # 驗證：target_text 必須在 stem 中原樣出現
    for q in questions:
        tt = q.get("target_text")
        if tt:
            assert tt in q["stem"], f"Q{q['number_in_section']} target_text={tt!r} 未在題干中原樣出現"

    # 驗證：答案全覆蓋
    for q in questions:
        key = (q["section_code"], q["number_in_section"])
        assert key in ANSWERS, f"缺答案: {key}"

    explanations = []
    for sec, n, key_point, analysis_zh, distractors, evidence in EXPLANATIONS:
        explanations.append({
            "section_code": sec,
            "number_in_section": n,
            "key_point": key_point,
            "analysis_zh": analysis_zh,
            "distractors": [{"option": o, "why_wrong": w} for o, w in distractors],
            "evidence": evidence,
        })

    vocabulary = []
    for sec, n, word, reading, pos, meaning_zh, example_sentence, note, etymology_en in VOCABULARY:
        vocabulary.append({
            "section_code": sec,
            "number_in_section": n,
            "word": word,
            "reading": reading,
            "pos": pos,
            "meaning_zh": meaning_zh,
            "example_sentence": example_sentence,
            "note": note,
            "etymology_en": etymology_en,
        })

    # 覆蓋率檢查
    exp_keys = {(e["section_code"], e["number_in_section"]) for e in explanations}
    q_keys = {(q["section_code"], q["number_in_section"]) for q in questions}
    missing_exp = q_keys - exp_keys
    assert not missing_exp, f"缺解析: {missing_exp}"
    print(f"questions={len(questions)} explanations={len(explanations)} vocabulary={len(vocabulary)}")

    # 每題 ≥1 生詞（聽解無印刷題可豁免，僅警告）
    from collections import Counter
    vc = Counter((v["section_code"], v["number_in_section"]) for v in vocabulary)
    for qk in sorted(q_keys):
        if vc[qk] == 0:
            print(f"WARNING: 無生詞 {qk}")

    exam_json = {
        "exam": EXAM,
        "groups": GROUPS,
        "questions": questions,
        "explanations": explanations,
        "vocabulary": vocabulary,
    }
    with open(os.path.join(SEED, "exam.json"), "w", encoding="utf-8") as f:
        json.dump(exam_json, f, ensure_ascii=False, indent=2)

    lr = sum(1 for q in questions if q["section_code"] == "lang_reading")
    li = sum(1 for q in questions if q["section_code"] == "listening")
    manifest = {
        "level": "N1",
        "year": 2022,
        "month": 12,
        "total_questions": len(questions),
        "by_section": {"lang_reading": lr, "listening": li},
        "missing": [],
        "listening_without_printed_options": list(range(12, 29)),
        "answer_verified": True,
        "answer_source": "PDF p.17 答案表「2022年12月日语能力考试 N1真题答案」（本 PDF 內容）",
        "notes": (
            "本 PDF 共 18 頁：p.1 封面廣告、p.2–16 題目（言語知識・読解 66 題＋聽解印刷選項）、"
            "p.17 答案表、p.18 廣告。聽解問題3/4/5-1番本來就無印刷內容（options=[]，絕不臆造）；"
            "無聽解音頻，audio_url 為 null。問題5-2番（L29/L30）印刷選項為質問1/質問2共用。"
        ),
    }
    with open(os.path.join(SEED, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("exam.json + manifest.json 已生成")


if __name__ == "__main__":
    build()
