# ARR M3 — Final Statistical Audit

**Scope:** Reconcile M1–M3 populations, tests, and claim strength. No new SHAP/training.

---

## 1. Population ledger

| Population | n | Notes |
|------------|--:|-------|
| BASIL sentences (CSV) | 7,984 | Matched to launchnlp/BASIL @4fdbc4f |
| BASIL gold bias spans | 1,723 | 478 lex / 1,245 inf → **1,623** positive sentences |
| BD SHAP cache | 850 | 1 text-mismatch exclusion in M2C |
| DR SHAP cache | 837 | |
| DeBERTa SHAP cache | 400 | Magnitude/integrity caveats (M1) |
| M2C positive aligned | BD 475 / DR 467 / Deb 200 | All eligible, not subsample |
| M2C paired positive BD∩DR | 255 | Primary cross-model |
| M2B faithfulness medium | 200 paired BD∩DR | TP85 FP60 FN52 TN**3** |
| Human blind sample | 120 | 30×4 strata, seed 7 |
| Human HH complete present | 96 | 24 missing present on B |
| SHAP∩sample | BD34 DR42 Deb12 | Limits M3 SHAP–human n |

**Rule:** Never interpret unpaired model differences as architecture effects. Never treat TN faithfulness as established.

---

## 2. Claim-by-claim audit

### Faithfulness (M2B)

| Claim | Status | Evidence |
|-------|--------|----------|
| High-+SHAP / high-\|SHAP\| masks change P more than random/low-\|SHAP\| | **Supported** (BD, DR; TP/FP) | A_pos ≈ −0.33/−0.29; C−random \|ΔP\| ≈ +0.22 |
| Same for TN | **Unsupported** | n=3 |
| “Faithful explanations of reasoning” | **Overstated** if used | Prefer *attribution-guided sensitivity* |
| Applies to DeBERTa | **Not tested** in M2B | |

### Gold-span plausibility (M2C–M2D)

| Claim | Status | Evidence |
|-------|--------|----------|
| Lexical excess over length-matched random | **Supported** | BD +0.08, DR +0.13 |
| Informational excess after length control | **Weak / often unsupported** | Coverage ~70%; matched lex−inf ≈ 0 |
| Unqualified “lex ≫ inf” | **Overstated** | Coverage confound (M2D) |
| DR > BD on paired \|SHAP\| excess | **Supported** | n=255, CI excludes 0 |
| Magnitude = different mechanism | **Unsupported** | Confounded with confidence |

### Human validation (M3)

| Claim | Status | Evidence |
|-------|--------|----------|
| Humans agree strongly on type | **Unsupported** | κ_type=0.14 |
| SHAP > random vs human spans | **Supported (limited n)** | Excess +0.12–0.19 on cache∩sample |
| Full-sample SHAP–human | **Unsupported** | Only 34–42 overlaps |
| BASIL ≡ independent humans | **Unsupported** | Partial agreement; many dual disagreements |

### Taxonomy (M1)

| Claim | Status |
|-------|--------|
| 90–96% Emotional/Evaluative | **Retract** — catch-all artifact; Other ≈94% at p75 |
| Em/Ev taxonomy as main evidence frame | **Remove** — replace with BASIL lex/inf + Other |

---

## 3. Statistical practices — verified

- Sentence-level bootstrap CIs (seed 7) used for means and paired diffs.  
- Cluster bootstrap by triplet available in M2D for correlated articles.  
- Random baselines: length-and-count matched; 20 draws.  
- AP excludes all-gold / no-gold edge cases.  
- Multiple testing: not formally corrected across many strata — **do not** cherry-pick thin cells (both-type, Deb, TN).

## 4. Contradictions / overstatements to purge from manuscript

1. Same-mechanism / Emotional dominance.  
2. Informational SHAP recovery without coverage baseline.  
3. Calibration narrative based only on SHAP magnitude.  
4. Three-model symmetry (DeBERTa unevenly included).  
5. Equating faithfulness with human plausibility.

## 5. Small-strata red list (do not headline)

TN faithfulness (3); DeBERTa human–SHAP (≤10); both-humans-agree SHAP (≤10); HH needs-context (23); M2C both-type (23–26).
