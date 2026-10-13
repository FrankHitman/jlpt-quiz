# JLPT 刷題系統 — Agent 任務清單（TASKS.md）

> 專案目標：為 Charles（個人自用學習）打造一個免登入的線上 JLPT 刷題系統：
> PDF 試卷 → 結構化入庫（PostgreSQL）→ Web 模擬考（倒計時）＋專項練習（按題型）→ 提交後給正確率、錯題集、逐題解析。
> 介面語言：繁體中文。題庫內容僅供個人學習使用，不得對外發布。

## 0. 全局約定（所有 agent 必讀）

- 工作目錄：`~/workspace/jlpt-quiz/`，子目錄：`pipeline/`（解析管線）、`backend/`（FastAPI）、`frontend/`（React+Vite+TS）、`docs/`。
- 技術棧：PostgreSQL 16（`apt` 安裝）＋ Python 3.12 FastAPI ＋ SQLAlchemy ＋ React 18 + Vite + TypeScript。
- 資料庫：`jlpt_quiz`，帳號 `jlpt_app`（密碼見 `backend/.env`，僅本地使用）。
- 官方考試時間（N1，已查 jlpt.jp 官方指南＋2022 年改定）：**言語知識（文字・語彙・文法）・読解 ＝ 110 分鐘；聴解 ＝ 55 分鐘**（2022 年起聽解由 60 改為 55，題數同步調整為 30 題）。`sections.time_limit_min` 預設填 110 / 55，保留可配置。
- 每個任務完成後必須跑一遍自己的驗收標準，並把結果寫進任務回報。
- 不得臆造題目內容；掃描不清處標註 `[原文不清]`；若真有缺頁，標註 `[缺頁]` 並記入 manifest。
- 個人學習用途：題庫資料只存本地資料庫，不對外提供下載或公開服務。

## 題型代碼表（qtype_code，全系統統一）

| code | 中文名 | 問題編號 |
|---|---|---|
| kanji_reading | 漢字讀音 | 問題1 |
| vocab_fill | 語彙填空 | 問題2 |
| synonym | 近義詞替換 | 問題3 |
| word_usage | 詞語用法判斷 | 問題4 |
| grammar_fill | 文法填空 | 問題5 |
| sentence_order | 句子排序（★） | 問題6 |
| text_grammar | 文章文法 | 問題7 |
| short_reading | 短文讀解 | 問題8 |
| mid_reading | 中長文讀解 | 問題9 |
| long_reading | 長文讀解 | 問題10/12 |
| comparison_reading | 對比讀解 | 問題11 |
| info_retrieval | 資訊檢索 | 問題13 |
| listening_task | 聽解・課題理解 | 聽解問題1 |
| listening_point | 聽解・要點理解 | 聽解問題2 |
| listening_summary | 聽解・概要理解 | 聽解問題3 |
| listening_response | 聽解・即時應答 | 聽解問題4 |
| listening_comprehensive | 聽解・綜合理解 | 聽解問題5 |

section_code：`lang_reading`（言語知識・読解）、`listening`（聴解）。

---

## T1. 資料庫建置（DB agent）

**目標**：安裝 PostgreSQL 16，建庫建表，輸出連線資訊。

**輸入**：本文件的 schema 定義。

**輸出**：
1. 執行成功的 PostgreSQL 16（`sudo apt-get install -y postgresql`，啟動服務，開機自啟）。
2. 資料庫 `jlpt_quiz` ＋ 角色 `jlpt_app`（SUPERUSER 以便建表；密碼寫入 `~/workspace/jlpt-quiz/backend/.env`）。
3. 按下方 DDL 建表（欄位名、型別、約束照抄）。

