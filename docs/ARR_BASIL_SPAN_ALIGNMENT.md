# ARR BASIL Span Alignment (M1)

**Code:** `scripts/arr_m1/run_basil_span_recovery.py`  
**Outputs:** `outputs/arr_m1/basil_spans/`  
**Clones (outside repo git):**  
- `/Users/rick/DoksOhneidrive/BASIL_launchnlp` ← https://github.com/launchnlp/BASIL  
- `/Users/rick/DoksOhneidrive/BASIL_emnlp19` ← https://github.com/marshallwhiteorg/emnlp19-media-bias  

---

## 1. Version selection

| Release | Commit | Exact sentence+label match to `basil_sentences.csv` |
|---------|--------|------------------------------------------------------:|
| **launchnlp/BASIL (2nd release)** | `4fdbc4f68d5ddae648990063cb6dd11424d96222` | **7984 / 7984** |
| marshallwhiteorg/emnlp19-media-bias (1st) | `4a8865347588648ae14e63344c9686d2b0a4930e` | lower (see `alignment_report.json`) |

**Selected:** `launchnlp/BASIL` — matches `preprocess_basil.py` layout (`articles/`, `annotations/`) and is a perfect key/text/label match to the project CSV.

**Do not merge releases.** Annotation fixes between v1 and v2 are documented upstream in `annotation_changes.txt`.

---

## 2. Licensing

- Neither clone exposes a root `LICENSE*` file.  
- Data are research artifacts from Fan et al., EMNLP 2019 (“In Plain Sight…”).  
- **Do not redistribute** article full text or the full annotation dump via this GitHub project without confirming terms with the dataset authors.  
- M1 exports under `outputs/arr_m1/basil_spans/gold_spans.csv` contain identifiers + span offsets + span surface strings for analysis; treat as derived research working files, not a public data release.

---

## 3. Span schema (recovered)

From `phrase-level-annotations` entries:

| Field | Role |
|-------|------|
| `id` | `p{sentence_idx}` (flattened sentence index; title dropped) |
| `bias` | `lex` or `inf` |
| `start`, `end` | **Character offsets into the sentence text** |
| `txt` | Span surface form |
| `quote`, `polarity`, `aim`, `target`, … | Ancillary |

**Verification:** `text[start:end] == txt` for **1723 / 1723** spans (100%).

| Bias type | n spans |
|-----------|--------:|
| lexical (`lex`) | 478 |
| informational (`inf`) | 1245 |
| **Total** | **1723** |

---

## 4. Alignment counts vs project CSV

| Metric | Count |
|--------|------:|
| CSV sentences | 7984 |
| Repo sentences | 7984 |
| Common keys `(triplet_uuid, outlet_idx, sentence_idx)` | 7984 |
| Exact text + label match | **7984** |
| Text mismatch | **0** |
| Label mismatch | **0** |
| Only-in-repo / only-in-CSV | **0** |
| Recoverable alnum-only mismatches | 0 |
| Unrecoverable mismatches | **0** |

**Conclusion:** Existing `basil_sentences.csv` and SHAP caches keyed by those IDs are aligned to launchnlp BASIL v2. Safe for human–SHAP span overlap experiments (E3).

---

## 5. Identifiers preserved

- `triplet_uuid`, `article_uuid`, `outlet_idx`, `sentence_idx`, `paragraph_idx`, `year`  
- Span-level: `start`, `end`, `bias`, `quote`, `polarity`, `span_txt`  
- Export: `outputs/arr_m1/basil_spans/gold_spans.csv`  
- Cache coverage: `shap_cache_span_coverage.csv` (bias-detector SHAP keys ↔ span counts)

---

## 6. Usability for human-alignment analysis

**Yes.** Prerequisites met:

1. Gold lex/inf spans with verified offsets.  
2. Perfect join to sentence CSV and existing SHAP sentence keys.  
3. Stratification possible by `bias` type and quote status.

Remaining E3 work (not M1): annotation UI/protocol, IAA, SHAP-mass-in-span metrics — see experiment plan.
