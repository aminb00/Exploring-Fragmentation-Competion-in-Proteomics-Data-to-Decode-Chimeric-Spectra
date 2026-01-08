# PXD037527 - Proteomics Analysis Pipeline

Repository per l'analisi del dataset PXD037527.

## 📁 Struttura Repository

```
PXD037527/
├── 02ng_15m_12mz/          # Dati FragPipe (non tracciati su GitHub)
├── 02ng_30m_12mz/          # Dati FragPipe (non tracciati su GitHub)
├── 1.6-48mz_30m/           # Dati FragPipe (non tracciati su GitHub)
└── v.2.0.0/                # Pipeline di analisi
    ├── code/                # ✅ Tracciato su GitHub
    │   ├── *.ipynb
    │   ├── *.py
    │   └── utils/
    ├── raw_data/            # ❌ Non tracciato (file RAW/mzML)
    ├── processed_data/      # ❌ Non tracciato (CSV grandi)
    └── analysis/            # ❌ Non tracciato (output)
```

## 🎯 Cosa è tracciato su GitHub

- ✅ **Codice**: Tutti i notebook (`.ipynb`) e script Python (`.py`) in `v.2.0.0/code/`
- ✅ **Documentazione**: README, REPLICATION_PLAN.md, README_HPC.md
- ✅ **Config**: `.rsyncignore`, `.gitignore`
- ❌ **Dati**: File RAW, mzML, CSV grandi (da scaricare/processare su HPC)

## 🚀 Setup su HPC

1. **Clone repository:**
   ```bash
   git clone <repo-url>
   cd PXD037527
   ```

2. **Scarica dati RAW** (vedi `v.2.0.0/README_HPC.md`)

3. **Converti RAW → mzML:**
   ```bash
   cd v.2.0.0/code/utils
   python convert_raw.py
   ```

4. **Estrai features Biosaur:**
   ```bash
   cd ../..
   python code/02_biosaur_extract.py
   ```

5. **Esegui analisi:**
   ```bash
   # Apri notebook in VS Code Server
   code v.2.0.0/code/03_match_ms1.ipynb
   ```

## 📝 Note

- I file RAW e mzML sono troppo grandi per GitHub (>100MB)
- I CSV processati vengono generati localmente
- Le cartelle dati sono mantenute vuote su GitHub (con `.gitkeep`)

## 🔗 Link Utili

- Dataset PRIDE: [PXD037527](https://www.ebi.ac.uk/pride/archive/projects/PXD037527)
- Documentazione HPC: `v.2.0.0/README_HPC.md`
- Piano replicazione: `v.2.0.0/REPLICATION_PLAN.md`

