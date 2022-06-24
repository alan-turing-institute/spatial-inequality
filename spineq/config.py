import os
from pathlib import Path

from platformdirs import user_data_dir

ENV_SPINEQ_HOME = "SPINEQ_HOME"  # environment variable to define alternative data dir
DEFAULT_SPINEQ_HOME = user_data_dir("spineq")  # platform-specific default data dir
SPINEQ_HOME = os.getenv(ENV_SPINEQ_HOME, DEFAULT_SPINEQ_HOME)

DATA_DIR = Path(SPINEQ_HOME, "data")
RAW_DIR = Path(DATA_DIR, "raw")
PROCESSED_DIR = Path(DATA_DIR, "processed")

os.makedirs(SPINEQ_HOME, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