```sql
CREATE TABLE exams (
  id SERIAL PRIMARY KEY,
  level VARCHAR(2) NOT NULL DEFAULT 'N1',
  year INT NOT NULL,
  month INT NOT NULL CHECK (month IN (7,12)),
  title TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(level, year, month)
);
CREATE TABLE sections (
  id SERIAL PRIMARY KEY,
  exam_id INT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
  code VARCHAR(32) NOT NULL,
  name_jp TEXT NOT NULL,
  name_zh TEXT NOT NULL,
  time_limit_min INT NOT NULL,
  sort_order INT NOT NULL,
  UNIQUE(exam_id, code)
);
CREATE TABLE question_groups (
  id SERIAL PRIMARY KEY,
  exam_id INT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
  section_code VARCHAR(32) NOT NULL,
  group_type VARCHAR(32) NOT NULL,           -- passage | dialogue | instruction
  title TEXT,
  content TEXT NOT NULL,                      -- 文章/對話原文（聽解腳本）
  sort_order INT NOT NULL
);
CREATE TABLE questions (
  id SERIAL PRIMARY KEY,
  exam_id INT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
  group_id INT REFERENCES question_groups(id) ON DELETE SET NULL,
  section_code VARCHAR(32) NOT NULL,
  qtype_code VARCHAR(32) NOT NULL,
  mondai_no INT,                              -- 問題1..13（聽解為1..5）
  number_in_section INT NOT NULL,             -- section 內題號
  stem TEXT NOT NULL,                         -- 題干（含★標記與空格）
  options JSONB NOT NULL,                     -- [{"key":"1","text":"..."}]，固定4項
  correct_option VARCHAR(4) NOT NULL,
  target_text TEXT,                           -- 題干中需強調的候選詞（漢字讀音/近義詞題），可空
  audio_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(exam_id, section_code, number_in_section)
);
CREATE TABLE explanations (
  id SERIAL PRIMARY KEY,
  question_id INT NOT NULL UNIQUE REFERENCES questions(id) ON DELETE CASCADE,
  key_point TEXT,                             -- 考點（如：〜なくしては／一詞多義・搭配邊界）
  analysis_zh TEXT NOT NULL,                  -- 繁中解析
  distractors JSONB,                          -- [{"option":"2","why_wrong":"..."}] 迷惑選項為何錯
  evidence TEXT,                              -- 原文依據（讀解：引用關鍵句＋位置；無則NULL）
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE vocabulary (
  id SERIAL PRIMARY KEY,
  question_id INT REFERENCES questions(id) ON DELETE SET NULL,
  exam_id INT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
  word TEXT NOT NULL,
  reading TEXT,
  pos VARCHAR(16),
  meaning_zh TEXT,
  example_sentence TEXT,
  note TEXT,
  etymology_en TEXT                           -- 片假名外來語的詞源英文（如 lead），可空
);
-- 用戶系統預留（暫不啟用登入，表先建好、API 留接口）
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username TEXT UNIQUE,
  password_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE TABLE attempts (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE SET NULL,  -- 暫為 NULL
  exam_id INT REFERENCES exams(id) ON DELETE SET NULL,
  mode VARCHAR(16) NOT NULL,                  -- mock | practice（practice＝專項練習）
  section_code VARCHAR(32),
  qtype_code VARCHAR(32),
  time_limit_min INT,
  started_at TIMESTAMPTZ DEFAULT now(),
  submitted_at TIMESTAMPTZ,
  total INT,
  correct INT
);
CREATE TABLE attempt_answers (
  id SERIAL PRIMARY KEY,
  attempt_id INT NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
  question_id INT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  selected_option VARCHAR(4),
  is_correct BOOLEAN,
  answered_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(attempt_id, question_id)
);
-- 錯題本（需登入；提交時答錯自動收錄）
CREATE TABLE wrong_answers (
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
);
```

**驗收標準**：
- `psql -U jlpt_app -d jlpt_quiz -c '\dt'` 列出 9 張表。
- `backend/.env` 存在且 `DATABASE_URL` 可連線。
- 回報：PostgreSQL 版本、連線字串、建表清單。

**約束**：不得修改欄位名；`questions.options` 必須是 4 項陣列（由匯入程式保證，DB 層不強制）。

---

## T2. 試卷結構化＋答案核對＋解析入庫（資料 agent）

**目標**：把 2025 年 12 月 N1 試卷轉成標準 JSON，核對答案，撰寫逐題解析，匯入資料庫。

