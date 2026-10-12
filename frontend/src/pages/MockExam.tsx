import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { getApi } from '../api';
import type { AnsweringQuestion, ExamDetail } from '../types';
import { Timer } from '../components/Timer';
import { QuestionCard } from '../components/QuestionCard';
import { QuestionNav } from '../components/QuestionNav';

interface Progress {
  attempt_id: number;
  started_at: number;
  time_limit_min: number;
  answers: Record<string, string | null>;
  flags: string[];
}

const progKey = (examId: string, section: string) => `jlpt-progress-mock-${examId}-${section}`;

function loadProgress(examId: string, section: string): Progress | null {
  try {
    const s = localStorage.getItem(progKey(examId, section));
    return s ? (JSON.parse(s) as Progress) : null;
  } catch {
    return null;
  }
}

export default function MockExam() {
  const { examId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const examIdNum = Number(examId);
  // ?section=listening 開聽解模擬考，其餘預設言語讀解
  const SECTION = searchParams.get('section') === 'listening' ? 'listening' : 'lang_reading';

  const [exam, setExam] = useState<ExamDetail | null>(null);
  const [questions, setQuestions] = useState<AnsweringQuestion[] | null>(null);
  const [progress, setProgress] = useState<Progress | null>(() => loadProgress(examId, SECTION));
  const [idx, setIdx] = useState(0);
  const [now, setNow] = useState(() => Date.now());
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittedRef = useRef(false);

  useEffect(() => {
    if (!examIdNum) return;
    getApi()
      .then((a) => a.getExam(examIdNum))
      .then(setExam)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, [examIdNum]);

  // 有進行中進度時取題（支援重新整理後恢復）
  useEffect(() => {
    if (!progress || !examIdNum) return;
    getApi()
      .then((a) => a.getExamQuestions(examIdNum, SECTION))
      .then(setQuestions)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, [examIdNum, progress]);

  // 持久化進度
  useEffect(() => {
    if (progress) {
      try {
        localStorage.setItem(progKey(examId, SECTION), JSON.stringify(progress));
      } catch {
        /* 忽略 */
      }
    }
  }, [progress, examId]);

  // 倒計時 tick
  useEffect(() => {
    if (!progress || submittedRef.current) return;
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, [progress]);

  const secondsLeft = progress
    ? Math.max(0, progress.time_limit_min * 60 - Math.floor((now - progress.started_at) / 1000))
    : 0;

  const doSubmit = useCallback(
    async (auto: boolean) => {
      if (submittedRef.current || !progress || !questions) return;
      if (!auto) {
        const unanswered = questions.filter((q) => progress.answers[String(q.id)] == null).length;
        if (
          !window.confirm(
            `確定要提交嗎？${unanswered > 0 ? `還有 ${unanswered} 題未作答，將計為答錯。` : ''}`,
          )
        )
          return;
      }
      submittedRef.current = true;
      setSubmitting(true);
      try {
        const a = await getApi();
        const answers = questions.map((q) => ({
          question_id: q.id,
          selected_option: progress.answers[String(q.id)] ?? null,
        }));
        await a.submitAttempt(progress.attempt_id, answers);
        try {
          localStorage.removeItem(progKey(examId, SECTION));
        } catch {
          /* 忽略 */
        }
        navigate(`/result/${progress.attempt_id}`);
      } catch (e: unknown) {
        submittedRef.current = false;
        setSubmitting(false);
        setError(e instanceof Error ? e.message : String(e));
      }
    },
    [progress, questions, examId, navigate],
  );

  // 時間到自動提交
  useEffect(() => {
    if (progress && questions && secondsLeft <= 0 && !submittedRef.current) {
      void doSubmit(true);
    }
  }, [progress, questions, secondsLeft, doSubmit]);

  const start = async () => {
    setError(null);
    try {
      const a = await getApi();
      const att = await a.startAttempt({ exam_id: examIdNum, mode: 'mock', section_code: SECTION });
      const qs = await a.getExamQuestions(examIdNum, SECTION);
      const p: Progress = {
        attempt_id: att.attempt_id,
        started_at: Date.now(),
        time_limit_min: att.time_limit_min ?? 110,
        answers: {},
        flags: [],
      };
      setProgress(p);
      setQuestions(qs);
      setIdx(0);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const select = (key: string) => {
    if (!progress || !questions) return;
    const qid = String(questions[idx].id);
    setProgress({ ...progress, answers: { ...progress.answers, [qid]: key } });
  };

  const toggleFlag = () => {
    if (!progress || !questions) return;
    const qid = String(questions[idx].id);
    const flags = progress.flags.includes(qid)
      ? progress.flags.filter((f) => f !== qid)
      : [...progress.flags, qid];
    setProgress({ ...progress, flags });
  };

  // ---- 考前確認頁 ----
  if (!progress) {
    const section = exam?.sections.find((s) => s.code === SECTION);
    return (
      <div className="confirm">
        <h1>模擬考試</h1>
        {error && <div className="error">{error}</div>}
        {!exam ? (
          <div className="loading">載入中…</div>
        ) : (
          <>
            <h2>{exam.title}</h2>
            <ul className="rules">
              <li>範圍：{section?.name_zh ?? '—'}，共 {section?.question_count ?? '—'} 題</li>
              <li>時間：{section?.time_limit_min ?? 110} 分鐘倒計時，時間到自動提交</li>
              <li>可中途手動提交；可將題目「標記待定」稍後回來檢查</li>
              {SECTION === 'listening' && (
                <li>聽解音頻為整卷單個文件，請先播放再按順序作答</li>
              )}
            </ul>
            <button type="button" className="btn btn-primary btn-lg" onClick={() => void start()}>
              開始考試
            </button>
          </>
        )}
      </div>
    );
  }

  if (!questions) {
    return (
      <div className="loading-page">
        {error ? <div className="error">載入題目失敗：{error}</div> : <div className="loading">載入題目中…</div>}
      </div>
    );
  }

  // ---- 作答頁 ----
  const q = questions[idx];
  const answered = questions.map((qq) => progress.answers[String(qq.id)] != null);
  const flagged = questions.map((qq) => progress.flags.includes(String(qq.id)));
  const answeredCount = answered.filter(Boolean).length;

  return (
    <div className="mock-layout">
      <div className="mock-topbar">
        <Timer secondsLeft={secondsLeft} />
        <span className="mock-progress">
          第 {idx + 1} / {questions.length} 題・已答 {answeredCount}
        </span>
        <button
          type="button"
          className="btn btn-primary"
          disabled={submitting}
          onClick={() => void doSubmit(false)}
        >
          {submitting ? '提交中…' : '提交試卷'}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="mock-body">
        <aside className="mock-side">
          <QuestionNav total={questions.length} current={idx} answered={answered} flagged={flagged} onJump={setIdx} />
        </aside>
        <div className="mock-main">
          {q.group ? (
            <div className="split">
              <div className="passage-panel">
                {q.group.title && <h3>{q.group.title}</h3>}
                <div className="passage-scroll">{q.group.content}</div>
              </div>
              <QuestionCard question={q} selected={progress.answers[String(q.id)] ?? null} onSelect={select} />
            </div>
          ) : (
            <QuestionCard question={q} selected={progress.answers[String(q.id)] ?? null} onSelect={select} />
          )}
          <div className="mock-actions">
            <button type="button" className="btn" disabled={idx === 0} onClick={() => setIdx(idx - 1)}>
              上一題
            </button>
            <button
              type="button"
              className={flagged[idx] ? 'btn btn-flagged' : 'btn'}
              onClick={toggleFlag}
            >
              {flagged[idx] ? '取消待定' : '標記待定'}
            </button>
            <button
              type="button"
              className="btn"
              disabled={idx === questions.length - 1}
              onClick={() => setIdx(idx + 1)}
            >
              下一題
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
