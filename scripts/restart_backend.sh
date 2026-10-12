#!/bin/bash
# 重啟 jlpt-quiz 後端（避開 pkill 誤殺自身：腳本文件路徑不含匹配字串）
pkill -f "[u]vicorn app\.main" 2>/dev/null
sleep 2
cd ~/workspace/jlpt-quiz/backend
nohup ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 > ~/workspace/jlpt-quiz/scripts/backend.log 2>&1 &
sleep 5
curl -s -m 8 -o /dev/null -w "backend: %{http_code}\n" http://127.0.0.1:8000/api/health
