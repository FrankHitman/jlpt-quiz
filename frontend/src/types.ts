// 與後端 API 契約（TASKS.md T3）對齊的共用型別。
// 注意：作答用題目（AnsweringQuestion）絕不包含 correct_option。

export interface SectionSummary {
  code: string;
  name_zh: string;
  time_limit_min: number;
  question_count: number;
}

export interface ExamSummary {
  id: number;
  level: string;
  year: number;
  month: number;
  title: string;
  sections: SectionSummary[];
}

export interface QTypeStat {
  qtype_code: string;
  name_zh: string;
  count: number;
}

export interface ExamDetail extends ExamSummary {
  qtype_stats: QTypeStat[];
}

export interface OptionItem {
  key: string;
  text: string;
}

export interface QuestionGroupView {
  id: number;
  group_type: string;
  title: string | null;
  content: string;
}

export interface AnsweringQuestion {
  id: number;
  exam_id: number;
  group_id: number | null;
  section_code: string;
  qtype_code: string;
  mondai_no: number | null;
  number_in_section: number;
  stem: string;
  options: OptionItem[];
  group: QuestionGroupView | null;
}

export interface Distractor {
  option: string;
  why_wrong: string;
}

export interface Explanation {
  key_point: string | null;
  analysis_zh: string;
  distractors: Distractor[] | null;
  evidence: string | null;
}

export interface PerQuestionResult {
  question_id: number;
  selected_option: string | null;
  correct_option: string;
  is_correct: boolean;
  explanation: Explanation;
}

export interface SubmitResult {
  total: number;
  correct: number;
  accuracy: number;
  per_question: PerQuestionResult[];
  wrong_question_ids: number[];
}

export interface AttemptResult extends SubmitResult {
  attempt_id: number;
  exam_id: number;
  mode: string;
  section_code: string | null;
  qtype_code: string | null;
  submitted_at: string;
  questions: AnsweringQuestion[];
  /** 真實後端回傳：是否超時提交（mock 模式為 undefined） */
  overtime?: boolean;
}

export interface StartAttemptInput {
  exam_id: number;
  mode: 'mock' | 'special';
  section_code?: string;
  qtype_code?: string;
  question_ids?: number[];
}

export interface SubmitAnswer {
  question_id: number;
  selected_option: string | null;
}

export interface PracticeParams {
  qtype_code?: string;
  exam_id?: number;
  section?: string;
  limit?: number;
}

/** 前端統一使用的 API 介面：mock 與真實後端都實作它，切換零改動。 */
export interface QuizApi {
  listExams(): Promise<ExamSummary[]>;
  getExam(id: number): Promise<ExamDetail>;
  getExamQuestions(examId: number, section?: string): Promise<AnsweringQuestion[]>;
  getPracticeQuestions(params: PracticeParams): Promise<AnsweringQuestion[]>;
  startAttempt(input: StartAttemptInput): Promise<{ attempt_id: number; time_limit_min: number | null }>;
  submitAttempt(attemptId: number, answers: SubmitAnswer[]): Promise<SubmitResult>;
  getAttempt(attemptId: number): Promise<AttemptResult>;
}
