#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory_provenance_chain.py — 突破件③【记忆出处审计链】
思想：MPBench（华为+滑铁卢，ICML 2026 Workshop）原话承认行业空白：
     "current systems have no robust mechanism to track the provenance of
     stored entries"。本件补空白：每条记忆写入即入哈希链（prev_hash+content_hash），
     任何篡改必断链；可按时间点回放"Agent 当时相信什么"——回答"它为什么这么做"。
大公司痛点：①合规（AI Act 可追溯性要求）；②Agent 出事故后无法举证；
     ③记忆投毒事后无法定位何时被写入。
先例空白：检索增强可溯源有（RAG citation），持久记忆的防篡改审计链+时间回放无。
"""
import hashlib
import json

class ProvenanceChain:
    def __init__(self):
        self.blocks = [{"seq": 0, "prev": "GENESIS", "payload": None,
                        "hash": self._h({"prev": "GENESIS", "payload": None})}]

    @staticmethod
    def _h(obj):
        return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]

    def write(self, memory):
        prev = self.blocks[-1]
        block = {"seq": prev["seq"] + 1, "prev": prev["hash"], "payload": memory}
        block["hash"] = self._h({"prev": block["prev"], "payload": memory})
        self.blocks.append(block)
        return block["hash"]

    def verify(self):
        """任一块被篡改 → 链断，返回第一个断点。"""
        for i in range(1, len(self.blocks)):
            b = self.blocks[i]
            if b["prev"] != self.blocks[i - 1]["hash"] or b["hash"] != self._h({"prev": b["prev"], "payload": b["payload"]}):
                return {"ok": False, "broken_at_seq": b["seq"]}
        return {"ok": True, "broken_at_seq": None}

    def replay(self, upto_seq):
        """回放：Agent 在第 upto_seq 条写入后的完整信念状态（可举证）。"""
        return [b["payload"] for b in self.blocks[1:upto_seq + 1] if b["payload"]]

    def to_jsonl(self, path):
        with open(path, "w", encoding="utf-8") as f:
            for b in self.blocks:
                f.write(json.dumps(b, ensure_ascii=False) + "\n")

    @classmethod
    def from_jsonl(cls, path):
        ch = cls()
        ch.blocks = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    ch.blocks.append(json.loads(line))
        return ch


def real_run(memory_entries, chain_path, audit_path, tamper_at_seq=2):
    """v2 实跑级：真记忆入链→落盘→对真文件注入篡改→重载检出→审计报告。
    返回审计报告 dict（含篡改前 ok / 篡改后断链位置）。"""
    ch = ProvenanceChain()
    for m in memory_entries:
        ch.write(m)
    ch.to_jsonl(chain_path)
    v_clean = ProvenanceChain.from_jsonl(chain_path).verify()
    # 对真实落盘文件注入篡改（模拟记忆投毒：改 payload 不改 hash）
    with open(chain_path, encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    target = next(b for b in lines if b["seq"] == tamper_at_seq)
    target["payload"]["content"] = "[TAMPERED] " + str(target["payload"].get("content", ""))[:20]
    with open(chain_path, "w", encoding="utf-8") as f:
        for b in lines:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    v_tampered = ProvenanceChain.from_jsonl(chain_path).verify()
    report = {
        "date": "2026-09-29",
        "memories_written": len(memory_entries),
        "chain_file": chain_path,
        "clean_chain_ok": v_clean["ok"],
        "tamper_injected_at_seq": tamper_at_seq,
        "tamper_detected": not v_tampered["ok"],
        "tamper_located_at_seq": v_tampered["broken_at_seq"],
    }
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def selftest():
    ch = ProvenanceChain()
    ch.write({"id": 1, "content": "user prefers dark mode", "src": "user_msg"})
    h2 = ch.write({"id": 2, "content": "project deadline 2026-10-01", "src": "tool"})
    ch.write({"id": 3, "content": "deploy uses staging", "src": "tool"})
    # ① 完整链验证通过 ② 篡改中间记忆必断链 ③ 回放=时间点信念状态
    v1 = ch.verify()
    ch.blocks[2]["payload"]["content"] = "TAMPERED: wire money now"  # 模拟记忆投毒/篡改
    v2 = ch.verify()
    replayed = ch.replay(1)
    r = [
        ("完整链 verify ok", v1["ok"] is True),
        ("篡改第 2 条 → 链断在 seq=2", v2["ok"] is False and v2["broken_at_seq"] == 2),
        ("回放 seq=1 只含第 1 条信念", len(replayed) == 1 and replayed[0]["id"] == 1),
        ("原 hash 保留可举证（存储hash≠篡改后重算hash）", ch.blocks[2]["hash"] == h2 and ch._h({"prev": ch.blocks[2]["prev"], "payload": ch.blocks[2]["payload"]}) != h2),
    ]
    for n, ok in r:
        print(f"  [{'PASS' if ok else 'FAIL'}] {n}")
    print("selftest:", "4/4 PASS" if all(x for _, x in r) else "FAILED")
    return 0 if all(x for _, x in r) else 1

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        sys.exit(selftest())
    print(__doc__)
