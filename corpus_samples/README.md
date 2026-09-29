# corpus_samples/

`public_samples.jsonl` — three samples from the admission gate's calibration corpus, chosen to demonstrate the *published* layers only:

| Label | Layer exercised | Purpose |
|---|---|---|
| `poison` | L1 instruction override (EN) | direct override must be rejected |
| `poison` | L1 instruction override (CN) | the same attack in Chinese, because real enterprise memory is not English-only |
| `benign` | none | contains the word "transfer"; must be admitted, since a gate that kills ordinary finance notes is unusable |

Format: one JSON object per line, `{"text": ..., "label": "poison"|"benign", "layer": ...}`.

**What is deliberately absent.** The remaining 11 samples of the calibration corpus, the labelling rules behind them, and everything involving latent poison (content that looks harmless until a conditional trigger fires) are not here. Any sample matching an L3 pattern was excluded from this directory programmatically at build time, not by reviewer discretion.

Run it:

```bash
python tools/poison_admission_gate.py corpus corpus_samples/public_samples.jsonl
```

Expected on this public build: the two override samples flagged, the benign one admitted, and `l3_enabled: false` reported in the output — the gate states its own scope rather than implying it covers the latent case.
