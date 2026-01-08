#!/bin/bash
# Script per creare .gitkeep nelle cartelle vuote

# Cartelle principali
touch 02ng_15m_12mz/.gitkeep
touch 02ng_30m_12mz/.gitkeep
touch 1.6-48mz_30m/.gitkeep

# v.2.0.0 - solo struttura
touch v.2.0.0/raw_data/raw/.gitkeep
touch v.2.0.0/raw_data/mzML/.gitkeep
touch v.2.0.0/processed_data/.gitkeep
touch v.2.0.0/analysis/ms1_matching/.gitkeep

echo "✅ .gitkeep files creati"
