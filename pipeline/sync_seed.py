#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""非破壞性 seed 同步：把 exam.json 的修訂就地 UPDATE 進既有資料庫。

用法：
    python3 sync_seed.py pipeline/seed/2023-12/exam.json [更多 exam.json ...]
    python3 sync_seed.py --all                 # 同步 pipeline/seed/*/exam.json
    python3 sync_seed.py --all --dry-run       # 只報告差異，不寫入

為什麼不用 import_exam.py 更新已上線的庫：
    import_exam.py 的冪等做法是先 DELETE 整套 exam（ON DELETE CASCADE），
    會連帶刪掉 questions，並級聯刪除引用 question_id 的 attempt_answers
    與 wrong_answers（錯題本），question id 也會全部換新。

本腳本的做法（保留關聯性）：
    - exam 以 (level, year, month) 匹配；question 以
      (exam_id, section_code, number_in_section) 匹配（該組合有 UNIQUE 約束）。
    - 既有 question 一律 UPDATE 原行，id 不變，因此 users、attempts、
      attempt_answers、wrong_answers 的關聯全部保留。
    - explanation 以 question_id 匹配 UPDATE；缺失才 INSERT。
    - vocabulary 沒有任何用戶數據引用其 id：以 (question_id, word) 匹配
      UPDATE，seed 新增的 INSERT，seed 已移除的 DELETE（僅限該套試卷）。
    - question_group 以 (exam_id, section_code, sort_order) 匹配 UPDATE。
    - DB 中存在但 seed 已沒有的 question：不刪除（刪除會級聯用戶數據），
      只在報告中列為警告，交由人工決定。
    - correct_option 若與 DB 不同：照常 UPDATE，但會在報告中單獨列出，
      因為既有 attempt_answers.is_correct 與錯題本是按舊答案計算的，
      需要人工評估是否重算（本腳本不擅自重算、不刪除）。

