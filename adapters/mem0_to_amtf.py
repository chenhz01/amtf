# -*- coding: utf-8 -*-
"""mem0_to_amtf adapter — Mem0 记忆条目 → AMTF。
输入口径：Mem0 v2 REST `GET /v2/memories/` 返回的记忆条目结构
（id/memory/created_at/updated_at/score/metadata），见 Mem0 官方 API 文档。
本 adapter 只做 schema 转换，零代码复用（Mem0 本仓 Apache-2.0）。"""


def mem0_entry_to_amtf(m: dict) -> dict:
    """单条转换。映射：memory→content；created_at→created_at/valid_from；
    score→confidence（缺失=null 禁编造）；metadata→extras 透传（forward-compatible）。"""
    return {
        "schema_version": "amtf/1.0",
        "content": m.get("memory", m.get("content", "")),
        "created_at": m.get("created_at"),
        "valid_from": m.get("created_at"),
        "valid_until": None,  # Mem0 无失效概念 → 显式 null（永久），W1 警告兜底
        "provenance": {"channel": "mem0", "origin": m.get("id"), "trust": "medium"},
        "confidence": m.get("score") if isinstance(m.get("score"), (int, float)) else None,
    }


def mem0_export_to_amtf(memories: list, exporter="mem0-adapter/0.1") -> dict:
    return {"format": "amtf/1.0", "exported_at": None, "exporter": exporter,
            "entries": [mem0_entry_to_amtf(m) for m in memories]}
