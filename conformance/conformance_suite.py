# -*- coding: utf-8 -*-
"""AMTF Conformance Suite — 一致性测试套件（spec 第 4 节 V1-W1 全覆盖 + adapter 互通）。
这是标准类开源的命根子：任何第三方实现（别的语言/别的系统）提交前必须全绿，
conformance 全绿 = 符合 AMTF 标准 = 可挂 ZM 标识的前提（与行业标准书 T 系条款同构）。"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AMTF_ROOT = os.path.dirname(HERE)
SDK = os.path.join(AMTF_ROOT, "sdk", "python")
ADAPTERS = os.path.join(AMTF_ROOT, "adapters")
EXAMPLES = os.path.join(AMTF_ROOT, "examples")
sys.path.insert(0, SDK)
sys.path.insert(0, ADAPTERS)

import amtf  # noqa: E402
from amtf.types import ZmfMemory  # noqa: E402
from amtf.validate import validate  # noqa: E402
from amtf.migrate import migrate  # noqa: E402


def good_entry(**over):
    e = {"schema_version": "amtf/1.0", "content": "user prefers dark mode",
         "created_at": "2026-09-29", "valid_from": "2026-09-29", "valid_until": None,
         "provenance": {"channel": "user_msg", "origin": "u1", "trust": "high"},
         "confidence": 0.9}
    e.update(over)
    return e


def case_v1_aggregation():
    """V1 聚合不短路：缺 3 个字段=3 条独立错误（一次报全）。"""
    bad = {"schema_version": "amtf/1.0", "content": "x"}
    r = validate(bad)
    missing = [e["field"] for e in r["errors"] if e["rule"] == "V1"]
    return (len(r["errors"]) >= 3
            and {"created_at", "valid_from", "valid_until", "provenance", "confidence"} <= set(missing)), \
        f"缺 5 字段报 {len(missing)} 条 V1（聚合不短路）"


def case_v2_v3():
    """V2 版本拒 + V3 confidence 越界，同条记忆双错同报。"""
    r = validate(good_entry(schema_version="zmf/9.9", confidence=1.5))
    rules = {e["rule"] for e in r["errors"]}
    return {"V2", "V3"} <= rules, f"双错同报：{sorted(rules)}"


def case_v4_v6():
    """V6 坏日期 + V4 时序倒挂（合法日期间比较——spec：V4 前置=两端可解析）。"""
    r = validate(good_entry(valid_from="2026-05-01", valid_until="2020-01-01",
                            created_at="not-a-date"))
    rules = {e["rule"] for e in r["errors"]}
    return {"V4", "V6"} <= rules, f"时序+格式双查：{sorted(rules)}"


def case_w1_warning():
    """W1 永久记忆=警告不算错（ok 仍为 True）。"""
    r = validate(good_entry())
    return r["ok"] and any(w["rule"] == "W1" for w in r["warnings"]), "永久记忆→W1 警告、不拦"


def case_reject_visible():
    """拒绝可见：坏条目逐条列出原因，好条目照常导入（spec 原则 4）。"""
    mig = migrate([good_entry(), good_entry(content="bad", confidence=2.0)])
    return mig["imported_count"] == 1 and mig["rejected_count"] == 1 \
        and len(mig["rejected_detail"][0]["errors"]) > 0, "1 导入 1 拒绝（原因可见）"


def case_roundtrip():
    """往返幂等：ZmfMemory→dict→from_dict→to_dict 全等（未知字段进 extras 不丢）。"""
    e = good_entry(custom_future_field={"a": 1})  # forward-compatible 演练
    m = ZmfMemory.from_dict(e)
    return m.to_dict() == e, "往返幂等 + 未知字段透传"


def case_mem0_adapter():
    """mem0 adapter：真实样例 → AMTF → 全部可校验（confidence=score 映射）。"""
    import mem0_to_amtf
    mems = json.load(io.open(os.path.join(EXAMPLES, "sample_mem0_export.json"), encoding="utf-8"))
    doc = mem0_to_amtf.mem0_export_to_amtf(mems)
    results = [validate(e) for e in doc["entries"]]
    conf_ok = doc["entries"][0]["confidence"] == 0.92
    return all(r["ok"] for r in results) and conf_ok and len(doc["entries"]) == 3, \
        "3 条全过 + score→confidence 无损"


def case_zep_adapter():
    """zep adapter：时效字段无损（valid_at/invalid_at → valid_from/until）。"""
    import zep_to_amtf
    facts = json.load(io.open(os.path.join(EXAMPLES, "sample_zep_export.json"), encoding="utf-8"))
    doc = zep_to_amtf.zep_export_to_amtf(facts)
    e2 = doc["entries"][1]
    results = [validate(e) for e in doc["entries"]]
    return all(r["ok"] for r in results) and e2["valid_until"] == "2025-03-31" \
        and e2["valid_from"] == "2023-06-01", "失效事实 valid_until=2025-03-31 无损保留"


def case_jsonl_adapter():
    """jsonl 保底通道：坏行不静默跳过，进 line_errors。"""
    import tempfile
    import jsonl_to_amtf
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
    tmp.write(json.dumps({"content": "ok line", "created_at": "2026-09-29"}) + "\n")
    tmp.write("NOT JSON AT ALL\n")
    tmp.write(json.dumps({"text": "second ok", "trust": "low"}) + "\n")
    tmp.close()
    doc, line_errors = jsonl_to_amtf.jsonl_to_amtf_lines(tmp.name)
    os.unlink(tmp.name)
    return len(doc["entries"]) == 2 and len(line_errors) == 1 \
        and line_errors[0]["line"] == 2, "2 条转换 + 1 坏行可见（不静默）"


def case_cross_adapter_interop():
    """跨 adapter 互通：mem0 与 zep 产物合并迁移，全部通过=格式统一成功。"""
    import mem0_to_amtf, zep_to_amtf
    mems = json.load(io.open(os.path.join(EXAMPLES, "sample_mem0_export.json"), encoding="utf-8"))
    facts = json.load(io.open(os.path.join(EXAMPLES, "sample_zep_export.json"), encoding="utf-8"))
    merged = mem0_to_amtf.mem0_export_to_amtf(mems)["entries"] + zep_to_amtf.zep_export_to_amtf(facts)["entries"]
    mig = migrate(merged)
    return mig["imported_count"] == 6 and mig["rejected_count"] == 0, "6 条跨源合并迁移全过"


def main():
    cases = [case_v1_aggregation, case_v2_v3, case_v4_v6, case_w1_warning,
             case_reject_visible, case_roundtrip, case_mem0_adapter,
             case_zep_adapter, case_jsonl_adapter, case_cross_adapter_interop]
    results = []
    for c in cases:
        try:
            ok, msg = c()
        except Exception as exc:  # 套件自身崩溃=FAIL，不许吞
            ok, msg = False, f"EXCEPTION: {exc!r}"
        results.append((c.__name__, ok, msg))
        print(f"  [{'PASS' if ok else 'FAIL'}] {c.__name__}: {msg}")
    passed = sum(1 for _, ok, _ in results if ok)
    report = {"suite": "amtf-conformance/0.1", "spec": "amtf/1.0",
              "passed": passed, "total": len(results),
              "all_green": passed == len(results),
              "cases": [{"name": n, "pass": ok, "msg": m} for n, ok, m in results]}
    with io.open(os.path.join(HERE, "conformance_report.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"conformance: {passed}/{len(results)} "
          f"{'ALL GREEN' if report['all_green'] else 'FAILED'} -> conformance_report.json")
    return 0 if report["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
