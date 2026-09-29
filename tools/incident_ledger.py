# -*- coding: utf-8 -*-
"""
incident_ledger.py — 事故计数台账（突破件①，2026-09-27）
=========================================================
对应《约定-五流程能力突破-v1.0》达标度量：能力分数不靠自评，
靠事故计数——每次失分事故记一宗，同型复发双倍记（棘轮只升不降）。

用法：
    python incident_ledger.py add P2 "skip_depth 变量残留导致解析丢失"  # 记一笔
    python incident_ledger.py stats                                    # 台账统计
    python incident_ledger.py selftest                                 # 自测

台账文件：incident_ledger.jsonl（append-only，与脚本同目录）
计分口径（对齐五流程目标分）：
    当前分 = 100 - Σ(事故权重)，同型 30 天内复发权重×2
    权重：P1/P2/P3 各 -2 分/宗，P4/P5 各 -1 分/宗（设计/逐行/真实层是硬伤）
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "incident_ledger.jsonl")
WEIGHT = {"P1": 2, "P2": 2, "P3": 2, "P4": 1, "P5": 1}
RECURRENCE_WINDOW_DAYS = 30


def load_entries() -> list:
    if not os.path.exists(LEDGER):
        return []
    out = []
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"⚠ 台账有坏行（不计入）：{line[:60]}")
    return out


def add(ptype: str, desc: str, source: str = "manual") -> dict:
    assert ptype in WEIGHT, f"类型须为 P1-P5，收到 {ptype}"
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "date": date.today().isoformat(),
        "type": ptype,
        "desc": desc,
        "source": source,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def stats() -> dict:
    """统计各型事故数 + 同型复发双倍加权 + 当前推定分。"""
    entries = load_entries()
    today = date.today()
    per_type = {p: 0 for p in WEIGHT}
    weighted = {p: 0.0 for p in WEIGHT}
    seen_dates = {p: [] for p in WEIGHT}
    for e in entries:
        p = e["type"]
        per_type[p] += 1
        d = date.fromisoformat(e["date"])
        # 同型 30 天内复发 → 双倍
        recur = any(0 <= (d - prev).days <= RECURRENCE_WINDOW_DAYS
                    for prev in seen_dates[p])
        w = WEIGHT[p] * (2 if recur else 1)
        weighted[p] += w
        seen_dates[p].append(d)
    total_w = sum(weighted.values())
    return {"n_total": len(entries), "per_type": per_type,
            "weighted": weighted, "total_weight": total_w,
            "score": max(0, 100 - total_w)}


def print_stats() -> None:
    s = stats()
    print("=" * 62)
    print(f"事故台账  共 {s['n_total']} 宗   当前推定分：{s['score']}/100")
    print("-" * 62)
    print(f"{'流程':<6}{'事故数':>6}{'加权分(同型复发×2)':>20}")
    for p in WEIGHT:
        print(f"{p:<6}{s['per_type'][p]:>6}{s['weighted'][p]:>18.0f}")
    print("=" * 62)
    print("口径：能力分不靠自评，只看事故；同型 30 天内复发双倍记（棘轮）")


# ---------------- 自测 ----------------
def selftest() -> None:
    import tempfile
    global LEDGER
    bak, LEDGER = LEDGER, os.path.join(tempfile.gettempdir(), "il_test.jsonl")
    if os.path.exists(LEDGER):
        os.remove(LEDGER)
    try:
        today = date.today()
        # 同月两宗 P2（复发双倍）+ 一宗 P5（单倍）
        entries = [
            {"id": "a", "date": (today - timedelta(days=3)).isoformat(),
             "type": "P2", "desc": "t1", "source": "test"},
            {"id": "b", "date": today.isoformat(),
             "type": "P2", "desc": "t2", "source": "test"},
            {"id": "c", "date": today.isoformat(),
             "type": "P5", "desc": "t3", "source": "test"},
        ]
        with open(LEDGER, "w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        s = stats()
        assert s["n_total"] == 3, s
        assert s["per_type"]["P2"] == 2
        assert s["weighted"]["P2"] == 6, "首宗2分+复发宗2×2=4，合计6"
        assert s["weighted"]["P5"] == 1
        assert s["score"] == 100 - 7, s   # P2=6 + P5=1
        print("selftest 3/3 通过 ✅（计数/同型双倍/推定分）")
    finally:
        os.remove(LEDGER)
        LEDGER = bak


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        selftest()
    elif len(sys.argv) >= 4 and sys.argv[1] == "add":
        e = add(sys.argv[2].upper(), " ".join(sys.argv[3:]))
        print(f"已记 {e['type']} @{e['date']}：{e['desc']}")
        print_stats()
    elif len(sys.argv) >= 2 and sys.argv[1] == "stats":
        print_stats()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
