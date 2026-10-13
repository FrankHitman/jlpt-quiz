import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getApi } from '../api';
import type { AnsweringQuestion, ExamSummary, PerQuestionResult, SubmitResult } from '../types';
import { qtypeOptionsForLevel } from '../qtypes';
import { QuestionCard } from '../components/QuestionCard';
import { ReviewItem } from '../components/ReviewItem';

interface PracticeProgress {
  examId: string;
  level: string;
  qtype: string;
  limit: string;
  question_ids: number[];
  answers: Record<string, string | null>;
}

const PRACTICE_PROG_KEY = 'jlpt-progress-practice';

function loadPracticeProgress(): PracticeProgress | null {
  try {
    const s = localStorage.getItem(PRACTICE_PROG_KEY);
    return s ? (JSON.parse(s) as PracticeProgress) : null;
  } catch {
    return null;
  }
}

function savePracticeProgress(p: PracticeProgress | null) {
  try {
    if (p) localStorage.setItem(PRACTICE_PROG_KEY, JSON.stringify(p));
    else localStorage.removeItem(PRACTICE_PROG_KEY);
  } catch {
    /* 忽略（隱私模式等） */
  }
}

export default function Practice() {
  const [searchParams] = useSearchParams();
  const [exams, setExams] = useState<ExamSummary[]>([]);
  const [examId, setExamId] = useState(searchParams.get('examId') ?? '');
  const [level, setLevel] = useState('');
  const [qtype, setQtype] = useState('');
  const [limit, setLimit] = useState('20');
  const [questions, setQuestions] = useState<AnsweringQuestion[] | null>(null);
  const [answers, setAnswers] = useState<Record<string, string | null>>({});
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [restored, setRestored] = useState(false);
  const [restoring, setRestoring] = useState(true);

  useEffect(() => {
    getApi()
      .then((a) => a.listExams())
      .then((list) => {
        setExams(list);
        setExamId((prev) => {
          if (prev && list.some((e) => String(e.id) === prev)) return prev;
          return list.length > 0 ? String(list[0].id) : '';
        });
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  // iOS 切後台可能整頁重載：恢復上次未提交的練習進度
  useEffect(() => {
    const saved = loadPracticeProgress();
    if (!saved || saved.question_ids.length === 0) {
      setRestoring(false);
      return;
    }
    let cancelled = false;
    getApi()
      .then(async (a) => {
        const pool = await a.getPracticeQuestions({
          exam_id: saved.examId ? Number(saved.examId) : undefined,
          qtype_code: saved.qtype || undefined,
          limit: 100,
        });
        if (cancelled) return;
        const byId = new Map(pool.map((q) => [q.id, q]));
        const qs = saved.question_ids
          .map((id) => byId.get(id))
          .filter((q): q is AnsweringQuestion => !!q);
        if (qs.length === 0) {
          savePracticeProgress(null);
        } else {
          setExamId(saved.examId);
          setLevel(saved.level);
          setQtype(saved.qtype);
          setLimit(saved.limit);
          setQuestions(qs);
          setAnswers(saved.answers);
          setRestored(true);
        }
        setRestoring(false);
      })
      .catch(() => {
        if (!cancelled) setRestoring(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const levels = [...new Set(exams.map((e) => e.level))];
  const visibleExams = level ? exams.filter((e) => e.level === level) : exams;
  // 題型下拉與級別級聯：只顯示所選級別實際有的題型
  const qtypeOptions = useMemo(() => qtypeOptionsForLevel(level), [level]);

  const isListeningQtype = qtype.startsWith('listening');

  const load = async () => {
    setError(null);
    setResult(null);
    setAttemptId(null);
    setAnswers({});
    setRestored(false);
    savePracticeProgress(null);
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

  // 作答過程中持久化（iOS 切後台重載後可恢復）
  const progressRef = useRef<PracticeProgress | null>(null);
  useEffect(() => {
    if (questions && questions.length > 0 && !result) {
      const p: PracticeProgress = {
        examId,
        level,
        qtype,
        limit,
        question_ids: questions.map((q) => q.id),
        answers,
      };
      progressRef.current = p;
      savePracticeProgress(p);
    } else {
      progressRef.current = null;
    }
  }, [questions, answers, result, examId, level, qtype, limit]);

  // iOS 上 beforeunload 不可靠，用 pagehide 在頁面被丟棄前同步落盤
  //（應對「剛作答就切後台、effect 還沒跑」的競態）
  useEffect(() => {
    const flush = () => savePracticeProgress(progressRef.current);
    window.addEventListener('pagehide', flush);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') flush();
    });
    return () => {
      window.removeEventListener('pagehide', flush);
    };
  }, []);

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
      savePracticeProgress(null);
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
    setRestored(false);
    savePracticeProgress(null);
  };

  const discardRestored = () => {
    savePracticeProgress(null);
    setRestored(false);
    reset();
  };

  return (
    <div className="practice">
      <h1>專項練習</h1>
      <p className="hint">無倒計時；提交整套後逐題顯示 ✓/✗、正確答案與解析。</p>

      <div className="filter-card">
        <label>
          級別
          <select
            value={level}
            onChange={(e) => {
              const lv = e.target.value;
              setLevel(lv);
              // 級別變更後，若當前已選題型在該級別不存在，回到「全部題型」
              const opts = qtypeOptionsForLevel(lv);
              if (qtype && !opts.some((o) => o.code === qtype)) setQtype('');
              const first = exams.find((x) => !lv || x.level === lv);
              setExamId(first ? String(first.id) : '');
            }}
          >
            <option value="">全部級別</option>
            {levels.map((lv) => (
              <option key={lv} value={lv}>
                {lv}
              </option>
            ))}
          </select>
        </label>
        <label>
          試卷
          <select value={examId} onChange={(e) => setExamId(e.target.value)}>
            {visibleExams.map((e) => (
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
            {qtypeOptions.map((o) => (
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

      {restoring && <div className="loading">恢復進度中…</div>}

      {!restoring && restored && questions !== null && questions.length > 0 && !result && (
        <div className="notice">
          已恢復上次未完成的練習（{Object.values(answers).filter((v) => v != null).length}/
          {questions.length} 題已作答）。
          <button type="button" className="link-btn" onClick={discardRestored}>
            丟棄並重新篩選
          </button>
        </div>
      )}

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
