#!/usr/bin/env python3
"""
extract_biosaur_simple.py
==========================
Simple, clean Biosaur2 feature extraction script.

Usage:
    python3 extract_biosaur_simple.py
    
    Or with custom biosaur2 path:
    BIOSAUR_CMD=/custom/path/biosaur2 python3 extract_biosaur_simple.py
"""

import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
MZML_DIR = Path("/scratch/antwerpen/211/vsc21150/PXD037527/mzML")
OUT_DIR = Path("/scratch/antwerpen/211/vsc21150/PXD037527/biosaur_features")

# Biosaur2 command (can override with environment variable)
BIOSAUR_CMD = os.environ.get(
    "BIOSAUR_CMD",
    "/data/antwerpen/211/vsc21150/Exploring-Fragmentation-Competion-in-Proteomics-Data-to-Decode-Chimeric-Spectra/.venv/bin/biosaur2"
)

# Processing parameters
NUM_PROCESSES = 4  # Cores per file


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():
    """Main execution."""
    
    print("=" * 70)
    print("BIOSAUR2 FEATURE EXTRACTION")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Input:  {MZML_DIR}")
    print(f"Output: {OUT_DIR}")
    print(f"Biosaur2: {BIOSAUR_CMD}")
    print(f"Processes per file: {NUM_PROCESSES}")
    print("=" * 70)
    print()
    
    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check biosaur2 exists
    if not Path(BIOSAUR_CMD).exists():
        print(f"❌ ERROR: Biosaur2 not found at: {BIOSAUR_CMD}")
        print("\nTo fix:")
        print("  1. Install: pip install biosaur2")
        print("  2. Or set: export BIOSAUR_CMD=/path/to/biosaur2")
        sys.exit(1)
    
    # Get list of mzML files
    mzml_files = sorted(MZML_DIR.glob("*.mzML"))
    if not mzml_files:
        print(f"❌ ERROR: No mzML files found in {MZML_DIR}")
        sys.exit(1)
    
    print(f"Found {len(mzml_files)} mzML files to process\n")
    
    # Process each file
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, mzml_file in enumerate(mzml_files, 1):
        output_file = OUT_DIR / f"{mzml_file.stem}.features.tsv"
        
        # Skip if already processed
        if output_file.exists() and output_file.stat().st_size > 1000:
            print(f"[{i}/{len(mzml_files)}] ⏭️  SKIP: {mzml_file.name} (already done)")
            skip_count += 1
            continue
        
        print(f"[{i}/{len(mzml_files)}] 🔄 Processing: {mzml_file.name}")
        
        try:
            # Run biosaur2
            subprocess.run(
                [
                    BIOSAUR_CMD,
                    "-i", str(mzml_file),
                    "-o", str(OUT_DIR),
                    "-p", str(NUM_PROCESSES)
                ],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Verify output
            if output_file.exists() and output_file.stat().st_size > 100:
                print(f"[{i}/{len(mzml_files)}] ✅ SUCCESS: {mzml_file.name}")
                success_count += 1
            else:
                print(f"[{i}/{len(mzml_files)}] ❌ FAILED: {mzml_file.name} (empty output)")
                fail_count += 1
                
        except subprocess.CalledProcessError as e:
            print(f"[{i}/{len(mzml_files)}] ❌ FAILED: {mzml_file.name}")
            if e.stderr:
                print(f"    Error: {e.stderr[:200]}")
            fail_count += 1
            
        except Exception as e:
            print(f"[{i}/{len(mzml_files)}] ❌ FAILED: {mzml_file.name}")
            print(f"    Exception: {str(e)[:200]}")
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Processed successfully: {success_count}")
    print(f"⏭️  Skipped (already done): {skip_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📁 Output directory: {OUT_DIR}")
    
    # Count total features
    try:
        feature_files = list(OUT_DIR.glob("*.features.tsv"))
        total_features = 0
        for f in feature_files:
            try:
                with open(f) as fh:
                    total_features += sum(1 for _ in fh) - 1  # Subtract header
            except:
                pass
        print(f"📊 Total features extracted: {total_features:,}")
    except:
        pass
    
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Exit with error code if failures
    if fail_count > 0:
        sys.exit(1)
    else:
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