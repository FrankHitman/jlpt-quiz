import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getApi } from '../api';
import type { ExamSummary } from '../types';
import { sectionDisplay } from '../qtypes';

export default function Home() {
  const [exams, setExams] = useState<ExamSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getApi()
      .then((a) => a.listExams())
      .then(setExams)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  if (error) return <div className="error">載入試卷失敗：{error}</div>;
  if (!exams) return <div className="loading">載入中…</div>;

  return (
    <div className="home">
      <h1>選擇試卷</h1>
      <p className="hint">模擬考試含倒計時並計分；專項練習可按題型篩選、無倒計時。</p>
      <div className="exam-grid">
        {exams.map((exam) => {
          const total = exam.sections.reduce((s, x) => s + x.question_count, 0);
          return (
            <div key={exam.id} className="exam-card">
              <div className="exam-title">{exam.title}</div>
              <div className="exam-meta">
                {exam.year}年{exam.month}月・{exam.level}・共 {total} 題
              </div>
              <ul className="exam-sections">
                {exam.sections.map((s) => (
                  <li key={s.code}>
                    {sectionDisplay(s.code, s.name_zh)}：{s.question_count} 題・{s.time_limit_min} 分鐘
                  </li>
                ))}
              </ul>
              <div className="exam-actions">
                <Link className="btn btn-primary" to={`/mock/${exam.id}`}>
                  模擬考試
                </Link>
                <Link className="btn" to={`/practice?examId=${exam.id}`}>
                  專項練習
                </Link>
              </div>
              <div className="exam-note">模擬考僅提供「言語知識・讀解」（110 分鐘）；聽解暫無音頻。</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
