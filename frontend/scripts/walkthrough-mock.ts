// Mock API 走查：驗證計分、答案不洩露、題型篩選、成績回查。
// 以 exam.json 為獨立答案表（oracle），核對 mock 伺服器判分結果。

const mem = new Map<string, string>();
(globalThis as Record<string, unknown>).localStorage = {
  getItem: (k: string) => (mem.has(k) ? (mem.get(k) as string) : null),
  setItem: (k: string, v: string) => {
    mem.set(k, v);
  },
  removeItem: (k: string) => {
    mem.delete(k);
  },
};

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { mockApi } from '../src/mocks/mockServer.js';

const oracle = JSON.parse(readFileSync(join(__dirname, '..', 'src', 'mocks', 'exam.json'), 'utf-8')) as {
  questions: { correct_option: string }[];
};

function assert(cond: boolean, msg: string): void {
  if (!cond) {
    console.error('FAIL:', msg);
    process.exit(1);
  }
  console.log('ok:', msg);
}

async function main(): Promise<void> {
  // 1. 試卷列表
  const exams = await mockApi.listExams();
  assert(exams.length === 1, 'listExams 回傳 1 份試卷');
  const lr = exams[0].sections.find((s) => s.code === 'lang_reading');
  assert(!!lr && lr.time_limit_min === 110 && lr.question_count === 66, 'lang_reading：110 分鐘、66 題');

  // 2. 開始模擬考 → 取題（驗證不洩露答案）
  const att = await mockApi.startAttempt({ exam_id: 1, mode: 'mock', section_code: 'lang_reading' });
  assert(att.time_limit_min === 110, 'mock attempt 時限為 110 分鐘');
  const qs = await mockApi.getExamQuestions(1, 'lang_reading');
  assert(qs.length === 66, '取題 66 題');
  assert(qs.every((q) => !('correct_option' in q)), '作答用題目不含 correct_option（未洩露）');
  assert(qs.some((q) => q.group !== null), '讀解題內嵌 group 文章物件');

  // 3. 提交：前 60 題選 '1'，後 6 題留白
  const answers = qs.map((q, i) => ({ question_id: q.id, selected_option: i < 60 ? '1' : null }));
  const res = await mockApi.submitAttempt(att.attempt_id, answers);
  const expectedCorrect = qs.filter(
    (q, i) => i < 60 && oracle.questions[q.id - 1].correct_option === '1',
  ).length;
  assert(res.total === 66, '判分 total=66');
  assert(res.correct === expectedCorrect, `correct=${res.correct}，與答案表核對一致`);
  assert(
    Math.abs(res.accuracy - Math.round((expectedCorrect / 66) * 1000) / 10) < 1e-9,
    `accuracy=${res.accuracy}% 計算正確`,
  );
  assert(res.wrong_question_ids.length === 66 - expectedCorrect, 'wrong_question_ids 數量正確');
  assert(
    res.per_question.every((p) => p.explanation && p.explanation.analysis_zh.length > 0),
    '每題都有繁中解析',
  );
  const aWrong = res.per_question.find((p) => !p.is_correct);
  assert(
    !!aWrong && aWrong.correct_option === oracle.questions[aWrong.question_id - 1].correct_option,
    '錯題回傳的 correct_option 與答案表一致',
  );

  // 4. 專項練習：篩「文法填空」
  const gq = await mockApi.getPracticeQuestions({ qtype_code: 'grammar_fill', exam_id: 1, limit: 20 });
  assert(gq.length === 10, '文法填空共 10 題（limit=20 取全）');
  assert(gq.every((q) => q.qtype_code === 'grammar_fill'), '篩選結果只含文法填空題型');
  assert(gq.every((q) => !('correct_option' in q)), '練習題目同樣不洩露答案');

  // 5. 專項作答 → 成績回查
  const att2 = await mockApi.startAttempt({
    exam_id: 1,
    mode: 'special',
    qtype_code: 'grammar_fill',
    question_ids: gq.map((q) => q.id),
  });
  assert(att2.time_limit_min === 0, '專項練習無倒計時（time_limit_min=0）');
  await mockApi.submitAttempt(
    att2.attempt_id,
    gq.map((q) => ({ question_id: q.id, selected_option: '2' })),
  );
  const got = await mockApi.getAttempt(att2.attempt_id);
  assert(got.questions.length === 10 && got.total === 10, 'getAttempt 回傳題目與成績');
  assert(got.mode === 'special' && got.qtype_code === 'grammar_fill', 'getAttempt 保留 mode/qtype');

  console.log('ALL MOCK WALKTHROUGH PASSED');
}

void main();
