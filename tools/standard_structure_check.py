# -*- coding: utf-8 -*-
"""
standard_structure_check.py — 行业标准书结构校验器
防线：防止标准文档退化回「只有结论没有道理」的精简病。
机器断言：每条条款卡（T*/S*）必须含四层 —— 费曼 / 缘由 / 权威对照 / 正明证据。
用法：python standard_structure_check.py [html_path]   # 缺省校验最新版 v3.0
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = None  # 公开仓不含内部标准书，由调用方显式传入 html 路径

LAYERS = [("费曼", "l-fm"), ("缘由", "l-why"), ("权威对照", "l-auth"), ("正明证据", "l-zm")]


def check(path: str) -> tuple[list[str], int]:
    html = open(path, encoding="utf-8").read()
    # 抓条款卡：class="clause"（战术层）或 "clause s"（战略层）
    cards = re.findall(r'<div class="clause(?: s)?">(.*?)\n</div>', html, re.S)
    errors, n_clauses = [], 0
    for card in cards:
        m = re.search(r'<div class="ctitle">(T\d|S\d)', card)
        if not m:
            errors.append("存在无编号条款卡")
            continue
        cid = m.group(1)
        n_clauses += 1
        for label, cls in LAYERS:
            if cls not in card:
                errors.append(f"{cid} 缺少层 [{label}]")
            elif label not in card:
                errors.append(f"{cid} 层[{label}] class 存在但标签文字缺失")
    return errors, n_clauses


def selftest() -> None:
    # 正例：四层齐备
    good = '<div class="clause"><div class="ctitle">T1 · 写入闸</div>' + "".join(
        f'<div class="layer {c}"><span class="lb">{l}</span>x</div>' for l, c in LAYERS) + "\n</div>"
    # 反例：缺缘由层
    bad = good.replace("l-why", "l-x")
    open("_t_good.html", "w", encoding="utf-8").write(good)
    open("_t_bad.html", "w", encoding="utf-8").write(bad)
    e1, n1 = check("_t_good.html")
    e2, n2 = check("_t_bad.html")
    os.remove("_t_good.html")
    os.remove("_t_bad.html")
    assert n1 == 1 and not e1, (n1, e1)
    assert n2 == 1 and any("缘由" in x for x in e2), (n2, e2)
    print("selftest: 2/2 通过（正例全绿 / 缺层被拦）")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
        return
    if len(sys.argv) <= 1 and not DEFAULT:
        print("usage: python standard_structure_check.py <standard.html>")
        sys.exit(2)
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    errors, n = check(path)
    print(f"校验对象: {os.path.basename(path)}")
    print(f"条款数: {n}  要求四层: 费曼/缘由/权威对照/正明证据")
    if errors:
        print(f"❌ 未通过 ({len(errors)} 处):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"✅ {n}/{n} 条款四层齐备")


if __name__ == "__main__":
    main()
