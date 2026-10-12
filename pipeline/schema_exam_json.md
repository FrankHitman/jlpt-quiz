# exam.json 格式說明（JLPT N1 刷題系統・試卷結構化標準）

供以後年份（2015-07 … 2025-12 …）的資料 agent 複用。JSON 為 UTF-8（`ensure_ascii=False`）。

## 頂層結構

```json
{
  "exam": {"level": "N1", "year": 2025, "month": 12, "title": "2025年12月 JLPT N1"},
  "groups": [...],
  "questions": [...],
  "explanations": [...],
  "vocabulary": [...]
}
```

## exam

| 欄位 | 型別 | 說明 |
|---|---|---|
| level | string | 固定 `"N1"` |
| year | int | 如 2025 |
| month | int | 7 或 12 |
| title | string | 如 `"2025年12月 JLPT N1"` |

## groups（文章組）

讀解的每一篇文章建一個 group；語彙・文法（問題1–7）與聽解不建 group（question 的 `group_local_id` 為 null）。

| 欄位 | 型別 | 說明 |
|---|---|---|
| local_id | string | 組內唯一 ID，如 `"g_mid2"`、`"g_info"`；questions 用 `group_local_id` 引用 |
| section_code | string | `"lang_reading"` 或 `"listening"` |
| group_type | string | `"passage"`（讀解文章） |
| title | string\|null | 如 `"問題9 (2) キャリア教育"` |
| content | string | 文章全文（含「（中略）」與（注）腳註）；表格轉為文字敘述，數字精確 |
| sort_order | int | 試卷順序（1 起） |

## questions

| 欄位 | 型別 | 說明 |
|---|---|---|
| group_local_id | string\|null | 對應 groups.local_id；無文章時為 null |
| section_code | string | `"lang_reading"`／`"listening"` |
| qtype_code | string | 必須使用 TASKS.md 題型代碼表（如 `kanji_reading`、`mid_reading`、`listening_task`） |
| mondai_no | int\|null | 大題編號：言語知識・読解為 1–13，聽解為 1–5 |
| number_in_section | int | section 內題號＝**試卷原題號**（言語知識・読解：1–66；聽解：1–30） |
| stem | string | 題干原文。問題6 保留 ★ 標記；聽解無題干時寫題型＋場景說明（如 `"聽解問題3・概要理解（無印刷內容，聽後作答）"`） |
| options | array | `[{"key":"1","text":"..."},...]`。有印刷選項時必須 4 項；聽解無印刷選項（問題3、問題4、問題5-1番）時為 `[]`（絕不編造選項） |
| correct_option | string | `"1"`–`"4"`，以答案表為最終依據 |
| target_text | string\|null | 題干中需強調的候選詞原文（如漢字讀音題的 `頑丈`、近義詞題的 `誇張`）；前端渲染時加粗＋下劃線。必須在 `stem` 中原樣出現 |

## explanations

以 `(section_code, number_in_section)` 對應到 question。

| 欄位 | 型別 | 說明 |
|---|---|---|
| section_code | string | 同上 |
| number_in_section | int | 同上 |
| key_point | string\|null | 考點（如 `"〜なくしては（N1）"`、`"一詞多義・搭配邊界"`）；文法題註明級別 |
| analysis_zh | string | 繁中解析：正確答案為何對（必填） |
| distractors | array | `[{"option":"2","why_wrong":"..."}]`；每個迷惑選項都要具體說明錯因（搭配錯誤／語義不合／偷換概念…），不可只寫「不符合」；無迷惑選項概念時（如聽解問題3/4）為 `[]` |
| evidence | string\|null | 讀解題必填：引用原文關鍵句（≤50 字）＋位置（如「第2段第3句」）；聽解寫應對策略要點可留空 |
| option_readings | object\|null | 四個選項的假名注音，如 `{"1":"がんじょう","2":"かんじょう"}`；選項本身已是純假名時該鍵可省略 |
| option_meanings | object\|null | 四個選項的中文意思，如 `{"1":"堅固","2":"感情"}`；與 option_readings 同規則，純假名選項/無印刷選項可省略 |

## vocabulary

以 `(section_code, number_in_section)` 連結到出處題；找不到對應題時 question_id 記 NULL（exam_id 必填）。

| 欄位 | 型別 | 說明 |
|---|---|---|
| section_code | string | 出處題的 section |
| number_in_section | int | 出處題號 |
| word | string | 單詞（如 `"卓越"`） |
| reading | string\|null | 讀音（如 `"たくえつ"`） |
| pos | string\|null | 詞性（≤16 字，如 `"形容動詞"`、`"副詞"`） |
| meaning_zh | string\|null | 繁中釋義 |
| example_sentence | string\|null | 例句（優先用真題原句） |
| note | string\|null | 記憶點／易混淆辨析 |
| etymology_en | string\|null | 片假名外來語的詞源英文（如 `"lead"`、`"career anchor"`）；非外來語留空 |

## manifest.json（同目錄）

```json
{
  "level": "N1",
  "year": 2025,
  "month": 12,
  "total_questions": 96,
  "by_section": {"lang_reading": 66, "listening": 30},
  "missing": [],
  "listening_without_printed_options": [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
  "answer_verified": true,
  "answer_source": "考生上傳的答案速查表圖片（非本 PDF 內容）",
  "notes": "…"
}
```

- `missing`：缺頁導致無法還原的題號（如 `"lang_reading:51"`）；**絕不臆造**，有缺就在此列出並跳過入庫。
- `answer_verified`：是否已逐題用答案表核對過 `correct_option`。
- 每次新增年份複用本格式；`import_exam.py` 讀取本格式入庫。
