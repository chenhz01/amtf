# -*- coding: utf-8 -*-
"""
ab_sampler.py — A/B 实验每日采样器（2026-09-27）
=================================================
对应《规定-R3未做好坏对比-v1.2》R3②执行项：A/B 实验从"声称"启动为
"预注册 + 数据采集"。设计冻结于 ab_preregistration.json（n=175/组）。

每日动作（已并入 18:00 巡检自动化）：
    python ab_sampler.py add "决策事件描述" 0.75 0.25,0.25,0.2,0.05
        —— 登记一条当日决策样本（week_parity 按日历自动判 A/B）
    python ab_sampler.py status
        —— 两组进度 + 距收满差多少 + 收满提示可跑检验
    python ab_sampler.py selftest

周交替规则（预注册 assignment 字段）：按 ISO 周号 % 4 →
    0,1 → A（对照） 2,3 → B（实验）→ 实际即 A/B/B/A 循环抵消漂移
评分口径（R-DA2 同口径，写死于预注册 metric.rubric）：
    四维各 0.25：钱包影响明确/证据链完整/方案对比≥3/事后验证通过
"""
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "ab_samples.jsonl")
PREREG = os.path.join(HERE, "ab_preregistration.json")


def week_parity(d: date) -> str:
    """ISO 周号 % 4：0,1→A（对照）；2,3→B（实验）。A/B/B/A 循环。"""
    return "A" if d.isocalendar()[1] % 4 in (0, 1) else "B"


def load_prereg() -> dict:
    with open(PREREG, encoding="utf-8") as f:
        return json.load(f)


def add(desc: str, quality: float, four_dims: str, scored_by: str = "owner",
        d: date | None = None) -> dict:
    dims = [float(x) for x in four_dims.split(",")]
    assert len(dims) == 4 and all(0 <= x <= 0.25 for x in dims), \
        f"四维各 0-0.25，收到 {dims}"
    q = sum(dims)
    assert abs(q - quality) < 1e-6, f"quality {quality} 与四维合计 {q} 不一致"
    rec = {"date": (d or date.today()).isoformat(),
           "week_parity": week_parity(d or date.today()),
           "desc": desc, "quality": q, "four_dims": dims,
           "scored_by": scored_by, "blind": True}
    with open(SAMPLES, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def status() -> dict:
    n_target = load_prereg()["sample_size_per_group"]
    counts = {"A": 0, "B": 0}
    sums = {"A": 0.0, "B": 0.0}
    if os.path.exists(SAMPLES):
        with open(SAMPLES, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                counts[r["week_parity"]] += 1
                sums[r["week_parity"]] += r["quality"]
    out = {"target_per_group": n_target, "counts": counts,
           "means": {k: (round(sums[k] / counts[k], 3) if counts[k] else None)
                     for k in counts},
           "remaining": {k: max(0, n_target - counts[k]) for k in counts}}
    out["ready"] = all(counts[k] >= n_target for k in counts)
    return out


def print_status() -> None:
    s = status()
    print("=" * 60)
    print(f"A/B 采样进度（预注册 n={s['target_per_group']}/组，α=0.05, power=0.80）")
    print(f"  A 对照组：{s['counts']['A']:>4} 条  均值 {s['means']['A']}  差 {s['remaining']['A']}")
    print(f"  B 实验组：{s['counts']['B']:>4} 条  均值 {s['means']['B']}  差 {s['remaining']['B']}")
    if s["ready"]:
        print("  ✅ 两组收满 → 可跑两独立样本 t 检验（勿中途加样）")
    else:
        print("  ⏳ 采集期：评分盲态（不告知分组），口径见 ab_preregistration.json")
    print("=" * 60)


def selftest() -> None:
    import tempfile
    global SAMPLES
    bak, SAMPLES = SAMPLES, os.path.join(tempfile.gettempdir(), "ab_test.jsonl")
    if os.path.exists(SAMPLES):
        os.remove(SAMPLES)
    try:
        # 口径一致性
        r = add("测试决策", 0.75, "0.25,0.25,0.2,0.05", d=date(2026, 9, 27))
        assert r["quality"] == 0.75 and r["week_parity"] in ("A", "B"), r
        try:
            add("坏条目", 0.9, "0.25,0.25,0.25,0.05", d=date(2026, 9, 27))
            raise AssertionError("四维合计不符应被拒")
        except AssertionError as e:
            if "四维合计" not in str(e):
                raise
        s = status()
        assert s["counts"]["A"] + s["counts"]["B"] == 1, s
        assert not s["ready"] and s["remaining"]["A"] > 0
        print("ab_sampler selftest 2/2 通过 ✅（口径一致/进度统计）")
    finally:
        os.remove(SAMPLES)
        SAMPLES = bak


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        selftest()
    elif len(sys.argv) >= 5 and sys.argv[1] == "add":
        r = add(sys.argv[2], float(sys.argv[3]), sys.argv[4])
        print(f"已采样 {r['date']} 组{r['week_parity']} q={r['quality']}")
        print_status()
    elif len(sys.argv) >= 2 and sys.argv[1] == "status":
        print_status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
