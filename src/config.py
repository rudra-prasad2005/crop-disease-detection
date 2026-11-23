"""Central configuration: paths, hyperparameters, dataset constants.

Edit values here to retrain with different settings. All other modules
import from this file, so there are no magic numbers scattered around.
"""
from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
def get_project_root() -> Path:
    """Return the project root regardless of the current working directory.

    The package can be invoked as `python -m src.train` (cwd = project root)
    or as `python src/train.py` (cwd also = project root in our setup).
    `__file__` resolves to `<root>/src/config.py`, so `parent.parent` is the root.
    """
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT: Path = get_project_root()

# Dataset archive (already in the project dir) and where it gets extracted.
ARCHIVE_PATH: Path = PROJECT_ROOT / "archive.zip"
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
SPLIT_DIR: Path = DATA_DIR / "splits"
TRAIN_DIR: Path = SPLIT_DIR / "train"
VALID_DIR: Path = SPLIT_DIR / "valid"

# PlantVillage layout: `plantvillage dataset/color/<Class>/<image>.JPG`.
# Only the `color` variant is used — grayscale/segmented are discarded.
SOURCE_VARIANT: str = "color"
RAW_COLOR_DIR: Path = RAW_DIR / "plantvillage dataset" / SOURCE_VARIANT

# Model artifacts are tracked alongside the source model. Training reports and
# visualizations are generated under outputs/.
MODELS_DIR: Path = PROJECT_ROOT / "models"
MODEL_PATH: Path = MODELS_DIR / "plant_disease.keras"
CLASS_NAMES_JSON: Path = MODELS_DIR / "class_names.json"

# Generated artifacts (plots, reports, grad-cam) land here.
OUTPUT_DIR: Path = PROJECT_ROOT / "outputs"
CURVES_PATH: Path = OUTPUT_DIR / "training_curves.png"
CONFUSION_PATH: Path = OUTPUT_DIR / "confusion_matrix.png"
REPORT_PATH: Path = OUTPUT_DIR / "classification_report.txt"
GRADCAM_DIR: Path = OUTPUT_DIR / "gradcam"

# Sidecar reference data (kept from the original directory listing).
PESTICIDE_CSV: Path = PROJECT_ROOT / "pesticide.csv"


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED: int = 42


# ---------------------------------------------------------------------------
# Image / training hyperparameters
# ---------------------------------------------------------------------------
IMG_SIZE: tuple[int, int] = (224, 224)
BATCH_SIZE: int = 32
TRAIN_SPLIT: float = 0.80  # 80/20 train/valid split per class


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
# The imported trained checkpoint uses MobileNetV2.
BASE_MODEL_NAME: str = "MobileNetV2"
DROPOUT: float = 0.3


# ---------------------------------------------------------------------------
# Two-phase training schedule
# ---------------------------------------------------------------------------
PHASE1_EPOCHS: int = 10
PHASE1_LR: float = 1e-3

# Negative value = "unfreeze the last |FINE_TUNE_AT| layers".
# MobileNetV2 has ~155 layers; unfreezing the top 50 is a common sweet spot.
FINE_TUNE_AT: int = -50

PHASE2_EPOCHS: int = 10
PHASE2_LR: float = 1e-5  # 100x smaller — critical for stable fine-tuning


# ---------------------------------------------------------------------------
# Evaluation / explainability
# ---------------------------------------------------------------------------
NUM_GRADCAM_SAMPLES: int = 5


# ---------------------------------------------------------------------------
# Eager sanity side-effects: make sure the output dir exists on import so that
# downstream modules can write into it without each one re-doing mkdir.
# ---------------------------------------------------------------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRADCAM_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)