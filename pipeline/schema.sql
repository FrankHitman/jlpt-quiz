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
  option_readings JSONB,                      -- {"1":"がんじょう",...} 四個選項的假名注音（純假名選項可省略）
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
  email TEXT UNIQUE,
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

-- 錯題本（需登錄）
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
