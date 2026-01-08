# PXD037527 v.2.0.0 - HPC Setup

## 📋 Checklist Pre-Transfer

### ✅ Pronto
- [x] Struttura directory completa
- [x] Script Python (`02_biosaur_extract.py`, `convert_raw.py`)
- [x] Notebook (`03_match_ms1.ipynb`)
- [x] Dati processati (`psm_clean.csv`, `psm_chimeric.csv`)
- [x] 23/24 file RAW (manca `02ng_6.raw`)

### ⚠️ Da fare PRIMA del transfer
1. **Scarica il file mancante:**
   - `Ex_AuLC1_15m_2D19_3_20um30cm_SPE50_15118120_OTOT_11860_12mz_02ng_6.raw`

2. **Verifica path negli script:**
   - `convert_raw.py` ha path hardcoded per ThermoRawFileParser (macOS)
   - Su HPC, usa variabile d'ambiente `THERMO_PARSER` o modifica il path

3. **Verifica comandi su HPC:**
   - `biosaur2` o `biosaur` (versione installata)
   - `ThermoRawFileParser` (path corretto)

## 📁 Struttura Directory

```
v.2.0.0/
├── code/
│   ├── 01_chimeric_inspection.ipynb
│   ├── 02_biosaur_extract.py
│   ├── 03_match_ms1.ipynb
│   └── utils/
│       └── convert_raw.py
├── processed_data/
│   ├── psm_clean.csv
│   └── psm_chimeric.csv
├── raw_data/
│   ├── raw/          (23 file RAW - manca 02ng_6)
│   └── mzML/         (vuoto - verrà popolato su HPC)
└── analysis/
    └── ms1_matching/ (vuoto - output di 03_match_ms1.ipynb)
```

## 🚀 Workflow su HPC

### Step 1: Converti RAW → mzML
```bash
cd code/utils
# Modifica THERMO_PARSER se necessario
export THERMO_PARSER=/path/to/ThermoRawFileParser
python convert_raw.py
```

### Step 2: Estrai features Biosaur
```bash
cd ../..
# Modifica BIOSAUR_CMD se necessario
export BIOSAUR_CMD=biosaur2  # o il path completo
python code/02_biosaur_extract.py
```

### Step 3: Match MS1 (notebook)
```bash
# Apri 03_match_ms1.ipynb
# Modifica RUN_NAME nella cella 1 se necessario
```

## 📊 Dimensione Totale
- `raw_data/`: ~7.7 GB (file RAW)
- `processed_data/`: ~568 MB (CSV)
- `code/`: ~156 KB (script/notebook)
- **Totale**: ~8.3 GB

## ⚙️ Variabili d'Ambiente (HPC)
```bash
export THERMO_PARSER=/path/to/ThermoRawFileParser
export BIOSAUR_CMD=biosaur2  # o path completo
```

## 🔍 File Mancanti
- `raw_data/raw/Ex_AuLC1_15m_2D19_3_20um30cm_SPE50_15118120_OTOT_11860_12mz_02ng_6.raw`

