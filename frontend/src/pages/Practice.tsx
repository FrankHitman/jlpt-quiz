import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getApi } from '../api';
import type { AnsweringQuestion, ExamSummary, PerQuestionResult, SubmitResult } from '../types';
import { QTYPE_OPTIONS } from '../qtypes';
import { QuestionCard } from '../components/QuestionCard';
import { ReviewItem } from '../components/ReviewItem';

export default function Practice() {
  const [searchParams] = useSearchParams();
  const [exams, setExams] = useState<ExamSummary[]>([]);
  const [examId, setExamId] = useState(searchParams.get('examId') ?? '');
  const [qtype, setQtype] = useState('');
  const [limit, setLimit] = useState('20');
  const [questions, setQuestions] = useState<AnsweringQuestion[] | null>(null);
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getApi()
      .then((a) => a.listExams())
      .then((list) => {
        setExams(list);
        setExamId((prev) => prev || (list.length > 0 ? String(list[0].id) : ''));
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  const isListeningQtype = qtype.startsWith('listening');

  const load = async () => {
    setError(null);
    setResult(null);
    setAttemptId(null);
    setAnswers({});
    if (isListeningQtype) {
      setQuestions([]);
      return;
    }
    setLoading(true);
    try {
      const a = await getApi();
      const qs = await a.getPracticeQuestions({
        exam_id: examId ? Number(examId) : undefined,
        qtype_code: qtype || undefined,
        limit: Number(limit),
      });
      setQuestions(qs);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const submit = async () => {
    if (!questions || questions.length === 0) return;
    const unanswered = questions.filter((qq) => answers[String(qq.id)] == null && qq.options.length > 0).length;
    if (!window.confirm(`確定提交整套練習嗎？${unanswered > 0 ? `還有 ${unanswered} 題未作答。` : ''}`)) return;
    setLoading(true);
    try {
      const a = await getApi();
      const att = await a.startAttempt({
        exam_id: Number(examId),
        mode: 'special',
        qtype_code: qtype || undefined,
        question_ids: questions.map((qq) => qq.id),
      });
      const r = await a.submitAttempt(
        att.attempt_id,
        questions.map((qq) => ({ question_id: qq.id, selected_option: answers[String(qq.id)] ?? null })),
      );
      setResult(r);
      setAttemptId(att.attempt_id);
      window.scrollTo({ top: 0 });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const resultByQ = useMemo(() => {
    const m = new Map<number, PerQuestionResult>();
    result?.per_question.forEach((p) => m.set(p.question_id, p));
    return m;
  }, [result]);

  const reset = () => {
    setQuestions(null);
    setResult(null);
    setAttemptId(null);
    setAnswers({});
  };

  return (
    <div className="practice">
      <h1>專項練習</h1>
      <p className="hint">無倒計時；提交整套後逐題顯示 ✓/✗、正確答案與解析。</p>

      <div className="filter-card">
        <label>
          試卷
          <select value={examId} onChange={(e) => setExamId(e.target.value)}>
            {exams.map((e) => (
              <option key={e.id} value={String(e.id)}>
                {e.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          題型
          <select value={qtype} onChange={(e) => setQtype(e.target.value)}>
            <option value="">全部題型</option>
            {QTYPE_OPTIONS.map((o) => (
              <option key={o.code} value={o.code}>
                {o.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          題數
          <select value={limit} onChange={(e) => setLimit(e.target.value)}>
            <option value="10">10 題</option>
            <option value="20">20 題</option>
            <option value="30">30 題</option>
            <option value="50">50 題</option>
          </select>
        </label>
        <button type="button" className="btn btn-primary" disabled={loading} onClick={() => void load()}>
          {loading ? '載入中…' : '開始練習'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {questions !== null && isListeningQtype && (
        <div className="notice">聽解題型暫無音頻，本系統暫不提供該題型練習。</div>
      )}

      {questions !== null && !isListeningQtype && questions.length === 0 && !result && (
        <div className="notice">沒有符合條件的題目，請調整篩選條件。</div>
      )}

      {result && attemptId !== null && (
        <div className="result-summary">
          <div className="accuracy">
            正確率 <strong>{result.accuracy}%</strong>
          </div>
          <div>
            答對 {result.correct} / 共 {result.total} 題・答錯 {result.wrong_question_ids.length} 題
          </div>
          <div className="result-actions">
            <button type="button" className="btn" onClick={reset}>
              重新篩選
            </button>
            <Link className="btn" to={`/result/${attemptId}`}>
              查看成績統計
            </Link>
          </div>
        </div>
      )}

      {questions !== null && questions.length > 0 && (
        <div className="practice-list">
          {questions.map((q, i) =>
            result ? (
              <ReviewItem key={q.id} question={q} result={resultByQ.get(q.id)!} index={i} />
            ) : (
              <div key={q.id} className="practice-item">
                <div className="practice-num">第 {i + 1} 題</div>
                {q.group ? (
                  <div className="split">
                    <div className="passage-panel">
                      {q.group.title && <h3>{q.group.title}</h3>}
                      <div className="passage-scroll">{q.group.content}</div>
                    </div>
                    <QuestionCard
                      question={q}
                      selected={answers[String(q.id)] ?? null}
                      onSelect={(key) => setAnswers({ ...answers, [String(q.id)]: key })}
                    />
                  </div>
                ) : (
                  <QuestionCard
                    question={q}
                    selected={answers[String(q.id)] ?? null}
                    onSelect={(key) => setAnswers({ ...answers, [String(q.id)]: key })}
                  />
                )}
              </div>
            ),
          )}
          {!result && (
            <div className="practice-submit">
              <button type="button" className="btn btn-primary btn-lg" disabled={loading} onClick={() => void submit()}>
                {loading ? '提交中…' : '提交整套'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