**輸入**：
- `~/workspace/jlpt-quiz/pipeline/seed/2025-12/2025_12_N1.pdf`：掃描版試卷（45 頁）。**需自行用 `pdftoppm -r 120` 轉為 PNG 並逐頁轉錄題干與選項**（第 1 頁為廣告頁跳過；夾雜的「樹先生日語」廣告忽略）。
- 答案依據：**PDF 第 19 頁答案速查表**（轉成圖片後自行讀取，為最終答案依據）。
- 解析底稿：`~/workspace/your_files/2025年12月JLPT_N1真題考點分析.md`（逐題考點、迷惑選項辨析、讀解原文依據均已整理好，直接採用）。
- **已知修正**：問題1第4題「卓越」正讀 **たくえつ**，正確答案為 **2**（轉錄註記的 `答案:1` 是錯的，以答案表為準）
- **勘誤（2026-10-06 已更正）**：曾誤標「考試第 18 頁缺失」，實查證實**並無缺頁**——PDF 第 19 頁即考試第 18 頁，含問題9文章(2)（キャリア教育）全文與第 51 題；PDF 第 20 頁含第 52 題。51、52 題解析見 `~/workspace/your_files/2025年12月JLPT_N1真題考點分析_缺頁補做.md`（51→2，52→1）。**絕不臆造**任何題目內容。

**輸出**：
1. `~/workspace/jlpt-quiz/pipeline/schema_exam_json.md`：標準 JSON 格式說明（供以後年份複用）。
2. `~/workspace/jlpt-quiz/pipeline/seed/2025-12/exam.json`：完整結構化試卷，格式：
   ```json
   {
     "exam": {"level":"N1","year":2025,"month":12,"title":"2025年12月 JLPT N1"},
     "groups": [{"local_id":"g_mid2","section_code":"lang_reading","group_type":"passage","title":"...","content":"...","sort_order":6}],
     "questions": [{"group_local_id":"g_mid2","section_code":"lang_reading","qtype_code":"mid_reading","mondai_no":9,"number_in_section":53,"stem":"...","options":[{"key":"1","text":"..."},{"key":"2","text":"..."},{"key":"3","text":"..."},{"key":"4","text":"..."}],"correct_option":"3"}],
     "explanations": [{"section_code":"lang_reading","number_in_section":53,"key_point":"...","analysis_zh":"...","distractors":[{"option":"1","why_wrong":"..."}], "evidence":"..."}],
     "vocabulary": [{"number_in_section":4,"section_code":"lang_reading","word":"卓越","reading":"たくえつ","meaning_zh":"卓越、傑出","example_sentence":"...","note":"..."}]
   }
   ```
3. `~/workspace/jlpt-quiz/pipeline/import_exam.py`：通用匯入程式（讀 JSON → 寫 DB；冪等：同一 `level/year/month` 重跑先刪舊資料）。
4. `~/workspace/jlpt-quiz/pipeline/seed/2025-12/manifest.json`：`{"total_questions": N, "missing": [...], "answer_verified": true, "notes": "..."}`。
5. 資料庫中有一套完整 2025-12 試題＋解析。

**答案核對規則**（重要）：
- 以 PDF 第 19 頁答案表為最終依據，逐題比對轉錄的答案；不一致時以答案表為準並記入 manifest。
- 每題必須 4 個選項；`correct_option` 必須是其中之一。

**解析撰寫規則**：
- 每題都要有 `analysis_zh`（繁中）：說明正確答案為何對。
- 每個迷惑選項都要有 `why_wrong`：具體指出錯在哪（搭配錯誤／語義不合／偷換概念…），不要只寫「不符合」。
- 讀解題 `evidence` 必須引用原文關鍵句並註明位置（如「第2段第3句」）；引用原文不超過 50 字。
- 文法題 `key_point` 註明句型級別（N1/N2）。
- 聽解題：本 PDF 只有題目冊（無音頻無腳本），`stem` 註明題型與場景，`content` 留空，`analysis_zh` 寫應對策略；`audio_url` 留 NULL。

