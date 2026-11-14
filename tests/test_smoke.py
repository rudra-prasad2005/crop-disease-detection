"""Smoke tests for the plant-disease pipeline.

These tests intentionally avoid training (which is slow and needs a GPU).
They verify:
  * module imports
  * configuration values are sane
  * utility helpers behave correctly
  * `predict` raises a useful error when the trained model is missing
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


def test_config_paths_resolve():
    from src import config

    # PROJECT_ROOT should be the parent of src/.
    assert config.PROJECT_ROOT.is_dir()
    assert (config.PROJECT_ROOT / "src").is_dir()


def test_config_hyperparams_in_range():
    from src import config

    assert config.SEED == 42
    assert 0 < config.TRAIN_SPLIT < 1
    assert config.BATCH_SIZE > 0
    assert config.IMG_SIZE == (224, 224)
    assert config.PHASE1_EPOCHS > 0
    assert config.PHASE2_EPOCHS > 0
    assert config.PHASE2_LR < config.PHASE1_LR, (
        "Phase 2 LR should be smaller than phase 1 (fine-tune at low LR)."
    )


def test_set_seed_makes_random_deterministic():
    from src.utils import set_seed

    set_seed(123)
    a = [np.random.rand() for _ in range(5)]
    set_seed(123)
    b = [np.random.rand() for _ in range(5)]
    assert a == b, "set_seed should produce identical random sequences."


def test_is_empty_dir(tmp_path: Path):
    from src.utils import is_empty_dir

    # pytest pre-creates tmp_path as an empty dir — that's already covered by
    # the `True` assertion below. For the "missing" case we use a path that
    # definitely doesn't exist.
    missing = tmp_path / "does_not_exist_xyz"
    assert is_empty_dir(missing) is False

    assert is_empty_dir(tmp_path) is True
    (tmp_path / "x.txt").write_text("hi")
    assert is_empty_dir(tmp_path) is False


def test_predict_raises_when_model_missing(tmp_path: Path, monkeypatch):
    """If outputs/best_model.h5 doesn't exist, predict should fail loudly."""
    pytest.importorskip("tensorflow", reason="predict.py imports tensorflow at module load")
    from src import config, predict

    # Point CONFIG at a tmp dir so we don't trip over real outputs/.
    fake_outputs = tmp_path / "outputs"
    fake_outputs.mkdir()
    monkeypatch.setattr(config, "MODEL_PATH", fake_outputs / "best_model.h5")
    monkeypatch.setattr(config, "CLASS_NAMES_JSON", fake_outputs / "class_names.json")

    with pytest.raises(FileNotFoundError, match="Trained model not found"):
        predict.predict(tmp_path / "leaf.jpg")


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("tensorflow"),
    reason="TensorFlow not installed — skipping model build test.",
)
def test_build_model_output_shape():
    import tensorflow as tf

    from src.model import build_model, unfreeze_top_layers

    model = build_model(num_classes=38, base_name="EfficientNetB0")
    assert model.output_shape == (None, 38)
    assert not any(
        isinstance(layer, tf.keras.layers.Rescaling) for layer in model.layers
    )
    trainable_count = unfreeze_top_layers(model, fine_tune_at=-50)
    assert model.layers[1].trainable
    assert trainable_count > 0
