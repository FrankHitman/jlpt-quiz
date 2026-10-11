import type {
  AnsweringQuestion,
  AttemptResult,
  ExamDetail,
  ExamSummary,
  Explanation,
  PerQuestionResult,
  QuizApi,
  StartAttemptInput,
  SubmitAnswer,
  SubmitResult,
} from '../types';
import { qtypeName } from '../qtypes';
import raw from './exam.json';

/**
 * Mock 後端：以後端 API 契約（TASKS.md T3）為準實作 QuizApi。
 * 資料來自 T2 產出的真實結構化試卷（pipeline/seed/2025-12/exam.json），
 * correct_option 只存在於「伺服器端」資料中，getExamQuestions / getPracticeQuestions
 * 回傳前會剝除——UI 邏輯永遠拿不到答案，只能經 submitAttempt 取得判分結果。
 */

interface RawOption {
  key: string;
  text: string;
}
interface RawQuestion {
  group_local_id: string | null;
  section_code: string;
  qtype_code: string;
  mondai_no: number | null;
  number_in_section: number;
  stem: string;
  options: RawOption[];
  correct_option: string;
}
interface RawGroup {
  local_id: string;
  section_code: string;
  group_type: string;
  title: string | null;
  content: string;
  sort_order: number;
}
interface RawDistractor {
  option: string;
  why_wrong: string;
}
interface RawExplanation {
  section_code: string;
  number_in_section: number;
  key_point: string | null;
  analysis_zh: string;
  distractors: RawDistractor[] | null;
  evidence: string | null;
}
interface RawExamJson {
  exam: { level: string; year: number; month: number; title: string };
  groups: RawGroup[];
  questions: RawQuestion[];
  explanations: RawExplanation[];
}

const data = raw as unknown as RawExamJson;
const EXAM_ID = 1;

const SECTION_META: Record<string, { name_zh: string; time_limit_min: number }> = {
  lang_reading: { name_zh: '言語知識・讀解', time_limit_min: 110 },
  listening: { name_zh: '聽解', time_limit_min: 55 },
};

type QuestionRow = RawQuestion & { id: number };
type GroupRow = RawGroup & { id: number };

const questions: QuestionRow[] = data.questions.map((q, i) => ({ ...q, id: i + 1 }));
const groups: GroupRow[] = data.groups.map((g, i) => ({ ...g, id: i + 1 }));
const groupByLocal = new Map<string, GroupRow>(groups.map((g) => [g.local_id, g]));
const explanationByKey = new Map<string, RawExplanation>(
  data.explanations.map((e) => [`${e.section_code}:${e.number_in_section}`, e]),
);

function toAnswering(q: QuestionRow): AnsweringQuestion {
  const g = q.group_local_id ? (groupByLocal.get(q.group_local_id) ?? null) : null;
  return {
    id: q.id,
    exam_id: EXAM_ID,
    group_id: g ? g.id : null,
    section_code: q.section_code,
    qtype_code: q.qtype_code,
    mondai_no: q.mondai_no,
    number_in_section: q.number_in_section,
    stem: q.stem,
    options: q.options.map((o) => ({ key: o.key, text: o.text })),
    group: g ? { id: g.id, group_type: g.group_type, title: g.title, content: g.content } : null,
  };
}

function getExplanation(q: QuestionRow): Explanation {
  const e = explanationByKey.get(`${q.section_code}:${q.number_in_section}`);
  if (!e) return { key_point: null, analysis_zh: '暫無解析', distractors: null, evidence: null };
  return {
    key_point: e.key_point,
    analysis_zh: e.analysis_zh,
    distractors: e.distractors,
    evidence: e.evidence,
  };
}

// ---- 作答紀錄：localStorage 持久化，重新整理不遺失 ----
const LS_KEY = 'jlpt-quiz-mock-v1';

interface StoredAttempt {
  attempt_id: number;
  exam_id: number;
  mode: 'mock' | 'special';
  section_code?: string;
  qtype_code?: string;
  question_ids: number[];
  started_at: string;
  submitted_at: string | null;
  result: SubmitResult | null;
}

interface Store {
  seq: number;
  attempts: Record<string, StoredAttempt>;
}

function loadStore(): Store {
  try {
    const s = localStorage.getItem(LS_KEY);
    if (s) return JSON.parse(s) as Store;
  } catch {
    /* 忽略，fallback 到空 store */
  }
  return { seq: 1, attempts: {} };
}

function saveStore(store: Store): void {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(store));
  } catch {
    /* 忽略 */
  }
}

function buildResult(sa: StoredAttempt, answers: SubmitAnswer[]): SubmitResult {
  const answerByQ = new Map<number, string | null>(answers.map((a) => [a.question_id, a.selected_option]));
  const per_question: PerQuestionResult[] = sa.question_ids.map((qid) => {
    const q = questions[qid - 1];
    const selected = answerByQ.get(qid) ?? null;
    const is_correct = selected !== null && selected === q.correct_option;
    return {
      question_id: qid,
      selected_option: selected,
      correct_option: q.correct_option,
      is_correct,
      explanation: getExplanation(q),
    };
  });
  const correct = per_question.filter((p) => p.is_correct).length;
  const total = per_question.length;
  return {
    total,
    correct,
    accuracy: total === 0 ? 0 : Math.round((correct / total) * 1000) / 10,
    per_question,
    wrong_question_ids: per_question.filter((p) => !p.is_correct).map((p) => p.question_id),
  };
}

