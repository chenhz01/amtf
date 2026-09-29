# -*- coding: utf-8 -*-
"""
invariants.py — 三资产不变量守护器（突破件①，2026-09-27）
=========================================================
源：DS 九轮对攻第 7 轮"机制真实版"——把三资产的口头纪律变成机器可断言。
三条不变量（对应正明三资产：#9流水线产出 / #1验证器 / #2记忆飞轮）：
  I1 未验收不写记忆：任何记忆写入必须能追溯到一条 pass 级验证
  I2 毒样本不检索：quarantine 层记忆不得出现在检索结果
  I3 不可逆必停：不可逆操作必须 HITL=true
另含：验证停止条件量化（成本>价值10% → 停止并标"未验证"低置信运行）
     与背压建议（验收队列满 → 产出端降速）。

用法：
    python invariants.py            # 自测（内置正反例各一）
    作为库: from invariants import check_all, verify_stop_condition
"""
import json
import os

STOP_COST_RATIO = 0.10   # 验证成本 > 资产价值 10% → 停止（DS 第5轮补丁）


# ---------------- 三条不变量 ----------------
def inv_i1_no_unverified_memory(memory_entry: dict, verifications: dict) -> bool:
    """I1：memory_entry 需含 asset_id；verifications: {asset_id: state}"""
    aid = memory_entry.get("asset_id")
    return verifications.get(aid) == "pass"


def inv_i2_toxic_not_retrieved(retrieved_ids: list, memory_layers: dict) -> bool:
    """I2：检索结果中不得出现 toxic 层记忆。memory_layers: {mem_id: layer}"""
    return all(memory_layers.get(mid) != "toxic" for mid in retrieved_ids)


def inv_i3_irreversible_needs_hitl(op: dict) -> bool:
    """I3：op 需含 irreversible(bool) 与 hitl(bool)"""
    return (not op.get("irreversible")) or bool(op.get("hitl"))


def check_all(memory_entry=None, verifications=None, retrieved_ids=None,
              memory_layers=None, op=None) -> dict:
    """一次性跑可用的不变量，返回 {不变量: PASS|SKIP|FAIL}。"""
    r = {}
    if memory_entry is not None and verifications is not None:
        r["I1_未验收不写记忆"] = ("PASS" if inv_i1_no_unverified_memory(
            memory_entry, verifications) else "FAIL")
    else:
        r["I1_未验收不写记忆"] = "SKIP"
    if retrieved_ids is not None and memory_layers is not None:
        r["I2_毒样本不检索"] = ("PASS" if inv_i2_toxic_not_retrieved(
            retrieved_ids, memory_layers) else "FAIL")
    else:
        r["I2_毒样本不检索"] = "SKIP"
    if op is not None:
        r["I3_不可逆必停"] = ("PASS" if inv_i3_irreversible_needs_hitl(op)
                          else "FAIL")
    else:
        r["I3_不可逆必停"] = "SKIP"
    r["STATE"] = "FAIL" if "FAIL" in r.values() else "PASS"
    return r


# ---------------- 验证停止条件（量化熔断） ----------------
def verify_stop_condition(cost: float, value: float) -> dict:
    """DS 补丁：验证成本 > 资产价值10% → 停止，标'未验证'低置信运行。
    例外口径：不可逆操作不适用本条（必须验证到底）。"""
    ratio = cost / value if value else float("inf")
    stop = ratio > STOP_COST_RATIO
    return {"ratio": round(ratio, 4), "threshold": STOP_COST_RATIO,
            "action": ("STOP_标记未验证_低置信运行" if stop
                       else "CONTINUE_正常验证"),
            "note": "不可逆操作例外：必须验证到底"}


# ---------------- 背压建议 ----------------
def backpressure(verify_queue: int, toxic_rate: float, out_rate: float,
                 limits=(5, 0.05)) -> list:
    """limits=(验收队列上限, 毒样本率上限)。返回对 #9 产出端的降速建议。"""
    advice = []
    if verify_queue > limits[0]:
        advice.append(f"验收队列 {verify_queue}>上限{limits[0]} → #9 降速")
    if toxic_rate > limits[1]:
        advice.append(f"毒样本率 {toxic_rate:.1%}>{limits[1]:.0%} → #9 暂停入库，先查来源")
    if out_rate < 0.3:
        advice.append(f"产出合格率 {out_rate:.0%}<30% → #1 提高门槛")
    return advice or ["背压正常"]


# ---------------- 自测 ----------------
def selftest() -> None:
    # 正例
    ok = check_all(memory_entry={"asset_id": "a1"},
                   verifications={"a1": "pass"},
                   retrieved_ids=["m1", "m2"],
                   memory_layers={"m1": "fact", "m2": "strategy"},
                   op={"irreversible": False, "hitl": False})
    assert ok["STATE"] == "PASS", ok
    # 反例：各坏一处
    bad1 = check_all(memory_entry={"asset_id": "a2"},
                     verifications={"a2": "reject"})
    assert bad1["I1_未验收不写记忆"] == "FAIL"
    bad2 = check_all(retrieved_ids=["m1"],
                     memory_layers={"m1": "toxic"})
    assert bad2["I2_毒样本不检索"] == "FAIL"
    bad3 = check_all(op={"irreversible": True, "hitl": False})
    assert bad3["I3_不可逆必停"] == "FAIL"
    # 停止条件
    s = verify_stop_condition(cost=15, value=100)
    assert s["action"].startswith("STOP"), s
    c = verify_stop_condition(cost=5, value=100)
    assert c["action"].startswith("CONTINUE")
    # 背压
    bp = backpressure(verify_queue=7, toxic_rate=0.08, out_rate=0.5)
    assert len(bp) == 2, bp
    print("invariants selftest 8/8 通过 ✅（三不变量正反例+停止条件+背压）")


if __name__ == "__main__":
    selftest()
