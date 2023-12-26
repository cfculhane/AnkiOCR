#!/usr/bin/env python3
import shutil
from pathlib import Path

from tqdm import tqdm

PROJECT_DIR = Path(__file__).parent.parent
ANKIOCR_SRC_DIR = Path(PROJECT_DIR, "src", "anki_ocr")
DEST_DIR = Path(PROJECT_DIR, "dist", "anki_ocr")
EXCLUDED_FILES = ["*.pickle", "*.pkl", "*.sqlite", ".pyc", "meta.json"]
EXCLUDED_DIRS = ["__pycache__", "logs"]

if __name__ == "__main__":
    if DEST_DIR.exists():
        print(f"Removing {DEST_DIR}")
        shutil.rmtree(DEST_DIR)
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    # Copy anki_ocr files to dist/anki_ocr
    for file in tqdm(ANKIOCR_SRC_DIR.rglob("*")):
        if any([file.match(excluded) for excluded in EXCLUDED_FILES]):
            continue
        if any([file.match(excluded) for excluded in EXCLUDED_DIRS]):
            continue
        if file.is_dir():
            continue
        rel_path = file.relative_to(ANKIOCR_SRC_DIR)
        dist_path = DEST_DIR.joinpath(rel_path)
        dist_path.parent.mkdir(parents=True, exist_ok=True)
        dist_path.write_bytes(file.read_bytes())

    # Create anki_ocr zip and rename to anki_ocr.ankiaddon
    shutil.make_archive(str(DEST_DIR.absolute()), "zip", DEST_DIR)
    shutil.move(f"{DEST_DIR}.zip", f"{DEST_DIR}.ankiaddon")
    print(f"Created {DEST_DIR}.ankiaddon")
