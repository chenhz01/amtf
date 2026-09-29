# -*- coding: utf-8 -*-
"""amtf-memory CLI — validate / diff 两个命令。
用法：python -m amtf.cli validate <export.json> | python -m amtf.cli diff <a.json> <b.json>"""
import argparse
import json
import sys


def cmd_validate(args):
    from .validate import validate_file
    r = validate_file(args.file)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r["ok"] else 1


def _load_entries(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    return doc.get("entries", [])


def _key(e):
    return (e.get("content", ""), e.get("valid_from"), e.get("valid_until"))


def cmd_diff(args):
    """迁移审计：对比两份 AMTF 导出，报 新增/消失/变更（含时效与溯源变化）。"""
    a, b = { _key(e): e for e in _load_entries(args.a) }, { _key(e): e for e in _load_entries(args.b) }
    added = [b[k] for k in b.keys() - a.keys()]
    removed = [a[k] for k in a.keys() - b.keys()]
    changed = []
    for k in a.keys() & b.keys():
        diffs = {f: {"a": a[k].get(f), "b": b[k].get(f)}
                 for f in ("confidence", "provenance", "schema_version")
                 if a[k].get(f) != b[k].get(f)}
        if diffs:
            changed.append({"content": k[0][:60], "fields": diffs})
    out = {"added": len(added), "removed": len(removed), "changed": changed,
           "detail_added": [e["content"][:60] for e in added][:20],
           "detail_removed": [e["content"][:60] for e in removed][:20]}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="amtf-memory")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate", help="校验 AMTF 导出文件")
    v.add_argument("file")
    d = sub.add_parser("diff", help="对比两份 AMTF 导出（迁移审计）")
    d.add_argument("a")
    d.add_argument("b")
    args = p.parse_args(argv)
    return {"validate": cmd_validate, "diff": cmd_diff}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