**驗收標準**：
- `SELECT count(*) FROM questions` ＝ manifest 的 total_questions；`explanations` 覆蓋率 100%。
- 隨機抽 5 題人工比對：題干、選項、答案、解析無誤。
- 重跑 `import_exam.py` 不產生重複資料。

**約束**：`qtype_code` 必須使用本文件的題型代碼表；不得虛構缺頁內容。

---

## T3. 後端 API（後端 agent）

**目標**：FastAPI 服務，實現題庫查詢、作答、判分、解析回傳；預留用戶系統接口。

**輸入**：T1 的資料庫、T2 的資料、API 契約（下方）。

**輸出**：`~/workspace/jlpt-quiz/backend/` 完整專案（`requirements.txt`、`app/`、`app/main.py`、`app/models.py`、`app/schemas.py`、`app/routers/*.py`、`app/auth.py`、`.env`），監聽 `127.0.0.1:8000`。

**API 契約**（base `/api`，全部回傳 JSON）：

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/api/exams` | 試卷列表：`[{id, level, year, month, title, sections:[{code, name_zh, time_limit_min, question_count}]}]` |
| GET | `/api/exams/{id}` | 試卷詳情（含 sections 與各題型題數統計） |
| GET | `/api/exams/{id}/questions?section=lang_reading` | 作答用題目：**不含** `correct_option`；含 `target_text`（題干強調詞，無則 null）；group 文章以 `group` 物件內嵌 |
| GET | `/api/practice/questions?qtype_code=&exam_id=&section=&limit=20` | 專項練習題目（不含答案） |
| POST | `/api/attempts` | 開始作答 `{exam_id, mode, section_code?, qtype_code?, question_ids?}`（mode 枚舉：`mock` 模擬考、`practice` 專項練習） → `{attempt_id, time_limit_min}` |
| POST | `/api/attempts/{id}/submit` | 提交 `{answers:[{question_id, selected_option}]}` → `{total, correct, accuracy, per_question:[{question_id, selected_option, correct_option, is_correct, explanation:{key_point, analysis_zh, distractors, evidence, vocabulary:[{word, reading, meaning_zh, etymology_en}]}}], wrong_question_ids}` |
| GET | `/api/attempts/{id}` | 查看某次作答結果（含錯題＋解析） |
| POST | `/api/auth/register` | 註冊 `{username, password}` → `{token, user}`；重複用戶名 400 |
| POST | `/api/auth/login` | 登入 `{username, password}` → `{token, user}`；失敗 401 |
| GET | `/api/auth/me` | 憑 token 回當前用戶（需登入） |
| GET | `/api/wrong-answers?mastered=&qtype_code=` | 錯題本列表（需登入）：question（無答案）＋explanation（含生詞）＋wrong_count/mastered |
| POST | `/api/wrong-answers/{id}/master` | 標記已掌握（需登入） |
| POST | `/api/wrong-answers/{id}/unmaster` | 取消掌握（需登入） |
| DELETE | `/api/wrong-answers/{id}` | 刪除錯題（需登入） |
| POST | `/api/wrong-answers/practice` | 錯題重練 `{question_ids}` → 建 `mode='practice'`、`section_code='wrong_review'` 的 attempt（需登入） |

**用戶系統預留**（`app/auth.py`）：
- `get_current_user_optional()`：讀 `Authorization: Bearer <token>`；無 header 則回 `None`，**不得報錯**；有 header 但未啟用則忽略。
- 所有 `/api/attempts*` 經由該依賴把 `user_id`（可為 NULL）寫入 attempts 表。
- `users` 表已建好，啟用時只需實作 register/login 發 token。

**用戶系統已啟用（2026-10-11）**：
- JWT（pyjwt，HS256，30 天有效期），密鑰取 `JWT_SECRET` 環境變數（無則開發預設值＋日誌警告）。
- `POST /api/attempts`、`/submit` 用可選認證：登入用戶自動寫入 `attempts.user_id`，匿名保持 NULL。
- 提交時：登入用戶答錯的題自動 upsert 進 `wrong_answers`（wrong_count+1；曾掌握則重置）；`section_code='wrong_review'` 的重練提交中答對的題自動 mastered=true、review_count+1。

**驗收標準**：
- `uvicorn app.main:app` 啟動無報錯；`curl`  walkthrough：建 attempt → 取題 → 提交 → 正確率計算正確 → 錯題解析完整。
- 考試模式取題 API **絕不洩露** `correct_option`（寫一個測試斷言）。
- 倒計時由前端控制，後端記錄 `submitted_at` 並在超時提交時照常判分（標記 `overtime:true`）。

**約束**：CORS 允許 `http://localhost:5173`；錯誤回傳統一 `{"detail": ...}`。

