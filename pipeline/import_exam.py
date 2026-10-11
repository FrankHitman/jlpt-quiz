#!/usr/bin/env python3
"""匯入結構化試卷 JSON 到 PostgreSQL（JLPT N1 刷題系統）。

用法：
    python3 import_exam.py pipeline/seed/2025-12/exam.json

- 讀取 ~/workspace/jlpt-quiz/backend/.env 的 DATABASE_URL（psycopg 直連）。
- 冪等：同一 (level, year, month) 已存在時先刪除舊 exam（CASCADE 級聯），再重建。
- sections 由程式自動建立（lang_reading 110 分鐘 / listening 55 分鐘，見 TASKS.md 全局約定）。
"""
import json
import os
import re
import sys

WORKSPACE = os.path.expanduser("~/workspace/jlpt-quiz")
ENV_PATH = os.path.join(WORKSPACE, "backend", ".env")

# section 預設（TASKS.md 全局約定：官方考試時間）
SECTIONS = [
    {
        "code": "lang_reading",
        "name_jp": "言語知識（文字・語彙・文法）・読解",
        "name_zh": "語言知識（文字・詞彙・文法）・讀解",
        "time_limit_min": 110,
        "sort_order": 1,
    },
    {
        "code": "listening",
        "name_jp": "聴解",
        "name_zh": "聽解",
        "time_limit_min": 55,
        "sort_order": 2,
    },
]


def load_database_url() -> str:
    if not os.path.exists(ENV_PATH):
        sys.exit(f"ERROR: 找不到 {ENV_PATH}（DB agent 尚未建好 .env）")
    url = None
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "DATABASE_URL":
                url = v.strip().strip('"').strip("'")
    if not url:
        sys.exit(f"ERROR: {ENV_PATH} 沒有 DATABASE_URL")
    return url


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("用法: python3 import_exam.py <exam.json>")
    json_path = sys.argv[1]
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    try:
        import psycopg
    except ImportError:
        sys.exit("ERROR: 需要 psycopg（pip install 'psycopg[binary]'）")

    exam = data["exam"]
    level, year, month = exam["level"], exam["year"], exam["month"]

    # ---- 輕量驗證 ----
    warnings = []
    for q in data["questions"]:
        opts = q.get("options") or []
        if opts:
            if len(opts) != 4:
                warnings.append(
                    f"Q{q['section_code']}:{q['number_in_section']} 選項數={len(opts)}（應為4）"
                )
            keys = [o["key"] for o in opts]
            if q["correct_option"] not in keys:
                warnings.append(
                    f"Q{q['section_code']}:{q['number_in_section']} correct_option={q['correct_option']} 不在選項中"
                )
        tt = q.get("target_text")
        if tt and tt not in (q.get("stem") or ""):
            warnings.append(
                f"Q{q['section_code']}:{q['number_in_section']} target_text={tt!r} 未在題干中原樣出現"
            )
    for w in warnings:
        print("WARNING:", w)

    conn = psycopg.connect(load_database_url())
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # 冪等：刪舊資料（CASCADE 級聯 questions/groups/explanations/vocabulary）
            cur.execute(
                "DELETE FROM exams WHERE level=%s AND year=%s AND month=%s",
                (level, year, month),
            )
            deleted = cur.rowcount
            if deleted:
                print(f"已刪除舊資料：exams {deleted} 筆（級聯）")

            cur.execute(
                "INSERT INTO exams (level, year, month, title) VALUES (%s,%s,%s,%s) RETURNING id",
                (level, year, month, exam["title"]),
            )
            exam_id = cur.fetchone()[0]

            for s in SECTIONS:
                cur.execute(
                    """INSERT INTO sections (exam_id, code, name_jp, name_zh, time_limit_min, sort_order)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (exam_id, s["code"], s["name_jp"], s["name_zh"],
                     s["time_limit_min"], s["sort_order"]),
                )

            group_id_map = {}
            for g in data.get("groups", []):
                cur.execute(
                    """INSERT INTO question_groups (exam_id, section_code, group_type, title, content, sort_order)
                       VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (exam_id, g["section_code"], g["group_type"], g.get("title"),
                     g["content"], g["sort_order"]),
                )
                group_id_map[g["local_id"]] = cur.fetchone()[0]

            qid_map = {}  # (section_code, number_in_section) -> question id
            for q in data["questions"]:
                gid = group_id_map.get(q.get("group_local_id")) if q.get("group_local_id") else None
                cur.execute(
                    """INSERT INTO questions
                       (exam_id, group_id, section_code, qtype_code, mondai_no,
                        number_in_section, stem, options, correct_option, target_text, audio_url)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (exam_id, gid, q["section_code"], q["qtype_code"], q.get("mondai_no"),
                     q["number_in_section"], q["stem"],
                     json.dumps(q.get("options") or [], ensure_ascii=False),
                     q["correct_option"], q.get("target_text"), q.get("audio_url")),
                )
                qid_map[(q["section_code"], q["number_in_section"])] = cur.fetchone()[0]

            n_exp = 0
            for e in data.get("explanations", []):
                qid = qid_map.get((e["section_code"], e["number_in_section"]))
                if qid is None:
                    print(f"WARNING: explanation 找不到對應題目 {e['section_code']}:{e['number_in_section']}，跳過")
                    continue
                cur.execute(
                    """INSERT INTO explanations (question_id, key_point, analysis_zh, distractors, evidence)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (qid, e.get("key_point"), e["analysis_zh"],
                     json.dumps(e.get("distractors") or [], ensure_ascii=False),
                     e.get("evidence")),
                )
                n_exp += 1

            n_vocab = 0
            for v in data.get("vocabulary", []):
                qid = qid_map.get((v.get("section_code"), v.get("number_in_section")))
                cur.execute(
                    """INSERT INTO vocabulary
                       (question_id, exam_id, word, reading, pos, meaning_zh, example_sentence, note, etymology_en)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (qid, exam_id, v["word"], v.get("reading"), v.get("pos"),
                     v.get("meaning_zh"), v.get("example_sentence"), v.get("note"),
                     v.get("etymology_en")),
                )
                n_vocab += 1

        conn.commit()
        print(f"匯入完成：exam_id={exam_id}（{level} {year}-{month:02d}）")
        print(f"  groups={len(group_id_map)} questions={len(qid_map)} "
              f"explanations={n_exp} vocabulary={n_vocab}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
