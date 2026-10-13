# JLPT 刷題系統

個人自用的 N1 真題刷題網站：PDF 試卷結構化入庫（PostgreSQL）→ 網頁模擬考（倒計時）／專項練習 → 提交後給正確率、錯題集、逐題解析。免登入，預留用戶系統升級接口。

## 在自己的電腦上運行（推薦）

需先安裝 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows／Mac 均可）。

```bash
# 1. 解壓原始碼包，進入目錄
cd jlpt-quiz

# 2. 一鍵啟動（首次會自動建表並匯入 2025-12 真題，約 2-3 分鐘）
docker compose up -d --build

# 3. 瀏覽器打開
# http://localhost:5173
```

常用命令：`docker compose logs -f` 查看日誌；`docker compose down` 停止（加 `-v` 會清空題庫資料）。

> 版本更新：下載新版原始碼包覆蓋後，直接 `docker compose up -d --build` 即可——後端容器啟動時會自動做冪等遷移（加列、補新數據），舊的作答記錄不受影響，只有該套試卷的作答「明細」在數據版本變化時會重導清空。

> 進階：部署到雲伺服器時，把 `docker-compose.yml` 中的 `VITE_API_BASE` 改為伺服器的公網地址（如 `http://你的IP:8000/api`）後重新 `docker compose up -d --build` 即可。

## 手動運行（不使用 Docker）

```bash
# 1. 資料庫（含自動重建；VM 更換後跑一次即可恢復）
~/workspace/jlpt-quiz/scripts/ensure_db.sh

# 2. 後端 API（http://127.0.0.1:8000，文件：/docs）
cd ~/workspace/jlpt-quiz/backend && ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3. 前端（http://127.0.0.1:5173）
cd ~/workspace/jlpt-quiz/frontend/dist && python3 -m http.server 5173 --bind 127.0.0.1
```

或由看門狗一次搞定（含每 30 分鐘自檢）：`~/workspace/jlpt-quiz/scripts/watchdog.sh`
（已設 cron 每 30 分鐘執行，VM 更換後自動恢復服務。）

## 目錄結構

```
jlpt-quiz/
├── TASKS.md                 # agent 任務清單（含 DB schema、API 契約）
├── README.md                # 本文件
├── scripts/
│   ├── ensure_db.sh         # 冪等：重裝 postgres → 還原 pgdata → 建表 → 匯入試卷
│   └── watchdog.sh          # 保活：DB＋後端＋前端（cron 每 30 分鐘）
├── pgdata/                  # PostgreSQL 資料目錄（持久化在 workspace）
├── pipeline/
│   ├── schema.sql           # 9 張表 DDL
│   ├── schema_exam_json.md  # 試卷 JSON 格式說明
│   ├── import_exam.py       # 通用匯入程式（冪等）
│   └── seed/2025-12/        # 2025-12 真題：exam.json、transcription.md、manifest.json
├── backend/                 # FastAPI（:8000）
│   ├── .env                 # DATABASE_URL（chmod 600，僅本地）
│   ├── app/                 # main/models/schemas/routers/auth
│   └── venv/
└── frontend/                # React+Vite+TS；dist/ 為生產構建（接真實後端）
```

## 功能

- **首頁**：試卷卡片（年份／題數／考試時間），「模擬考試」「專項練習」兩個入口
- **模擬考**：言語知識・讀解 110 分鐘倒計時（官方時間；聽解 55 分鐘，暫無音頻不提供模擬），時間到自動提交，中途可手動提交；題號面板＋標記待定；刷新可恢復進度
- **專項練習**：按年份＋題型篩選（如文法填空、一詞多義），無倒計時，提交後逐題即時顯示對錯＋解析
- **成績頁**：正確率、按 section／題型統計、錯題集（你的答案／正確答案／完整解析／讀解原文依據），可只看錯題
- **用戶系統預留**：`users` 表已建；`app/auth.py` 的 `get_current_user_optional()` 無 header 回 None；`/api/auth/register`、`/api/auth/login` 暫回 501

## 新增一套試卷

1. 把 PDF（題目＋答案）放到 `pipeline/seed/<年份>-<月份>/`
2. 按 `pipeline/schema_exam_json.md` 整理成 `exam.json`（題干、4 選項、以答案表為準核對答案、逐題解析＋迷惑選項辨析＋讀解原文依據）
3. 跑 `(cd pipeline && ../backend/venv/bin/python import_exam.py)`（同一卷重跑會先清舊資料）

## 考試時間（jlpt.jp 官方）

N1：言語知識（文字・語彙・文法）・読解 **110 分鐘**；聴解 **55 分鐘**（2022 年起由 60 改為 55，題數同步調整為 30 題）。存於 `sections.time_limit_min`，可配置。

## 備份與恢復

`backup` 服務每天自動備份一次資料庫（pg_dump，存於部署目錄下的 `backups/`），
預設保留 7 天（`BACKUP_RETENTION_DAYS` 環境變數可調）。

恢復（在 VPS 部署目錄下執行）：

```bash
./scripts/restore.sh backups/jlpt_quiz-20261014-030000.dump
```

把備份同步到自己的電腦（二選一）：

```bash
# 方案 A：rsync 腳本（推薦，見文件內註釋填好 VPS 信息後加到本機 crontab）
bash scripts/pull-backup.sh

# 方案 B：ansible（ansible/ 目錄下有現成 playbook）
cp ansible/inventory.ini.example ansible/inventory.ini  # 填好後
ansible-playbook -i ansible/inventory.ini ansible/pull-backup.yml
```

## 已知限制

- 聽解暫無音頻：只入庫了題目冊資訊（題型＋選項），模擬考暫不含聽解
- 未啟用登入：作答記錄的 `user_id` 暫為 NULL
- 服務跑在 VM 本機：公開上線需自行部署到 VPS（`docker-compose.yml` 待補）
- 題庫內容僅供個人學習，不對外發布
