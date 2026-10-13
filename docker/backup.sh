#!/bin/sh
# 定時備份：啟動時立即備份一次，之後每 24 小時備份一次。
# 備份文件：/backups/jlpt_quiz-YYYYMMDD-HHMMSS.dump（pg_dump custom 格式）
# 超過 BACKUP_RETENTION_DAYS 天的舊備份自動刪除。
set -e

: "${PGHOST:?需要 PGHOST}" "${PGUSER:?需要 PGUSER}" \
  "${PGDATABASE:?需要 PGDATABASE}" "${PGPASSWORD:?需要 PGPASSWORD}"

BACKUP_DIR=/backups
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

mkdir -p "$BACKUP_DIR"

while true; do
  TS=$(date +%Y%m%d-%H%M%S)
  FILE="$BACKUP_DIR/jlpt_quiz-$TS.dump"
  echo "[backup] dumping to $FILE ..."
  if pg_dump -Fc -f "$FILE"; then
    echo "[backup] done: $(du -h "$FILE" | cut -f1)"
  else
    echo "[backup] FAILED, removing partial file"
    rm -f "$FILE"
  fi
  find "$BACKUP_DIR" -name "jlpt_quiz-*.dump" -mtime +"$RETENTION_DAYS" -delete
  echo "[backup] sleeping 24h"
  sleep 86400
done
