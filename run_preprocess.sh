#!/bin/bash
#SBATCH --job-name=pxd037527_preprocess
#SBATCH --output=preprocess_%j.log
#SBATCH --error=preprocess_%j.err
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=64
#SBATCH --mem=128G
#SBATCH --partition=skylake

# ============================================================
# PXD037527 Preprocessing Pipeline
# ============================================================
# 
# Step 1: Download RAW files from PRIDE FTP (~60 files, ~100 GB)
# Step 2: Convert RAW → mzML (ThermoRawFileParser, 64 cores)
# Step 3: Load PSM with correct indexing (fix the bug!)
#
# Usage:
#   sbatch run_preprocess.sh
#
# Or run steps individually:
#   python 01_download_raw.py
#   python 02_convert_raw_to_mzml.py --cores 64
#   python 03_load_psm_clean.py --cores 64
# ============================================================

echo "============================================================"
echo "PXD037527 PREPROCESSING PIPELINE"
echo "============================================================"
echo "Start time: $(date)"
echo "Node: $SLURM_NODELIST"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: $SLURM_MEM_PER_NODE MB"
echo "============================================================"

# Environment setup
module load Python/3.11.3-GCCcore-12.3.0  # Adjust for your HPC
module load mono  # For ThermoRawFileParser

# Activate conda environment (adjust path)
source /data/antwerpen/211/vsc21150/miniconda3/etc/profile.d/conda.sh
conda activate proteomics_py311

# Project directory
PROJECT_DIR="/data/antwerpen/211/vsc21150/phase1/PXD037527/v.2.0.0"
CODE_DIR="$PROJECT_DIR/code"

cd "$CODE_DIR"

# ============================================================
# STEP 1: Download RAW files
# ============================================================
echo ""
echo "============================================================"
echo "STEP 1/3: Download RAW files from PRIDE"
echo "============================================================"

python 01_download_raw.py
if [ $? -ne 0 ]; then
    echo "❌ Step 1 failed!"
    exit 1
fi

echo "✅ Step 1 complete"

# ============================================================
# STEP 2: Convert RAW → mzML
# ============================================================
echo ""
echo "============================================================"
echo "STEP 2/3: Convert RAW → mzML"
echo "============================================================"

# Set ThermoRawFileParser path (adjust if needed)
export THERMORAWFILEPARSER="$PROJECT_DIR/tools/ThermoRawFileParser/ThermoRawFileParser.exe"

python 02_convert_raw_to_mzml.py --cores $SLURM_CPUS_PER_TASK
if [ $? -ne 0 ]; then
    echo "❌ Step 2 failed!"
    exit 1
fi

echo "✅ Step 2 complete"

# ============================================================
# STEP 3: Load PSM with correct keys
# ============================================================
echo ""
echo "============================================================"
echo "STEP 3/3: Load PSM with correct spectrum keys"
echo "============================================================"

python 03_load_psm_clean.py --cores $SLURM_CPUS_PER_TASK
if [ $? -ne 0 ]; then
    echo "❌ Step 3 failed!"
    exit 1
fi

echo "✅ Step 3 complete"

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "============================================================"
echo "ALL STEPS COMPLETE!"
echo "============================================================"
echo "End time: $(date)"
echo ""
echo "Output files:"
echo "  RAW files: $PROJECT_DIR/raw_data/raw/"
echo "  mzML files: $PROJECT_DIR/raw_data/mzML_proper/"
echo "  PSM clean: $PROJECT_DIR/processed_data/psm_clean.csv"
echo "  PSM chimeric: $PROJECT_DIR/processed_data/psm_chimeric.csv"
echo ""
echo "Next step: Run 04_load_spectra.py to load mzML spectra"
echo "============================================================"
