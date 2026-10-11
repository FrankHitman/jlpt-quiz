import type { AnsweringQuestion, PerQuestionResult } from '../types';
import { qtypeName } from '../qtypes';

interface Props {
  question: AnsweringQuestion;
  /** 作答模式下已選的選項 key；回顧模式可傳 result.selected_option */
  selected: string | null;
  onSelect?: (key: string) => void;
  disabled?: boolean;
  /** 回顧模式：顯示 ✓/✗、正確答案與解析 */
  review?: PerQuestionResult | null;
  showHeader?: boolean;
}

export function QuestionCard({ question, selected, onSelect, disabled, review, showHeader = true }: Props) {
  const isReview = !!review;
  return (
    <div className="qcard">
      {showHeader && (
        <div className="qcard-meta">
          <span className="qtype-tag">{qtypeName(question.qtype_code)}</span>
          {question.mondai_no != null && <span>問題{question.mondai_no}</span>}
          <span>第 {question.number_in_section} 題</span>
        </div>
      )}
      <div className="qcard-stem">{question.stem}</div>
      {question.options.length === 0 ? (
        <div className="notice">此題為聽解題，無印刷選項（暫無音頻，僅供查看題型）。</div>
      ) : (
        <div className="options">
          {question.options.map((o) => {
            let cls = 'option';
            if (isReview && review) {
              if (o.key === review.correct_option) cls += ' option-correct';
              else if (o.key === review.selected_option) cls += ' option-wrong';
            } else if (selected === o.key) {
              cls += ' option-selected';
            }
            return (
              <button
                key={o.key}
                type="button"
                className={cls}
                disabled={disabled || isReview}
                onClick={() => onSelect?.(o.key)}
              >
                <span className="option-key">{o.key}</span>
                <span className="option-text">{o.text}</span>
                {isReview && review && o.key === review.correct_option && <span className="mark">✓</span>}
                {isReview && review && o.key === review.selected_option && o.key !== review.correct_option && (
                  <span className="mark">✗</span>
                )}
              </button>
            );
          })}
        </div>
      )}
      {isReview && review && (
        <div className="explanation">
          <div className="expl-row">
            <strong>你的答案：</strong>
            {review.selected_option ?? '未作答'}
            <span className="expl-sep">　</span>
            <strong>正確答案：</strong>
            {review.correct_option}
          </div>
          {review.explanation.key_point && (
            <div className="expl-row">
              <strong>考點：</strong>
              {review.explanation.key_point}
            </div>
          )}
          <div className="expl-row">
            <strong>解析：</strong>
            {review.explanation.analysis_zh}
          </div>
          {review.explanation.distractors && review.explanation.distractors.length > 0 && (
            <div className="expl-row">
              <strong>迷惑選項：</strong>
              <ul className="distractors">
                {review.explanation.distractors.map((d) => (
                  <li key={d.option}>
                    選項 {d.option}：{d.why_wrong}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {review.explanation.evidence && (
            <div className="expl-row">
              <strong>原文依據：</strong>
              {review.explanation.evidence}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
