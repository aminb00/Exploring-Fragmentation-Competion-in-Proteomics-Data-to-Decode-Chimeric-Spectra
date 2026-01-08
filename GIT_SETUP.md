# Setup Git Repository - PXD037527

## ✅ Configurazione Completata

### File creati:
- ✅ `.gitignore` - Ignora file grandi e mantiene solo codice
- ✅ `.gitattributes` - Configurazione per file binari (opzionale LFS)
- ✅ `.gitkeep` files - Mantiene cartelle vuote su GitHub
- ✅ `README.md` - Documentazione principale
- ✅ `create_gitkeep.sh` - Script per ricreare .gitkeep

## 📋 Cosa verrà tracciato su GitHub

### ✅ Tracciati (codice e documentazione):
```
v.2.0.0/
├── code/
│   ├── *.ipynb          (notebook)
│   ├── *.py             (script Python)
│   └── utils/
│       └── *.py
├── *.md                 (README, REPLICATION_PLAN, README_HPC)
├── .rsyncignore
└── .gitkeep files       (mantengono cartelle vuote)
```

### ❌ Ignorati (dati grandi):
- `*.raw` (file RAW Thermo)
- `*.mzML` (file mzML convertiti)
- `*.csv` grandi (psm_clean.csv, psm_chimeric.csv)
- `biosaur_features/` (output Biosaur)
- Tutti i file in `02ng_*` e `1.6-48mz_*`

## 🚀 Comandi Git

### Inizializza repository (se non esiste):
```bash
cd /path/to/PXD037527
git init
git add .gitignore .gitattributes README.md
git add v.2.0.0/code/
git add v.2.0.0/*.md
git add v.2.0.0/.rsyncignore
git add .gitkeep files
git commit -m "Initial commit: code and structure only"
```

### Verifica cosa verrà tracciato:
```bash
git status
git ls-files
```

### Push su GitHub:
```bash
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

## 📝 Note Importanti

1. **File RAW e mzML** non vanno su GitHub (troppo grandi)
2. **CSV processati** vengono generati su HPC
3. **Cartelle vuote** sono mantenute con `.gitkeep`
4. Su HPC, dopo il clone, scarica i file RAW manualmente

## 🔄 Workflow su HPC

1. **Clone repo:**
   ```bash
   git clone <repo-url>
   cd PXD037527
   ```

2. **Scarica file RAW** (vedi `v.2.0.0/README_HPC.md`)

3. **Esegui pipeline:**
   ```bash
   cd v.2.0.0/code/utils
   python convert_raw.py
   cd ../..
   python code/02_biosaur_extract.py
   ```

4. **I file generati** (mzML, CSV, features) rimangono locali su HPC

