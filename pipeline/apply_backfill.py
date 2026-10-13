#!/usr/bin/env python3
"""校驗 pipeline/backfill/backfill-*.json 並寫入 explanations.option_readings/option_meanings。

校驗規則：
- question_id 存在，且該題 options 非空
- readings/meanings 的鍵必須是該題選項鍵的子集
- 值必須是非空字符串
- readings 鍵對應的選項含漢字時才允許（純假名選項填了注音則警告但保留）
- meanings 必須覆蓋全部選項鍵（缺鍵則報錯，不寫入該題）
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))
from app.db import SessionLocal  # noqa: E402
from sqlalchemy import text  # noqa: E402


def has_kanji(s: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in s)


def main() -> None:
    backfill_dir = Path(__file__).resolve().parent / "backfill"
    files = sorted(backfill_dir.glob("backfill-*.json"))
    if not files:
        print("no backfill files")
        return

    # 2024-07 N1 Q1-Q19 已用 fix-2024-07-n1.json 重寫（題目已更換），
    # backfill-C.json 中對應題號的注音/意思是針對舊（錯誤）題目的，必須跳過。
    fix_path = backfill_dir / "fix-2024-07-n1.json"
    skip_qids: set[str] = set()
    if fix_path.exists():
        skip_qids = set(json.loads(fix_path.read_text(encoding="utf-8")).keys())
        print(f"跳過 fix-2024-07-n1.json 已覆蓋的 {len(skip_qids)} 題")

    db = SessionLocal()
    total_ok, total_skip = 0, 0
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        notes = data.pop("__notes__", {})
        if notes:
            print(f"[{f.name}] __notes__:")
            for qid, note in notes.items():
                print(f"  Q{qid}: {note}")
        for qid, v in data.items():
            if qid in skip_qids:
                continue
            readings = v.get("readings", {}) or {}
            meanings = v.get("meanings", {}) or {}
            row = db.execute(
                text("SELECT options FROM questions WHERE id = :qid"), {"qid": int(qid)}
            ).fetchone()
            if row is None:
                print(f"  SKIP Q{qid}: question 不存在")
                total_skip += 1
                continue
            opts = row[0] or []
            opt_map = {o.get("key"): o.get("text", "") for o in opts}
            if not opt_map:
                print(f"  SKIP Q{qid}: 無印刷選項")
                total_skip += 1
                continue
            bad_keys = (set(readings) | set(meanings)) - set(opt_map)
            if bad_keys:
                print(f"  SKIP Q{qid}: 鍵 {bad_keys} 不在選項中")
                total_skip += 1
                continue
            empty_vals = [k for k, val in list(readings.items()) + list(meanings.items())
                          if not (val or "").strip()]
            if empty_vals:
                print(f"  SKIP Q{qid}: 空值 {empty_vals}")
                total_skip += 1
                continue
            missing_meanings = set(opt_map) - set(meanings)
            if missing_meanings:
                print(f"  SKIP Q{qid}: meanings 缺選項 {missing_meanings}")
                total_skip += 1
                continue
            for k, r in readings.items():
                if not has_kanji(opt_map[k]) and r != opt_map[k]:
                    print(f"  WARN Q{qid} 選項{k} 純假名卻有注音: {r}")
            db.execute(
                text("""UPDATE explanations
                        SET option_readings = :rd, option_meanings = :mn
                        WHERE question_id = :qid"""),
                {"rd": json.dumps(readings, ensure_ascii=False),
                 "mn": json.dumps(meanings, ensure_ascii=False),
                 "qid": int(qid)},
            )
            total_ok += 1
    db.commit()
    print(f"寫入 {total_ok} 題，跳過 {total_skip} 題")
    db.close()


if __name__ == "__main__":
    main()
