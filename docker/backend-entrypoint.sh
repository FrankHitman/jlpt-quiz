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
import os, glob, subprocess, psycopg
url = os.environ['DATABASE_URL']
conn = psycopg.connect(url)
conn.autocommit = True
with conn.cursor() as cur:
    n = cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_name='questions'").fetchone()[0]
    if n == 0:
        print("[entrypoint] creating tables from schema.sql")
        cur.execute(open('/app/pipeline/schema.sql', encoding='utf-8').read())
    q = cur.execute("SELECT count(*) FROM questions").fetchone()[0]
    print("[entrypoint] questions in db:", q)
    if q == 0:
        for jf in sorted(glob.glob('/app/pipeline/seed/*/exam.json')):
            print("[entrypoint] importing", jf)
            subprocess.run(['python3', '/app/pipeline/import_exam.py', jf], check=True)
conn.close()
EOF

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
