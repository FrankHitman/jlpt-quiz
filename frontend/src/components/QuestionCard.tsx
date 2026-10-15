import type { AnsweringQuestion, PerQuestionResult } from '../types';
import { qtypeName } from '../qtypes';
import { apiOrigin } from '../api/client';
import { ExplanationBlock } from './ExplanationBlock';

/**
 * 把 stem 中第一次出現的 target_text 包成粗體＋下劃線。
 * 用 React 切分渲染，不用 dangerouslySetInnerHTML。
 */
export function renderStem(stem: string, targetText: string | null) {
  if (!targetText) return stem;
  const idx = stem.indexOf(targetText);
  if (idx < 0) return stem;
  return (
    <>
      {stem.slice(0, idx)}
      <strong>
        <u>{targetText}</u>
      </strong>
      {stem.slice(idx + targetText.length)}
    </>
  );
}

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
      <div className="qcard-stem">{renderStem(question.stem, question.target_text)}</div>
      {question.audio_url && (
        <div className="qcard-audio">
          <audio controls preload="none" src={`${apiOrigin()}${question.audio_url}`}>
            你的瀏覽器不支援音頻播放。
          </audio>
          <div className="audio-hint">聽力音頻（整卷共用）：播放後按順序作答</div>
        </div>
      )}
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
            {review.selected_option
              ? `選項 ${review.selected_option} ${question.options.find((o) => o.key === review.selected_option)?.text ?? ''}`
              : '未作答'}
          </div>
          <ExplanationBlock
            explanation={review.explanation}
            options={question.options}
            correctOption={review.correct_option}
            stemZh={question.stem_zh}
          />
        </div>
      )}
    </div>
  );
}
