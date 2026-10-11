#!/usr/bin/env python3
"""等待 PostgreSQL 就緒（最多 20 分鐘），然後執行試卷匯入＋驗證。"""
import os
import subprocess
import sys
import time

WORKSPACE = os.path.expanduser("~/workspace/jlpt-quiz")
ENV = os.path.join(WORKSPACE, "backend", ".env")
SEED = os.path.join(WORKSPACE, "pipeline", "seed", "2025-12")
IMPORTER = os.path.join(WORKSPACE, "pipeline", "import_exam.py")
EXAM_JSON = os.path.join(SEED, "exam.json")


def get_url():
    if not os.path.exists(ENV):
        return None
    for line in open(ENV, encoding="utf-8"):
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def db_ready():
    url = get_url()
    if not url:
        return False
    try:
        import psycopg
        c = psycopg.connect(url, connect_timeout=5)
        c.close()
        return True
    except Exception:
        return False


deadline = time.time() + 20 * 60
while time.time() < deadline:
    if db_ready():
        break
    time.sleep(30)
else:
    print("TIMEOUT: 20 分鐘內 DB 未就緒（backend/.env 或連線失敗）")
    print("JSON＋importer＋manifest 已完成，待 DB 就緒後執行：")
    print(f"  python3 {IMPORTER} {EXAM_JSON}")
    sys.exit(2)

print("DB 就緒，開始匯入…")
r = subprocess.run([sys.executable, IMPORTER, EXAM_JSON],
                   capture_output=True, text=True)
print(r.stdout)
print(r.stderr, file=sys.stderr)
if r.returncode != 0:
    print("IMPORT FAILED")
    sys.exit(1)

# 冪等驗證：重跑一次，題數應不變
r2 = subprocess.run([sys.executable, IMPORTER, EXAM_JSON],
                    capture_output=True, text=True)
print("重跑輸出：", r2.stdout.strip().split("\n")[-1] if r2.stdout.strip() else "(empty)")

import psycopg
conn = psycopg.connect(get_url())
cur = conn.cursor()
counts = {}
for t in ["exams", "sections", "question_groups", "questions",
          "explanations", "vocabulary"]:
    cur.execute(f"SELECT count(*) FROM {t}")
    counts[t] = cur.fetchone()[0]
    print(f"{t}: {counts[t]}")
# explanations 覆蓋率
cur.execute("""SELECT count(*) FROM questions q
               LEFT JOIN explanations e ON e.question_id = q.id
               WHERE e.id IS NULL""")
print("無解析題數:", cur.fetchone()[0])
conn.close()

ok = (counts["questions"] == 96 and counts["explanations"] == 96
      and counts["question_groups"] == 13 and counts["vocabulary"] == 26)
print("驗收:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
