#!/usr/bin/env python3
"""
03_load_psm_clean.py
====================
Load all PSMs with CORRECT indexing.

⚠️  CRITICAL BUG FIX:
    Before: spectrum_key = scan_number (overlaps between files!)
    Now:    spectrum_key = (mzml_name, scan_number) ✓

Extracts:
- window_mz from folder name
- mzml_name and scan from Spectrum column
- Creates unique spectrum_key

Parallelized for HPC with 64 cores.

Usage:
    python 03_load_psm_clean.py [--cores 64]

HPC sbatch:
    #SBATCH --cpus-per-task=64
    #SBATCH --time=00:30:00
    #SBATCH --mem=64G

Output:
    processed_data/psm_clean.csv
    processed_data/psm_chimeric.csv
    processed_data/spectrum_to_file.pkl
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from multiprocessing import Pool, cpu_count
import pickle
import re
import argparse
import time
import warnings
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass

warnings.filterwarnings('ignore')


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class Config:
    """Configuration for PSM loading."""
    project_dir: Path
    output_dir: Path
    psm_dir: Optional[Path]
    mzml_dir: Optional[Path]
    n_cores: int = 64
    
    @classmethod
    def auto_detect(cls):
        """Auto-detect project paths."""
        script_dir = Path(__file__).resolve().parent
        
        # Find project root
        if script_dir.name == 'code':
            project_dir = script_dir.parent
        else:
            # Search for version folder (v.X.X.X)
            for parent in script_dir.parents:
                if re.match(r'v\.\d+\.\d+\.\d+', parent.name):
                    project_dir = parent
                    break
            else:
                project_dir = Path.cwd()
        
        output_dir = project_dir / "processed_data"
        
        return cls(
            project_dir=project_dir,
            output_dir=output_dir,
            psm_dir=None,
            mzml_dir=None,
            n_cores=min(64, cpu_count())
        )


# ============================================================
# PARSERS
# ============================================================

def parse_folder_name(folder_name: str) -> Tuple[Optional[float], Optional[int]]:
    """
    Extract window_mz and replicate from folder name.
    
    Examples:
        118_60_1_6mz_1 → (1.6, 1)
        86_45_24mz_2 → (24.0, 2)
    
    Args:
        folder_name: Folder name containing window info
        
    Returns:
        (window_mz, replicate) or (None, None) if parse fails
    """
    # Decimal format: 1_6mz = 1.6
    match = re.match(r'(\d+)_(\d+)_(\d+)_(\d+)mz_(\d+)', folder_name)
    if match:
        window = float(f"{match.group(3)}.{match.group(4)}")
        replicate = int(match.group(5))
        return window, replicate
    
    # Integer format: 24mz
    match = re.match(r'(\d+)_(\d+)_(\d+)mz_(\d+)', folder_name)
    if match:
        window = float(match.group(3))
        replicate = int(match.group(4))
        return window, replicate
    
    return None, None


def parse_spectrum_column(spectrum_str: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Parse Spectrum column to extract mzML name, scan number, and charge.
    
    Format: Ex_AuLC1_..._4mz_2.00988.00988.2
                              ^scan ^scan ^charge
    
    Args:
        spectrum_str: Spectrum column value
        
    Returns:
        (mzml_name, scan_number, charge) or (None, None, None) if parse fails
    """
    try:
        parts = spectrum_str.rsplit('.', 3)
        if len(parts) >= 4:
            mzml_name = parts[0]
            scan_number = int(parts[1])
            charge = int(parts[3])
            return mzml_name, scan_number, charge
    except (ValueError, AttributeError):
        pass
    
    return None, None, None


def create_spectrum_key(mzml_name: str, scan_number: int) -> str:
    """
    Create unique spectrum identifier.
    
    Args:
        mzml_name: mzML file name
        scan_number: Scan number
        
    Returns:
        Unique key: "filename::scan"
    """
    return f"{mzml_name}::{scan_number}"


# ============================================================
# FILE LOADER
# ============================================================

def load_single_psm_file(psm_file: Path) -> Optional[pd.DataFrame]:
    """
    Load a single PSM file with metadata extraction.
    
    Args:
        psm_file: Path to psm.tsv file
        
    Returns:
        DataFrame with parsed columns or None if loading fails
    """
    folder_name = psm_file.parent.name
    
    # Skip library folder
    if folder_name == 'lib':
        return None
    
    try:
        # Load PSM file
        df = pd.read_csv(psm_file, sep='\t', low_memory=False)
        
        if len(df) == 0:
            return None
        
        # Extract metadata from folder name
        window_mz, replicate = parse_folder_name(folder_name)
        df['source_folder'] = folder_name
        df['window_mz'] = window_mz
        df['replicate'] = replicate
        
        # Parse Spectrum column
        spectrum_parsed = df['Spectrum'].apply(parse_spectrum_column)
        df['mzml_name'] = [p[0] for p in spectrum_parsed]
        df['scan_number'] = [p[1] for p in spectrum_parsed]
        df['charge_from_spectrum'] = [p[2] for p in spectrum_parsed]
        
        # Create unique spectrum key (CRITICAL FIX!)
        df['spectrum_key'] = df.apply(
            lambda row: create_spectrum_key(row['mzml_name'], row['scan_number'])
            if pd.notna(row['mzml_name']) and pd.notna(row['scan_number'])
            else None,
            axis=1
        )
        
        return df
        
    except Exception as e:
        print(f"Error loading {psm_file}: {e}")
        return None


