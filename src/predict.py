"""Standalone inference.

Run with:
    python -m src.predict path/to/leaf.jpg
    python -m src.predict path/to/leaf.jpg --top-k 5

Loads the trained model from `models/plant_disease.keras` and class names from
`models/class_names.json`. Resizes an RGB image and passes raw [0, 255] pixels;
the model owns all backbone preprocessing.

No external scaling or normalization is applied.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

from . import config


def _load_class_names() -> list[str]:
    if not config.CLASS_NAMES_JSON.is_file():
        raise FileNotFoundError(
            f"class_names.json not found at {config.CLASS_NAMES_JSON}. "
            f"Run `python -m src.train` first so it can be written."
        )
    with config.CLASS_NAMES_JSON.open() as f:
        return json.load(f)


def _load_image(path: Path) -> np.ndarray:
    """Load an image from disk as float32 [H, W, 3] in [0, 255].

    We let the model's Rescaling layer handle the /255. PIL handles JPG/PNG/BMP.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    img = Image.open(path).convert("RGB")
    img = img.resize(config.IMG_SIZE, Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32)
    return arr


def predict(image_path: Path, top_k: int = 3):
    """Return a list of (class_name, probability) tuples, sorted desc."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if not config.MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Trained model not found at {config.MODEL_PATH}. "
            f"Run `python -m src.train` first."
        )

    class_names = _load_class_names()

    # Eager execution is the default in TF 2.x — load_model returns an
    # already-built model so a one-off predict is cheap.
    model = tf.keras.models.load_model(config.MODEL_PATH)
    if model.output_shape[-1] != len(class_names):
        raise ValueError(
            f"Model has {model.output_shape[-1]} outputs but "
            f"{len(class_names)} class names are configured. Retrain the model."
        )

    arr = _load_image(image_path)
    batch = tf.expand_dims(arr, axis=0)  # [1, H, W, 3]
    probs = model.predict(batch, verbose=0)[0]

    # Sort probabilities desc, take top-k.
    top_idx = probs.argsort()[::-1][:top_k]
    top = [(class_names[i], float(probs[i])) for i in top_idx]
    return top


def main():
    parser = argparse.ArgumentParser(
        description="Plant disease classifier — predict a single image."
    )
    parser.add_argument(
        "image_path", type=Path,
        help="Path to the leaf image to classify (jpg/png/bmp).",
    )
    parser.add_argument(
        "--top-k", type=int, default=3,
        help="Number of top predictions to print (default: 3).",
    )
    args = parser.parse_args()

    top = predict(args.image_path, top_k=args.top_k)

    print(f"Image: {args.image_path}")
    print(f"Top-{args.top_k} predictions:")
    for cls, p in top:
        bar = "#" * int(round(p * 40))
        print(f"  {p:7.4f}  {bar:<40s}  {cls}")

    best_cls, best_p = top[0]
    print(f"\nPredicted: {best_cls}  (confidence: {best_p:.4f})")


if __name__ == "__main__":
    main()