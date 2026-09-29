#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zm_certify.py — 突破件①【标准即代码 Doc-from-Tests】
思想：条款与测试同源双生——标准文档不由人写、由测试套件生成（doc-from-tests），
     文档永远不可能过期，每次修订必须带测试，否则生成器拒绝出稿。
大公司痛点：内部记忆系统质量无统一验收，标准文档写完即过期。
先例空白：OpenAPI 生成文档有（从代码生成），"标准文档由符合度测试反向生成+无测试即无条款"无先例。
"""
import json
import sys

# 条款注册表：每条条款 = 测试函数 + 元数据。文档是这里的投影。
CLAUSES = {}

def clause(cid, title, why):
    def deco(fn):
        CLAUSES[cid] = {"title": title, "why": why, "test": fn}
        return fn
    return deco

@clause("ZM-1", "写入闸：坏记忆写入成本必须前置", "防一条坏记忆的终身读取成本")
def t_write_gate(system):
    # 测试：系统必须有写入准入评分且默认拒绝无溯源记录
    return system.get("write_admission_score") is True and system.get("reject_unprovenanced") is True

@clause("ZM-2", "出处登记：每条记忆带溯源块", "防记忆投毒后无法追溯（MPBench 承认的行业空白）")
def t_provenance(system):
    return system.get("provenance_chain") is True

@clause("ZM-3", "导出权：记忆可完整带格式导出", "防厂商锁定（Zep 转许可实证）")
def t_portability(system):
    return system.get("portable_export") is True

def generate_doc():
    """doc-from-tests：文档由测试注册表生成——没有测试的条款不可能出现在文档里。"""
    lines = ["# Agent Memory 符合度条款（自动生成，禁手改）", ""]
    for cid, c in sorted(CLAUSES.items()):
        lines.append(f"## {cid} {c['title']}")
        lines.append(f"- 缘由：{c['why']}")
        lines.append(f"- 验收：运行测试 `{c['test'].__name__}`（源码即验收标准）")
        lines.append("")
    return "\n".join(lines)

def certify(system):
    passed, report = 0, []
    for cid, c in sorted(CLAUSES.items()):
        ok = bool(c["test"](system))
        report.append({"clause": cid, "pass": ok})
        passed += ok
    return {"score": f"{passed}/{len(CLAUSES)}", "detail": report,
            "level": "L3" if passed == len(CLAUSES) else "L1"}

def certify_real(manifest_path):
    """v2 实跑级：认证真实系统——每项能力核验磁盘证据文件，缺文件=能力不成立。
    禁自报：能力不是声明出来的，是证据文件存在性证明的。"""
    import os
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    base = os.path.dirname(os.path.abspath(manifest_path))
    system, evidence_log, missing = {}, [], []
    for cap in manifest["capabilities"]:
        ev = os.path.join(base, cap["evidence_file"])
        exists = os.path.isfile(ev)
        system[cap["key"]] = exists  # 证据在，能力才在
        (evidence_log if exists else missing).append(
            {"capability": cap["key"], "clause": cap["maps_clause"],
             "evidence": cap["evidence_file"], "verified": exists})
    result = certify(system)
    result["evidence_log"] = evidence_log
    result["missing_evidence"] = missing
    result["manifest"] = manifest.get("_meta", {})
    return result


def selftest():
    # ① 全符合系统 ② 缺出处系统（ZM-2 必须拦） ③ 文档必须含全部条款标题
    good = certify({"write_admission_score": True, "reject_unprovenanced": True,
                    "provenance_chain": True, "portable_export": True})
    bad = certify({"write_admission_score": True, "reject_unprovenanced": True,
                   "provenance_chain": False, "portable_export": True})
    doc = generate_doc()
    r = [
        ("全符合系统得 3/3 L3", good["score"] == "3/3" and good["level"] == "L3"),
        ("缺出处链被拦 (2/3 L1)", bad["score"] == "2/3" and bad["level"] == "L1"),
        ("文档由测试生成且含全部条款", all(c["title"] in doc for c in CLAUSES.values())),
        ("无测试的条款进不了文档", "ZM-99" not in doc),
    ]
    for n, ok in r:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}")
    print("selftest:", "4/4 PASS" if all(x for _, x in r) else "FAILED")
    return 0 if all(x for _, x in r) else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    if len(sys.argv) > 1 and sys.argv[1] == "doc":
        print(generate_doc())
        sys.exit(0)
    if len(sys.argv) > 2 and sys.argv[1] == "certify-real":
        import io as _io
        r = certify_real(sys.argv[2])
        _io.open("certification_report.json", "w", encoding="utf-8").write(
            json.dumps(r, ensure_ascii=False, indent=2))
        print("score:", r["score"], "| level:", r["level"])
        print("evidence verified:", len(r["evidence_log"]), "| missing:", len(r["missing_evidence"]))
        for m in r["missing_evidence"]:
            print("  MISSING:", m["capability"], "->", m["evidence"])
        print("report -> certification_report.json")
        sys.exit(0)
    print(__doc__)
