#!/bin/bash
# watchdog.sh — 每 30 分鐘由 cron 執行：保證 DB 與後端服務存活。
# VM 被更換後自動重建一切（postgres 重裝＋資料還原＋後端重啟）。
set -e
QUIZ="$HOME/workspace/jlpt-quiz"
LOG="$QUIZ/scripts/watchdog.log"
exec >>"$LOG" 2>&1
echo "=== $(date '+%F %T') watchdog start ==="

# 1. 資料庫
"$QUIZ/scripts/ensure_db.sh" || echo "ensure_db FAILED"

# 2. 後端
if ! curl -s -m 8 http://127.0.0.1:8000/api/exams > /dev/null; then
  echo "backend down, restarting..."
  cd "$QUIZ/backend"
  nohup ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > "$QUIZ/scripts/backend.log" 2>&1 &
  sleep 4
  curl -s -m 8 http://127.0.0.1:8000/api/exams > /dev/null && echo "backend restarted OK" || echo "backend restart FAILED"
else
  echo "backend OK"
fi

# 3. 前端靜態服務（dist 已構建為接真實後端版本）
if ! curl -s -m 8 -o /dev/null http://127.0.0.1:5173/; then
  echo "frontend down, restarting..."
  cd "$QUIZ/frontend/dist"
  nohup python3 -m http.server 5173 --bind 127.0.0.1 > "$QUIZ/scripts/frontend.log" 2>&1 &
  sleep 2
  echo "frontend restarted"
else
  echo "frontend OK"
fi
echo "=== $(date '+%F %T') watchdog done ==="
