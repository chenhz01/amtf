# -*- coding: utf-8 -*-
"""jsonl_to_amtf adapter — 通用 JSONL → AMTF（保底通道：任意系统都能先走这条路）。
纪律：字段缺失→None 显式留空，由校验器点名（spec 原则 1 禁静默补值）。
被拒条目逐条列出（spec 原则 4 拒绝可见），绝不静默丢弃。"""
import json


def jsonl_to_amtf_lines(path: str, exporter="jsonl-adapter/0.1"):
    """逐行转换 JSONL → AMTF 导出封装。返回 (export_doc, line_errors)。
    line_errors: [{line, errors}]——解析失败的行也可见，不静默跳过。"""
    entries, line_errors = [], []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                m = json.loads(line)
            except json.JSONDecodeError as e:
                line_errors.append({"line": i, "errors": [{"rule": "PARSE", "msg": str(e)}]})
                continue
            entries.append({
                "schema_version": "amtf/1.0",
                "content": m.get("content", m.get("text", m.get("memory", ""))),
                "created_at": m.get("created_at") or m.get("date"),
                "valid_from": m.get("valid_from") or m.get("created_at") or m.get("date"),
                "valid_until": m.get("valid_until"),
                "provenance": {"channel": m.get("channel", "generic-jsonl"),
                               "origin": m.get("origin"), "trust": m.get("trust")},
                "confidence": m.get("confidence") if isinstance(m.get("confidence"), (int, float)) else None,
            })
    return {"format": "amtf/1.0", "exported_at": None, "exporter": exporter,
            "entries": entries}, line_errors
