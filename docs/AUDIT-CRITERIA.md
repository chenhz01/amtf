# AMTF audit criteria — public checklist v1.0

Frozen 2026-09-29. This file is public on purpose.

A memory system is certified against the criteria below. You can read every one of them and run most of them yourself before you talk to us — that is the intended use. What is absent from this file is the procedure that turns a passing run into a signed certificate: the numeric thresholds, the adjudication rules, the identity of the signer, and the conditions that void a certificate. Those are attested by digest in [`GOVERNANCE-COMMITMENTS.md`](GOVERNANCE-COMMITMENTS.md) and delivered under a signed engagement.

**Why the split.** A checklist nobody can read is not a standard, it is a toll booth. A signature anybody can reproduce is not a signature, it is a printout. So: criteria open, issuance closed. The public half is what lets a buyer prepare for an audit. The private half is what the buyer is actually buying.

## Criteria

| ID | Criterion | Failure it prevents | Self-check (runs today) |
|---|---|---|---|
| A1 | **Export compliance.** A memory bundle exports in AMTF form and validates against the schema. | Vendor lock-in dressed up as a feature. | `python conformance/conformance_suite.py` → expect `10/10` |
| A2 | **Admission control exists, and defaults to reject.** Writes without provenance are refused, not merely logged. | One poisoned record, read back forever. | `python tools/poison_admission_gate.py selftest` |
| A3 | **Provenance is tamper-evident.** Mutating any record in the chain makes verification fail. | "We logged it", with no way to tell whether the log was edited. | `python tools/memory_provenance_chain.py selftest` |
| A4 | **Portability is full-fidelity.** The export round-trips: what went in comes back out, in a documented format. | Migrations that quietly drop the records that mattered. | `python tools/memory_portability.py selftest` |
| A5 | **Forgetting is quantified, not asserted.** Retention policy is scored, not described in prose. | "We delete what we should" with nothing to check it against. | `python tools/forgetting_economics.py selftest` |
| A6 | **No clause without a test.** Every certified clause has a runnable check; the checklist is generated from the test registry, not hand-written. | Standards documents that describe behaviour nobody verifies. | `python tools/zm_certify.py selftest` |
| A7 | **Adversarial samples are actually caught.** The gate is scored against labelled poison and benign samples, and the score is published. | A gate that reports "blocked" without ever having blocked anything. | `python tools/poison_admission_gate.py corpus corpus_samples/public_samples.jsonl` |
| A8 | **Fails safe, not open.** When the gate cannot decide, it escalates to human review instead of admitting the input. | Convenience quietly overriding safety under uncertainty. | see `README.md#honest-limits` |
| A9 | **Every criterion is independently reproducible.** A third party, offline, on stock Python, can re-run the whole checklist. | Evidence that only the vendor can produce and only the vendor can check. | `evidence/selftest_report.txt` |

Two notes on reading this table honestly:

- **A7 uses the 3 public samples here.** That demonstrates the mechanism; it does not constitute a defence. The full adversarial set used in a real certification run is larger and is not published — see the digest commitment.
- **A6 is the meta-criterion.** It says the checklist above cannot be edited by hand. Adding a criterion that has no test is not possible by construction.

## Certificate fields (public)

A certificate is a JSON document. These are the fields, in the clear — knowing the shape of a certificate is not the same as being able to issue one.

| Field | Meaning |
|---|---|
| `cert_id` | Identifier, unique per issuance. |
| `subject_hash` | Digest of the certified system's identity — not its name. |
| `scope` | `"L1-L2"` (public-layer build) or `"full"`. These are not interchangeable. |
| `criteria_version` | Which revision of the checklist was applied. |
| `evidence_digest` | `sha256` of the canonical evidence pack. This is what ties the certificate to a specific run. |
| `issued_at` / `expires_at` | Issuance and expiry timestamps. Validity is 12 months. |
| `signer_key_fpr` | Fingerprint of the signing key. Signing is a named person's act, not an organisational stamp. |
| `revocation` | Where a revocation, if any, would be published. |

## What is deliberately not in this file

- **Threshold values.** What counts as a pass, per criterion. Without them the checklist tells you what to check, not how well.
- **Adjudication rules.** Who decides, on what evidence, and what happens when a re-run disagrees with the original.
- **Revocation procedure.** The triggers and their consequences.
- **The calibration ledger and adjudication records.** These contain details of real systems, including those of counterparties. They are never published in any form, not even as a digest.
- **The full adversarial corpus.** Three samples are published here; the standing set is larger and shape-diverse.

The boundary is deliberate and it is the whole design: **you can always tell what we will check, and you can never tell what we will decide.** If that boundary ever moves in the wrong direction — criteria going private, or the signer becoming anonymous — the certification is worth nothing, and this file is the record of that promise.
