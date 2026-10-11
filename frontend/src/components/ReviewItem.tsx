import { useState } from 'react';
import type { AnsweringQuestion, PerQuestionResult } from '../types';
import { QuestionCard } from './QuestionCard';

interface Props {
  question: AnsweringQuestion;
  result: PerQuestionResult;
  /** 在本套中的顯示序號（1-based） */
  index: number;
}

/** 錯題／成績回顧用的單題：✓/✗ 標記＋完整解析＋可展開的文章。 */
export function ReviewItem({ question, result, index }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <div className={result.is_correct ? 'review-item review-ok' : 'review-item review-bad'}>
      <div className="review-head">
        <span className={result.is_correct ? 'badge badge-ok' : 'badge badge-bad'}>
          {result.is_correct ? '✓ 答對' : '✗ 答錯'}
        </span>
        <span>
          第 {index + 1} 題（卷內第 {question.number_in_section} 題）
        </span>
        {question.group && (
          <button type="button" className="link-btn" onClick={() => setOpen(!open)}>
            {open ? '收起文章' : '查看文章'}
          </button>
        )}
      </div>
      {open && question.group && (
        <div className="passage-box">
          {question.group.title && <div className="passage-title">{question.group.title}</div>}
          <div className="passage-content">{question.group.content}</div>
        </div>
      )}
      <QuestionCard question={question} selected={result.selected_option} review={result} />
    </div>
  );
}
