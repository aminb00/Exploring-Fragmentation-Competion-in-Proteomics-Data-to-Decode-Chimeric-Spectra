# PXD037527 Replication Plan

## Goal
Replicate PXD012671 v.2.0.0 pipeline for PXD037527 (larger dataset with more chimericity)

## Source: PXD012671/v.2.0.0
## Target: PXD037527/v.2.0.0

---

## Status

### ✅ Already done in PXD037527:
- `01_chimeric_inspection.ipynb` - Initial PSM loading and chimericity check
- `02_biosaur_extract.py` - MS1 feature extraction
- `chimeric_analysis_cleaned.ipynb` - Basic chimeric analysis

### 📋 To replicate (in order):

1. **03_match_ms1.ipynb** - Match PSMs to Biosaur MS1 features
   - Input: psm.tsv + biosaur features
   - Output: psm_with_ms1.csv
   - Changes needed: Update paths for PXD037527 structure

2. **08_prositComparison.ipynb** - Generate Prosit predictions & compare
   - Input: psm_with_ms1.csv + mzML
   - Output: ordered_sample_X.csv (with prosit_mz, prosit_intensity)
   - Changes needed: Handle 87 runs instead of 1, sample selection strategy

3. **lasso_peakmatching_clean.ipynb** - LASSO deconvolution
   - Input: ordered_sample_X.csv + mzML
   - Output: LASSO coefficients, validation metrics
   - Changes needed: Minimal (just paths)

---

## Key differences PXD012671 vs PXD037527:

| Aspect | PXD012671 | PXD037527 |
|--------|-----------|-----------|
| PSMs | ~200K | ~2.2M (11x more) |
| Runs | 1 run | 87 runs |
| Chimericity | Moderate | Higher (expected) |
| mzML files | 1 file | Multiple (need to find) |

---

## Strategy

**Phase 1** (Current): One notebook at a time, starting with prerequisites
**Phase 2**: Once data flow works, replicate LASSO notebooks
**Phase 3**: Validation and comparison PXD012671 vs PXD037527

---

## Notes

- PXD037527 structure:
  - `02ng_30m_12mz/fragpipe_mbr/` - 87 psm.tsv files
  - `1.6-48mz_30m/fragpipe/` - additional data
  - Need to check for mzML files location

- Memory considerations: 2.2M PSMs may require sampling or batching

