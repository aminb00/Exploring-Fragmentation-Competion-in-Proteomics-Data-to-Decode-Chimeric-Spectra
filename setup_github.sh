#!/bin/bash
# ============================================
# Script per caricare v.3.0.0 su GitHub (versione vetrina)
# ============================================

# 1. Vai nella cartella del progetto
cd /data/antwerpen/211/vsc21150/Exploring-Fragmentation-Competion-in-Proteomics-Data-to-Decode-Chimeric-Spectra/v.3.0.0

# 2. Inizializza il repository Git (se non esiste già)
git init

# 3. Aggiungi il remote (sostituisci con il tuo URL)
# git remote add origin https://github.com/TUO_USERNAME/TUO_REPO.git

# 4. Verifica cosa verrà incluso (dovrebbe escludere cache, pkl, raw_data)
echo "=== File che verranno tracciati ==="
git status

# 5. Aggiungi tutti i file (rispettando .gitignore)
git add .

# 6. Verifica cosa è stato staged
echo "=== File staged per il commit ==="
git status

# 7. Crea il commit
git commit -m "Initial commit: v.3.0.0 - Analysis pipeline for chimeric spectra deconvolution"

# 8. Push su GitHub (main o master)
# git push -u origin main
# oppure
# git push -u origin master

echo "=== Done! ==="
echo "File inclusi:"
echo "- Scripts: 01_download_raw.py, 02_convert_raw_to_mzml.py, 03_load_psm_clean.py, biosaur_simple.py, extract_biosaur_parallel_clean.py"
echo "- Notebooks: 04_chimeric_analysis.ipynb, 05_Annotation&Prosit.ipynb, 06_LASSO.ipynb"
echo "- Plots: plots/*.png"
echo "- Documentation: README.md, README_preprocess.md"
echo ""
echo "File esclusi automaticamente da .gitignore:"
echo "- cache/ (file temporanei e pacchetti Python)"
echo "- raw_data/ (file mzML e RAW)"
echo "- *.pkl (file binari pickle)"
echo "- *.slurm, *.out, *.err (file job HPC)"
