// 真實後端端到端走查：經前端 realApi 客戶端（非 mock）
// 建 attempt → 取題（驗答案不洩露）→ 提交 → getAttempt（驗題目合併）→ 專項篩選
import { realApi } from '../src/api/client';

function assert(cond: boolean, msg: string): void {
  if (!cond) {
    console.error('FAIL:', msg);
    process.exit(1);
  }
  console.log('ok:', msg);
}

async function main(): Promise<void> {
  const exams = await realApi.listExams();
  assert(exams.length >= 1, `listExams 回傳 ${exams.length} 份試卷`);
  const exam = exams[0];
  const lr = exam.sections.find((s) => s.code === 'lang_reading');
  assert(!!lr && lr.time_limit_min === 110 && lr.question_count === 66, 'lang_reading：110 分鐘、66 題');

  const att = await realApi.startAttempt({ exam_id: exam.id, mode: 'mock', section_code: 'lang_reading' });
  assert(att.time_limit_min === 110, 'mock attempt 時限 110 分鐘');

  const qs = await realApi.getExamQuestions(exam.id, 'lang_reading');
  assert(qs.length === 66, '取題 66 題');
  assert(qs.every((q) => !('correct_option' in q)), '作答用題目不洩露 correct_option');
  assert(qs.some((q) => q.group && q.group.content.length > 0), '讀解題內嵌 group 文章');

  // 前 60 題選 '1'，後 6 題留白 → 提交
  const answers = qs.map((q, i) => ({ question_id: q.id, selected_option: i < 60 ? '1' : null }));
  const res = await realApi.submitAttempt(att.attempt_id, answers);
  assert(res.total === 66, '判分 total=66');
  assert(res.wrong_question_ids.length === 66 - res.correct, 'wrong_question_ids 數量自洽');
  assert(
    Math.abs(res.accuracy - Math.round((res.correct / 66) * 1000) / 10) < 1e-9,
    `accuracy=${res.accuracy}% 計算正確`,
  );
  assert(res.per_question.every((p) => p.explanation && p.explanation.analysis_zh), '每題都有解析');

  // getAttempt：驗證前端客戶端把題目合併回來
  const got = await realApi.getAttempt(att.attempt_id);
  assert(got.questions.length === 66, `getAttempt 合併回 66 題題目（實得 ${got.questions.length}）`);
  assert(got.questions.every((q) => q.stem && q.options.length === 4), '合併的題目含題干與 4 選項');
  assert(!('correct_option' in got.questions[0]), '合併題目仍不洩露答案');

  // 專項練習：篩「文法填空」
  const gq = await realApi.getPracticeQuestions({ qtype_code: 'grammar_fill', exam_id: exam.id, limit: 20 });
  assert(gq.length === 10 && gq.every((q) => q.qtype_code === 'grammar_fill'), '文法填空只回傳該題型 10 題');
  const att2 = await realApi.startAttempt({
    exam_id: exam.id,
    mode: 'special',
    qtype_code: 'grammar_fill',
    question_ids: gq.map((q) => q.id),
  });
  assert(att2.time_limit_min === 0 || att2.time_limit_min === null, '專項練習無倒計時');
  await realApi.submitAttempt(
    att2.attempt_id,
    gq.map((q) => ({ question_id: q.id, selected_option: '3' })),
  );
  const got2 = await realApi.getAttempt(att2.attempt_id);
  assert(got2.questions.length === 10, `專項 getAttempt 合併回 10 題（實得 ${got2.questions.length}）`);
  assert(got2.qtype_code === 'grammar_fill', '保留 qtype_code');

  console.log('ALL REAL E2E CHECKS PASSED');
}

void main();
