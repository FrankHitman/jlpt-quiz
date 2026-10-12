// 與後端 API 契約（TASKS.md T3）對齊的共用型別。
// 注意：作答用題目（AnsweringQuestion）絕不包含 correct_option。

export interface SectionSummary {
  code: string;
  name_zh: string;
  time_limit_min: number;
  question_count: number;
  has_audio: boolean;
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
  /** 題干中需強調的候選詞原文（漢字讀音／近義詞題）；無則為 null */
  target_text: string | null;
  /** 聽力音頻 URL（相對於 API origin，如 /static/audio/xxx.mp3）；無則為 null */
  audio_url: string | null;
  options: OptionItem[];
  group: QuestionGroupView | null;
}

export interface Distractor {
  option: string;
  why_wrong: string;
}

export interface VocabularyItem {
  word: string;
  reading: string | null;
  meaning_zh: string | null;
  etymology_en: string | null;
}

export interface Explanation {
  key_point: string | null;
  analysis_zh: string;
  distractors: Distractor[] | null;
  evidence: string | null;
  /** 四個選項的假名注音，如 {"1":"がんじょう"}；無則為 null（mock/舊數據可省略） */
  option_readings?: Record<string, string> | null;
  /** 四個選項的中文意思，如 {"1":"堅固"}；無則為 null */
  option_meanings?: Record<string, string> | null;
  vocabulary: VocabularyItem[];
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
  // ---- 認證（真實後端；演示模式不支援） ----
  register(username: string, password: string): Promise<AuthSession>;
  registerWithCaptcha(input: {
    username: string;
    email: string;
    password: string;
    captcha_id: string;
    captcha_code: string;
  }): Promise<AuthSession>;
  login(username: string, password: string): Promise<AuthSession>;
  captcha(): Promise<{ captcha_id: string; image: string }>;
  me(): Promise<AuthUser>;
  // ---- 錯題本（真實後端；需登入） ----
  listWrongAnswers(params?: {
    mastered?: boolean;
    qtype_code?: string;
  }): Promise<WrongAnswerItem[]>;
  setWrongAnswerMastered(id: number, mastered: boolean): Promise<WrongAnswerItem>;
  deleteWrongAnswer(id: number): Promise<void>;
  startWrongPractice(questionIds: number[]): Promise<{
    attempt_id: number;
    questions: AnsweringQuestion[];
  }>;
}

export interface AuthUser {
  id: number;
  username: string;
  email?: string | null;
}

export interface AuthSession {
  token: string;
  user: AuthUser;
}

export interface WrongAnswerItem {
  id: number;
  question: AnsweringQuestion;
  correct_option: string;
  explanation: Explanation;
  wrong_count: number;
  mastered: boolean;
  mastered_at: string | null;
  review_count: number;
  last_reviewed_at: string | null;
  created_at: string | null;
}
