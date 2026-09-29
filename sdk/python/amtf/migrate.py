# -*- coding: utf-8 -*-
"""zmf.migrate — 跨厂商迁移（spec 第 1 节原则 4：拒绝可见，禁静默丢弃）。"""
import json

from .validate import validate


def migrate(entries: list) -> dict:
    """批量迁移：逐条校验，可导入/被拒/警告全量可见。
    返回 {total, imported, rejected, rejected_detail, warnings_count}。"""
    imported, rejected, rejected_detail, warnings_count = [], [], [], 0
    for i, e in enumerate(entries):
        r = validate(e)
        if r["ok"]:
            imported.append(e)
            warnings_count += len(r["warnings"])
        else:
            rejected.append(i)
            rejected_detail.append({"entry": i, "errors": r["errors"]})  # 拒绝可见
    return {"total": len(entries), "imported": imported,
            "imported_count": len(imported), "rejected_count": len(rejected),
            "rejected": rejected, "rejected_detail": rejected_detail,
            "warnings_count": warnings_count}


def migrate_file(path: str, out_path: str = None) -> dict:
    """读 AMTF 导出文件→迁移→（可选）把可导入集写成新 AMTF 文件。"""
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    result = migrate(doc.get("entries", []))
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"format": doc.get("format"), "exported_at": doc.get("exported_at"),
                       "exporter": f"amtf-migrate/{doc.get('exporter', 'unknown')}",
                       "entries": result["imported"]}, f, ensure_ascii=False, indent=2)
        result["written_to"] = out_path
    return result
