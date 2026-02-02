#!/usr/bin/env python3
"""
extract_biosaur_parallel.py
============================
Production-ready parallel Biosaur2 feature extraction.

Usage:
    python3 extract_biosaur_parallel.py

Requirements:
    - biosaur2 installed
    - mzML files in /scratch/.../PXD037527/mzML/
    
Output:
    - Features in /scratch/.../PXD037527/biosaur_features/
"""

import subprocess
import sys
from pathlib import Path
from multiprocessing import Pool, cpu_count
from datetime import datetime
import time


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration for parallel Biosaur2 extraction."""
    
    # Paths
    MZML_DIR = Path("/scratch/antwerpen/211/vsc21150/PXD037527/mzML")
    OUT_DIR = Path("/scratch/antwerpen/211/vsc21150/PXD037527/biosaur_features")
    
    # Biosaur2 executable
    BIOSAUR_CMD = "/data/antwerpen/211/vsc21150/Exploring-Fragmentation-Competion-in-Proteomics-Data-to-Decode-Chimeric-Spectra/.venv/bin/biosaur2"
    
    # Parallelization
    CORES_PER_FILE = 8
    N_PARALLEL = 4  # Process 4 files simultaneously
    
    # Biosaur2 parameters
    MIN_INTENSITY = 1000  # Skip low signals for speed


# ============================================================================
# WORKER FUNCTION
# ============================================================================

def process_single_file(mzml_file: Path) -> tuple[str, bool, str]:
    """
    Process a single mzML file with Biosaur2.
    
    Args:
        mzml_file: Path to input mzML file
        
    Returns:
        (filename, success, message)
    """
    output_file = Config.OUT_DIR / f"{mzml_file.stem}.features.tsv"
    
    # Skip if already exists and not empty
    if output_file.exists() and output_file.stat().st_size > 1000:
        return (mzml_file.name, True, "SKIP")
    
    try:
        # Run Biosaur2 with correct parameters
        result = subprocess.run(
            [
                Config.BIOSAUR_CMD,
                str(mzml_file),
                "-o", str(output_file),
                "-nprocs", str(Config.CORES_PER_FILE),
                "-mini", str(Config.MIN_INTENSITY)
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout per file
        )
        
        # Verify output exists
        if output_file.exists() and output_file.stat().st_size > 100:
            return (mzml_file.name, True, "OK")
        else:
            return (mzml_file.name, False, "Output file empty or missing")
            
    except subprocess.TimeoutExpired:
        return (mzml_file.name, False, "TIMEOUT (>2h)")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr[:200] if e.stderr else "Unknown error"
        return (mzml_file.name, False, f"ERROR: {error_msg}")
    except Exception as e:
        return (mzml_file.name, False, f"EXCEPTION: {str(e)[:200]}")


# ============================================================================
# VALIDATION
# ============================================================================

def validate_setup() -> bool:
    """Validate that all requirements are met."""
    
    print("Validating setup...")
    errors = []
    
    # Check mzML directory
    if not Config.MZML_DIR.exists():
        errors.append(f"mzML directory not found: {Config.MZML_DIR}")
    else:
        mzml_files = list(Config.MZML_DIR.glob("*.mzML"))
        if not mzml_files:
            errors.append(f"No mzML files in: {Config.MZML_DIR}")
        else:
            print(f"  ✓ Found {len(mzml_files)} mzML files")
    
    # Check biosaur2
    if not Path(Config.BIOSAUR_CMD).exists():
        errors.append(f"Biosaur2 not found: {Config.BIOSAUR_CMD}")
    else:
        print(f"  ✓ Biosaur2 found")
    
    # Create output directory
    try:
        Config.OUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Output directory ready: {Config.OUT_DIR}")
    except Exception as e:
        errors.append(f"Cannot create output directory: {e}")
    
    # Print errors if any
    if errors:
        print("\n❌ VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("  ✓ All checks passed\n")
    return True


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution function."""
    
    print("=" * 70)
    print("BIOSAUR2 PARALLEL FEATURE EXTRACTION")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"mzML directory: {Config.MZML_DIR}")
    print(f"Output directory: {Config.OUT_DIR}")
    print(f"Parallelization: {Config.N_PARALLEL} files × {Config.CORES_PER_FILE} cores")
    print(f"Total cores: {Config.N_PARALLEL * Config.CORES_PER_FILE}")
    print("=" * 70)
    print()
    
    # Validate setup
    if not validate_setup():
        sys.exit(1)
    
    # Get list of mzML files
    mzml_files = sorted(Config.MZML_DIR.glob("*.mzML"))
    print(f"Processing {len(mzml_files)} files...")
    print()
    
    # Process in parallel
    start_time = time.time()
    
    with Pool(processes=Config.N_PARALLEL) as pool:
        results = pool.map(process_single_file, mzml_files)
    
    elapsed_time = time.time() - start_time
    
    # Print results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    for filename, success, message in results:
        status = "✅" if success else "❌"
        if message == "SKIP":
            status = "⏭️ "
        print(f"{status} {filename:<60} {message}")
    
    # Summary
    n_ok = sum(1 for _, success, msg in results if success and msg == "OK")
    n_skip = sum(1 for _, success, msg in results if msg == "SKIP")
    n_fail = sum(1 for _, success, _ in results if not success)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Completed successfully: {n_ok}")
    print(f"Skipped (already done): {n_skip}")
    print(f"Failed: {n_fail}")
    print(f"Total time: {elapsed_time/60:.1f} minutes")
    print(f"Average per file: {elapsed_time/len(mzml_files):.1f} seconds")
    print(f"Output directory: {Config.OUT_DIR}")
    print("=" * 70)
    
    # Count features
    try:
        feature_files = list(Config.OUT_DIR.glob("*.features.tsv"))
        total_features = 0
        for f in feature_files:
            try:
                total_features += sum(1 for _ in open(f)) - 1
            except:
                pass
        print(f"\nTotal MS1 features extracted: {total_features:,}")
    except:
        pass
    
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with error code if failures
    if n_fail > 0:
        print(f"\n⚠️  {n_fail} files failed. Check errors above.")
        sys.exit(1)
    else:
        print("\n✅ All files processed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)