DATABASE_URL 來源：環境變數優先，其次 <專案根>/backend/.env，
最後 ~/workspace/jlpt-quiz/backend/.env（與 import_exam.py 相同）。
"""
import argparse
import glob
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

SECTIONS = [
    {"code": "lang_reading", "name_jp": "言語知識（文字・語彙・文法）・読解",
     "name_zh": "語言知識（文字・詞彙・文法）・讀解", "time_limit_min": 110, "sort_order": 1},
    {"code": "listening", "name_jp": "聴解", "name_zh": "聽解",
     "time_limit_min": 55, "sort_order": 2},
]


def load_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    candidates = [
        os.path.join(PROJECT_ROOT, "backend", ".env"),
        os.path.expanduser("~/workspace/jlpt-quiz/backend/.env"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ERROR: 找不到 DATABASE_URL（環境變數與 backend/.env 都沒有）")


def jdump(v):
    if v is None:
        return None
    return json.dumps(v, ensure_ascii=False)


def jnorm(v):
    """JSONB 經 psycopg 讀回為 Python 物件；統一成可比較形態。"""
    if v is None:
        return None
    return json.loads(json.dumps(v, ensure_ascii=False))


def sync_exam(cur, data, dry_run, report):
    exam = data["exam"]
    level, year, month = exam["level"], exam["year"], exam["month"]
    tag = f"{level} {year}-{month:02d}"
    st = {"q_upd": 0, "q_ins": 0, "e_upd": 0, "e_ins": 0,
          "v_upd": 0, "v_ins": 0, "v_del": 0, "g_upd": 0, "g_ins": 0,
          "answer_changes": [], "orphan_questions": []}
    report["exams"].append((tag, st))

    cur.execute("SELECT id, title FROM exams WHERE level=%s AND year=%s AND month=%s",
                (level, year, month))
    row = cur.fetchone()
    is_new = row is None
    if is_new:
        cur.execute("INSERT INTO exams (level, year, month, title) VALUES (%s,%s,%s,%s) RETURNING id",
                    (level, year, month, exam["title"]))
        exam_id = cur.fetchone()[0]
        for s in SECTIONS:
            cur.execute("""INSERT INTO sections (exam_id, code, name_jp, name_zh, time_limit_min, sort_order)
                           VALUES (%s,%s,%s,%s,%s,%s)""",
                        (exam_id, s["code"], s["name_jp"], s["name_zh"], s["time_limit_min"], s["sort_order"]))
    else:
        exam_id, db_title = row
        if db_title != exam["title"]:
            cur.execute("UPDATE exams SET title=%s WHERE id=%s", (exam["title"], exam_id))
        # sections 只補缺，不覆寫既有時間設定
        cur.execute("SELECT code FROM sections WHERE exam_id=%s", (exam_id,))
        have_codes = {r[0] for r in cur.fetchall()}
        for s in SECTIONS:
            if s["code"] not in have_codes:
                cur.execute("""INSERT INTO sections (exam_id, code, name_jp, name_zh, time_limit_min, sort_order)
                               VALUES (%s,%s,%s,%s,%s,%s)""",
                            (exam_id, s["code"], s["name_jp"], s["name_zh"], s["time_limit_min"], s["sort_order"]))

    # ---- question_groups：以 (section_code, sort_order) 匹配 ----
    cur.execute("SELECT id, section_code, sort_order, group_type, title, content FROM question_groups WHERE exam_id=%s",
                (exam_id,))
    gmap = {}
    for gid, sc, so, gt, ti, co in cur.fetchall():
        gmap[(sc, so)] = (gid, gt, ti, co)
    local_to_db = {}
    for g in data.get("groups", []):
        key = (g["section_code"], g["sort_order"])
        if key in gmap:
            gid, gt, ti, co = gmap[key]
            local_to_db[g["local_id"]] = gid
            if (gt, ti, co) != (g["group_type"], g.get("title"), g["content"]):
                cur.execute("UPDATE question_groups SET group_type=%s, title=%s, content=%s WHERE id=%s",
                            (g["group_type"], g.get("title"), g["content"], gid))
                st["g_upd"] += 1
        else:
            cur.execute("""INSERT INTO question_groups (exam_id, section_code, group_type, title, content, sort_order)
                           VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (exam_id, g["section_code"], g["group_type"], g.get("title"), g["content"], g["sort_order"]))
            local_to_db[g["local_id"]] = cur.fetchone()[0]
            st["g_ins"] += 1

    # ---- questions：以 (section_code, number_in_section) 匹配，UPDATE 保留 id ----
    cur.execute("""SELECT id, section_code, number_in_section, group_id, qtype_code, mondai_no,
                          stem, stem_zh, options, correct_option, target_text, audio_url
                   FROM questions WHERE exam_id=%s""", (exam_id,))
    qmap = {}
    for r in cur.fetchall():
        qmap[(r[1], r[2])] = r
    seed_qkeys = set()
    qid_map = {}
    for q in data["questions"]:
        key = (q["section_code"], q["number_in_section"])
        seed_qkeys.add(key)
        gid = local_to_db.get(q.get("group_local_id")) if q.get("group_local_id") else None
        new_vals = (gid, q["qtype_code"], q.get("mondai_no"), q["stem"], q.get("stem_zh"),
                    jnorm(q.get("options") or []), str(q["correct_option"]), q.get("target_text"),
                    q.get("audio_url"))
        if key not in qmap:
            cur.execute("""INSERT INTO questions
                           (exam_id, group_id, section_code, qtype_code, mondai_no,
                            number_in_section, stem, stem_zh, options, correct_option, target_text, audio_url)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (exam_id, new_vals[0], key[0], new_vals[1], new_vals[2], key[1],
                         new_vals[3], new_vals[4], jdump(new_vals[5]), new_vals[6], new_vals[7], new_vals[8]))
            qid_map[key] = cur.fetchone()[0]
            st["q_ins"] += 1
            continue
        r = qmap[key]
        qid = r[0]
        qid_map[key] = qid
        old_vals = (r[3], r[4], r[5], r[6], r[7], jnorm(r[8]), r[9], r[10], r[11])
        if old_vals[6] != new_vals[6]:
            st["answer_changes"].append(f"{tag} {key[0]} Q{key[1]}: {old_vals[6]} -> {new_vals[6]}")
        if old_vals != new_vals:
            cur.execute("""UPDATE questions SET group_id=%s, qtype_code=%s, mondai_no=%s, stem=%s,
                                  stem_zh=%s, options=%s, correct_option=%s, target_text=%s, audio_url=%s
                           WHERE id=%s""",
                        (new_vals[0], new_vals[1], new_vals[2], new_vals[3], new_vals[4],
                         jdump(new_vals[5]), new_vals[6], new_vals[7], new_vals[8], qid))
            st["q_upd"] += 1
    for key in qmap:
        if key not in seed_qkeys:
            st["orphan_questions"].append(f"{tag} {key[0]} Q{key[1]} (id={qmap[key][0]})")

    # ---- explanations：以 question_id 匹配 ----
    cur.execute("""SELECT e.question_id, e.key_point, e.analysis_zh, e.distractors, e.evidence,
                          e.option_readings, e.option_meanings
                   FROM explanations e JOIN questions q ON q.id = e.question_id
                   WHERE q.exam_id=%s""", (exam_id,))
    emap = {r[0]: r[1:] for r in cur.fetchall()}
    for e in data.get("explanations", []):
        key = (e["section_code"], e["number_in_section"])
        qid = qid_map.get(key)
        if qid is None:
            report["warnings"].append(f"{tag} explanation 找不到題目 {key}，跳過")
            continue
        # 與 import_exam.py 的儲存形態對齊：distractors 缺省 []、readings/meanings 缺省 {}，
        # 避免 None 與空集合的表示差異造成每次同步都誤判有變更。
        new_vals = (e.get("key_point"), e["analysis_zh"], jnorm(e.get("distractors") or []),
                    e.get("evidence"), jnorm(e.get("option_readings") or {}),
                    jnorm(e.get("option_meanings") or {}))
        if qid not in emap:
            cur.execute("""INSERT INTO explanations
                           (question_id, key_point, analysis_zh, distractors, evidence, option_readings, option_meanings)
                           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                        (qid, new_vals[0], new_vals[1], jdump(new_vals[2]), new_vals[3],
                         jdump(new_vals[4]), jdump(new_vals[5])))
            st["e_ins"] += 1
        else:
            old = emap[qid]
            old_vals = (old[0], old[1], jnorm(old[2]), old[3], jnorm(old[4]), jnorm(old[5]))
            if old_vals != new_vals:
                cur.execute("""UPDATE explanations SET key_point=%s, analysis_zh=%s, distractors=%s,
                                      evidence=%s, option_readings=%s, option_meanings=%s
                               WHERE question_id=%s""",
                            (new_vals[0], new_vals[1], jdump(new_vals[2]), new_vals[3],
                             jdump(new_vals[4]), jdump(new_vals[5]), qid))
                st["e_upd"] += 1

    # ---- vocabulary：無用戶數據引用其 id，可安全增刪改 ----
    cur.execute("SELECT id, question_id, word, reading, pos, meaning_zh, example_sentence, note, etymology_en "
                "FROM vocabulary WHERE exam_id=%s", (exam_id,))
    vmap = {}
    for r in cur.fetchall():
        vmap[(r[1], r[2])] = r
    seed_vkeys = set()
    for v in data.get("vocabulary", []):
        qid = qid_map.get((v.get("section_code"), v.get("number_in_section"))) \
            if v.get("section_code") is not None else None
        key = (qid, v["word"])
        seed_vkeys.add(key)
        new_vals = (v.get("reading"), v.get("pos"), v.get("meaning_zh"),
                    v.get("example_sentence"), v.get("note"), v.get("etymology_en"))
        if key not in vmap:
            cur.execute("""INSERT INTO vocabulary
                           (question_id, exam_id, word, reading, pos, meaning_zh, example_sentence, note, etymology_en)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        (qid, exam_id, v["word"], *new_vals))
            st["v_ins"] += 1
        else:
            r = vmap[key]
            if tuple(r[3:9]) != new_vals:
                cur.execute("""UPDATE vocabulary SET reading=%s, pos=%s, meaning_zh=%s,
                                      example_sentence=%s, note=%s, etymology_en=%s WHERE id=%s""",
                            (*new_vals, r[0]))
                st["v_upd"] += 1
    for key, r in vmap.items():
        if key not in seed_vkeys:
            cur.execute("DELETE FROM vocabulary WHERE id=%s", (r[0],))
            st["v_del"] += 1
    return st


def main():
    ap = argparse.ArgumentParser(description="非破壞性 seed 同步（保留 question id 與用戶數據關聯）")
    ap.add_argument("files", nargs="*", help="exam.json 路徑")
    ap.add_argument("--all", action="store_true", help="同步 pipeline/seed/*/exam.json 全部")
    ap.add_argument("--dry-run", action="store_true", help="只報告差異，最後 rollback 不寫入")
    args = ap.parse_args()

    files = list(args.files)
    if args.all:
        files += sorted(glob.glob(os.path.join(SCRIPT_DIR, "seed", "*", "exam.json")))
    if not files:
        ap.error("請給 exam.json 路徑，或用 --all")
    files = sorted(set(files))

    try:
        import psycopg
    except ImportError:
        sys.exit("ERROR: 需要 psycopg（pip install 'psycopg[binary]'）")

    report = {"exams": [], "warnings": []}
    conn = psycopg.connect(load_database_url())
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            for jf in files:
                with open(jf, encoding="utf-8") as f:
                    data = json.load(f)
                sync_exam(cur, data, args.dry_run, report)
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    tot = {"q_upd": 0, "q_ins": 0, "e_upd": 0, "e_ins": 0,
           "v_upd": 0, "v_ins": 0, "v_del": 0, "g_upd": 0, "g_ins": 0}
    answer_changes, orphans = [], []
    for tag, st in report["exams"]:
        for k in tot:
            tot[k] += st[k]
        answer_changes += st["answer_changes"]
        orphans += st["orphan_questions"]
        changed = sum(st[k] for k in tot)
        if changed or st["answer_changes"] or st["orphan_questions"]:
            print(f"{tag}: questions upd={st['q_upd']} ins={st['q_ins']}, "
                  f"explanations upd={st['e_upd']} ins={st['e_ins']}, "
                  f"vocab upd={st['v_upd']} ins={st['v_ins']} del={st['v_del']}, "
                  f"groups upd={st['g_upd']} ins={st['g_ins']}")
    print(f"[sync_seed] {'DRY-RUN（未寫入）' if args.dry_run else '已提交'}："
          f"{len(report['exams'])} 套試卷，questions upd={tot['q_upd']} ins={tot['q_ins']}，"
          f"explanations upd={tot['e_upd']} ins={tot['e_ins']}，"
          f"vocab upd={tot['v_upd']} ins={tot['v_ins']} del={tot['v_del']}，"
          f"groups upd={tot['g_upd']} ins={tot['g_ins']}")
    for a in answer_changes:
        print("ANSWER-CHANGE（既有作答/錯題本按舊答案計算，請人工評估）:", a)
    for o in orphans:
        print("WARNING seed 已無此題但 DB 保留（未刪除，避免級聯用戶數據）:", o)
    for w in report["warnings"]:
        print("WARNING:", w)


if __name__ == "__main__":
    main()
