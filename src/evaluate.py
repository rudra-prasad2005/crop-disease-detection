"""Evaluation: accuracy, classification report, confusion matrix, top confused pairs.

Run with:
    python -m src.evaluate
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix)

from . import config
from .data import build_datasets, prepare
from .utils import set_seed


def _top_confused_pairs(cm: np.ndarray, class_names, k: int = 10):
    """Return the (k) most-confused (off-diagonal) class pairs.

    Each entry is (true_idx, pred_idx, count). The diagonal holds correctly-
    classified counts; everything else is a confusion.
    """
    cm_off = cm.copy().astype(int)
    np.fill_diagonal(cm_off, 0)  # zero out the correct predictions
    flat = []
    for i in range(cm_off.shape[0]):
        for j in range(cm_off.shape[1]):
            if cm_off[i, j] > 0:
                flat.append((i, j, cm_off[i, j]))
    flat.sort(key=lambda t: -t[2])
    return flat[:k]


def _load_class_names() -> list[str]:
    """Load class names from the JSON written by train.py / data.py.

    Falls back to the directory scan only if the JSON is missing — that path
    should only fire on a fresh checkout where training hasn't run yet.
    """
    if config.CLASS_NAMES_JSON.is_file():
        with config.CLASS_NAMES_JSON.open() as f:
            return json.load(f)
    return None  # let caller fall back to the scan order


def main():
    set_seed(config.SEED)

    # 1. Build the validation dataset. Prefer class names from the JSON
    # written by train.py so metrics are reproducible across machines.
    _, valid_ds, scanned_names = build_datasets()
    valid_ds = prepare(valid_ds, training=False)
    class_names = _load_class_names() or scanned_names
    if class_names != scanned_names:
        raise ValueError(
            "Saved class-name order does not match the validation directory "
            "class order. Rebuild class_names.json by retraining."
        )

    # 2. Load the trained model
    import tensorflow as tf
    if not config.MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Trained model not found at {config.MODEL_PATH}. "
            f"Run `python -m src.train` first."
        )
    model = tf.keras.models.load_model(config.MODEL_PATH)
    print(f"[eval] Loaded {config.MODEL_PATH}.")
    if model.output_shape[-1] != len(class_names):
        raise ValueError(
            f"Model has {model.output_shape[-1]} outputs but "
            f"{len(class_names)} class names were loaded."
        )

    # 3. Predict
    print("[eval] Running inference on the validation set...")
    y_true_probs = []
    for batch_x, batch_y in valid_ds:
        y_true_probs.append(batch_y.numpy())
    y_true = np.concatenate(y_true_probs, axis=0)
    y_true_idx = np.argmax(y_true, axis=1)

    y_pred_probs = model.predict(valid_ds, verbose=1)
    y_pred_idx = np.argmax(y_pred_probs, axis=1)
    predicted_counts = np.bincount(y_pred_idx, minlength=len(class_names))
    dominant_share = predicted_counts.max() / len(y_pred_idx)
    print(
        f"[eval] Predicted classes: {np.count_nonzero(predicted_counts)}/"
        f"{len(class_names)}; largest class share: {dominant_share:.2%}"
    )
    if dominant_share >= 0.99:
        print(
            "[eval] WARNING: predictions have collapsed to one class. "
            "Check that the checkpoint, class-name ordering, and raw [0, 255] "
            "input contract match the model used for training."
        )

    # 4. Overall accuracy
    acc = accuracy_score(y_true_idx, y_pred_idx)
    print(f"\n[eval] Validation accuracy: {acc:.4f}")

    # 5. Classification report
    report = classification_report(
        y_true_idx, y_pred_idx,
        target_names=class_names, digits=4, zero_division=0,
    )
    print("\n[eval] Classification report:\n" + report)
    config.REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.REPORT_PATH.write_text(report)
    print(f"[eval] Saved classification report -> {config.REPORT_PATH}")

    # 6. Confusion matrix
    cm = confusion_matrix(y_true_idx, y_pred_idx)
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(
        cm, annot=False, fmt="d", cmap="Blues",
        xticklabels=class_names, yticklabels=class_names,
        ax=ax, cbar_kws={"label": "Count"},
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix (val acc = {acc:.2%})")
    plt.xticks(rotation=90, fontsize=7)
    plt.yticks(rotation=0, fontsize=7)
    fig.tight_layout()
    fig.savefig(config.CONFUSION_PATH, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[eval] Saved confusion matrix -> {config.CONFUSION_PATH}")

    # 7. Top confused pairs
    pairs = _top_confused_pairs(cm, class_names, k=10)
    print("\n[eval] Top 10 most-confused class pairs (true -> predicted, count):")
    for i, j, n in pairs:
        print(f"  {class_names[i]:45s} -> {class_names[j]:45s} : {n}")

    return acc


if __name__ == "__main__":
    main()