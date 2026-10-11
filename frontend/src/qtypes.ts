// 題型代碼表（TASKS.md 全系統統一），繁體中文名供 UI 顯示。
export const QTYPE_ZH: Record<string, string> = {
  kanji_reading: '漢字讀音',
  vocab_fill: '語彙填空',
  synonym: '近義詞替換',
  word_usage: '詞語用法判斷',
  grammar_fill: '文法填空',
  sentence_order: '句子排序（★）',
  text_grammar: '文章文法',
  short_reading: '短文讀解',
  mid_reading: '中長文讀解',
  long_reading: '長文讀解',
  comparison_reading: '對比讀解',
  info_retrieval: '資訊檢索',
  listening_task: '聽解・課題理解',
  listening_point: '聽解・要點理解',
  listening_summary: '聽解・概要理解',
  listening_response: '聽解・即時應答',
  listening_comprehensive: '聽解・綜合理解',
};

export const SECTION_ZH: Record<string, string> = {
  lang_reading: '言語知識・讀解',
  listening: '聽解',
};

export function qtypeName(code: string): string {
  return QTYPE_ZH[code] ?? code;
}

export function sectionName(code: string): string {
  return SECTION_ZH[code] ?? code;
}

/** UI 顯示用：已知代碼一律用繁體中文名，未知則用後端回傳的 name_zh。 */
export function sectionDisplay(code: string, fallback?: string): string {
  return SECTION_ZH[code] ?? fallback ?? code;
}

/** 題型下拉選單用的有序選項（按試卷出現順序）。 */
export const QTYPE_OPTIONS: { code: string; name: string }[] = Object.entries(QTYPE_ZH).map(
  ([code, name]) => ({ code, name }),
);
