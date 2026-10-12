#!/bin/bash
# Docker 容器啟動入口：等 DB → 建表 → 匯入 seed 試卷 → 啟動 uvicorn
set -e

# pipeline/import_exam.py 只讀固定路徑 ~/workspace/jlpt-quiz/backend/.env，這裡按容器環境生成它
mkdir -p /root/workspace/jlpt-quiz/backend
echo "DATABASE_URL=$DATABASE_URL" > /root/workspace/jlpt-quiz/backend/.env
export HOME=/root

echo "[entrypoint] waiting for postgres..."
until python3 -c "import os,psycopg; psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=3).close()" 2>/dev/null; do
  sleep 2
done
echo "[entrypoint] postgres is up"

python3 - <<'EOF'
import os, glob, json, subprocess, psycopg
url = os.environ['DATABASE_URL']
conn = psycopg.connect(url)
conn.autocommit = True
with conn.cursor() as cur:
    # 1) 全新庫：建表
    n = cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='questions'").fetchone()[0]
    if n == 0:
        print("[entrypoint] creating tables from schema.sql")
        cur.execute(open('/app/pipeline/schema.sql', encoding='utf-8').read())
    # 2) 舊庫升級：冪等遷移（以後新增欄位/表也在此處追加）
    for ddl in [
        "ALTER TABLE questions ADD COLUMN IF NOT EXISTS target_text TEXT",
        "ALTER TABLE vocabulary ADD COLUMN IF NOT EXISTS etymology_en TEXT",
        "ALTER TABLE explanations ADD COLUMN IF NOT EXISTS option_readings JSONB",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT",
        """CREATE TABLE IF NOT EXISTS wrong_answers (
          id SERIAL PRIMARY KEY,
          user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
          attempt_id INT REFERENCES attempts(id) ON DELETE SET NULL,
          created_at TIMESTAMPTZ DEFAULT now(),
          wrong_count INT NOT NULL DEFAULT 1,
          mastered BOOLEAN NOT NULL DEFAULT FALSE,
          mastered_at TIMESTAMPTZ,
          review_count INT NOT NULL DEFAULT 0,
          last_reviewed_at TIMESTAMPTZ,
          UNIQUE(user_id, question_id)
        )""",
    ]:
        cur.execute(ddl)
    # 3) 匯入 seed 試卷
    seeds = sorted(glob.glob('/app/pipeline/seed/*/exam.json'))
    q_db = cur.execute("SELECT count(*) FROM questions").fetchone()[0]
    print("[entrypoint] questions in db:", q_db)
    if q_db == 0:
        for jf in seeds:
            print("[entrypoint] importing", jf)
            subprocess.run(['python3', '/app/pipeline/import_exam.py', jf], check=True)
    else:
        # 舊庫：seed 比庫新（多了 target_text / 生詞等）時重新匯入；
        # import 冪等，但會清空該套試卷的舊作答明細（attempt_answers 級聯）
        need = False
        for jf in seeds:
            data = json.load(open(jf, encoding='utf-8'))
            seed_tt = sum(1 for q in data['questions'] if q.get('target_text'))
            db_tt = cur.execute("SELECT count(*) FROM questions WHERE target_text IS NOT NULL").fetchone()[0]
            seed_v = len(data.get('vocabulary', []))
            db_v = cur.execute("SELECT count(*) FROM vocabulary").fetchone()[0]
            if seed_tt > db_tt or seed_v != db_v:
                need = True
                break
        if need:
            print("[entrypoint] seed data newer than db, re-importing")
            for jf in seeds:
                subprocess.run(['python3', '/app/pipeline/import_exam.py', jf], check=True)
        else:
            print("[entrypoint] db already up to date")
conn.close()
EOF

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
