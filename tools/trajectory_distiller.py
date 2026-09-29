# -*- coding: utf-8 -*-
"""
trajectory_distiller.py — 解决轨迹蒸馏器（13轮DS补账件②，2026-09-28）
======================================================================
源：DS 13 轮第 12 轮 Socratic-SWE——"Agent 自己的解决轨迹就是训练信号"：
把历史轨迹（失败+修复模式）蒸馏为结构化技能卡，优化压力指向**填补能力
缺口**而非**绕过评估标准**（SWE-bench Verified 三轮迭代 50.40% 实证）。

对正明的落法：incident_ledger.jsonl 的事故台账就是"失败轨迹"，
本件把它蒸馏为修复模式卡（pattern_cards.json）——同型事故 ≥2 宗
即升格为模式卡（含：症状/根因类型/修复动作/防复发闸），卡挂五流程
对应闸位。台账只记账，蒸馏才长能力。

用法：
    python trajectory_distiller.py distill    # 从台账蒸馏模式卡
    python trajectory_distiller.py selftest
"""
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "incident_ledger.jsonl")
CARDS = os.path.join(HERE, "pattern_cards.json")
# 同型（P型+描述相似）事故达到该数 → 升格模式卡
PROMOTION_THRESHOLD = 2
MIN_SHARED_BIGRAMS = 3   # 共享字符 bigram ≥3 视为同型（短中文文本友好）


def _bigrams(text: str) -> set:
    s = "".join(c for c in text if c.isalnum())
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _similar(a: str, b: str) -> bool:
    ba, bb = _bigrams(a), _bigrams(b)
    if not ba or not bb:
        return False
    return len(ba & bb) >= MIN_SHARED_BIGRAMS


def distill() -> dict:
    """台账 → 模式卡。同型 ≥2 宗升格，<2 宗留在观察池。"""
    if not os.path.exists(LEDGER):
        return {"promoted": [], "pool": [], "note": "台账为空"}
    entries = []
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    # 贪心聚类：P 型相同且描述 bigram 相似 → 同组
    groups: list[list[dict]] = []
    for e in entries:
        placed = False
        for g in groups:
            if (g[0]["type"] == e["type"]
                    and _similar(g[0]["desc"], e["desc"])):
                g.append(e)
                placed = True
                break
        if not placed:
            groups.append([e])
    promoted, pool = [], []
    for g in groups:
        sig = g[0]["type"] + ":" + g[0]["desc"][:12]
        card = {"signature": sig, "count": len(g),
                "symptom": g[0]["desc"][:80],
                "evidence": [e.get("evidence", "") for e in g if e.get("evidence")],
                "dates": [e["date"] for e in g]}
        if len(g) >= PROMOTION_THRESHOLD:
            card["fix_action"] = "同型复发 → 按五流程对应闸位加机械检查点（棘轮只升不降）"
            promoted.append(card)
        else:
            pool.append(card)
    with open(CARDS, "w", encoding="utf-8") as f:
        json.dump({"promoted": promoted, "pool": pool}, f,
                  ensure_ascii=False, indent=2)
    return {"promoted": [c["signature"] for c in promoted],
            "pool": [c["signature"] for c in pool],
            "cards_file": CARDS}


def selftest() -> None:
    import tempfile
    global LEDGER, CARDS
    bak_l, bak_c = LEDGER, CARDS
    LEDGER = os.path.join(tempfile.gettempdir(), "td_ledger.jsonl")
    CARDS = os.path.join(tempfile.gettempdir(), "td_cards.json")
    try:
        # 造台账：同型 P2 两宗（应升格）+ 孤例 P5 一宗（留观察池）
        rows = [
            {"type": "P2", "desc": "变量残留导致解析丢块", "date": "2026-09-27",
             "evidence": "blocks=0 输出"},
            {"type": "P2", "desc": "变量重命名残留导致检查失效", "date": "2026-09-28",
             "evidence": "grep 命中 1 处"},
            {"type": "P5", "desc": "汇报漏了对比段", "date": "2026-09-28"},
        ]
        with open(LEDGER, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        out = distill()
        assert len(out["promoted"]) == 1 and out["promoted"][0].startswith("P2:"), out
        assert len(out["pool"]) == 1 and out["pool"][0].startswith("P5:"), out
        cards = json.load(open(CARDS, encoding="utf-8"))
        assert cards["promoted"][0]["count"] == 2
        assert cards["promoted"][0]["fix_action"], "升格卡必须带修复动作"
        print("trajectory_distiller selftest 通过 ✅（同型升格/孤例入池/卡带修复动作）")
    finally:
        os.remove(LEDGER)
        if os.path.exists(CARDS):
            os.remove(CARDS)
        LEDGER, CARDS = bak_l, bak_c


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        selftest()
    else:
        out = distill()
        print(json.dumps(out, ensure_ascii=False, indent=2))