---

## T4. 前端（前端 agent）

**目標**：React + Vite + TS 單頁應用，繁體中文介面，實現選卷、模擬考、專項練習、成績＋錯題本。

**輸入**：T3 的 API（以契約為準；若後端未就緒，先用 `src/mocks/` 假資料開發，接口對齊後切換）。

**輸出**：`~/workspace/jlpt-quiz/frontend/` 完整專案，`npm run dev` 跑在 `5173`。

**頁面／功能**：

1. **首頁 `/`**：試卷卡片（年份、屆別、題數、兩 section 倒計時長）；兩個入口：「模擬考試」「專項練習」。
2. **模擬考 `/mock/:examId`**：
   - 開始前確認頁（顯示 110 分鐘／55 分鐘規則、題數）。
   - 倒計時器（`lang_reading` 110 分鐘；聽解暫不提供模擬考——無音頻——顯示提示）；時間到自動提交；**中途可手動提交**。
   - 題號面板（答題狀態色塊）、上一題／下一題、標記待定。
   - 閱讀文章與題目左右分欄（文章可滾動）。
3. **專項練習 `/practice`**：篩選器（年份＋題型，如「文法填空」「一詞多義」）；**無倒計時**；提交整套後每題即時顯示 ✓/✗＋正確答案＋解析。
4. **成績頁 `/result/:attemptId`**：正確率、按 section／題型統計、**錯題集**（題干＋你的答案＋正確答案＋完整解析＋原文依據），支援「只看錯題」篩選。
5. **AuthContext 已實作（2026-10-11）**：`src/auth/AuthContext.tsx` 為真實實作（localStorage 存 token、啟動時 `/auth/me` 恢復、401 自動登出）；頂欄有登入／註冊彈窗、用戶名＋退出；`/wrong-book` 錯題本頁（篩選未掌握／已掌握／題型、展開解析、勾選重練、標記掌握／刪除）。匿名模式一切照舊可用。

**驗收標準**：
- `npm run build` 成功；手動走查：選卷 → 模擬考倒計時 → 中途提交 → 成績頁正確率與錯題解析正確。
- 專項練習選「文法填空」只出現該題型題目。
- 任何頁面重新整理不白屏（路由用 HashRouter 或正確 fallback）。

**約束**：UI 文字一律繁體中文；日文題目原文照登；不准把 `correct_option` 寫死在前端。

---

## T5. 整合測試與交付（coordinator）

1. 後端＋前端＋DB 全鏈路跑通；用 2025-12 資料做一次完整模擬考提交，核對正確率。
2. 寫 `~/workspace/jlpt-quiz/README.md`：啟動步驟（DB／後端／前端）、目錄結構、如何新增一套試卷（放 PDF → 跑管線 → 匯入）。
3. 回報 Charles：服務位址、功能清單、已知限制（聽解無音頻、未啟用登入）。

## 依賴關係

```
T1 ─┬─→ T2 ─→ T3 ─→ T4 ─→ T5
    └────────→ T3（schema 已定可並行，但建議等 T1 完成）
```
- T1 與 T2 可並行（T2 的 JSON 不依賴 DB）。
- T3 需要 T1 的庫；需要 T2 的資料做驗收（可用 T2 完成前先 stub）。
- T4 需要 T3 的 API 契約（先 mock 開發）。
