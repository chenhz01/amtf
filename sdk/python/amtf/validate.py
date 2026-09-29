# -*- coding: utf-8 -*-
"""zmf.validate — 校验器（spec 第 4 节 V1-V6+W1 的代码投影）。
与 v1 MVP 的本质区别：错误聚合不短路——一次报出所有问题（迁移审计需要全量问题清单）。"""
import json
import re
from datetime import datetime
from typing import Union

from .types import REQUIRED, TRUST_LEVELS

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ].*)?$")


def _parse_dt(v) -> bool:
    """宽松 ISO 解析：日期或日期时间均可。"""
    if not isinstance(v, str) or not ISO_RE.match(v):
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00").split(".")[0][:26])
        return True
    except ValueError:
        return False


def validate(entry: Union[dict, object]) -> dict:
    """校验单条 AMTF 记忆。返回 {ok, errors:[{rule, field, msg}], warnings:[{rule, msg}]}。
    错误聚合：V1 逐字段独立检查，缺三个字段报三条错误。"""
    d = entry.to_dict() if hasattr(entry, "to_dict") else dict(entry)
    errors, warnings = [], []

    # V1 必填字段逐个点名（聚合不短路）
    for k in REQUIRED:
        if k not in d:
            errors.append({"rule": "V1", "field": k, "msg": f"missing required field: {k}"})

    # V2 版本
    if d.get("schema_version") not in (None, "amtf/1.0"):
        errors.append({"rule": "V2", "field": "schema_version",
                       "msg": f"unsupported version: {d.get('schema_version')!r}"})

    # V3 confidence
    c = d.get("confidence")
    if c is not None and (not isinstance(c, (int, float)) or isinstance(c, bool) or not 0 <= c <= 1):
        errors.append({"rule": "V3", "field": "confidence", "msg": "must be null or a number in [0,1]"})

    # V5 provenance.trust
    p = d.get("provenance")
    if p is not None:
        if not isinstance(p, dict):
            errors.append({"rule": "V5", "field": "provenance", "msg": "must be an object or null"})
        else:
            for k in ("channel", "origin", "trust"):
                if k not in p:
                    errors.append({"rule": "V5", "field": f"provenance.{k}", "msg": f"missing: {k}"})
            if p.get("trust") not in TRUST_LEVELS and p.get("trust") is not None:
                errors.append({"rule": "V5", "field": "provenance.trust",
                               "msg": f"trust must be in {sorted(TRUST_LEVELS)}"})

    # V4 + V6 时间字段
    dates = {k: d.get(k) for k in ("created_at", "valid_from", "valid_until")}
    for k, v in dates.items():
        if v is not None and not _parse_dt(v):
            errors.append({"rule": "V6", "field": k, "msg": f"not ISO 8601: {v!r}"})
    if dates["valid_from"] and dates["valid_until"]:
        if _parse_dt(dates["valid_from"]) and _parse_dt(dates["valid_until"]) \
                and dates["valid_from"][:10] > dates["valid_until"][:10]:
            errors.append({"rule": "V4", "field": "valid_until",
                           "msg": f"valid_until {dates['valid_until']} earlier than valid_from {dates['valid_from']}"})

    # W1 永久记忆警告（信息性，不算错）
    if "valid_until" in d and d["valid_until"] is None:
        warnings.append({"rule": "W1", "msg": "valid_until=null (permanent memory) — confirm intentional"})

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def validate_file(path: str) -> dict:
    """校验一个 AMTF 导出文件（封装结构），逐条聚合。"""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if doc.get("format") != "amtf/1.0":
        return {"ok": False, "file": path,
                "errors": [{"rule": "V2", "field": "format",
                            "msg": f"expected format amtf/1.0, got {doc.get('format')!r}"}],
                "warnings": []}
    all_errors, all_warnings, n = [], [], 0
    for i, e in enumerate(doc.get("entries", [])):
        n += 1
        r = validate(e)
        for err in r["errors"]:
            all_errors.append({"entry": i, **err})
        for w in r["warnings"]:
            all_warnings.append({"entry": i, **w})
    return {"ok": not all_errors, "file": path, "entries": n,
            "errors": all_errors, "warnings": all_warnings}
