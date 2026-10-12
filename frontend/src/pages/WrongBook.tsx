import { useCallback, useEffect, useMemo, useState } from 'react';
import { getApi } from '../api';
import { promptLogin, useAuth } from '../auth/AuthContext';
import { ExplanationBlock } from '../components/ExplanationBlock';
import { QuestionCard, renderStem } from '../components/QuestionCard';
import { ReviewItem } from '../components/ReviewItem';
import { QTYPE_OPTIONS, qtypeName } from '../qtypes';
import type {
  AnsweringQuestion,
  PerQuestionResult,
  SubmitResult,
  WrongAnswerItem,
} from '../types';

type Phase = 'list' | 'answering' | 'result';
type MasterFilter = 'all' | 'unmastered' | 'mastered';

function fmtDate(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`;
}

export default function WrongBook() {
  const { user, ready } = useAuth();
  const [phase, setPhase] = useState<Phase>('list');
  const [items, setItems] = useState<WrongAnswerItem[]>([]);
  const [masterFilter, setMasterFilter] = useState<MasterFilter>('unmastered');
  const [qtype, setQtype] = useState('');
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 重新練習狀態
  const [practiceQuestions, setPracticeQuestions] = useState<AnsweringQuestion[]>([]);
  const [practiceAnswers, setPracticeAnswers] = useState<Record<string, string | null>>({});
  const [practiceAttemptId, setPracticeAttemptId] = useState<number | null>(null);
  const [practiceResult, setPracticeResult] = useState<SubmitResult | null>(null);

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setError(null);
    try {
      const api = await getApi();
      const params: { mastered?: boolean; qtype_code?: string } = {};
      if (masterFilter !== 'all') params.mastered = masterFilter === 'mastered';
      if (qtype) params.qtype_code = qtype;
      const list = await api.listWrongAnswers(params);
      setItems(list);
      setSelected(new Set());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [user, masterFilter, qtype]);

  useEffect(() => {
    if (ready && user) load();
  }, [ready, user, load]);

  const toggleSelect = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleExpand = (id: number) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const setMastered = async (item: WrongAnswerItem, mastered: boolean) => {
    try {
      const api = await getApi();
      const updated = await api.setWrongAnswerMastered(item.id, mastered);
      setItems((prev) => prev.map((w) => (w.id === item.id ? updated : w)));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const removeItem = async (item: WrongAnswerItem) => {
    if (!window.confirm('確定從錯題本刪除這道題嗎？')) return;
    try {
      const api = await getApi();
      await api.deleteWrongAnswer(item.id);
      setItems((prev) => prev.filter((w) => w.id !== item.id));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const startPractice = async () => {
    if (selected.size === 0) return;
    const ids = items.filter((w) => selected.has(w.id)).map((w) => w.question.id);
    setLoading(true);
    setError(null);
    try {
      const api = await getApi();
      const r = await api.startWrongPractice(ids);
      setPracticeQuestions(r.questions);
      setPracticeAttemptId(r.attempt_id);
      setPracticeAnswers({});
      setPracticeResult(null);
      setPhase('answering');
      window.scrollTo({ top: 0 });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const submitPractice = async () => {
    if (!practiceAttemptId || practiceQuestions.length === 0) return;
    const unanswered = practiceQuestions.filter(
      (qq) => practiceAnswers[String(qq.id)] == null && qq.options.length > 0,
    ).length;
    if (
      !window.confirm(
        `確定提交嗎？${unanswered > 0 ? `還有 ${unanswered} 題未作答。` : ''}答對的題目會自動標記為已掌握。`,
      )
    )
      return;
    setLoading(true);
    try {
      const api = await getApi();
      const r = await api.submitAttempt(
        practiceAttemptId,
        practiceQuestions.map((qq) => ({
          question_id: qq.id,
          selected_option: practiceAnswers[String(qq.id)] ?? null,
        })),
      );
      setPracticeResult(r);
      setPhase('result');
      window.scrollTo({ top: 0 });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const backToList = () => {
    setPhase('list');
    setPracticeQuestions([]);
    setPracticeResult(null);
    setPracticeAttemptId(null);
    setPracticeAnswers({});
    load();
  };

  const resultByQ = useMemo(() => {
    const m = new Map<number, PerQuestionResult>();
    practiceResult?.per_question.forEach((p) => m.set(p.question_id, p));
    return m;
  }, [practiceResult]);

  const autoMasteredCount = useMemo(
    () => practiceResult?.per_question.filter((p) => p.is_correct).length ?? 0,
    [practiceResult],
  );

  if (!ready) return <div className="page"><p className="hint">載入中…</p></div>;

  if (!user) {
    return (
      <div className="page">
        <h1>錯題本</h1>
        <p className="hint">錯題本需要登入後使用，答錯的題目會自動收錄，方便複習與重新練習。</p>
        <button type="button" className="primary-btn" onClick={promptLogin}>
          去登入
        </button>
      </div>
    );
  }

  if (phase === 'answering') {
    return (
      <div className="page">
        <h1>錯題重練（{practiceQuestions.length} 題）</h1>
        <p className="hint">無倒計時；提交後答對的題目會自動標記為已掌握。</p>
        {practiceQuestions.map((qq, i) => (
          <div key={qq.id} className="answer-block">
            <div className="answer-index">第 {i + 1} 題</div>
            <QuestionCard
              question={qq}
              selected={practiceAnswers[String(qq.id)] ?? null}
              onSelect={(key) =>
                setPracticeAnswers((prev) => ({ ...prev, [String(qq.id)]: key }))
              }
              showHeader={false}
            />
          </div>
        ))}
        <div className="action-bar">
          <button type="button" className="primary-btn" onClick={submitPractice} disabled={loading}>
            {loading ? '提交中…' : '提交'}
          </button>
          <button type="button" className="ghost-btn" onClick={backToList}>
            返回錯題本
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  if (phase === 'result' && practiceResult) {
    return (
      <div className="page">
        <h1>重練結果</h1>
        <div className="score-card">
          <div className="score-main">
            {practiceResult.correct} / {practiceResult.total}（{practiceResult.accuracy}%）
          </div>
          <p className="hint">
            {autoMasteredCount > 0
              ? `其中 ${autoMasteredCount} 題答對，已自動標記為已掌握。`
              : '沒有答對的題目，它們仍留在錯題本中。'}
          </p>
        </div>
        {practiceQuestions.map((qq, i) => {
          const r = resultByQ.get(qq.id);
          if (!r) return null;
          return <ReviewItem key={qq.id} question={qq} result={r} index={i} />;
        })}
        <div className="action-bar">
          <button type="button" className="primary-btn" onClick={backToList}>
            返回錯題本
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page wrong-book">
      <h1>錯題本</h1>
      <p className="hint">模擬考／練習中答錯的題目會自動收錄在這裡。勾選題目可重新練習。</p>

      <div className="filter-card">
        <div className="tabs">
          {(
            [
              ['unmastered', '未掌握'],
              ['mastered', '已掌握'],
              ['all', '全部'],
            ] as [MasterFilter, string][]
          ).map(([v, label]) => (
            <button
              key={v}
              type="button"
              className={masterFilter === v ? 'tab active' : 'tab'}
              onClick={() => setMasterFilter(v)}
            >
              {label}
            </button>
          ))}
        </div>
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
        {selected.size > 0 && (
          <button type="button" className="primary-btn" onClick={startPractice} disabled={loading}>
            重新練習（{selected.size} 題）
          </button>
        )}
      </div>

      {error && <p className="error">{error}</p>}
      {loading && <p className="hint">載入中…</p>}

      {!loading && items.length === 0 && (
        <p className="hint">
          {masterFilter === 'unmastered'
            ? '太好了，目前沒有未掌握的錯題！'
            : '這裡還沒有錯題。'}
        </p>
      )}

      {items.map((w) => (
        <div key={w.id} className={`wrong-item${w.mastered ? ' is-mastered' : ''}`}>
          <div className="wrong-head">
            <input
              type="checkbox"
              checked={selected.has(w.id)}
              onChange={() => toggleSelect(w.id)}
              aria-label="選擇"
            />
            <span className="qtype-tag">{qtypeName(w.question.qtype_code)}</span>
            <span className="wrong-meta">
              錯 {w.wrong_count} 次
              {w.review_count > 0 && `・已複習 ${w.review_count} 次`}
              {w.created_at && `・${fmtDate(w.created_at)} 收錄`}
            </span>
            {w.mastered && <span className="badge badge-ok">已掌握</span>}
            <span className="wrong-actions">
              <button type="button" className="link-btn" onClick={() => toggleExpand(w.id)}>
                {expanded.has(w.id) ? '收起解析' : '查看解析'}
              </button>
              <button
                type="button"
                className="link-btn"
                onClick={() => setMastered(w, !w.mastered)}
              >
                {w.mastered ? '取消掌握' : '標記已掌握'}
              </button>
              <button type="button" className="link-btn danger" onClick={() => removeItem(w)}>
                刪除
              </button>
            </span>
          </div>
          <div className="wrong-stem">
            {renderStem(w.question.stem, w.question.target_text)}
          </div>
          {expanded.has(w.id) && (
            <div className="wrong-expl">
              <ExplanationBlock
                explanation={w.explanation}
                options={w.question.options}
                correctOption={w.correct_option}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
