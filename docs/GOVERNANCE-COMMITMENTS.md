# Governance commitments — published digests, unpublished content

Frozen 2026-09-29.

Two governance assets exist and are maintained. Their contents are deliberately absent from this repository. Their **SHA-256 digests are published here**, so the claim "this file existed, in this state, on this date" can be tested by anyone later — without the file being readable now.

**Digest convention.** `sha256` over the file's UTF-8 bytes with LF line endings, lowercase hex. Reproduce any digest below with:

```bash
python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read().replace(b'\r\n',b'\n')).hexdigest())" <file>
```

## Committed assets

| ID | What it is | Digest (sha256) | First committed |
|---|---|---|---|
| `amtf-certification-procedure` | The issuance and adjudication procedure: thresholds, signer identity, dispute handling, revocation triggers, ledger schema. The step that turns a passing audit into a signed certificate. | `81810c3955bb919faad9bb0904d5fb4645682827267f46cb00c5555a1881e837` | 2026-09-29 |
| `amtf-l3-latent-layer` | The latent-trigger detection layer (L3) and its calibration table, excluded from the public build. | `bc016be4b4b5416028e7eb03839af2ff6d6640774ff977960f780f77abb70d5a` | 2026-09-29 |

The public checklist these assets operate on is in [`AUDIT-CRITERIA.md`](AUDIT-CRITERIA.md). The criteria are open; the digests above cover what decides.

## What these digests do and do not prove

**They prove:** the bytes existed in this state no later than the date recorded above, and any future holder of a file can confirm it is byte-identical to the one attested here.

**They do not prove:** what is inside. A digest binds content to time. It does not disclose content. That is the whole trade: enough to establish integrity and priority, not enough to read the procedure out of it.

**They are not prior art.** A published digest is not an enabling disclosure. Anyone who wants the procedure reads the public criteria, then signs an engagement. Publishing the digest does not put the procedure in the public domain, and it is not offered under any open licence.

## Hash history

Digests are appended, never replaced. A digest once published stays published even after it is superseded — that is the only way it stays useful as a timestamp.

| Date | ID | Digest | Note |
|---|---|---|---|
| 2026-09-29 | `amtf-certification-procedure` | `81810c39…81e837` | v1.0, first publication |
| 2026-09-29 | `amtf-l3-latent-layer` | `bc016be4…b70d5a` | first publication |

## Never committed, not even as a digest

The adjudication ledger, the threshold file, the calibration records, and the adjudicated sample corpus. A digest of those would leak size and change frequency, which is information about the systems they describe. They exist; they are simply not attested here.