export const mockApi: QuizApi = {
  async listExams(): Promise<ExamSummary[]> {
    const e = data.exam;
    const sections = Object.keys(SECTION_META)
      .map((code) => ({
        code,
        name_zh: SECTION_META[code].name_zh,
        time_limit_min: SECTION_META[code].time_limit_min,
        question_count: questions.filter((q) => q.section_code === code).length,
      }))
      .filter((s) => s.question_count > 0);
    return [{ id: EXAM_ID, level: e.level, year: e.year, month: e.month, title: e.title, sections }];
  },

  async getExam(id: number): Promise<ExamDetail> {
    if (id !== EXAM_ID) throw new Error('找不到該試卷');
    const e = data.exam;
    const sections = Object.keys(SECTION_META)
      .map((code) => ({
        code,
        name_zh: SECTION_META[code].name_zh,
        time_limit_min: SECTION_META[code].time_limit_min,
        question_count: questions.filter((q) => q.section_code === code).length,
      }))
      .filter((s) => s.question_count > 0);
    const order: string[] = [];
    const counts = new Map<string, number>();
    for (const q of questions) {
      if (!counts.has(q.qtype_code)) order.push(q.qtype_code);
      counts.set(q.qtype_code, (counts.get(q.qtype_code) ?? 0) + 1);
    }
    return {
      id: EXAM_ID,
      level: e.level,
      year: e.year,
      month: e.month,
      title: e.title,
      sections,
      qtype_stats: order.map((code) => ({
        qtype_code: code,
        name_zh: qtypeName(code),
        count: counts.get(code) ?? 0,
      })),
    };
  },

  async getExamQuestions(examId: number, section?: string): Promise<AnsweringQuestion[]> {
    if (examId !== EXAM_ID) throw new Error('找不到該試卷');
    return questions
      .filter((q) => !section || q.section_code === section)
      .sort((a, b) => a.number_in_section - b.number_in_section)
      .map(toAnswering);
  },

  async getPracticeQuestions(params: {
    qtype_code?: string;
    exam_id?: number;
    section?: string;
    limit?: number;
  }): Promise<AnsweringQuestion[]> {
    const list = questions
      .filter(
        (q) =>
          (!params.exam_id || params.exam_id === EXAM_ID) &&
          (!params.section || q.section_code === params.section) &&
          (!params.qtype_code || q.qtype_code === params.qtype_code),
      )
      .sort((a, b) => a.number_in_section - b.number_in_section);
    return list.slice(0, params.limit ?? 20).map(toAnswering);
  },

  async startAttempt(input: StartAttemptInput): Promise<{ attempt_id: number; time_limit_min: number }> {
    let ids: number[];
    if (input.question_ids && input.question_ids.length > 0) {
      ids = input.question_ids.filter((id) => id >= 1 && id <= questions.length);
    } else {
      ids = questions
        .filter(
          (q) =>
            (!input.section_code || q.section_code === input.section_code) &&
            (!input.qtype_code || q.qtype_code === input.qtype_code),
        )
        .sort((a, b) => a.number_in_section - b.number_in_section)
        .map((q) => q.id);
    }
    if (ids.length === 0) throw new Error('沒有符合條件的題目');
    const store = loadStore();
    const attempt_id = store.seq++;
    store.attempts[String(attempt_id)] = {
      attempt_id,
      exam_id: input.exam_id,
      mode: input.mode,
      section_code: input.section_code,
      qtype_code: input.qtype_code,
      question_ids: ids,
      started_at: new Date().toISOString(),
      submitted_at: null,
      result: null,
    };
    saveStore(store);
    const section = input.section_code ? SECTION_META[input.section_code] : undefined;
    return {
      attempt_id,
      time_limit_min: input.mode === 'mock' && section ? section.time_limit_min : 0,
    };
  },

  async submitAttempt(attemptId: number, answers: SubmitAnswer[]): Promise<SubmitResult> {
    const store = loadStore();
    const sa = store.attempts[String(attemptId)];
    if (!sa) throw new Error('找不到該作答紀錄');
    const result = buildResult(sa, answers);
    sa.result = result;
    sa.submitted_at = new Date().toISOString();
    saveStore(store);
    return result;
  },

  async getAttempt(attemptId: number): Promise<AttemptResult> {
    const store = loadStore();
    const sa = store.attempts[String(attemptId)];
    if (!sa) throw new Error('找不到該作答紀錄');
    if (!sa.result) throw new Error('該作答尚未提交');
    return {
      attempt_id: sa.attempt_id,
      exam_id: sa.exam_id,
      mode: sa.mode,
      section_code: sa.section_code ?? null,
      qtype_code: sa.qtype_code ?? null,
      submitted_at: sa.submitted_at ?? sa.started_at,
      questions: sa.question_ids.map((id) => toAnswering(questions[id - 1])),
      ...sa.result,
    };
  },
};
