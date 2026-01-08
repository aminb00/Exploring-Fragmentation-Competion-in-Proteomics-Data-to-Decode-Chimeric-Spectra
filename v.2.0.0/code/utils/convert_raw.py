from pathlib import Path
import os
import subprocess

# Percorsi di base (relativi a v.2.0.0 di PXD037527)
BASE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BASE_DIR.parents[2]

RAW_DIR = BASE_DIR / "raw_data/raw"
MZML_DIR = BASE_DIR / "raw_data/mzML"
BIOSAUR_DIR = BASE_DIR / "processed_data/biosaur_features"

# Parser Thermo (override con env THERMO_PARSER se serve)
# Su HPC: export THERMO_PARSER=/path/to/ThermoRawFileParser
PARSER_DEFAULT = REPO_ROOT / "ThermoRawFileParser-v.2.0.0-dev-osx/ThermoRawFileParser"
PARSER_STR = os.environ.get("THERMO_PARSER", str(PARSER_DEFAULT))
PARSER = Path(PARSER_STR) if PARSER_STR else None

if PARSER and not PARSER.exists():
    raise SystemExit(f"❌ ThermoRawFileParser non trovato: {PARSER}\n"
                     f"   Imposta THERMO_PARSER=/path/to/ThermoRawFileParser")

RAW_DIR.mkdir(parents=True, exist_ok=True)
MZML_DIR.mkdir(parents=True, exist_ok=True)
BIOSAUR_DIR.mkdir(parents=True, exist_ok=True)

# Lista file raw (tutti quelli in raw_data/raw)
raw_files = sorted(RAW_DIR.glob("*.raw"))
if not raw_files:
    raise SystemExit(f"❌ Nessun file .raw trovato in {RAW_DIR}")

print("Parser:", PARSER)
print("RAW dir:", RAW_DIR)
print("mzML dir:", MZML_DIR)
print("Biosaur dir:", BIOSAUR_DIR)

# converti raw -> mzML
for raw_file in raw_files:
    print(f"Converting {raw_file.name}")
    cmd = [str(PARSER), "-i", str(raw_file), "-o", str(MZML_DIR), "-f", "1"]
    subprocess.run(cmd, check=True)

print("Conversione completata!")

# esegui biosaur su ogni mzML
mzml_files = sorted(MZML_DIR.glob("*.mzML"))
if not mzml_files:
    raise SystemExit(f"❌ Nessun file .mzML trovato in {MZML_DIR}")

# Usa biosaur2 se disponibile, altrimenti biosaur
BIOSAUR_CMD = os.environ.get("BIOSAUR_CMD", "biosaur2")
for mzml_file in mzml_files:
    print(f"Biosaur su {mzml_file.name}")
    cmd = [BIOSAUR_CMD, "-i", str(mzml_file), "-o", str(BIOSAUR_DIR), "-p", "4"]
    subprocess.run(cmd, check=True)

print(f"Fatto! Features salvate in: {BIOSAUR_DIR}")
