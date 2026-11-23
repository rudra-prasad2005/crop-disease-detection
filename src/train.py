"""Training entry point.

Run with:
    python -m src.train

This script is idempotent: if the archive is already extracted, the splits
already exist, and a saved model is found, training still runs (it just
skips the data-prep steps).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt

from . import config
from .data import apply_class_weights, class_weights_from_counts, prepare_all
from .model import build_model, compile_for_phase, get_callbacks, unfreeze_top_layers
from .utils import set_seed


def _plot_curves(histories, out_path: Path) -> None:
    """Two-panel figure: loss (left) and accuracy (right), both phases stacked."""
    fig, (ax_loss, ax_acc) = plt.subplots(1, 2, figsize=(14, 5))

    epochs_offset = 0
    for phase_idx, h in enumerate(histories, start=1):
        n = len(h.history["loss"])
        epochs = list(range(epochs_offset + 1, epochs_offset + n + 1))
        epochs_offset += n

        label_suffix = f" (phase {phase_idx})"
        ax_loss.plot(epochs, h.history["loss"], label=f"train{label_suffix}")
        ax_loss.plot(epochs, h.history["val_loss"], label=f"valid{label_suffix}")
        ax_acc.plot(epochs, h.history["accuracy"], label=f"train{label_suffix}")
        ax_acc.plot(epochs, h.history["val_accuracy"], label=f"valid{label_suffix}")

        # Mark the boundary between phases so the two are visually distinct.
        if phase_idx < len(histories):
            ax_loss.axvline(epochs_offset + 0.5, color="grey", linestyle="--", alpha=0.5)
            ax_acc.axvline(epochs_offset + 0.5, color="grey", linestyle="--", alpha=0.5)

    ax_loss.set_title("Loss"); ax_loss.set_xlabel("Epoch"); ax_loss.set_ylabel("Loss")
    ax_loss.legend(); ax_loss.grid(alpha=0.3)
    ax_acc.set_title("Accuracy"); ax_acc.set_xlabel("Epoch"); ax_acc.set_ylabel("Accuracy")
    ax_acc.legend(); ax_acc.grid(alpha=0.3)

    fig.suptitle("Training curves (two-phase fine-tuning)", fontsize=14)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"[train] Saved training curves -> {out_path}")


def main():
    set_seed(config.SEED)

    # 1. Data
    train_ds, valid_ds, class_names, augment_fn = prepare_all()
    num_classes = len(class_names)
    train_counts = [
        sum(1 for path in (config.TRAIN_DIR / name).iterdir() if path.is_file())
        for name in class_names
    ]
    class_weights = class_weights_from_counts(train_counts)
    train_ds = apply_class_weights(train_ds, class_weights)
    print(
        "[train] Applied inverse-square-root class weights "
        f"(range {class_weights.min():.3f}-{class_weights.max():.3f})."
    )

    # Persist class names for predict.py / evaluate.py to load.
    config.CLASS_NAMES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with config.CLASS_NAMES_JSON.open("w") as f:
        json.dump(class_names, f, indent=2)
    print(f"[train] Classes ({num_classes}): {class_names[:5]} ... {class_names[-2:]}")

    # 2. Build + compile for phase 1
    model = build_model(
        num_classes=num_classes,
        base_name=config.BASE_MODEL_NAME,
        dropout=config.DROPOUT,
    )
    compile_for_phase(model, config.PHASE1_LR)
    model.summary(print_fn=lambda s: print("[train]", s))

    callbacks, phase1_ckpt = get_callbacks(phase=1, ckpt_path=config.MODEL_PATH)

    # 3. Phase 1: train only the head (base is frozen)
    print("\n[train] ===== Phase 1: training head (base frozen) =====")
    h1 = model.fit(
        train_ds,
        validation_data=valid_ds,
        epochs=config.PHASE1_EPOCHS,
        callbacks=callbacks,
        verbose=1,
    )

    # 4. Phase 2: unfreeze top layers and fine-tune at low LR
    print("\n[train] ===== Phase 2: fine-tuning top of base =====")
    n_unfrozen = unfreeze_top_layers(model, config.FINE_TUNE_AT)
    print(f"[train] Unfroze the last {n_unfrozen} layers of the base.")
    # Recompile with a fresh low-LR optimizer. This resets optimizer moments,
    # not model weights, so the Phase 1 classifier head is preserved.
    compile_for_phase(model, config.PHASE2_LR)

    callbacks, phase2_ckpt = get_callbacks(phase=2, ckpt_path=config.MODEL_PATH)

    h2 = model.fit(
        train_ds,
        validation_data=valid_ds,
        epochs=config.PHASE2_EPOCHS,
        callbacks=callbacks,
        verbose=1,
    )

    # 5. Restore and promote the exact best Phase 2 checkpoint.
    import tensorflow as tf

    if not phase2_ckpt.is_file():
        raise FileNotFoundError(
            f"Phase 2 did not produce its best-model checkpoint: {phase2_ckpt}"
        )
    best_model = tf.keras.models.load_model(phase2_ckpt, compile=False)
    if best_model.output_shape[-1] != num_classes:
        raise ValueError(
            f"Phase 2 checkpoint has {best_model.output_shape[-1]} outputs; "
            f"expected {num_classes}."
        )
    best_model.save(config.MODEL_PATH)
    print(f"[train] Saved final model -> {config.MODEL_PATH}")
    print(
        f"[train] Best Phase 2 validation accuracy: "
        f"{max(h2.history['val_accuracy']):.4f}"
    )

    # 6. Plot
    _plot_curves([h1, h2], config.CURVES_PATH)

    print("[train] Done.")


if __name__ == "__main__":
    main()