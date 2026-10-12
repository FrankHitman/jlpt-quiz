# -*- coding: utf-8 -*-
"""Run build_a/b/c and merge into part_a.json."""
import sys, json
sys.path.insert(0, "/tmp/n22107")
import build_a, build_b, build_c  # noqa: F401  (these populate build_a's lists)

out = {
    "groups": [],
    "questions": build_a.questions,
    "explanations": build_a.explanations,
    "vocabulary": build_a.vocabulary,
}
p = "/home/hatch/workspace/jlpt-quiz/pipeline/seed/2021-07-N2/parts/part_a.json"
json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)

# ---- validation ----
d = json.load(open(p))
qs = {q["number_in_section"]: q for q in d["questions"]}
es = {(e["section_code"], e["number_in_section"]) for e in d["explanations"]}
assert sorted(qs) == list(range(1, 31)), f"missing: {[n for n in range(1,31) if n not in qs]}"
for n, q in qs.items():
    assert len(q["options"]) == 4, n
    assert q["correct_option"] in "1234", n
    assert (q["section_code"], n) in es, f"no explanation for {n}"
    if q["target_text"]:
        assert q["target_text"] in q["stem"], f"target not in stem: {n}"
    e = [x for x in d["explanations"] if x["number_in_section"] == n][0]
    assert set(e["option_readings"]) == set(e["option_meanings"]), f"key mismatch: {n}"
    assert q["correct_option"] not in [x["option"] for x in e["distractors"]], f"distractor contains answer: {n}"
    assert len(e["distractors"]) == 3, f"distractor count: {n}"
for n in range(1, 31):
    assert any(v["number_in_section"] == n for v in d["vocabulary"]), f"no vocab: {n}"
print(f"questions={len(d['questions'])} explanations={len(d['explanations'])} vocab={len(d['vocabulary'])}")
print("ALL CHECKS PASSED")
