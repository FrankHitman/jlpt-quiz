#!/bin/bash
# 從資料庫備份恢復。
# 用法（在 VPS 的部署目錄下執行）：
#   ./scripts/restore.sh backups/jlpt_quiz-20261014-030000.dump
#
# 會先停掉 backend/backup 避免連接衝突，重建 jlpt_quiz 庫後用 pg_restore 還原。
set -e

FILE="${1:?用法：restore.sh <dump 文件路徑>}"
[ -f "$FILE" ] || { echo "找不到文件：$FILE"; exit 1; }

echo "[restore] stopping backend & backup..."
docker compose stop backend backup

echo "[restore] recreating database..."
docker compose exec -T db psql -U jlpt_app -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='jlpt_quiz' AND pid <> pg_backend_pid();" > /dev/null
docker compose exec -T db dropdb -U jlpt_app jlpt_quiz
docker compose exec -T db createdb -U jlpt_app jlpt_quiz

echo "[restore] restoring from $FILE ..."
docker compose exec -T db pg_restore -U jlpt_app -d jlpt_quiz --no-owner < "$FILE"

echo "[restore] starting backend & backup..."
docker compose start backend backup
echo "[restore] done"
