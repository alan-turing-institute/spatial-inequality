import os
from pathlib import Path

DATA_DIR = Path(os.path.dirname(__file__), "../data")
RAW_DIR = Path(DATA_DIR, "raw")
PROCESSED_DIR = Path(DATA_DIR, "processed")
