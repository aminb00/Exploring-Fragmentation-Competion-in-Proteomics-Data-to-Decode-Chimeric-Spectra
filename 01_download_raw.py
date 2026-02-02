#!/usr/bin/env python3
"""
01_download_raw.py
==================
Download RAW files da PRIDE FTP per il dataset WWA_30m.

Parallelizzato con ThreadPoolExecutor (16 connessioni FTP simultanee).
Non serve usare tutti i 64 core perché il download è I/O bound.

Usage:
    python 01_download_raw.py [--dry-run] [--max-files N]

HPC sbatch:
    #SBATCH --time=06:00:00
    #SBATCH --mem=8G
"""

import ftplib
import os
import sys
import argparse
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
import pandas as pd

# ============================================================
# CONFIGURAZIONE HPC - AUTO-DETECT PATHS
# ============================================================

def find_project_dir():
    """Auto-rileva project directory dallo script."""
    script_dir = Path(__file__).resolve().parent
    
    # Se script è in code/, project è il parent
    if script_dir.name == 'code':
        return script_dir.parent
    
    # Altrimenti cerca v.X.X.X nella gerarchia
    for parent in script_dir.parents:
        if re.match(r'v\.\d+\.\d+\.\d+', parent.name):
            return parent
    
    # Fallback: directory corrente
    return Path.cwd()

PROJECT_DIR = find_project_dir()
RAW_DIR = PROJECT_DIR / "raw_data" / "raw"

# Cerca la cartella fragpipe in varie posizioni possibili
PSM_SEARCH_PATHS = [
    PROJECT_DIR / "raw_data" / "PXD037527" / "1.6-48mz_30m" / "fragpipe",
    PROJECT_DIR / "raw_data" / "PXD037527" / "1.6-48mz_30m",
    PROJECT_DIR / "raw_data" / "1.6-48mz_30m" / "fragpipe",
    PROJECT_DIR / "raw_data" / "fragpipe",
]

def find_psm_dir():
    """Trova la directory con i PSM files."""
    for path in PSM_SEARCH_PATHS:
        if path.exists():
            psm_files = list(path.rglob("psm.tsv"))
            if psm_files:
                print(f"Found PSM dir: {path}")
                return path
    return None

PSM_DIR = find_psm_dir()

FTP_HOST = "ftp.pride.ebi.ac.uk"
FTP_PATH = "/pride/data/archive/2023/07/PXD037527/"

# 16 download paralleli (limite pratico per FTP)
N_DOWNLOADS = 1

print_lock = Lock()


def safe_print(msg):
    with print_lock:
        print(msg, flush=True)


def get_required_raw_files():
    """Trova i RAW file necessari leggendo i PSM."""
    print("Scanning PSM files...")
    
    raw_files = set()
    psm_files = [f for f in PSM_DIR.rglob("psm.tsv") if 'lib' not in f.parts]
    
    for pf in psm_files:
        try:
            df = pd.read_csv(pf, sep='\t', usecols=['Spectrum'], nrows=5)
            mzml_name = df['Spectrum'].iloc[0].rsplit('.', 3)[0]
            raw_files.add(mzml_name + ".raw")
        except:
            pass
    
    print(f"Found {len(raw_files)} unique RAW files needed")
    return sorted(raw_files)


def download_file(args):
    """Scarica un singolo file."""
    filename, local_path = args
    
    if local_path.exists() and local_path.stat().st_size > 1_000_000:
        return (filename, "SKIP", 0)
    
    try:
        ftp = ftplib.FTP(FTP_HOST, timeout=300)
        ftp.login()
        ftp.cwd(FTP_PATH)
        ftp.voidcmd('TYPE I')
        
        start = time.time()
        with open(local_path, 'wb') as f:
            ftp.retrbinary(f'RETR {filename}', f.write, blocksize=1024*1024)
        
        ftp.quit()
        elapsed = time.time() - start
        size_mb = local_path.stat().st_size / 1e6
        
        return (filename, "OK", size_mb)
        
    except Exception as e:
        if local_path.exists():
            local_path.unlink()
        return (filename, f"FAIL: {e}", 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--max-files', type=int, default=None)
    parser.add_argument('--psm-dir', type=str, default=None, 
                        help='Path to fragpipe directory with psm.tsv files')
    args = parser.parse_args()
    
    print("="*70)
    print("01. DOWNLOAD RAW FILES FROM PRIDE")
    print("="*70)
    print(f"Project dir: {PROJECT_DIR}")
    print(f"Output dir: {RAW_DIR}")
    
    # Determine PSM directory
    global PSM_DIR
    if args.psm_dir:
        PSM_DIR = Path(args.psm_dir)
    
    if PSM_DIR is None or not PSM_DIR.exists():
        print(f"\n❌ ERROR: Cannot find PSM directory!")
        print(f"   Searched in:")
        for p in PSM_SEARCH_PATHS:
            exists = "✓" if p.exists() else "✗"
            print(f"     [{exists}] {p}")
        print(f"\n   Specify manually with: --psm-dir /path/to/fragpipe/")
        print(f"   Example: python 01_download_raw.py --psm-dir /data/.../1.6-48mz_30m/fragpipe")
        sys.exit(1)
    
    print(f"PSM dir: {PSM_DIR}")
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get required files
    required = get_required_raw_files()
    
    # Check FTP
    print(f"\nConnecting to {FTP_HOST}...")
    ftp = ftplib.FTP(FTP_HOST, timeout=60)
    ftp.login()
    ftp.cwd(FTP_PATH)
    available = []
    ftp.retrlines('NLST', available.append)
    available = set(f for f in available if f.endswith('.raw'))
    ftp.quit()
    
    # Filter
    to_download = [f for f in required if f in available]
    missing = [f for f in required if f not in available]
    
    print(f"Required: {len(required)}, Available: {len(to_download)}, Missing: {len(missing)}")
    
    if args.max_files:
        to_download = to_download[:args.max_files]
    
    if args.dry_run:
        print(f"\n[DRY RUN] Would download {len(to_download)} files")
        return
    
    # Download
    print(f"\nDownloading {len(to_download)} files with {N_DOWNLOADS} threads...")
    
    download_args = [(f, RAW_DIR / f) for f in to_download]
    stats = {"OK": 0, "SKIP": 0, "FAIL": 0}
    total_mb = 0
    
    start = time.time()
    with ThreadPoolExecutor(max_workers=N_DOWNLOADS) as ex:
        futures = {ex.submit(download_file, a): a[0] for a in download_args}
        for i, fut in enumerate(as_completed(futures), 1):
            fn, status, mb = fut.result()
            if "OK" in status:
                stats["OK"] += 1
                total_mb += mb
                safe_print(f"[{i}/{len(to_download)}] ✅ {fn} ({mb:.0f} MB)")
            elif "SKIP" in status:
                stats["SKIP"] += 1
                safe_print(f"[{i}/{len(to_download)}] ⏭️  {fn}")
            else:
                stats["FAIL"] += 1
                safe_print(f"[{i}/{len(to_download)}] ❌ {fn}")
    
    elapsed = time.time() - start
    print(f"\n{'='*70}")
    print(f"Downloaded: {stats['OK']} ({total_mb/1e3:.1f} GB)")
    print(f"Skipped: {stats['SKIP']}, Failed: {stats['FAIL']}")
    print(f"Time: {elapsed/60:.1f} min, Speed: {total_mb/elapsed:.1f} MB/s")


if __name__ == "__main__":
    main()
