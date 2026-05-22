# Strategy for Expanded SHAP Analysis

## Current Status
- **Dataset size:** 1000 samples (test split)
- **SHAP samples analyzed:** 30 (limited by `max_shap_examples=30`)
- **Actual confusion matrix:** TP=448, FP=37, TN=404, FN=111
- **Stratified sample available:** 
  - Up to 100 TP (from 448 available)
  - Up to 37 FP (ALL available - this is the full set!)
  - Up to 100 TN (from 404 available)
  - **Total available:** Up to 237 samples, but limited by `max_shap_examples`

## Why Expand the Analysis?

### Current Limitations:
1. **Small sample size (30)** may not capture all patterns
2. **Word-level statistics** may be skewed by rare words appearing only once
3. **Function word patterns** need more samples to confirm
4. **False positive analysis** (5 samples) is too small for robust conclusions
5. **Top words** may change with more data

### Benefits of Expansion:
1. **More robust statistics** - Word frequencies and SHAP patterns stabilize
2. **Better coverage** - More diverse examples of TP/FP/TN patterns
3. **Stronger paper findings** - Larger sample size = more credible results
4. **Rare word detection** - Words that appear multiple times are more reliable indicators
5. **Statistical significance** - Can perform proper statistical tests

## Recommended Approach

### Option 1: Moderate Expansion (RECOMMENDED)
**Set `max_shap_examples = 150`**
- **Coverage:** 
  - ~33% of available TP (50-100 samples)
  - **ALL available FPs (37 samples)** - Complete FP coverage!
  - ~25-50% of available TN (50-100 samples)
- **Time estimate:** 2-4 hours (depending on hardware)
- **Benefits:**
  - 5x more data than current (30 → 150)
  - **Complete FP analysis** - All 37 false positives analyzed
  - Better statistical power for TP and TN
  - Still manageable computation time
  - Good balance for paper

### Option 2: Full Stratified Sample
**Set `max_shap_examples = 237`** (or higher to include all available)
- **Coverage:** 
  - 100 TP (from 448 available)
  - **37 FP (ALL available)** - Complete coverage
  - 100 TN (from 404 available)
- **Time estimate:** 4-8 hours (depending on hardware)
- **Benefits:**
  - Complete coverage of all available FPs
  - Maximum statistical power for TP and TN
  - Most comprehensive analysis
- **Drawbacks:**
  - Time-consuming (but less than originally estimated)
  - May be overkill for workshop paper

### Option 3: Hybrid Approach (BEST FOR PAPER)
**Two-stage analysis:**

1. **Stage 1: Broad statistical analysis (all 1000 samples)**
   - Run inference on all samples (already done)
   - Analyze prediction patterns, confidence distributions
   - Identify interesting subsets for detailed SHAP analysis
   - **Time:** ~5 minutes (inference already done)

2. **Stage 2: Targeted SHAP analysis (150-200 samples)**
   - Focus SHAP on most interesting cases
   - Stratified by prediction type AND confidence levels
   - Include edge cases (high confidence FPs, low confidence TPs)
   - **Time:** 3-5 hours

## Implementation Steps

### Step 1: Update Configuration
```python
max_shap_examples = 150  # Increased from 30
```

### Step 2: Re-run SHAP Analysis
- This will take longer but provide more comprehensive results
- Monitor progress - SHAP shows progress bars

### Step 3: Re-run Research Analysis
- The `research_analysis.ipynb` will automatically use the new data
- Word-level statistics will be more robust
- Top words will be more reliable (higher counts)

### Step 4: Compare Results
- Check if findings from 30 samples hold with 150 samples
- Identify new patterns that emerge with more data
- Update KEY_FINDINGS.md with expanded analysis

## Expected Improvements

### Word-Level Statistics:
- **Current:** Many words appear only once (count=1)
- **With 150 samples:** More words appear multiple times, more reliable statistics
- **Top words:** May change as rare words get filtered out

### False Positive Analysis:
- **Current:** Only 5 FP samples (out of 37 total available)
- **With 150 samples:** **ALL 37 FP samples** (complete coverage!)
- **Benefit:** Complete FP analysis - can identify ALL false positive patterns
- **Critical:** Since there are only 37 FPs total, expanding to 150 ensures we analyze all of them

### Statistical Power:
- **Current:** Limited by small sample size
- **With 150 samples:** Can perform proper statistical tests
- **Benefit:** More credible findings for paper

## Computational Considerations

### Time Estimates (CPU):
- **30 samples:** ~45-60 minutes
- **150 samples:** ~2-4 hours
- **300 samples:** ~6-10 hours

### Time Estimates (GPU):
- **30 samples:** ~15-20 minutes
- **150 samples:** ~1-2 hours
- **300 samples:** ~3-5 hours

### Memory:
- SHAP analysis is memory-efficient
- Should work fine with 150-300 samples

## Recommendation

**For ACL Workshop Paper: Use Option 1 (150 samples) - STRONGLY RECOMMENDED**

**Rationale:**
1. **5x improvement** over current analysis (30 → 150)
2. **Complete FP coverage** - All 37 false positives analyzed (vs. only 5 currently)
3. **Manageable time** (2-4 hours on CPU, 1-2 hours on GPU)
4. **Good statistical power** for paper findings
5. **More reliable word statistics** (higher counts, words appear multiple times)
6. **Critical for FP analysis** - Since only 37 FPs exist, 150 samples ensures we get all of them

**After running 150 samples:**
- If patterns are clear and stable → sufficient for paper
- If new patterns emerge → consider expanding to 300
- If computational time is acceptable → can always expand later

## Next Steps

1. **Update `max_shap_examples = 150`** in configuration cell
2. **Re-run SHAP analysis cells** (will take 2-4 hours)
3. **Re-run research_analysis.ipynb** to get updated statistics
4. **Compare findings** between 30 and 150 sample analyses
5. **Update KEY_FINDINGS.md** with expanded results

## Alternative: Incremental Analysis

If time is limited, you can:
1. Run SHAP on 50 samples first (quick check)
2. Verify patterns are consistent
3. Then expand to 150 if needed

This allows you to validate that the expansion is worth the time before committing to a full 150-sample run.

