import type { Explanation, OptionItem } from '../types';

/**
 * 解析區塊：考點＋解析＋正確答案（含注音）＋迷惑選項（含注音）＋原文依據＋生詞。
 * 可在成績回顧與錯題本復用。
 */
export function ExplanationBlock({
  explanation,
  options,
  correctOption,
}: {
  explanation: Explanation;
  options: OptionItem[];
  correctOption: string | null;
}) {
  const textOf = (key: string): string => options.find((o) => o.key === key)?.text ?? '';
  const readingOf = (key: string): string | null => {
    const r = explanation.option_readings?.[key];
    if (!r) return null;
    // 注音與原文相同（純假名選項）時不重複顯示
    return r === textOf(key) ? null : r;
  };
  const meaningOf = (key: string): string | null =>
    explanation.option_meanings?.[key] ?? null;
  /** 選項標註：選項3 部門（ぶもん；部門）——有注音/意思才顯示括號 */
  const optLabel = (key: string): React.ReactNode => {
    const notes = [readingOf(key), meaningOf(key)].filter(Boolean) as string[];
    return (
      <>
        選項 {key} {textOf(key)}
        {notes.length > 0 ? `（${notes.join('；')}）` : ''}
      </>
    );
  };

  return (
    <div className="explanation">
      {explanation.key_point && (
        <div className="expl-row">
          <strong>考點：</strong>
          {explanation.key_point}
        </div>
      )}
      <div className="expl-row">
        <strong>解析：</strong>
        {explanation.analysis_zh}
      </div>
      {correctOption && (
        <div className="expl-row">
          <strong>正確答案：</strong>
          {optLabel(correctOption)}
        </div>
      )}
      {explanation.distractors && explanation.distractors.length > 0 && (
        <div className="expl-row">
          <strong>迷惑選項：</strong>
          <ul className="distractors">
            {explanation.distractors.map((d) => (
              <li key={d.option}>
                {optLabel(d.option)}：{d.why_wrong}
              </li>
            ))}
          </ul>
        </div>
      )}
      {explanation.evidence && (
        <div className="expl-row">
          <strong>原文依據：</strong>
          {explanation.evidence}
        </div>
      )}
      {explanation.vocabulary && explanation.vocabulary.length > 0 && (
        <div className="expl-row">
          <strong>生詞：</strong>
          <ul className="vocab-list">
            {explanation.vocabulary.map((v, i) => (
              <li key={i}>
                {v.word}
                {v.reading ? `（${v.reading}）` : ''}
                {v.meaning_zh ? `：${v.meaning_zh}` : ''}
                {v.etymology_en ? ` ← 英語 ${v.etymology_en}` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
