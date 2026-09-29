#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forgetting_economics.py — 突破件②【遗忘经济学：负记忆率 NMR】
思想：行业全部在卷"记得更多更准"（LongMemEval 只考记住），无人标准化"忘"。
     本件把"坏记忆"从质量问题变成经济问题：NMR（Negative Memory Rate）
     = 坏记忆被读取的次数占比 × 单次误导成本 × 剩余生命周期——一条坏记忆的
     代价是终身的，因为每次检索都可能命中它。
大公司痛点：记忆规模越大检索越烂（行业盘点已证），他们的解法是堆算力；
     NMR 给出第二变量：先减负再检索，成本曲线立刻不同。
先例空白：无任何 benchmark 考"遗忘质量"；无任何记忆系统公布 NMR。
"""
import json

def nmr(memories, mislead_cost_usd=0.02):
    """NMR = 坏记忆读取占比；年化误导成本 = 坏读取次数 × 单次成本。
    memories: [{id, is_bad, reads}]"""
    total_reads = sum(m["reads"] for m in memories)
    bad_reads = sum(m["reads"] for m in memories if m["is_bad"])
    if total_reads == 0:
        return {"nmr": 0.0, "annual_cost_usd": 0.0}
    nmr_val = bad_reads / total_reads
    return {"nmr": round(nmr_val, 4),
            "annual_cost_usd": round(bad_reads * mislead_cost_usd, 2)}

def forgetting_admission(mem, existing_nmr=0.0, threshold=0.10):
    """遗忘准入评分：写入前预估该记忆的负面风险，超阈值→建议'不写入'
    （把 T1 写入闸从直觉变成公式）。风险=无溯源×0.5 + 无时效×0.3 + 与既有记忆冲突×0.2"""
    risk = 0.0
    if not mem.get("provenance"):
        risk += 0.5
    if not mem.get("valid_until"):
        risk += 0.3
    if mem.get("conflicts_existing"):
        risk += 0.2
    verdict = "REJECT" if risk >= threshold and risk > 0.5 else ("QUARANTINE" if risk >= threshold else "ADMIT")
    return {"risk": risk, "verdict": verdict}

def nmr_from_incidents(path, mislead_cost_usd=0.02):
    """v2 实跑级：从真实事故台账算 NMR。
    口径（推算级，须标触发条件）：每条事故=一次坏记忆写入；
    同型事故每复发一次=坏记忆被"再读取"一次（教训未入记忆，代价重付一次）。
    总读取=全部事故数；坏读取=复发次数（同 desc 第二次起计）。
    成本为推算锚：单次同类事故纠偏成本 $0.02 起（下限口径，实际人工纠偏远高）。"""
    from collections import Counter
    incidents = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                incidents.append(json.loads(line))
    desc_counts = Counter(i["desc"] for i in incidents)
    total = len(incidents)
    recurrences = sum(c - 1 for c in desc_counts.values() if c > 1)
    if total == 0:
        return {"nmr": 0.0, "annual_cost_usd": 0.0, "total_incidents": 0, "recurrences": 0}
    return {"nmr": round(recurrences / total, 4),
            "annual_cost_usd": round(recurrences * mislead_cost_usd, 2),
            "total_incidents": total, "recurrences": recurrences,
            "repeated": {d: c for d, c in desc_counts.items() if c > 1}}


def selftest():
    mems = [{"id": "a", "is_bad": False, "reads": 90},
            {"id": "b", "is_bad": True, "reads": 10},
            {"id": "c", "is_bad": True, "reads": 0}]
    r1 = nmr(mems)
    # ② 坏记忆无读取→NMR=0（坏而未被读≠有害，读完才有害——这是与'准确率'指标的本质区别）
    r2 = nmr([{"id": "x", "is_bad": True, "reads": 0}, {"id": "y", "is_bad": False, "reads": 100}])
    # ③ 准入：无溯源+冲突的必拒；有溯源+时效的必收
    a1 = forgetting_admission({"provenance": False, "valid_until": None, "conflicts_existing": True})
    a2 = forgetting_admission({"provenance": True, "valid_until": "2027-01-01", "conflicts_existing": False})
    r = [
        ("NMR=10/100=0.1，年成本 $0.2", r1["nmr"] == 0.1 and r1["annual_cost_usd"] == 0.2),
        ("坏记忆零读取时 NMR=0（读到才有害）", r2["nmr"] == 0.0),
        ("无溯源+冲突 → REJECT", a1["verdict"] == "REJECT"),
        ("有溯源+时效 → ADMIT", a2["verdict"] == "ADMIT"),
    ]
    for n, ok in r:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}")
    print("selftest:", "4/4 PASS" if all(x for _, x in r) else "FAILED")
    return 0 if all(x for _, x in r) else 1

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    if len(sys.argv) > 2 and sys.argv[1] == "nmr-real":
        r = nmr_from_incidents(sys.argv[2])
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0)
    print(__doc__)
