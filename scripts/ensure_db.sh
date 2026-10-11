#!/bin/bash
# ensure_db.sh — 冪等：保證 PostgreSQL 可用且 jlpt_quiz 資料庫已還原。
# 用途：VM 被更換後（/usr、/var 會被清空），一鍵重建資料庫。
# 資料以 Debian 預設 cluster（/var/lib/postgresql，隨 VM 重置）運行；
# 真正的持久來源是 ~/workspace/jlpt-quiz/pipeline/seed/*/exam.json，重建約 2 分鐘。
set -e
QUIZ="$HOME/workspace/jlpt-quiz"
export PATH="/usr/bin:$PATH"

log() { echo "[ensure_db] $*"; }

# 1. 二進制檔（VM 更換後需重裝）
if [ ! -x /usr/bin/pg_ctlcluster ]; then
  log "postgres binaries missing, reinstalling..."
  sudo apt-get update -qq
  sudo apt-get install -y -qq postgresql
fi

# 2. 啟動 Debian cluster 16/main
if ! sudo -u postgres /usr/bin/pg_isready -q 2>/dev/null; then
  log "starting cluster 16/main..."
  sudo /usr/bin/pg_ctlcluster 16 main start
fi
sudo -u postgres /usr/bin/pg_isready -q || { log "FATAL: postgres did not start"; exit 1; }

# 3. 角色與資料庫（密碼與 backend/.env 保持一致，後端經 127.0.0.1 scram-sha-256 連線）
DBPASS="$(grep '^DATABASE_URL=' "$QUIZ/backend/.env" | sed 's/.*jlpt_app://; s/@.*//')"
if [ -z "$DBPASS" ]; then log "FATAL: cannot read password from backend/.env"; exit 1; fi
PSQL="sudo -u postgres /usr/bin/psql"
$PSQL -tA -c "SELECT 1 FROM pg_roles WHERE rolname='jlpt_app'" | grep -q 1 || \
  { log "creating role jlpt_app"; $PSQL -c "CREATE ROLE jlpt_app LOGIN SUPERUSER"; }
$PSQL -c "ALTER ROLE jlpt_app PASSWORD '$DBPASS'" > /dev/null
$PSQL -tA -c "SELECT 1 FROM pg_database WHERE datname='jlpt_quiz'" | grep -q 1 || \
  { log "creating database jlpt_quiz"; $PSQL -c "CREATE DATABASE jlpt_quiz OWNER jlpt_app"; }

# 4. 建表（若缺）
if [ "$($PSQL -d jlpt_quiz -tA -c "SELECT count(*) FROM information_schema.tables WHERE table_name='questions'")" = "0" ]; then
  log "creating tables from schema.sql"
  cp "$QUIZ/pipeline/schema.sql" /tmp/jlpt_schema.sql && chmod 644 /tmp/jlpt_schema.sql
  $PSQL -d jlpt_quiz -f /tmp/jlpt_schema.sql > /dev/null
fi

# 5. 匯入試卷（若空）
if [ "$($PSQL -d jlpt_quiz -tA -c 'SELECT count(*) FROM questions')" = "0" ]; then
  log "importing 2025-12 exam data..."
  (cd "$QUIZ/pipeline" && "$QUIZ/backend/venv/bin/python" import_exam.py "$QUIZ/pipeline/seed/2025-12/exam.json")
fi

log "OK — questions=$($PSQL -d jlpt_quiz -tA -c 'SELECT count(*) FROM questions'), explanations=$($PSQL -d jlpt_quiz -tA -c 'SELECT count(*) FROM explanations')"
