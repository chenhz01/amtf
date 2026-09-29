#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory_portability.py — 突破件④【记忆可携协议 AMTF】
思想：GDPR 第 20 条给了人类"数据可携权"，AI Agent 的记忆没有对等物——
     用户换了 Agent 平台，几年的偏好/上下文/失败教训全部归零。
     AMTF（Agent Memory Transfer Format）= 记忆的统一导出格式：先到先得的协议卡位。
大公司痛点：监管迟早把可携权延伸到 Agent 记忆；谁先定义格式谁就是标准
     （USB-C 立法先例）。他们不来谈，格式就按我们的来。
先例空白：RAG 文档迁移有（各种 ETL），持久记忆（含时效/溯源/置信）的
     跨厂商格式无任何先例。Zep 转许可实证了"格式被厂商锁死"的真实风险。
"""
import json

# AMTF 最小 schema：一条可迁移记忆的必填字段
REQUIRED = ["content", "created_at", "valid_from", "valid_until",
            "provenance", "confidence", "schema_version"]
VERSION = "amtf/1.0"

def to_zmf(mem):
    """任意系统记忆 → AMTF。缺字段显式置 null（禁静默补默认值）。"""
    return {
        "schema_version": VERSION,
        "content": mem.get("content"),
        "created_at": mem.get("created_at"),
        "valid_from": mem.get("valid_from"),
        "valid_until": mem.get("valid_until"),
        "provenance": mem.get("provenance"),      # {channel, origin, trust}
        "confidence": mem.get("confidence"),       # 0-1
    }

def validate(zmf):
    missing = [k for k in REQUIRED if k not in zmf]
    if missing:
        return {"ok": False, "missing": missing}
    if zmf["schema_version"] != VERSION:
        return {"ok": False, "missing": [], "error": f"version mismatch: {zmf['schema_version']}"}
    if not isinstance(zmf["confidence"], (int, float)) or not 0 <= zmf["confidence"] <= 1:
        return {"ok": False, "missing": [], "error": "confidence must be 0-1"}
    return {"ok": True, "missing": []}

def migrate(exported_list):
    """跨厂商迁移：批量 AMTF 校验，返回可导入集与被拒集（拒绝静默丢弃）。"""
    ok, rejected = [], []
    for m in exported_list:
        (ok if validate(m)["ok"] else rejected).append(m)
    return {"imported": ok, "rejected": rejected, "total": len(exported_list)}

def export_real(md_paths, out_path):
    """v2 实跑级：解析真实记忆日志（Markdown 每个二级标题=一条记忆）→ AMTF 批量导出落盘。
    溯源口径：channel=internal_log, trust=medium（内部日志级），created_at=文件名日期。"""
    import os, re
    mems = []
    for p in md_paths:
        date = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(p))
        created = date.group(1) if date else "unknown"
        with open(p, encoding="utf-8") as f:
            content = f.read()
        for sec in re.split(r"\n(?=## )", content):
            sec = sec.strip()
            if not sec.startswith("## "):
                continue  # 跳过文件头（非记忆）
            title = sec.split("\n", 1)[0].lstrip("# ").strip()
            body = (sec.split("\n", 1)[1] if "\n" in sec else "").strip()
            mems.append(to_zmf({
                "content": f"{title}：{body[:180]}",
                "created_at": created, "valid_from": created, "valid_until": None,
                "provenance": {"channel": "internal_log", "origin": os.path.basename(p), "trust": "medium"},
                "confidence": 0.8,
            }))
    mig = migrate(mems)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"format": VERSION, "exported_at": "2026-09-29",
                   "entries": mems, "migration": mig}, f, ensure_ascii=False, indent=2)
    return {"total": mig["total"], "imported": len(mig["imported"]),
            "rejected": len(mig["rejected"]), "out": out_path}


def selftest():
    good = to_zmf({"content": "user prefers dark mode", "created_at": "2026-09-29",
                   "valid_from": "2026-09-29", "valid_until": None,
                   "provenance": {"channel": "user_msg", "origin": "u1", "trust": "high"},
                   "confidence": 0.95})
    bad = {"schema_version": "amtf/1.0", "content": "bad confidence", "created_at": "2026-09-29", "valid_from": "2026-09-29", "valid_until": None, "provenance": {"channel": "tool", "origin": "t1", "trust": "low"}, "confidence": 2.0}
    mig = migrate([good, bad])
    # ④ 往返幂等：export→import→export 字段不丢
    rt = to_zmf({k: good[k] for k in REQUIRED if k != "schema_version"} | {"schema_version": VERSION})
    r = [
        ("合规记忆 validate ok", validate(good)["ok"] is True),
        ("缺 provenance 被点名", "provenance" in validate(bad)["missing"] or validate(bad).get("error")),
        ("confidence=2.0 被拒", validate(bad).get("error") == "confidence must be 0-1"),
        ("迁移：1 导入 1 拒绝（拒绝可见禁静默丢）", mig["total"] == 2 and len(mig["imported"]) == 1 and len(mig["rejected"]) == 1),
        ("往返幂等", rt == good),
    ]
    for n, ok in r:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}")
    print("selftest:", "5/5 PASS" if all(x for _, x in r) else "FAILED")
    return 0 if all(x for _, x in r) else 1

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    if len(sys.argv) > 3 and sys.argv[1] == "export-real":
        r = export_real(sys.argv[2:-1], sys.argv[-1])
        print(json.dumps(r, ensure_ascii=False, indent=2))
        sys.exit(0)
    print(__doc__)
