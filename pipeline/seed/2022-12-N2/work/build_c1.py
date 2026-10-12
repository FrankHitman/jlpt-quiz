# -*- coding: utf-8 -*-
"""2022-12 N2 読解 part_c — 問題10-11"""
import json

groups = []
questions = []
explanations = []
vocabulary = []

def G(local_id, title, content, order):
    groups.append({"local_id": local_id, "section_code": "lang_reading",
                   "group_type": "passage", "title": title, "content": content,
                   "sort_order": order})

def Q(nis, mondai, qtype, gid, stem, opts, correct):
    questions.append({"group_local_id": gid, "section_code": "lang_reading",
                      "qtype_code": qtype, "mondai_no": mondai,
                      "number_in_section": nis, "stem": stem,
                      "options": [{"key": str(i+1), "text": t} for i, t in enumerate(opts)],
                      "correct_option": str(correct), "target_text": None, "audio_url": None})

def E(nis, key_point, analysis, distractors, evidence, readings, meanings):
    explanations.append({"section_code": "lang_reading", "number_in_section": nis,
                         "key_point": key_point, "analysis_zh": analysis,
                         "distractors": [{"option": str(o), "why_wrong": w} for o, w in distractors],
                         "evidence": evidence, "option_readings": readings, "option_meanings": meanings})

def V(nis, word, reading, pos, meaning, example=None):
    vocabulary.append({"section_code": "lang_reading", "number_in_section": nis,
                       "word": word, "reading": reading, "pos": pos,
                       "meaning_zh": meaning, "example_sentence": example, "etymology_en": None})

# ============ 問題10 (1) Q52 ============
G("g_s1", "問題10 (1) 人物情報", 
"人物の情報を集めるときはひとりの意見だけでなく、複数の意見を聞くのは、そうしないと、人物の全体像がわからないからだ。情景や物体を眺める時、人の判断はあまり変わらない。しかし、人物を見るとき、人が感じる印象はかなり違うのである。ある人物のプロフィールを書くのならば、ひとりが会いに行っただけでは不完全だ。ふたりで会いに行って、それぞれがどういう印象を持ったのかを合わせた方がいい。採用の面接を複数で行うのも、同じ理由からだと思う。", 1)
Q(52, 10, "short_reading", "g_s1", "筆者の考えに合うのはどれか。",
["物も人物も、複数の意見を聞いて判断することが必要だ",
 "物を見る時より人物を見る時の方が、人が持つ印象は正確だ",
 "人物の印象は、見る状況によって異なる",
 "人物を判断するには、ひとりが持つ印象だけでは不十分だ"], 4)
E(52, "短文読解・主張把握",
"正解是 4。關鍵句：「ひとりが会いに行っただけでは不完全だ。ふたりで会いに行って、それぞれがどういう印象を持ったのかを合わせた方がいい。」人物判斷不能只靠一個人的印象。※本套解析 PDF 讀解部分無答案標記，答案按文章內容判定。",
[(1, "文章只說人物需要多人意見，沒說物也要；「物も」以偏概全。"),
 (2, "文章說人物印象「かなり違う」，沒說哪個更正確。"),
 (3, "文章說的是不同人印象不同，不是同一人因狀況而異。")],
"「ひとりが会いに行っただけでは不完全だ」（第4句）",
{"1": "ものもじんぶつも、ふくすうのいけんをきいてはんだんすることがひつようだ",
 "2": "ものをみるときよりじんぶつをみるときのほうが、ひとがもついんしょうはせいかくだ",
 "3": "じんぶつのいんしょうは、みるじょうきょうによってことなる",
 "4": "じんぶつをはんだんするには、ひとりがもついんしょうだけではじゅうぶんでない"},
{"1": "無論是物還是人物，都需要聽取多方意見再判斷",
 "2": "看人物時人所抱有的印象比看物體時更正確",
 "3": "對人物的印象會因觀察的狀況而有所不同",
 "4": "要判斷人物，僅憑單個人的印象是不夠的"})
V(52, "全体像", "ぜんたいぞう", "名詞", "整體形象")
V(52, "不完全", "ふかんぜん", "形容動詞", "不完全")

# ============ 問題10 (2) Q53 ============
G("g_s2", "問題10 (2) 山森大学お知らせ",
"山森大学》お知らせ\n8月10日\n移転作業に伴うパソコン自習室の利用について\n先日お知らせしたように、キャンパスの整備にあたり、現在2号館のパソコン自習室が4号館に移転します。移転作業に伴い、利用は9月5日までになるとお知らせしましたが、工事期間の変更により8月31日に閉室することになりました。移転先の利用開始は10月1日で変更ありません。移転が完了するまでは、6号館のパソコン自習室、および図書館の情報検索室をご利用ください。\n問い合わせ先：情報支援センター\n電話：071-992-8555", 2)
Q(53, 10, "short_reading", "g_s2", "このお知らせで伝えたいことは何か。",
["9月5日から2号館のパソコン自習室が利用できなくなること",
 "10月1日から6号館のパソコン自習室が利用できること",
 "2号館のパソコン自習室の閉室日が早まったこと",
 "4号館のパソコン自習室の利用開始日が早まったこと"], 3)
E(53, "短文読解・通知文",
"正解是 3。關鍵句：「利用は9月5日までになるとお知らせしましたが、工事期間の変更により8月31日に閉室することになりました。」閉室日從 9 月 5 日提前到 8 月 31 日。※本套解析 PDF 讀解部分無答案標記，答案按文章內容判定。",
[(1, "9月5日是舊通知的日期，新通知改為8月31日閉室。"),
 (2, "6号館是移轉完成前的臨時替代，不是10月1日開始；10月1日是4号館。"),
 (4, "4号館的利用開始日是10月1日，「変更ありません」，沒有提前。")],
"「8月31日に閉室することになりました」（第3句）",
{"1": "9がつ5にちから2ごうかんのパソコンじしゅうしつがりようできなくなること",
 "2": "10がつ1にちから6ごうかんのパソコンじしゅうしつがりようできること",
 "3": "2ごうかんのパソコンじしゅうしつのへいしつびがはやまったこと",
 "4": "4ごうかんのパソコンじしゅうしつのりようかいしびがはやまったこと"},
{"1": "從9月5日起不能使用2號館的電腦自習室",
 "2": "從10月1日起可以開始使用6號館的電腦自習室",
 "3": "2號館電腦自習室的關閉日期提前了",
 "4": "4號館電腦自習室的開始使用日期提前了"})
V(53, "閉室", "へいしつ", "名詞", "關閉（室）")
V(53, "移転", "いてん", "名詞", "搬遷、移轉")

json.dump({"groups": groups, "questions": questions, "explanations": explanations, "vocabulary": vocabulary},
          open("/home/hatch/workspace/jlpt-quiz/pipeline/seed/2022-12-N2/work/c1.json", "w"), ensure_ascii=False, indent=1)
print("c1 done:", len(questions), "questions")
