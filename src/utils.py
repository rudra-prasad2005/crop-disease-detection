"""Small utilities shared across the pipeline."""
from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np


def set_seed(seed: int) -> None:
    """Seed Python, NumPy, and (if available) TensorFlow for reproducibility.

    Note: full determinism on GPU is not guaranteed because of non-deterministic
    CUDA kernels, but seeding removes the easy sources of variance so that
    re-runs produce comparable results.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ["TF_DETERMINISTIC_OPS"] = "1"

    try:
        import tensorflow as tf  # imported lazily so non-TF scripts don't pay the import cost

        tf.random.set_seed(seed)
        # Best-effort op-level determinism. Available since TF 2.9.
        try:
            tf.config.experimental.enable_op_determinism()
        except (AttributeError, RuntimeError):
            # Already enabled, or running in a context that doesn't allow it.
            pass
    except ImportError:
        # TensorFlow not installed — fine for utility-only scripts (predict, evaluate).
        pass


def is_empty_dir(path: Path) -> bool:
    """True if the directory exists and has no entries."""
    return path.is_dir() and not any(path.iterdir())