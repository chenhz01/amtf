# -*- coding: utf-8 -*-
"""zmf.types — 单条记忆的类型定义（spec 第 2 节的代码投影）。"""
from dataclasses import dataclass, field, asdict
from typing import Optional

VERSION = "amtf/1.0"
REQUIRED = ["schema_version", "content", "created_at", "valid_from",
            "valid_until", "provenance", "confidence"]
TRUST_LEVELS = {"high", "medium", "low"}


@dataclass
class ZmfMemory:
    """一条可迁移记忆。所有字段显式——缺失=null，禁静默补默认值（spec 原则 1）。"""
    content: str
    created_at: Optional[str] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None          # null = 仍然有效（显式声明）
    provenance: Optional[dict] = None          # {channel, origin, trust}
    confidence: Optional[float] = None         # 0-1；未知=null 禁编造
    schema_version: str = VERSION
    extras: dict = field(default_factory=dict)  # forward-compatible：未知字段收这里

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in REQUIRED}
        d.update(self.extras)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ZmfMemory":
        known = {k: d.get(k) for k in REQUIRED}
        known["content"] = known["content"] if known["content"] is not None else ""
        m = cls(**known)
        m.extras = {k: v for k, v in d.items() if k not in REQUIRED}
        return m
