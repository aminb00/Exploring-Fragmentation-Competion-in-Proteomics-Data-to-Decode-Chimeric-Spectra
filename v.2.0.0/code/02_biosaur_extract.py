import os
import subprocess
from pathlib import Path

# Percorso base relativo a PXD037527/v.2.0.0
BASE_DIR = Path(__file__).resolve().parents[1]
MZML_DIR = BASE_DIR / "raw_data/mzML"
OUT_DIR = BASE_DIR / "processed_data/biosaur_features"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Comando Biosaur2 (sovrascrivibile con env BIOSAUR_CMD)
BIOSAUR_CMD = os.environ.get("BIOSAUR_CMD", "/opt/anaconda3/envs/proteomics/bin/biosaur2")

# Lista automatica di file mzML; se vuoi limitarli, filtra qui.
mzml_files = sorted(MZML_DIR.glob("*.mzML"))

if not mzml_files:
    raise SystemExit(f"❌ Nessun file mzML trovato in {MZML_DIR}")

for mzml_file in mzml_files:
    print(f"Processing {mzml_file}")
    try:
        subprocess.run(
            [BIOSAUR_CMD, "-i", str(mzml_file), "-o", str(OUT_DIR), "-p", "4"],
            check=True
        )
        print(f"✅ Done: {mzml_file.name}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error processing {mzml_file}: {e}")

print(f"All features saved in: {OUT_DIR}")
