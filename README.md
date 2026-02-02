# Exploring Fragmentation Competition in Proteomics Data to Decode Chimeric Spectra

## 📋 Overview
This repository contains the analysis pipeline for investigating fragmentation competition in proteomics mass spectrometry data, with a focus on decoding chimeric spectra using LASSO-based deconvolution methods.

## 📁 Repository Structure

```
v.3.0.0/
├── 01_download_raw.py          # Download raw MS data from PRIDE
├── 02_convert_raw_to_mzml.py   # Convert RAW to mzML format
├── 03_load_psm_clean.py        # Load and clean PSM data
├── 04_chimeric_analysis.ipynb  # Chimeric spectra analysis
├── 05_Annotation&Prosit.ipynb  # Peak annotation & Prosit predictions
├── 06_LASSO.ipynb              # LASSO deconvolution analysis
├── biosaur_simple.py           # Biosaur feature extraction utilities
├── extract_biosaur_parallel_clean.py  # Parallel biosaur extraction
├── README_preprocess.md        # Preprocessing documentation
├── plots/                      # Generated figures
│   ├── 01_chimeric_analysis/   # Chimericity visualizations
│   └── 05_ranking_analysis/    # Ranking & concordance plots
├── processed_data/             # Output CSV files and summary statistics
└── analysis/                   # Additional analysis outputs
```

## 🔬 Analysis Pipeline

### 1. Data Acquisition & Preprocessing
- **01_download_raw.py**: Downloads raw MS files from PRIDE repository
- **02_convert_raw_to_mzml.py**: Converts vendor RAW files to open mzML format
- **03_load_psm_clean.py**: Loads PSM identifications and applies quality filters

### 2. Chimeric Spectra Analysis
- **04_chimeric_analysis.ipynb**: Identifies and characterizes chimeric spectra based on isolation window analysis

### 3. Peak Annotation & Prosit Integration
- **05_Annotation&Prosit.ipynb**: Annotates fragment ions and integrates Prosit intensity predictions

### 4. LASSO Deconvolution
- **06_LASSO.ipynb**: Applies LASSO regression to deconvolve chimeric spectra and estimate peptide contributions

## 📊 Key Outputs

### Plots
- Chimericity distribution by isolation window
- PSM distribution by category
- Concordance heatmaps
- Correlation analyses
- LASSO performance metrics
- Regularization paths
- Prediction quality assessments

### Data Files
- `psm_clean.csv` / `psm_chimeric.csv`: Filtered PSM datasets
- Concordance and correlation statistics
- Tie analysis results

## 🛠️ Requirements

```python
# Core dependencies
pandas
numpy
scipy
scikit-learn

# MS-specific
pyteomics
spectrum_utils

# Visualization
matplotlib
seaborn

# Prosit integration
requests
```

## 📖 Citation

If you use this code, please cite:
[Your publication details here]

## 📄 License

[Your license here]

## 👤 Contact

[Your contact information]
