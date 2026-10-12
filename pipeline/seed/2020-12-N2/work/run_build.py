#!/usr/bin/env python3
import json, os
work = os.path.dirname(os.path.abspath(__file__))
# Execute build_d.py first (defines helpers + 問題1), then parts 2-5 in the same namespace
ns = {"__name__": "__main__"}
for f in ["build_d.py", "build_d2.py", "build_d3.py", "build_d4.py", "build_d5.py"]:
    with open(os.path.join(work, f), encoding="utf-8") as fh:
        exec(compile(fh.read(), f, "exec"), ns)

groups = ns["groups"]; questions = ns["questions"]
explanations = ns["explanations"]; vocabulary = ns["vocabulary"]

# ---- validation ----
assert len(questions) == 30, len(questions)
nis_all = sorted(q["number_in_section"] for q in questions)
assert nis_all == list(range(1, 31)), nis_all
gids = {g["local_id"] for g in groups}
for q in questions:
    assert q["group_local_id"] in gids, q["number_in_section"]
    assert q["correct_option"] in "1234", q["number_in_section"]
    assert q["audio_url"] == "/static/audio/2020-12-N2-listening.mp3"
    if q["options"]:
        assert len(q["options"]) == 4, q["number_in_section"]
assert len(gids) == len(groups), "duplicate local_id"
e_keys = {(e["section_code"], e["number_in_section"]) for e in explanations}
q_keys = {(q["section_code"], q["number_in_section"]) for q in questions}
assert e_keys == q_keys, "explanation/question mismatch"
for e in explanations:
    r, m = e["option_readings"] or {}, e["option_meanings"] or {}
    assert set(r.keys()) == set(m.keys()), f"reading/meaning key mismatch nis={e['number_in_section']}"
    for d in e["distractors"]:
        assert d["option"] != [q for q in questions
                               if q["number_in_section"] == e["number_in_section"]][0]["correct_option"]
for v in vocabulary:
    assert (v["section_code"], v["number_in_section"]) in q_keys
# answer check against official answer table
expected = {1:"3",2:"2",3:"4",4:"3",5:"2",6:"4",7:"2",8:"3",9:"4",10:"1",
            11:"2",12:"1",13:"3",14:"4",15:"3",16:"3",17:"2",18:"2",19:"3",
            20:"1",21:"2",22:"2",23:"3",24:"1",25:"3",26:"1",27:"1",
            28:"1",29:"3",30:"4"}
for q in questions:
    assert q["correct_option"] == expected[q["number_in_section"]], \
        f"answer mismatch nis={q['number_in_section']}"

out = {"groups": groups, "questions": questions,
       "explanations": explanations, "vocabulary": vocabulary}
p = "/home/hatch/workspace/jlpt-quiz/pipeline/seed/2020-12-N2/parts/part_d.json"
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.load(open(p, encoding="utf-8"))  # re-validate
print(f"OK: groups={len(groups)} questions={len(questions)} "
      f"explanations={len(explanations)} vocabulary={len(vocabulary)}")
