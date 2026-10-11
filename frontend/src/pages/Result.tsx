import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getApi } from '../api';
import type { AttemptResult, PerQuestionResult } from '../types';
import { qtypeName, sectionName } from '../qtypes';
import { ReviewItem } from '../components/ReviewItem';

export default function Result() {
  const { attemptId = '' } = useParams();
  const [data, setData] = useState<AttemptResult | null>(null);
  const [onlyWrong, setOnlyWrong] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getApi()
      .then((a) => a.getAttempt(Number(attemptId)))
      .then(setData)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, [attemptId]);

  const resultByQ = useMemo(() => {
    const m = new Map<number, PerQuestionResult>();
    data?.per_question.forEach((p) => m.set(p.question_id, p));
    return m;
  }, [data]);

  const stats = useMemo(() => {
    if (!data) return null;
    const bySection = new Map<string, { total: number; correct: number }>();
    const byQtype = new Map<string, { total: number; correct: number }>();
    const qtypeOrder: string[] = [];
    for (const q of data.questions) {
      const ok = resultByQ.get(q.id)?.is_correct ?? false;
      const s = bySection.get(q.section_code) ?? { total: 0, correct: 0 };
      s.total += 1;
      if (ok) s.correct += 1;
      bySection.set(q.section_code, s);
      if (!byQtype.has(q.qtype_code)) qtypeOrder.push(q.qtype_code);
      const t = byQtype.get(q.qtype_code) ?? { total: 0, correct: 0 };
      t.total += 1;
      if (ok) t.correct += 1;
      byQtype.set(q.qtype_code, t);
    }
    return { bySection, byQtype, qtypeOrder };
  }, [data, resultByQ]);

  const items = useMemo(() => {
    if (!data) return [];
    return data.questions
      .map((q, i) => ({ q, i, r: resultByQ.get(q.id) }))
      .filter((x): x is { q: (typeof data.questions)[number]; i: number; r: PerQuestionResult } =>
        !!x.r && (!onlyWrong || !x.r.is_correct),
      );
  }, [data, resultByQ, onlyWrong]);

  if (error) return <div className="error">載入成績失敗：{error}</div>;
  if (!data || !stats) return <div className="loading">載入中…</div>;

  const pct = (correct: number, total: number) =>
    total === 0 ? '—' : `${Math.round((correct / total) * 1000) / 10}%`;

  return (
    <div className="result-page">
      <h1>成績報告</h1>
      <div className="result-summary">
        <div className="accuracy">
          正確率 <strong>{data.accuracy}%</strong>
        </div>
        <div>
          {data.mode === 'mock' ? '模擬考試' : '專項練習'}・答對 {data.correct} / 共 {data.total} 題
          {data.overtime && <span className="badge badge-mock">超時提交</span>}
        </div>
      </div>

      <h2>按單元統計</h2>
      <table className="stat-table">
        <thead>
          <tr>
            <th>單元</th>
            <th>答對</th>
            <th>總題數</th>
            <th>正確率</th>
          </tr>
        </thead>
        <tbody>
          {[...stats.bySection.entries()].map(([code, s]) => (
            <tr key={code}>
              <td>{sectionName(code)}</td>
              <td>{s.correct}</td>
              <td>{s.total}</td>
              <td>{pct(s.correct, s.total)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>按題型統計</h2>
      <table className="stat-table">
        <thead>
          <tr>
            <th>題型</th>
            <th>答對</th>
            <th>總題數</th>
            <th>正確率</th>
          </tr>
        </thead>
        <tbody>
          {stats.qtypeOrder.map((code) => {
            const s = stats.byQtype.get(code)!;
            return (
              <tr key={code}>
                <td>{qtypeName(code)}</td>
                <td>{s.correct}</td>
                <td>{s.total}</td>
                <td>{pct(s.correct, s.total)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="review-filter">
        <h2>錯題集</h2>
        <div className="filter-btns">
          <button type="button" className={onlyWrong ? 'btn' : 'btn btn-primary'} onClick={() => setOnlyWrong(false)}>
            全部題目
          </button>
          <button type="button" className={onlyWrong ? 'btn btn-primary' : 'btn'} onClick={() => setOnlyWrong(true)}>
            只看錯題（{data.wrong_question_ids.length}）
          </button>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="notice">沒有符合的題目。</div>
      ) : (
        items.map(({ q, i, r }) => <ReviewItem key={q.id} question={q} result={r} index={i} />)
      )}

      <div className="result-actions">
        <Link className="btn" to="/">
          返回首頁
        </Link>
        <Link className="btn" to="/practice">
          專項練習
        </Link>
      </div>
    </div>
  );
}
