"""Data pipeline: extract archive, split into train/valid, build tf.data pipelines.

Designed so a single `python -m src.train` invocation can go from a cold cache
(extracted archive → split → datasets → trained model) end-to-end.
"""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import numpy as np

from . import config
from .utils import is_empty_dir, set_seed


# ---------------------------------------------------------------------------
# 1. Extract
# ---------------------------------------------------------------------------
def extract_archive(archive_path: Path = config.ARCHIVE_PATH,
                     dest: Path = config.RAW_DIR) -> Path:
    """Unzip the PlantVillage archive into `data/raw/`.

    Idempotent: if `data/raw/plantvillage dataset/color/` already exists and is
    non-empty, this is a no-op. The archive is large (~2 GB) so we avoid
    re-extracting when possible.
    """
    color_dir = dest / "plantvillage dataset" / config.SOURCE_VARIANT
    if color_dir.is_dir() and any(color_dir.iterdir()):
        print(f"[data] Archive already extracted at {dest}. Skipping.")
        return dest

    if not archive_path.is_file():
        raise FileNotFoundError(
            f"Archive not found at {archive_path}. "
            f"Place archive.zip in the project root or update config.ARCHIVE_PATH."
        )

    print(f"[data] Extracting {archive_path} -> {dest} ...")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(dest)
    print("[data] Extraction complete.")
    return dest


# ---------------------------------------------------------------------------
# 2. Train/valid split (per-class, stratified)
# ---------------------------------------------------------------------------
def make_splits(src_dir: Path = config.RAW_COLOR_DIR,
                train_dir: Path = config.TRAIN_DIR,
                valid_dir: Path = config.VALID_DIR,
                train_ratio: float = config.TRAIN_SPLIT,
                seed: int = config.SEED) -> tuple[Path, Path]:
    """Split each class folder into train/ and valid/ subfolders.

    We do a per-class split (not a global shuffle) so every class appears in
    both train and validation. `image_dataset_from_directory` doesn't expose
    stratified splits directly, so we build the directories ourselves.

    Idempotent: skips if `train_dir` already has class subfolders.
    """
    if train_dir.is_dir() and any(p.is_dir() for p in train_dir.iterdir()):
        print(f"[data] Splits already exist at {train_dir.parent}. Skipping.")
        return train_dir, valid_dir

    if not src_dir.is_dir():
        raise FileNotFoundError(
            f"Source directory not found: {src_dir}. Did extract_archive() run?"
        )

    train_dir.mkdir(parents=True, exist_ok=True)
    valid_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(seed)
    class_names = sorted(p.name for p in src_dir.iterdir() if p.is_dir())
    print(f"[data] Splitting {len(class_names)} classes into train/valid "
          f"({train_ratio:.0%}/{1 - train_ratio:.0%})...")

    for cls in class_names:
        cls_src = src_dir / cls
        files = sorted(p for p in cls_src.iterdir() if p.is_file())
        if not files:
            print(f"[data]   Warning: class '{cls}' has no files, skipping.")
            continue

        idx = rng.permutation(len(files))
        split = int(len(files) * train_ratio)

        (train_dir / cls).mkdir(parents=True, exist_ok=True)
        (valid_dir / cls).mkdir(parents=True, exist_ok=True)

        for i in idx[:split]:
            shutil.copy2(files[i], train_dir / cls / files[i].name)
        for i in idx[split:]:
            shutil.copy2(files[i], valid_dir / cls / files[i].name)

    print(f"[data] Split complete. Train root: {train_dir} | Valid root: {valid_dir}")
    return train_dir, valid_dir


