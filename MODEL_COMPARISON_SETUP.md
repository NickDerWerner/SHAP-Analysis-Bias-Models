# Model Comparison Setup

This document explains how to run SHAP analysis on multiple bias detection models.

## Supported Models

1. **Original Model**: `himel7/bias-detector`
2. **DA-RoBERTa Model**: `mediabiasgroup/da-roberta-babe-ft`

## Running Analysis

### Using analysis.py (Recommended)

Run the original model:
```bash
python analysis.py --model himel7/bias-detector --model_suffix ""
```

Run the DA-RoBERTa model:
```bash
python analysis.py --model mediabiasgroup/da-roberta-babe-ft --model_suffix daroberta
```

### Using analysis.ipynb

1. **For Original Model:**
   - Set `model_name = "himel7/bias-detector"`
   - Set `model_suffix = ""`
   - Run all cells

2. **For DA-RoBERTa Model:**
   - Set `model_name = "mediabiasgroup/da-roberta-babe-ft"`
   - Set `model_suffix = "daroberta"`
   - **IMPORTANT**: Update the following file paths in cells 16 and 17:
     - Cell 16: Change `"shap_samples.jsonl"` to `f"shap_samples{output_suffix}.jsonl"`
     - Cell 17: Change `"global_word_importance.csv"` to `f"global_word_importance{output_suffix}.csv"`
   - Cell 25: Already updated with suffix support

## Output Files

Outputs will be created with suffixes:

### Original Model (suffix = ""):
- `outputs/shap_samples.jsonl`
- `outputs/global_word_importance.csv`
- `outputs/examples/shap_0.html`, etc.

### DA-RoBERTa Model (suffix = "daroberta"):
- `outputs/shap_samples_daroberta.jsonl`
- `outputs/global_word_importance_daroberta.csv`
- `outputs/examples/shap_daroberta_0.html`, etc.

## Analyzing Results

### Using research_analysis.ipynb

1. Open `research_analysis.ipynb`
2. In Cell 3, set `model_suffix = ""` for original model or `model_suffix = "_daroberta"` for DA-RoBERTa model
3. Run all cells to analyze that model's results

## Comparing Models

To compare both models:

1. Run analysis for both models (using different suffixes)
2. Run `research_analysis.ipynb` twice:
   - Once with `model_suffix = ""` (original model)
   - Once with `model_suffix = "_daroberta"` (DA-RoBERTa model)
3. Compare the outputs side-by-side

## Key Differences to Expect

The DA-RoBERTa model (`mediabiasgroup/da-roberta-babe-ft`) may show:
- Different top bias indicators
- Different false positive patterns
- Potentially better or different handling of tokenization
- Different SHAP value distributions

Use the suffix system to keep results separate and compare them systematically.

