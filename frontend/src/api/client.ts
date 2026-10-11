import type { AttemptResult, QuizApi } from '../types';

// 真實後端：base 可經 VITE_API_BASE 覆寫，預設本地 8000。
const BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined) ?? 'http://127.0.0.1:8000/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === 'string') detail = body.detail;
      else if (body.detail !== undefined) detail = JSON.stringify(body.detail);
    } catch {
      /* 保持預設錯誤訊息 */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const realApi: QuizApi = {
  listExams: () => request('/exams'),
  getExam: (id) => request(`/exams/${id}`),
  getExamQuestions: (examId, section) =>
    request(`/exams/${examId}/questions${section ? `?section=${encodeURIComponent(section)}` : ''}`),
  getPracticeQuestions: (p) => {
    const sp = new URLSearchParams();
    if (p.qtype_code) sp.set('qtype_code', p.qtype_code);
    if (p.exam_id !== undefined) sp.set('exam_id', String(p.exam_id));
    if (p.section) sp.set('section', p.section);
    if (p.limit !== undefined) sp.set('limit', String(p.limit));
    return request(`/practice/questions?${sp.toString()}`);
  },
  startAttempt: (input) =>
    request('/attempts', {
      method: 'POST',
      // 相容性對映：TASKS.md T3 契約規定 mode 為 mock | special，
      // 但後端目前實作校驗為 ^(mock|practice)$。待後端對齊契約後可移除此對映。
      body: JSON.stringify({ ...input, mode: input.mode === 'special' ? 'practice' : input.mode }),
    }),
  submitAttempt: (attemptId, answers) =>
    request(`/attempts/${attemptId}/submit`, {
      method: 'POST',
      body: JSON.stringify({ answers }),
    }),
  async getAttempt(id) {
    // 真實後端的 GET /attempts/{id} 只回傳判分結果（含 per_question），不內嵌題目；
    // 這裡按作答時的篩選條件把題目補回來，組出與契約一致的 AttemptResult。
    const res = await request<Omit<AttemptResult, 'questions'>>(`/attempts/${id}`);
    const ids = res.per_question.map((p) => p.question_id);
    let pool: Awaited<ReturnType<QuizApi['getExamQuestions']>>;
    if (res.section_code) {
      pool = await realApi.getExamQuestions(res.exam_id, res.section_code);
    } else {
      pool = await realApi.getPracticeQuestions({
        exam_id: res.exam_id,
        qtype_code: res.qtype_code ?? undefined,
        limit: 100, // 後端 limit 上限 100，一套試卷最多 96 題，足夠覆蓋
      });
    }
    const byId = new Map(pool.map((q) => [q.id, q]));
    const questions = ids
      .map((qid) => byId.get(qid))
      .filter((q): q is (typeof pool)[number] => !!q);
    const out: AttemptResult = { ...res, questions };
    return out;
  },
};
