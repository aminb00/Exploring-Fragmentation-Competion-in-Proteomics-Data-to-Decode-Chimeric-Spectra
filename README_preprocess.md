# PXD037527 Preprocessing Pipeline

## Overview

Questi 3 script preparano i dati per l'analisi della competizione di frammentazione:

| Script | Funzione | Tempo Stimato | I/O |
|--------|----------|---------------|-----|
| `01_download_raw.py` | Scarica RAW da PRIDE | 2-4 ore | Network |
| `02_convert_raw_to_mzml.py` | RAW → mzML | 30-60 min | Disk |
| `03_load_psm_clean.py` | Carica PSM con chiavi corrette | 2-5 min | Memory |

## ⚠️ BUG CRITICO FIXATO

Lo script `03_load_psm_clean.py` fixa il bug di indicizzazione:

```python
# ❌ PRIMA (bug): scan_number sovrappone tra file
spectra_dict[988]  # → spettro casuale da uno dei 6+ file con scan 988!

# ✅ ORA (fix): chiave univoca (file::scan)
spectra_dict["Ex_AuLC1_..._4mz_1::988"]  # → spettro corretto!
```

## Struttura Directory

```
phase1/PXD037527/v.2.0.0/
├── code/
│   ├── 01_download_raw.py
│   ├── 02_convert_raw_to_mzml.py
│   ├── 03_load_psm_clean.py
│   └── run_preprocess.sh
├── raw_data/
│   ├── raw/                     # ← RAW files (Step 1)
│   ├── mzML_proper/             # ← mzML files (Step 2)
│   └── PXD037527/
│       └── 1.6-48mz_30m/
│           └── fragpipe/        # ← PSM files (già presenti)
└── processed_data/
    ├── psm_clean.csv            # ← Output Step 3
    ├── psm_chimeric.csv         # ← Solo spettri chimerici
    └── spectrum_to_file.pkl     # ← Mapping spectrum_key → mzml
```

## Usage

### Option 1: Tutto insieme (SLURM)

```bash
# Copia gli script nella cartella code/
cp 01_download_raw.py 02_convert_raw_to_mzml.py 03_load_psm_clean.py run_preprocess.sh \
   /data/antwerpen/211/vsc21150/phase1/PXD037527/v.2.0.0/code/

# Submit job
cd /data/antwerpen/211/vsc21150/phase1/PXD037527/v.2.0.0/code/
sbatch run_preprocess.sh
```

### Option 2: Step by step

```bash
# Attiva environment
conda activate proteomics_py311

# Step 1: Download (solo se non hai già i RAW)
python 01_download_raw.py

# Step 2: Converti (se hai già i RAW)
python 02_convert_raw_to_mzml.py --cores 64

# Step 3: Carica PSM (SEMPRE necessario per fix bug)
python 03_load_psm_clean.py --cores 64
```

### Option 3: Solo Step 3 (se hai già mzML)

Se hai già scaricato e convertito i file, puoi eseguire solo:

```bash
python 03_load_psm_clean.py --cores 64
```

## Output Files

### psm_clean.csv

Colonne principali:

| Colonna | Descrizione |
|---------|-------------|
| `Spectrum` | Stringa originale |
| `spectrum_key` | **NUOVO!** Chiave univoca `mzml_name::scan` |
| `mzml_name` | Nome file mzML |
| `scan_number` | Numero scan |
| `window_mz` | Isolation window (1.6, 2, 4, ..., 48 mz) |
| `window_category` | narrow/medium/wide |
| `n_psm` | PSM per questo spettro |
| `is_chimeric` | True se n_psm ≥ 2 |
| `pep_len` | Lunghezza peptide |
| `Hyperscore`, `Peptide`, `Charge`, ... | Colonne FragPipe originali |

### spectrum_to_file.pkl

```python
import pickle
with open('spectrum_to_file.pkl', 'rb') as f:
    mapping = pickle.load(f)

# Uso:
mzml_name = mapping['Ex_AuLC1_..._4mz_1::988']
```

## Verifica Fix Bug

Dopo lo Step 3, controlla l'output:

```
BUG FIX VERIFICATION
======================================================================
Scan 988 appears in 6 different mzML files
  → Old key (scan only): Would get WRONG spectrum!
  → New key (file::scan): Gets CORRECT spectrum ✓
```

## Requirements

```bash
# Python packages
pip install pandas numpy tqdm

# Per Step 2 (conversione RAW)
# ThermoRawFileParser: https://github.com/compomics/ThermoRawFileParser
# mono: module load mono (su HPC)
```

## Prossimi Passi

Dopo questi 3 step, eseguire:

1. **04_load_spectra.py** - Carica spettri mzML con chiavi corrette
2. **05_annotate_by.py** - Annota b/y ions (ora con match rate ~19%!)
3. **06_prosit_predict.py** - Predizioni Prosit
4. **07_ranking.py** - Analisi ranking
5. **08_lasso.py** - Deconvoluzione LASSO

## Troubleshooting

### "ThermoRawFileParser not found"

```bash
# Imposta il path
export THERMORAWFILEPARSER=/path/to/ThermoRawFileParser.exe

# O scarica
wget https://github.com/compomics/ThermoRawFileParser/releases/download/v1.4.2/ThermoRawFileParser-linux.zip
unzip ThermoRawFileParser-linux.zip
```

### "mono not found"

```bash
module load mono  # Su HPC
# o
sudo apt install mono-complete  # Su Ubuntu
```

### Download FTP lento

Aumenta il timeout nel script o scarica durante la notte.

---

Author: [Your Name]  
Project: Fragmentation Competition in Chimeric Spectra  
Dataset: PXD037527 (Wide Window Acquisition)
