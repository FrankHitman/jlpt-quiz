#!/bin/bash
# Docker 容器啟動入口：等 DB → 建表/遷移 → 非破壞性同步 seed → 啟動 uvicorn
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
import os, psycopg
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
        "ALTER TABLE explanations ADD COLUMN IF NOT EXISTS option_meanings JSONB",
        "ALTER TABLE questions ADD COLUMN IF NOT EXISTS stem_zh TEXT",
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
conn.close()
EOF

# 3) seed 同步：一律使用非破壞性同步（pipeline/sync_seed.py）。
#    它按 (level,year,month) + (section_code,number_in_section) 匹配既有題目並就地
#    UPDATE，question id 不變，users / attempts / attempt_answers / wrong_answers
#    （錯題本）的關聯全部保留；全新庫則直接 INSERT 建庫。
#    舊的 SEED_AUTO_REIMPORT 已廢棄：它控制的 import_exam.py 重導會先 DELETE 整套
#    試卷並級聯刪除作答明細與錯題本，entrypoint 不再走那條路徑。
#    如需完全跳過同步，設 SEED_SYNC=0。
if [ "${SEED_SYNC:-1}" != "0" ]; then
  echo "[entrypoint] syncing seed data (non-destructive)..."
  python3 /app/pipeline/sync_seed.py --all
else
  echo "[entrypoint] SEED_SYNC=0, skipping seed sync"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
