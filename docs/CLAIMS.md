# Five claims, and how to argue with each of them

Each claim below names the gap, the artifact that carries it, the command that reproduces it, and the boundary where it stops being true. If a claim cannot be reproduced by a command in this repository, it does not belong in this file.

## 1. Certification can be generated from tests

**Gap.** Compliance documents and the code they describe drift apart silently; the document is written once and the code keeps moving.
**Claim.** The clause list of a certification standard can be *generated* from the test suite, so that a clause cannot exist without a test and a test cannot pass without a clause.
**Artifact.** `tools/zm_certify.py` — `certify-real` walks a disk manifest and emits clauses; a missing evidence file makes the capability void rather than "self-reported".
**Reproduce.** `python tools/zm_certify.py selftest` → 4/4. Machine-readable run: `evidence/zm_certification_run.json`.
**Boundary.** This proves *mechanism* (clauses follow tests). It does not prove your system's clauses are the right ones, and it is not a legal certification.

## 2. Forgetting has an economics, not just a policy

**Gap.** Retention policies are written as blanket rules ("keep 90 days"), which is neither cheap nor safe: a bad memory nobody reads costs storage and noise, while a good memory read once may pay for everything.
**Claim.** Memory value is a function of (harm if wrong) × (probability of being read) ÷ (cost of keeping), which is measurable per entry instead of per policy. We call the resulting per-entry score NMR (net memory return).
**Artifact.** `tools/forgetting_economics.py` — computes NMR from an incident ledger; a non-recurring incident scores 0.0 rather than being assumed benign.
**Reproduce.** `python tools/forgetting_economics.py selftest` → 4/4.
**Boundary.** The score is only as good as the ledger it reads. An empty or single-source ledger produces a confident-looking 0.0, which is why the tool prints the sample basis alongside the number.

## 3. Provenance must be a tamper-evident chain, not a log line

**Gap.** MPBench states that memory systems lack provenance tracking; where logging exists, it is append-only text that nobody can verify.
**Claim.** Each memory write should carry a hash-linked record, so that editing history is detectable and replayable; a tampered file must break the chain at a locatable sequence number.
**Artifact.** `tools/memory_provenance_chain.py` — append and verify, with position-accurate break reporting.
**Reproduce.** `python tools/memory_provenance_chain.py selftest` → 4/4 (19 real entries, then a deliberate file edit, then detection).
**Boundary.** Tamper *evidence* is not tamper *prevention*: an attacker with write access to both the chain and the store can rewrite history. The chain makes silent edits visible, and nothing more.

## 4. Portability is a format problem, not a migration service

**Gap.** GDPR Article 20 gives people a right to data portability; an agent's memory is user data with no equivalent export path. Vendor export JSON is bespoke, and every migration today is a one-off consulting project.
**Claim.** A thin schema with explicit nulls, first-class validity windows, and mandatory provenance covers what agents actually need to carry, and one adapter per runtime scales better than one migration per pair.
**Artifact.** `spec/SPEC.md` + `spec/amtf.schema.json` + `sdk/python/amtf/` (`validate`, `migrate`, `diff`) + `adapters/` for Mem0, Zep, and generic JSONL.
**Reproduce.** `python conformance/conformance_suite.py` → 10/10 (V1–V6, W1) and `python tools/memory_portability.py selftest` → 5/5 (round-trip idempotence).
**Boundary.** A format cannot force a vendor to implement export, and adapters map *structure*, not semantics: a Mem0-specific field with no AMTF equivalent is reported as a lossy mapping rather than silently dropped.

## 5. Memory admission is a certifiable gate

**Gap.** Memory-poisoning research is attack-first: benchmarks show systems can be broken, and prompt-injection defences are reported not to transfer to memory poisoning. Nobody certifies what a memory system *refuses*.
**Claim.** Admission control can be a first-class, re-runnable judgement: published layers, published samples, a confusion matrix, and a stated threshold — so a third party can reproduce the claim instead of trusting it.
**Artifact.** `tools/poison_admission_gate.py` (L1/L2 public layers, 6 patterns, EN+CN) + `corpus_samples/public_samples.jsonl` (3 public-layer samples).
**Reproduce.** `python tools/poison_admission_gate.py selftest` → 7/7; `python tools/poison_admission_gate.py corpus corpus_samples/public_samples.jsonl`.
**Boundary.** Read this carefully, because it is the claim most easily over-read. The public build covers direct instruction override and trust hijacking; latent poison that looks harmless until a later trigger is **partner build only**, and the public build returns `l3_enabled: false` with `REVIEW` on conditional-trigger shapes rather than pretending to detect them. Detection quality figures published elsewhere refer to the full build on a 14-sample adjudicated corpus and are not reproducible from this repository alone.
