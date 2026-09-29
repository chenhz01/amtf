# AMTF — Agent Memory Transfer Format Specification v1.0

> Status: **public draft v1.0**. This specification is the single source of truth for the SDK, adapters and conformance suite in this repository.
> Spec text and code are licensed under MIT (see `LICENSE`).
> 中文原文见 `SPEC.md`；两版如有冲突，以 `SPEC.md` 为准。

## 0. In one line

AMTF is a common export format for AI-agent long-term memory, so that switching platforms does not mean abandoning what the agent learned about you — GDPR Article 20, adapted for agents. Core = a thin schema; ecosystem = one export adapter per memory framework.

## 1. Design principles

1. **Explicit fields, never silent defaults.** A missing value must be `null` and named during validation. Filling in a default silently is the most dangerous lie in memory migration.
2. **Validity is first-class.** Every memory carries an effective window (`valid_from` / `valid_until`); "forever" is expressed as an explicit `null`, never by omission.
3. **Provenance is mandatory.** Every memory declares which channel it came from and at what trust level. Memories without provenance may migrate, but they must be marked.
4. **Rejections are visible.** Every rejected memory is listed with its reason. Silent dropping is forbidden.

## 2. Memory entry schema (single entry)

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema_version` | string | yes | always `"amtf/1.0"` |
| `content` | string | yes | the memory itself (a fact, preference, or lesson in natural language) |
| `created_at` | string\|null | yes | first write time, ISO 8601 date or datetime; `null` if unknown |
| `valid_from` | string\|null | yes | start of validity; `null` if unknown |
| `valid_until` | string\|null | yes | end of validity; **`null` means still valid** (stated, not omitted) |
| `provenance` | object\|null | yes | `{channel, origin, trust}`; `channel` from an enum, `origin` identifies the source, `trust` ∈ {high, medium, low}; whole object `null` if unknown |
| `confidence` | number\|null | yes | 0–1; `null` if unknown (never invent 0.8) |

## 3. Export envelope

```json
{
  "format": "amtf/1.0",
  "exported_at": "2026-09-29T18:00:00+08:00",
  "exporter": "mem0-adapter/0.1",
  "entries": [ { "...entry schema from section 2..." } ]
}
```

## 4. Validation rules (one-to-one with the conformance suite)

- V1: all seven required fields present — a missing field must raise its own error, aggregated without short-circuiting
- V2: `schema_version == "amtf/1.0"`
- V3: `confidence` is `null` or a float in 0–1
- V4: `valid_from <= valid_until` when both are non-null
- V5: `provenance.trust ∈ {high, medium, low}` when `provenance` is non-null
- V6: `created_at` / `valid_from` / `valid_until`, when non-null, must parse as ISO 8601
- W1 (warning): `valid_until=null` → "permanent memory — confirm this is intentional"

## 5. Compatibility promise

After v1.0, fields are only added — never renamed, never removed — and consumers must ignore unknown fields (forward-compatible).

## 6. Governance

Governance of this specification follows the principle "**checklist open, signature closed**", in three layers:

| Layer | Contents | Where |
|---|---|---|
| Open | Certification audit criteria A1–A9, certificate field definitions, scope boundaries | [`docs/AUDIT-CRITERIA.md`](../docs/AUDIT-CRITERIA.md) |
| Locked (digest-committed) | Issuance and adjudication procedure: thresholds, signers, dispute and revocation process, ledger structure | [`docs/GOVERNANCE-COMMITMENTS.md`](../docs/GOVERNANCE-COMMITMENTS.md) (SHA-256 digests only; body delivered under signed engagement) |
| Never published | Adjudication ledger, calibration records, corpus body | kept out of every public repository |

Certification is **not** issued by this repository — this repo ships the reproducible conformance suite and the criteria; who signs is recorded in GOVERNANCE-COMMITMENTS.md.
