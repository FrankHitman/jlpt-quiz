#!/bin/bash
# 把 VPS 上的最新資料庫備份拉取到本機（在你的 Mac 上運行）。
#
# 1. 填好下面四個變數（REMOTE_DIR 是 VPS 上部署目錄下的 backups）；
# 2. 確認 SSH 免密登入可用：ssh-copy-id user@host（如還沒設）；
# 3. 手動跑一次測試：bash scripts/pull-backup.sh
# 4. 加到 crontab 每天自動拉取：
#      crontab -e
#      0 4 * * * /bin/bash /path/to/pull-backup.sh >> ~/jlpt-backups/pull.log 2>&1
set -e

VPS_USER="root"                        # VPS 的 SSH 用戶名
VPS_HOST="jlpt.gothruwall.eu.org"      # VPS 地址或域名
REMOTE_DIR="/root/jlpt-quiz/backups"   # VPS 上部署目錄下的 backups
LOCAL_DIR="$HOME/jlpt-backups"         # 本機存放目錄
RETENTION_DAYS=14                      # 本機保留天數

mkdir -p "$LOCAL_DIR"
rsync -avz --include="jlpt_quiz-*.dump" --exclude="*" \
  "$VPS_USER@$VPS_HOST:$REMOTE_DIR/" "$LOCAL_DIR/"
find "$LOCAL_DIR" -name "jlpt_quiz-*.dump" -mtime +"$RETENTION_DAYS" -delete
LATEST=$(ls -t "$LOCAL_DIR"/jlpt_quiz-*.dump 2>/dev/null | head -1)
echo "[pull-backup] latest: ${LATEST:-無備份文件}"
