"""Grad-CAM explainability.

Generates `outputs/gradcam/sample_{i}.png` for `NUM_GRADCAM_SAMPLES` images
drawn from the validation set. Each image shows the original leaf plus a
heatmap overlay of where the model is "looking" — confirming that the
classifier keys off lesions rather than background.

Run with:
    python -m src.explain
"""
from __future__ import annotations

from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

from . import config
from .data import build_datasets, prepare
from .model import last_conv_layer_name
from .utils import set_seed


def _make_grad_model(model: tf.keras.Model, last_conv_layer_name: str):
    """Return a sub-model that outputs (conv feature map, predictions)."""
    import tensorflow as tf
    
    # 1. Locate the nested pre-trained model (index 2: Input -> Rescaling -> Base)
    base_model = model.get_layer(index=2)
    
    # 2. Build an inner model that gives both the conv layer output and the final base output
    inner_grad_model = tf.keras.Model(
        inputs=base_model.inputs, 
        outputs=[base_model.get_layer(last_conv_layer_name).output, base_model.output]
    )
    
    # 3. Reconstruct the full model architecture using our custom layers
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = model.get_layer("rescaling")(inputs)
    
    # Extract both the intermediate heatmap tensor and the final image features
    conv_output, base_output = inner_grad_model(x)
    
    # 4. Pass the features through our custom classification head
    x = model.get_layer("gap")(base_output)
    x = model.get_layer("head_dropout")(x)
    outputs = model.get_layer("predictions")(x)
    
    return tf.keras.Model(inputs, [conv_output, outputs])


def _gradcam(grad_model, img_array, pred_index=None):
    """Compute the Grad-CAM heatmap for a single image (already 224x224x3,
    in [0, 1] float32)."""
    with tf.GradientTape() as tape:
        # The model returns [conv_map, softmax_preds].
        conv_output, preds = grad_model(tf.expand_dims(img_array, axis=0))
        if pred_index is None:
            pred_index = tf.argmax(preds[0])
        class_channel = preds[:, pred_index]

    # Gradient of the chosen class score w.r.t. the feature map.
    grads = tape.gradient(class_channel, conv_output)

    # Global-average-pool the gradients over spatial dims to get channel weights.
    pooled = tf.reduce_mean(grads, axis=(0, 1, 2))

    # Weighted sum of feature maps (per-channel), then ReLU so we only keep
    # activations that *positively* influence the target class.
    conv_output = conv_output[0]
    heatmap = conv_output @ pooled[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


def _overlay_heatmap(img_array: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
    """Resize heatmap to image size, color it (JET colormap), and blend."""
    heatmap_uint8 = np.uint8(255 * heatmap)
    # cv2.resize expects (width, height) — note the swap.
    heatmap_resized = cv2.resize(heatmap_uint8, (img_array.shape[1], img_array.shape[0]))
    heatmap_color = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
    heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

    # Original image is float32 in [0, 1]; scale to [0, 255] for blending.
    img_uint8 = np.uint8(255 * img_array)
    overlay = np.uint8(heatmap_color * 0.4 + img_uint8 * 0.6)
    return overlay


def _load_class_names() -> list[str]:
    import json
    with config.CLASS_NAMES_JSON.open() as f:
        return json.load(f)


def main():
    set_seed(config.SEED)

    # 1. Build validation dataset
    _, valid_ds, scanned_names = build_datasets()
    valid_ds = prepare(valid_ds, training=False)

    # 2. Load the model
    if not config.MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Trained model not found at {config.MODEL_PATH}. "
            f"Run `python -m src.train` first."
        )
    model = tf.keras.models.load_model(config.MODEL_PATH)
    print(f"[gradcam] Loaded {config.MODEL_PATH}.")

    # 3. Locate the last conv layer and build a gradient model.
    last_conv = last_conv_layer_name(model.get_layer(index=2))
    print(f"[gradcam] Hooking into last conv layer: {last_conv}")
    grad_model = _make_grad_model(model, last_conv)

    # 4. Pick `NUM_GRADCAM_SAMPLES` images, one per class where possible, so
    # the visualizations cover a diverse set of diseases instead of all being
    # from the first batch (which is usually one or two dominant classes).
    n_samples = config.NUM_GRADCAM_SAMPLES
    if config.CLASS_NAMES_JSON.is_file():
        class_names = _load_class_names()
    else:
        class_names = scanned_names

    config.GRADCAM_DIR.mkdir(parents=True, exist_ok=True)

    # Walk the validation set once. For each new class we see, grab the first
    # image of that class until we have `n_samples` or we run out of classes.
    picked_by_class: dict[int, tuple] = {}  # true_idx -> (img_uint8, true_idx)
    for batch_x, batch_y in valid_ds:
        if len(picked_by_class) >= n_samples:
            break
        for i in range(batch_x.shape[0]):
            true_idx = int(tf.argmax(batch_y[i]).numpy())
            if true_idx not in picked_by_class:
                picked_by_class[true_idx] = (batch_x[i].numpy(), true_idx)
                if len(picked_by_class) >= n_samples:
                    break

    saved = 0
    for true_idx, (img_uint8, _) in picked_by_class.items():
        img = img_uint8 / 255.0  # normalize for overlay blending
        heatmap = _gradcam(grad_model, img_uint8)
        overlay = _overlay_heatmap(img, heatmap)

        pred_idx = int(np.argmax(
            model.predict(tf.expand_dims(img_uint8, axis=0), verbose=0)[0]
        ))

        fig, axes = plt.subplots(1, 2, figsize=(8, 4))
        axes[0].imshow(img); axes[0].axis("off")
        axes[0].set_title(f"Original\ntrue: {class_names[true_idx]}", fontsize=9)
        axes[1].imshow(overlay); axes[1].axis("off")
        color = "green" if pred_idx == true_idx else "red"
        axes[1].set_title(
            f"Grad-CAM\npred: {class_names[pred_idx]}",
            fontsize=9, color=color,
        )
        fig.tight_layout()
        out_path = config.GRADCAM_DIR / f"sample_{saved + 1}.png"
        fig.savefig(out_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        saved += 1

    print(f"[gradcam] Saved {saved} Grad-CAM visualizations to {config.GRADCAM_DIR}")


if __name__ == "__main__":
    main()