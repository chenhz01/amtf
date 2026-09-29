# -*- coding: utf-8 -*-
"""
intent_drift.py — 意图对账器（13轮DS补账件①，2026-09-28）
==========================================================
源：DS 13 轮第 13 轮 WANDERING 实证——"意图表示不因果驱动行为"
（钳制 SUCCESS 特征 ΔP(finish)=-0.001 ≈ 随机），唯一杠杆在行为层
（"the lever is behavioral, not representational"）。

对正明的直接含义：执行者自报"我完成了"（无论 CoT 还是结论）都不是
完成的行为证据；完成 = 意图条目逐项有行为产物对账。本件把这一机制
做成闸机：立案登记意图 → 收口行为层对账 → 漂移检出。

用法：
    python intent_drift.py selftest
作为库：
    from intent_drift import IntentLedger
    led = IntentLedger()
    led.register("修解析bug", ["bug修复", "测试通过"])
    led.reconcile("修解析bug", {"bug修复": ["smartpruner.py 已改"],
                                "测试通过": ["selftest 3/3 ✅"]})
"""
import json
import os

LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "intent_ledger.jsonl")


class IntentLedger:
    def register(self, task_id: str, intent_items: list) -> dict:
        """立案：登记maintainer意图，拆为可判定的行为证据条目。"""
        assert intent_items, "意图至少一条（否则无对账对象）"
        rec = {"task_id": task_id, "intent_items": list(intent_items),
               "registered": True}
        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def reconcile(self, task_id: str, evidence: dict) -> dict:
        """收口：不看自报，逐条对账行为证据。evidence={意图条目: [产物]}。"""
        entries = [json.loads(l) for l in open(LEDGER_PATH, encoding="utf-8")
                   if l.strip()]
        rec = next((e for e in entries if e["task_id"] == task_id), None)
        assert rec is not None, f"意图 {task_id} 未立案——先 register 再收口"
        missing, weak = [], []
        for item in rec["intent_items"]:
            prods = evidence.get(item)
            if not prods:
                missing.append(item)
            elif not any(str(p).strip() for p in prods):
                weak.append(item)   # 有字段无产物 = 空头支票
        drifted = bool(missing or weak)
        return {"task_id": task_id,
                "state": "DRIFTED" if drifted else "ALIGNED",
                "missing": missing, "weak": weak,
                "note": ("行为层缺证 → 意图未兑现，禁报完毕"
                         if drifted else "意图条目全部有行为证据")}


def selftest() -> None:
    import tempfile
    global LEDGER_PATH
    bak, LEDGER_PATH = LEDGER_PATH, os.path.join(
        tempfile.gettempdir(), "id_test.jsonl")
    if os.path.exists(LEDGER_PATH):
        os.remove(LEDGER_PATH)
    try:
        led = IntentLedger()
        # 对齐例：意图条目全有产物
        led.register("t1", ["修bug", "测试过"])
        r = led.reconcile("t1", {"修bug": ["smartpruner.py diff"],
                                 "测试过": ["selftest 3/3 ✅"]})
        assert r["state"] == "ALIGNED", r
        # 漂移例①：整条无证据（自报完成但拿不出产物）
        led.register("t2", ["修bug", "写文档"])
        r2 = led.reconcile("t2", {"修bug": ["diff ok"]})
        assert r2["state"] == "DRIFTED" and "写文档" in r2["missing"], r2
        # 漂移例②：空头支票（字段在、产物空）
        led.register("t3", ["验证"])
        r3 = led.reconcile("t3", {"验证": ["", "  "]})
        assert r3["state"] == "DRIFTED" and r3["weak"] == ["验证"], r3
        # 未立案拒收
        try:
            led.reconcile("t9", {})
            raise AssertionError("未立案应拒收")
        except AssertionError as e:
            assert "未立案" in str(e)
        print("intent_drift selftest 4/4 通过 ✅（对齐/整条漂移/空头支票/未立案拒收）")
    finally:
        os.remove(LEDGER_PATH)
        LEDGER_PATH = bak


if __name__ == "__main__":
    selftest()
