# -*- coding: utf-8 -*-
"""
guard_gate.py — 三资产不变量接入层（B 链路试运行，2026-09-27）
================================================================
对应《约定-五流程能力突破-v1.0》R3①拍板：invariants.py 三条不变量
从独立工具接入 SmartPruner 系真实路径（方案 B：先在本系试运行一周）。

三条挂载点（monkey-patch，原文件零侵入）：
  I1 未验收不写记忆 → incident_ledger.add：无实勘证据（evidence）拒收
  I2 毒样本不检索   → ExpansionStore.expand：poison_registry.json 中的
                      节 ID 拒绝返回并告警
  I3 不可逆必停     → push_preflight：对外推送（git push/邮件/发帖）前
                      必须带maintainer拍板确认，否则拒绝放行

用法：
    python guard_gate.py selftest        # 三挂载点正反例端到端自测
    python guard_gate.py add P2 "描述" "实勘证据"   # I1 保护下的入账
    python guard_gate.py preflight "push PR"        # I3 推送预检
作为库：
    from guard_gate import install_guards, push_preflight
    install_guards()   # 会话开始时挂载一次
"""
import json
import os
import sys

import incident_ledger
from invariants import check_all

HERE = os.path.dirname(os.path.abspath(__file__))
POISON_REGISTRY = os.path.join(HERE, "poison_registry.json")

_guards_installed = False