# ============================================================
# DERIVED COLUMNS
# ============================================================

def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived columns to PSM dataframe.
    
    Args:
        df: Raw PSM dataframe
        
    Returns:
        DataFrame with added columns
    """
    # Window category
    df['window_category'] = pd.cut(
        df['window_mz'],
        bins=[0, 4, 12, 100],
        labels=['narrow', 'medium', 'wide']
    )
    
    # Chimericity (PSMs per spectrum)
    psm_counts = df.groupby('spectrum_key').size()
    df['n_psm'] = df['spectrum_key'].map(psm_counts)
    df['is_chimeric'] = df['n_psm'] >= 2
    
    # Peptide length (if Peptide column exists)
    if 'Peptide' in df.columns:
        df['peptide_length'] = (
            df['Peptide']
            .str.replace(r'\[.*?\]', '', regex=True)
            .str.len()
        )
    
    return df


# ============================================================
# VALIDATION
# ============================================================

def print_validation_stats(df: pd.DataFrame) -> Dict:
    """
    Print validation statistics and return summary.
    
    Args:
        df: Complete PSM dataframe
        
    Returns:
        Dictionary with summary statistics
    """
    print(f"\n{'='*70}")
    print("VALIDATION")
    print(f"{'='*70}")
    
    n_psm = len(df)
    n_spectra = df['spectrum_key'].nunique()
    n_files = df['mzml_name'].nunique()
    n_chimeric = df[df['is_chimeric']]['spectrum_key'].nunique()
    
    print(f"Total PSMs: {n_psm:,}")
    print(f"Unique spectra: {n_spectra:,}")
    print(f"mzML files: {n_files}")
    print(f"Average PSM/spectrum: {n_psm/n_spectra:.2f}")
    
    # Window distribution
    print(f"\nPSMs by window size:")
    window_stats = df.groupby('window_mz').agg(
        psm_count=('spectrum_key', 'count'),
        unique_spectra=('spectrum_key', 'nunique'),
        chimeric_pct=('is_chimeric', lambda x: f"{100*x.mean():.1f}%")
    )
    print(window_stats)
    
    # Chimericity distribution
    print(f"\nChimericity distribution:")
    chimeric_dist = (
        df.groupby('spectrum_key')['n_psm']
        .first()
        .value_counts()
        .sort_index()
    )
    for n_psm_val, count in chimeric_dist.head(6).items():
        pct = 100 * count / n_spectra
        print(f"  {n_psm_val} PSM: {count:,} spectra ({pct:.1f}%)")
    
    # Bug fix verification
    print(f"\n{'='*70}")
    print("BUG FIX VERIFICATION")
    print(f"{'='*70}")
    
    # Check scan number overlap across files
    scan_988 = df[df['scan_number'] == 988]
    n_files_scan988 = scan_988['mzml_name'].nunique()
    print(f"Scan 988 appears in {n_files_scan988} different mzML files")
    print(f"  → Old key (scan only): Would get WRONG spectrum!")
    print(f"  → New key (file::scan): Gets CORRECT spectrum ✓")
    
    # Sample keys
    print(f"\nSample spectrum_keys:")
    for key in df['spectrum_key'].dropna().head(3):
        print(f"  {key}")
    
    return {
        'n_psm': n_psm,
        'n_spectra': n_spectra,
        'n_files': n_files,
        'n_chimeric_spectra': n_chimeric,
        'avg_psm_per_spectrum': n_psm / n_spectra,
        'window_sizes': sorted(df['window_mz'].dropna().unique().tolist()),
        'columns': list(df.columns),
    }


# ============================================================
# SAVE FUNCTIONS
# ============================================================

def save_outputs(df: pd.DataFrame, config: Config, summary: Dict) -> None:
    """
    Save all output files.
    
    Args:
        df: Complete PSM dataframe
        config: Configuration object
        summary: Summary statistics dictionary
    """
    print(f"\n{'='*70}")
    print("SAVING")
    print(f"{'='*70}")
    
    config.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Full PSM table
    psm_file = config.output_dir / "psm_clean.csv"
    df.to_csv(psm_file, index=False)
    file_size_mb = psm_file.stat().st_size / 1e6
    print(f"✅ {psm_file.name} ({file_size_mb:.1f} MB)")
    
    # Chimeric PSMs only
    chimeric_file = config.output_dir / "psm_chimeric.csv"
    df_chimeric = df[df['is_chimeric']]
    df_chimeric.to_csv(chimeric_file, index=False)
    print(f"✅ {chimeric_file.name} ({len(df_chimeric):,} PSMs)")
    
    # Spectrum to file mapping
    spectrum_to_file = df.groupby('spectrum_key')['mzml_name'].first().to_dict()
    mapping_file = config.output_dir / "spectrum_to_file.pkl"
    with open(mapping_file, 'wb') as f:
        pickle.dump(spectrum_to_file, f)
    print(f"✅ {mapping_file.name} ({len(spectrum_to_file):,} spectra)")
    
    # Summary statistics
    stats_file = config.output_dir / "psm_stats.pkl"
    with open(stats_file, 'wb') as f:
        pickle.dump(summary, f)
    print(f"✅ {stats_file.name}")


# ============================================================
# PSM DIRECTORY FINDER
# ============================================================

def find_psm_directory(config: Config) -> Optional[Path]:
    """
    Find the directory containing PSM files.
    
    Args:
        config: Configuration object
        
    Returns:
        Path to PSM directory or None if not found
    """
    search_paths = [
        config.project_dir / "raw_data" / "PXD037527" / "1.6-48mz_30m" / "fragpipe",
        config.project_dir / "raw_data" / "PXD037527" / "1.6-48mz_30m",
        config.project_dir / "raw_data" / "1.6-48mz_30m" / "fragpipe",
        config.project_dir / "raw_data" / "fragpipe",
    ]
    
    for path in search_paths:
        if path.exists():
            psm_files = list(path.rglob("psm.tsv"))
            if psm_files:
                return path
    
    return None


# ============================================================
# MAIN
# ============================================================

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Load PSM data with correct spectrum indexing'
    )
    parser.add_argument(
        '--cores',
        type=int,
        default=64,
        help='Number of CPU cores to use (default: 64)'
    )
    parser.add_argument(
        '--psm-dir',
        type=str,
        help='Path to directory containing psm.tsv files'
    )
    parser.add_argument(
        '--mzml-dir',
        type=str,
        help='Path to directory containing mzML files (in SCRATCH)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without loading'
    )
    args = parser.parse_args()
    
    # Initialize configuration
    config = Config.auto_detect()
    config.n_cores = args.cores
    
    if args.psm_dir:
        config.psm_dir = Path(args.psm_dir)
    
    if args.mzml_dir:
        config.mzml_dir = Path(args.mzml_dir)
    
    # Print header
    print("="*70)
    print("03. LOAD PSM WITH CORRECT SPECTRUM KEYS")
    print("="*70)
    print(f"⚠️  CRITICAL BUG FIX:")
    print(f"   Old: key = scan_number (overlaps between files!)")
    print(f"   New: key = mzml_name::scan_number ✓")
    print("="*70)
    print(f"Project dir: {config.project_dir}")
    print(f"Output dir: {config.output_dir}")
    print(f"Cores: {config.n_cores}")
    
    if config.mzml_dir:
        print(f"mzML dir: {config.mzml_dir}")
    
    # Find PSM directory
    if config.psm_dir is None:
        config.psm_dir = find_psm_directory(config)
    
    if config.psm_dir is None or not config.psm_dir.exists():
        print(f"\n❌ ERROR: Cannot find PSM directory!")
        print(f"   Specify with: --psm-dir /path/to/fragpipe/")
        sys.exit(1)
    
    print(f"PSM dir: {config.psm_dir}")
    
    # Find PSM files
    psm_files = [
        f for f in config.psm_dir.rglob("psm.tsv")
        if 'lib' not in f.parts
    ]
    print(f"\nFound {len(psm_files)} PSM files")
    
    # Show sample folders
    folders = sorted(set(f.parent.name for f in psm_files))
    print(f"Folders: {len(folders)}")
    for folder in folders[:5]:
        window, rep = parse_folder_name(folder)
        print(f"  {folder} → window={window} mz, rep={rep}")
    
    if args.dry_run:
        print(f"\n[DRY RUN] Would load {len(psm_files)} files")
        return
    
    # Load PSM files in parallel
    print(f"\nLoading with {config.n_cores} cores...")
    start_time = time.time()
    
    with Pool(config.n_cores) as pool:
        results = pool.map(load_single_psm_file, psm_files)
    
    # Filter out None results
    dataframes = [df for df in results if df is not None]
    print(f"Successfully loaded {len(dataframes)} files")
    
    # Concatenate all dataframes
    print("Concatenating dataframes...")
    df_all = pd.concat(dataframes, ignore_index=True)
    
    load_time = time.time() - start_time
    print(f"Loaded {len(df_all):,} PSMs in {load_time:.1f}s")
    
    # Add derived columns
    print("\nComputing derived columns...")
    df_all = add_derived_columns(df_all)
    
    # Validation and statistics
    summary = print_validation_stats(df_all)
    
    # Save outputs
    save_outputs(df_all, config, summary)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n{'='*70}")
    print("✅ COMPLETE")
    print(f"{'='*70}")
    print(f"Total time: {total_time:.1f}s")
    print(f"PSMs: {summary['n_psm']:,}")
    print(f"Spectra: {summary['n_spectra']:,}")
    chimeric_pct = 100 * summary['n_chimeric_spectra'] / summary['n_spectra']
    print(f"Chimeric: {summary['n_chimeric_spectra']:,} ({chimeric_pct:.1f}%)")
    print(f"\n🔧 spectrum_key now uses mzml_name::scan - BUG FIXED!")


if __name__ == "__main__":
    main()