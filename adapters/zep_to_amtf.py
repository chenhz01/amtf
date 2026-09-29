# -*- coding: utf-8 -*-
"""zep_to_amtf adapter — Zep (Graphiti 事实边) → AMTF。
输入口径：Graphiti fact edge 结构（fact/uuid/created_at/valid_at/invalid_at），
来自 Zep 官方文档对 temporal knowledge graph 的公开描述。
卖点映射：Zep 是全行业少有的**原生带时效**的记忆系统——valid_at/invalid_at
天然对应 AMTF valid_from/valid_until，几乎无损。
本 adapter 只做 schema 转换，零代码复用（zep-python Apache-2.0，2026-09-29 LICENSE 页核验）。"""


def zep_fact_to_amtf(e: dict) -> dict:
    """单条转换。invalid_at=null → AMTF valid_until=null（仍在生效），语义完全对齐。"""
    return {
        "schema_version": "amtf/1.0",
        "content": e.get("fact", e.get("content", "")),
        "created_at": e.get("created_at"),
        "valid_from": e.get("valid_at") or e.get("created_at"),
        "valid_until": e.get("invalid_at"),  # null=仍然生效（显式）
        "provenance": {"channel": "zep-graphiti", "origin": e.get("uuid"), "trust": "medium"},
        "confidence": None,  # Zep fact 无置信度字段 → null 禁编造
    }


def zep_export_to_amtf(facts: list, exporter="zep-adapter/0.1") -> dict:
    return {"format": "amtf/1.0", "exported_at": None, "exporter": exporter,
            "entries": [zep_fact_to_amtf(e) for e in facts]}
