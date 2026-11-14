"""Model construction and training callbacks.

Two-phase transfer learning:
  Phase 1: freeze the ImageNet-pretrained base, train the classifier head.
  Phase 2: unfreeze the top of the base, fine-tune at a much lower LR.

Keeping the model construction in one place means train.py / evaluate.py /
predict.py all build/load the exact same architecture.
"""
from __future__ import annotations

from typing import Sequence

from . import config


def build_base_model(name: str = config.BASE_MODEL_NAME):
    """Return an ImageNet-pretrained base model with the top classifier removed.

    `include_top=False` drops the original 1000-class classifier head — we
    replace it with a 38-class head in `build_model`.
    """
    import tensorflow as tf

    name = name.lower()
    if name == "efficientnetb0":
        return tf.keras.applications.EfficientNetB0(
            weights="imagenet", include_top=False,
            input_shape=(*config.IMG_SIZE, 3),
        )
    if name == "mobilenetv2":
        return tf.keras.applications.MobileNetV2(
            weights="imagenet", include_top=False,
            input_shape=(*config.IMG_SIZE, 3),
        )
    raise ValueError(f"Unknown base model: {name}")


def last_conv_layer_name(base) -> str:
    """Return the name of the last conv layer in the base model."""
    
    # FIX 1: Check the actual model name, not its generic Python class type
    name = base.name.lower()
    
    if "efficientnet" in name:
        return "top_conv"
    if "mobilenetv2" in name:
        # MobileNetV2's last feature block is named 'Conv_1' in many versions.
        for layer in reversed(base.layers):
            if "Conv_1" in layer.name or layer.name.endswith("Conv_1"):
                return layer.name
        return "Conv_1"
        
    # FIX 2: Fallback updated for Keras 3 compatibility (using .output.shape)
    for layer in reversed(base.layers):
        try:
            if len(layer.output.shape) == 4:
                return layer.name
        except (AttributeError, ValueError):
            # Skip layers that don't have a standard output shape
            continue
            
    raise RuntimeError("Could not locate a 4D-output conv layer for Grad-CAM.")


def build_model(num_classes: int,
                base_name: str = config.BASE_MODEL_NAME,
                dropout: float = config.DROPOUT):
    """Assemble the model: preprocessing → Base → GAP → Dropout → Dense.

    Preprocessing must match the selected Keras application. EfficientNet
    includes its own rescaling layer and expects pixels in [0, 255], while
    MobileNetV2 expects pixels normalized to [-1, 1].

    Augmentation is intentionally NOT inside the model graph — Keras 3
    deepcopies the trainer at the start of `model.fit()`, and the random
    augmentation layers hold non-picklable TF-internal state. Augmentation is
    applied via `dataset.map(augment_fn)` in `train.py` instead.
    """
    import tensorflow as tf

    inputs = tf.keras.Input(shape=(*config.IMG_SIZE, 3), name="input_image")

    base = build_base_model(base_name)
    if base_name.lower() == "mobilenetv2":
        x = tf.keras.layers.Rescaling(
            1.0 / 127.5, offset=-1, name="mobilenetv2_preprocessing"
        )(inputs)
    else:
        # EfficientNet contains its own Rescaling layer and expects [0, 255].
        x = inputs

    base.trainable = False  # Phase 1 starts with the base frozen.
    x = base(x, training=False)

    x = tf.keras.layers.GlobalAveragePooling2D(name="gap")(x)
    x = tf.keras.layers.Dropout(dropout, name="head_dropout")(x)
    outputs = tf.keras.layers.Dense(
        num_classes, activation="softmax", name="predictions"
    )(x)

    model = tf.keras.Model(inputs, outputs, name=f"{base_name}_plant_disease")
    return model


def compile_for_phase(model, learning_rate: float):
    """Compile with Adam + categorical cross-entropy. Called once per phase
    so phase 2's lower learning rate actually takes effect."""
    import tensorflow as tf

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss=tf.keras.losses.CategoricalCrossentropy(),
        metrics=[tf.keras.metrics.CategoricalAccuracy(name="accuracy")],
    )


def unfreeze_top_layers(model, fine_tune_at: int) -> int:
    """Unfreeze the last |fine_tune_at| layers of the base model.

    `fine_tune_at` is negative — we count from the end so the user doesn't
    have to know the exact total layer count for each architecture.

    Batch-normalization layers remain frozen so fine-tuning uses stable
    pretrained statistics. Returns the number of trainable base layers.
    """
    import tensorflow as tf

    base = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) or layer.name.endswith("efficientnetb0") \
                or layer.name.endswith("mobilenetv2"):
            base = layer
            break
    if base is None:
        # Fallback: scan for the layer with the most sub-layers.
        candidates = [l for l in model.layers if hasattr(l, "layers") and len(l.layers) > 10]
        if not candidates:
            raise RuntimeError("Could not locate the base model inside the assembled model.")
        base = max(candidates, key=lambda l: len(l.layers))

    n_unfreeze = abs(fine_tune_at)
    total = len(base.layers)
    if n_unfreeze > total:
        n_unfreeze = total

    base.trainable = True
    first_trainable = total - n_unfreeze
    trainable_count = 0
    for index, layer in enumerate(base.layers):
        layer.trainable = index >= first_trainable
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
        if layer.trainable:
            trainable_count += 1

    return trainable_count


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------
def get_callbacks(phase: int, ckpt_path):
    """Standard trio: EarlyStopping + ModelCheckpoint + ReduceLROnPlateau."""
    import tensorflow as tf

    suffix = ckpt_path.suffix  # e.g. ".h5"
    stem = ckpt_path.stem
    phase_ckpt = ckpt_path.with_name(f"{stem}_phase{phase}{suffix}")

    return [
        # Patience=5 gives the model a few epochs to escape a flat loss
        # before we kill it. `restore_best_weights` ensures the saved-best
        # weights are what we end up with, not the last-epoch weights.
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True,
            verbose=1, mode="max",
        ),
        # Save best per-phase; the final phase's best is what we ship as
        # `best_model.h5` at the end of train.py.
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(phase_ckpt), monitor="val_accuracy",
            save_best_only=True, save_weights_only=False, verbose=1, mode="max",
        ),
        # Halve the LR if val_accuracy plateaus for 3 epochs. Crucial in
        # phase 2 where the loss landscape is sharp.
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_accuracy", factor=0.5, patience=3,
            min_lr=1e-7, verbose=1, mode="max",
        ),
    ], phase_ckpt