# ---------------------------------------------------------------------------
# 3. tf.data pipelines
# ---------------------------------------------------------------------------
def build_datasets(img_size: tuple[int, int] = config.IMG_SIZE,
                   batch_size: int = config.BATCH_SIZE,
                   seed: int = config.SEED):
    """Build train and validation `tf.data.Dataset` objects via `image_dataset_from_directory`.

    We make **two separate calls** (one per directory) rather than a single call
    with `validation_split=`. The latter regenerates the split from a hash of
    file paths and silently re-shuffles whenever files are added to the source.

    Returns: (train_ds, valid_ds, class_names)
    """
    # Imported here so non-training scripts (predict, evaluate, explain) can
    # import this module without TF being installed.
    import tensorflow as tf

    if not config.TRAIN_DIR.is_dir() or is_empty_dir(config.TRAIN_DIR):
        raise RuntimeError(
            f"Train directory missing or empty: {config.TRAIN_DIR}. "
            f"Run `python -m src.train` first — it will build the splits."
        )

    common_kwargs = dict(
        label_mode="categorical",
        image_size=img_size,
        batch_size=batch_size,
        shuffle=False,
        seed=seed,
    )

    train_kwargs = dict(common_kwargs)
    train_kwargs["shuffle"] = True
    valid_kwargs = dict(common_kwargs)
    valid_kwargs["shuffle"] = False  # reproducible evaluation order

    train_ds = tf.keras.utils.image_dataset_from_directory(
        config.TRAIN_DIR, **train_kwargs
    )
    valid_ds = tf.keras.utils.image_dataset_from_directory(
        config.VALID_DIR, **valid_kwargs
    )

    class_names = train_ds.class_names
    print(f"[data] {len(class_names)} classes | train batches: "
          f"{len(train_ds)} | valid batches: {len(valid_ds)}")

    # Persist class names so predict.py / evaluate.py can load them without
    # having to scan the directory.
    config.CLASS_NAMES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with config.CLASS_NAMES_JSON.open("w") as f:
        json.dump(class_names, f, indent=2)

    return train_ds, valid_ds, class_names


# ---------------------------------------------------------------------------
# 4. Augmentation + prefetch
# ---------------------------------------------------------------------------
def make_augmentation():
    """Return a stateless `tf.data.Dataset.map` function that applies
    augmentation to a batch.

    Applied at the dataset level rather than inside the model graph — Keras 3
    deepcopies the trainer before `model.fit()` and the random augmentation
    layers hold non-picklable TF-internal state, so embedding them in the
    model causes a `TypeError: cannot pickle 'module' object`.

    Conservative magnitudes: leaves can be in any orientation and lighting in
    the field, so we don't go aggressive.
    """
    import tensorflow as tf

    layers = [
        tf.keras.layers.RandomRotation(0.10, seed=config.SEED),
        tf.keras.layers.RandomFlip("horizontal_and_vertical", seed=config.SEED),
        tf.keras.layers.RandomZoom(0.10, seed=config.SEED),
        tf.keras.layers.RandomBrightness(0.10, seed=config.SEED),
    ]

    def augment(images, labels):
        for layer in layers:
            images = layer(images)
        return images, labels

    return augment


def prepare(ds, training: bool = False, augment_fn=None):
    """Apply shuffle/augmentation/prefetch.

    Avoid caching decoded images in memory: a full PlantVillage split can
    occupy several gigabytes. In particular, caching after augmentation would
    also freeze the first epoch's random augmentations for every later epoch.
    """
    import tensorflow as tf

    if training:
        ds = ds.shuffle(1000, seed=config.SEED, reshuffle_each_iteration=True)
        if augment_fn is not None:
            ds = ds.map(augment_fn, num_parallel_calls=tf.data.AUTOTUNE)
    return ds.prefetch(tf.data.AUTOTUNE)


def class_weights_from_counts(class_counts) -> np.ndarray:
    """Return mild inverse-square-root weights with mean sample weight 1."""
    counts = np.asarray(class_counts, dtype=np.float64)
    if counts.ndim != 1 or counts.size == 0 or np.any(counts <= 0):
        raise ValueError("class_counts must be a non-empty sequence of positive counts.")

    weights = np.sqrt(counts.max() / counts)
    weights /= np.average(weights, weights=counts)
    return weights.astype(np.float32)


def apply_class_weights(ds, class_weights):
    """Attach per-example weights to a one-hot labeled dataset."""
    import tensorflow as tf

    weights = tf.constant(class_weights, dtype=tf.float32)

    def add_sample_weight(images, labels):
        sample_weights = tf.reduce_sum(
            tf.cast(labels, tf.float32) * weights, axis=-1
        )
        return images, labels, sample_weights

    return ds.map(add_sample_weight, num_parallel_calls=tf.data.AUTOTUNE).prefetch(
        tf.data.AUTOTUNE
    )


# ---------------------------------------------------------------------------
# 5. One-shot prep used by train.py
# ---------------------------------------------------------------------------
def prepare_all():
    """Run extract → split → build datasets → apply prepare. Returns the
    prepared datasets, class names, and augmentation function."""
    set_seed(config.SEED)
    extract_archive()
    make_splits()
    train_ds, valid_ds, class_names = build_datasets()
    augment_fn = make_augmentation()
    train_ds = prepare(train_ds, training=True, augment_fn=augment_fn)
    valid_ds = prepare(valid_ds, training=False)
    return train_ds, valid_ds, class_names, augment_fn