#!/usr/bin/env python3
"""
Parallel conversion of Thermo RAW files to mzML using ThermoRawFileParser in Singularity
"""

import os
import subprocess
import glob
from pathlib import Path
from multiprocessing import Pool, cpu_count
import argparse
from datetime import datetime

def convert_raw_file(args):
    """Convert a single RAW file to mzML"""
    raw_file, output_dir, container_path, no_peak_picking = args
    
    raw_file_abs = os.path.abspath(raw_file)
    output_dir_abs = os.path.abspath(output_dir)
    basename = os.path.basename(raw_file)
    
    # Build command
    cmd = [
        'singularity', 'exec',
        container_path,
        'ThermoRawFileParser.sh',
        f'-i={raw_file_abs}',
        f'-o={output_dir_abs}',
        '-f=2',  # indexed mzML
    ]
    
    if no_peak_picking:
        cmd.append('-p')
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting: {basename}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Completed: {basename}")
        return True, basename, None
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Failed: {basename}")
        print(f"  Error: {error_msg}")
        return False, basename, error_msg

def main():
    parser = argparse.ArgumentParser(
        description='Parallel conversion of Thermo RAW files to mzML'
    )
    parser.add_argument(
        '-i', '--input-dir',
        required=True,
        help='Directory containing RAW files'
    )
    parser.add_argument(
        '-o', '--output-dir',
        required=True,
        help='Output directory for mzML files'
    )
    parser.add_argument(
        '-c', '--container',
        required=True,
        help='Path to Singularity container (.sif file)'
    )
    parser.add_argument(
        '-j', '--jobs',
        type=int,
        default=4,
        help='Number of parallel jobs (default: 4)'
    )
    parser.add_argument(
        '-p', '--no-peak-picking',
        action='store_true',
        help='Disable peak picking'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find all RAW files
    raw_files = glob.glob(os.path.join(args.input_dir, '*.raw'))
    
    if not raw_files:
        print(f"No RAW files found in {args.input_dir}")
        return
    
    print(f"Found {len(raw_files)} RAW files")
    print(f"Using {args.jobs} parallel jobs")
    print(f"Container: {args.container}")
    print(f"Output directory: {args.output_dir}")
    print("-" * 80)
    
    # Prepare arguments for parallel processing
    task_args = [
        (raw_file, args.output_dir, args.container, args.no_peak_picking)
        for raw_file in raw_files
    ]
    
    # Process in parallel
    start_time = datetime.now()
    
    with Pool(processes=args.jobs) as pool:
        results = pool.map(convert_raw_file, task_args)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Summary
    print("-" * 80)
    successful = sum(1 for success, _, _ in results if success)
    failed = len(results) - successful
    
    print(f"\nConversion Summary:")
    print(f"  Total files: {len(raw_files)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Total time: {duration/60:.1f} minutes")
    print(f"  Average time per file: {duration/len(raw_files):.1f} seconds")
    
    if failed > 0:
        print("\nFailed files:")
        for success, basename, error in results:
            if not success:
                print(f"  - {basename}")
                if error:
                    print(f"    Error: {error[:100]}")

if __name__ == '__main__':
    main()