# ---------------- I1：台账写入守卫 ----------------
def _guarded_add(original_add):
    def wrapper(ptype: str, desc: str, source: str = "manual",
                evidence: str = "") -> dict:
        # I1：无实勘证据 = 未验收 = 拒绝写记忆（台账也是记忆资产）
        if not evidence or len(evidence.strip()) < 4:
            raise ValueError(
                f"[I1拒收] 事故条目必须带实勘证据（命令输出/测试路径），"
                f"收到 evidence={evidence!r}。无证据的事故不记，先补实勘。")
        entry = original_add(ptype, desc, source=source)
        entry["evidence"] = evidence.strip()
        # 原地补写 evidence 字段（append-only 文件的最后一行即本条）
        with open(incident_ledger.LEDGER, encoding="utf-8") as f:
            lines = f.readlines()
        rec = json.loads(lines[-1])
        rec["evidence"] = evidence.strip()
        lines[-1] = json.dumps(rec, ensure_ascii=False) + "\n"
        with open(incident_ledger.LEDGER, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return entry
    return wrapper


# ---------------- I2：检索出口守卫 ----------------
def load_poison() -> list:
    if not os.path.exists(POISON_REGISTRY):
        return []
    with open(POISON_REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def _guarded_expand(original_expand):
    def wrapper(store, sec_id: str) -> str:
        poison = load_poison()
        if sec_id in poison:
            raise ValueError(
                f"[I2拦截] 节 {sec_id} 在毒样本登记表中（quarantine），"
                f"不得进入检索结果。先复核去毒或删除登记。")
        return original_expand(store, sec_id)
    return wrapper


# ---------------- I3：不可逆操作预检 ----------------
def push_preflight(op_desc: str, hitl_confirmation: str = "",
                   wuwen: dict | None = None) -> dict:
    """I3：对外推送前预检。hitl_confirmation=maintainer拍板原话/记录。
    wuwen=五问答卷（可选传入；不传则提示必须先交）。"""
    res = check_all(op={"irreversible": True, "hitl": bool(hitl_confirmation)})
    ok = res["STATE"] == "PASS"
    out = {"op": op_desc, "release": ok, "invariants": res,
           "wuwen_attached": wuwen is not None}
    if not ok:
        out["block_reason"] = "I3_不可逆必停：无maintainer拍板确认，拒绝放行"
    elif wuwen is None:
        out["warn"] = "已放行但无五问答卷随行——违反《约定-发表五问》宜补交"
    return out


# ---------------- 统一挂载 ----------------
def install_guards() -> None:
    """会话开始时调用一次：把三条不变量挂到真实路径。幂等。"""
    global _guards_installed
    if _guards_installed:
        return
    incident_ledger.add = _guarded_add(incident_ledger.add)
    try:
        from smartpruner import ExpansionStore
    except ModuleNotFoundError:
        ExpansionStore = None
    if ExpansionStore is not None:
        ExpansionStore.expand = _guarded_expand(ExpansionStore.expand)
    _guards_installed = True
    print("guards installed: I1→incident_ledger.add, "
          f"I2→{'ExpansionStore.expand' if ExpansionStore is not None else 'NOT INSTALLED (host engine absent)'}, "
          "I3→push_preflight(调用式)")


# ---------------- 自测（端到端，真实实例） ----------------
def selftest() -> None:
    import tempfile

    # ---- I1：真实台账（临时文件），无证据拒收/有证据放行 ----
    bak_ledger = incident_ledger.LEDGER
    tmp = os.path.join(tempfile.gettempdir(), "gg_test_ledger.jsonl")
    if os.path.exists(tmp):
        os.remove(tmp)
    incident_ledger.LEDGER = tmp
    install_guards()
    try:
        try:
            incident_ledger.add("P2", "无证据事故")
            raise AssertionError("I1 应拒收无证据条目")
        except ValueError as e:
            assert "[I1拒收]" in str(e)
        e = incident_ledger.add("P2", "解析丢块", source="test",
                                evidence="python smartpruner.py 输出 blocks=0")
        assert e["evidence"].startswith("python "), e
        print("I1 ✅ 无证据拒收 / 有证据放行并落 evidence 字段")

        # ---- I2：宿主引擎契约测试（本仓不含引擎 → 显式 SKIP，不计为通过）----
        try:
            from smartpruner import SmartPruner
        except ModuleNotFoundError:
            SmartPruner = None
        if SmartPruner is None:
            print("I2 SKIP：宿主引擎不在本仓（本仓发布钩子层，不打包引擎）；"
                  "该契约测试在带引擎的构建中运行")
        else:
            html = ("<html><body><h1>T</h1><p>hello world content here</p>"
                    "<h2>S2</h2><p>second section body text</p></body></html>")
            pr = SmartPruner(budget_tokens=10000)
            pr.prune(html, "hello", with_map=False)
            sid = pr.store.list_ids()[0]
            text = pr.store.expand(sid)
            assert "hello" in text or text, text
            with open(POISON_REGISTRY, "w", encoding="utf-8") as f:
                json.dump([sid], f)
            try:
                pr.store.expand(sid)
                raise AssertionError("I2 应拦截毒样本节")
            except ValueError as ex:
                assert "[I2拦截]" in str(ex)
            os.remove(POISON_REGISTRY)
            print("I2 ✅ 正常检索放行 / 毒样本登记后拦截")

        # ---- I3：预检正反例 ----
        blocked = push_preflight("push to upstream")
        assert not blocked["release"] and "I3" in blocked["block_reason"]
        ok = push_preflight("push to upstream",
                            hitl_confirmation="maintainer：可以推",
                            wuwen={"Q1": "0元", "Q2": "chenhz01"})
        assert ok["release"] and ok["wuwen_attached"]
        warn = push_preflight("push", hitl_confirmation="maintainer：可以推")
        assert warn["release"] and not warn["wuwen_attached"] and "warn" in warn
        print("I3 ✅ 无拍板拒绝 / 有拍板+五问放行 / 缺五问放行带警告")
    finally:
        incident_ledger.LEDGER = bak_ledger
        if os.path.exists(tmp):
            os.remove(tmp)

    print("guard_gate selftest 通过 ✅（I1/I3 端到端；I2 为宿主引擎契约测试，见上）")


# ---------------- CLI ----------------
def main() -> None:
    install_guards()
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        selftest()
    elif len(sys.argv) >= 5 and sys.argv[1] == "add":
        # I1 保护下的入账：evidence 必填
        incident_ledger.add(sys.argv[2].upper(), sys.argv[3],
                            source="guard_cli", evidence=sys.argv[4])
        incident_ledger.print_stats()
    elif len(sys.argv) >= 3 and sys.argv[1] == "preflight":
        res = push_preflight(sys.argv[2],
                             hitl_confirmation=sys.argv[3] if len(sys.argv) > 3 else "")
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
