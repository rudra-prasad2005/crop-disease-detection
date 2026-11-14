"""Flask REST API for the Plant Disease Detection app.

Endpoints
---------
POST /api/predict       – Upload a leaf image, get top-K predictions + pesticide info
GET  /api/classes       – List all 38 class names
GET  /api/model-status  – Check whether the trained model exists
GET  /api/pesticides    – Full pesticide CSV as JSON
GET  /api/stats         – Training metrics (from classification_report.txt)
*    /*                 – Serve React frontend from static/
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from src import config

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# PlantVillage fallback class list (used when class_names.json is missing)
FALLBACK_CLASSES: list[str] = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]


def _load_pesticide_df() -> pd.DataFrame:
    """Load pesticide.csv into a DataFrame (cached on first call)."""
    if not hasattr(_load_pesticide_df, "_cache"):
        try:
            _load_pesticide_df._cache = pd.read_csv(config.PESTICIDE_CSV)
        except Exception:
            _load_pesticide_df._cache = pd.DataFrame(
                columns=["crop", "pest_type", "intensity", "pesticide"]
            )
    return _load_pesticide_df._cache


def _parse_class_name(class_name: str) -> tuple[str, str]:
    """Parse 'Crop___Disease_name' → (crop, disease human-readable).

    Handles both triple-underscore separator and spaces/underscores in disease.
    """
    if "___" in class_name:
        crop, disease_raw = class_name.split("___", 1)
    else:
        crop, disease_raw = class_name, "Unknown"
    # Clean up: underscores → spaces, strip extra whitespace
    disease = disease_raw.replace("_", " ").strip()
    crop = crop.replace("_", " ").strip()
    return crop, disease


def _lookup_pesticides(crop: str) -> list[dict]:
    """Return pesticide recommendations for the given crop (case-insensitive)."""
    df = _load_pesticide_df()
    if df.empty:
        return []
    mask = df["crop"].str.lower() == crop.lower()
    matches = df[mask]
    if matches.empty:
        return []
    # Deduplicate and return
    return (
        matches.drop_duplicates()
        .head(10)
        .to_dict(orient="records")
    )


def _load_class_names() -> list[str]:
    """Return class names from JSON, falling back to hardcoded list."""
    try:
        if config.CLASS_NAMES_JSON.is_file():
            with config.CLASS_NAMES_JSON.open() as f:
                return json.load(f)
    except Exception:
        pass
    return FALLBACK_CLASSES


def _parse_classification_report(text: str) -> dict:
    """Parse sklearn-style classification_report.txt into structured data."""
    lines = text.strip().splitlines()
    metrics: dict = {"per_class": [], "accuracy": None, "macro_avg": {}, "weighted_avg": {}}

    for line in lines:
        line = line.strip()
        if not line or line.startswith("-"):
            continue
        # Accuracy line: "accuracy                           0.95   8000"
        if line.startswith("accuracy"):
            parts = line.split()
            for p in parts[1:]:
                try:
                    metrics["accuracy"] = float(p)
                    break
                except ValueError:
                    continue
            continue
        # Macro / weighted avg
        if line.startswith("macro avg") or line.startswith("weighted avg"):
            key = "macro_avg" if line.startswith("macro") else "weighted_avg"
            nums = re.findall(r"[\d.]+", line)
            if len(nums) >= 3:
                metrics[key] = {
                    "precision": float(nums[0]),
                    "recall": float(nums[1]),
                    "f1_score": float(nums[2]),
                }
            continue
        # Per-class rows: "class_name   precision   recall   f1   support"
        parts = line.rsplit(None, 4)
        if len(parts) == 5:
            try:
                metrics["per_class"].append({
                    "class": parts[0],
                    "precision": float(parts[1]),
                    "recall": float(parts[2]),
                    "f1_score": float(parts[3]),
                    "support": int(parts[4]),
                })
            except ValueError:
                continue
    return metrics


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.route("/api/predict", methods=["POST"])
def api_predict():
    """Accept an image upload, run prediction, return results + pesticide info."""
    # --- Validate input ---
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided. Use field name 'image'."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename."}), 400

    # --- Check model availability ---
    if not config.MODEL_PATH.is_file():
        return jsonify({
            "success": False,
            "error": (
                "Model not trained yet. Please run `python -m src.train` to train "
                "the model before making predictions."
            ),
        }), 503

    if not config.CLASS_NAMES_JSON.is_file():
        return jsonify({
            "success": False,
            "error": (
                "class_names.json not found. The model must be trained first so that "
                "class names are generated."
            ),
        }), 503

    # --- Save uploaded image to a temp file ---
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1] or ".jpg")
    try:
        os.close(tmp_fd)
        file.save(tmp_path)

        # --- Run prediction ---
        from src.predict import predict  # lazy import to avoid loading TF at startup

        results = predict(Path(tmp_path), top_k=5)

        # Build response
        predictions = [
            {"class": cls_name, "confidence": round(prob, 6)}
            for cls_name, prob in results
        ]

        top_cls, top_prob = results[0]
        crop, disease = _parse_class_name(top_cls)

        top_prediction = {
            "class": top_cls,
            "confidence": round(top_prob, 6),
            "crop": crop,
            "disease": disease,
        }

        pesticide_info = _lookup_pesticides(crop)

        return jsonify({
            "success": True,
            "predictions": predictions,
            "top_prediction": top_prediction,
            "pesticide_info": pesticide_info,
        })

    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 503
    except Exception as e:
        return jsonify({"success": False, "error": f"Prediction failed: {e}"}), 500
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@app.route("/api/classes", methods=["GET"])
def api_classes():
    """Return the list of class names the model can predict."""
    try:
        classes = _load_class_names()
        return jsonify({
            "success": True,
            "classes": classes,
            "count": len(classes),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/model-status", methods=["GET"])
def api_model_status():
    """Return the current state of trained artifacts."""
    try:
        model_exists = config.MODEL_PATH.is_file()
        class_names_exist = config.CLASS_NAMES_JSON.is_file()

        status: dict = {
            "success": True,
            "model_exists": model_exists,
            "class_names_exist": class_names_exist,
            "model_path": str(config.MODEL_PATH),
            "model_name": config.BASE_MODEL_NAME,
            "image_size": list(config.IMG_SIZE),
            "dataset": "PlantVillage",
            "num_classes": 38,
            "ready": model_exists and class_names_exist,
        }

        # Add file sizes if they exist
        if model_exists:
            size_mb = config.MODEL_PATH.stat().st_size / (1024 * 1024)
            status["model_size_mb"] = round(size_mb, 2)

        return jsonify(status)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/pesticides", methods=["GET"])
def api_pesticides():
    """Return the full pesticide CSV data as JSON."""
    try:
        df = _load_pesticide_df()
        records = df.to_dict(orient="records")
        return jsonify({
            "success": True,
            "pesticides": records,
            "count": len(records),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return training/evaluation metrics if available."""
    try:
        if config.REPORT_PATH.is_file():
            text = config.REPORT_PATH.read_text(encoding="utf-8")
            metrics = _parse_classification_report(text)
            return jsonify({
                "success": True,
                "source": "classification_report.txt",
                "metrics": metrics,
            })
        else:
            # Placeholder stats when no report exists
            return jsonify({
                "success": True,
                "source": "placeholder",
                "metrics": {
                    "accuracy": None,
                    "macro_avg": {
                        "precision": None,
                        "recall": None,
                        "f1_score": None,
                    },
                    "weighted_avg": {
                        "precision": None,
                        "recall": None,
                        "f1_score": None,
                    },
                    "per_class": [],
                },
                "message": (
                    "No classification report found. Train the model with "
                    "`python -m src.train` to generate evaluation metrics."
                ),
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# React frontend catch-all
# ---------------------------------------------------------------------------

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    """Serve React static files; fall back to index.html for client-side routing."""
    static_dir = app.static_folder or "static"
    # If the file exists in static/, serve it directly
    full_path = os.path.join(static_dir, path)
    if path and os.path.isfile(full_path):
        return send_from_directory(static_dir, path)
    # Otherwise serve index.html (React Router handles the route)
    index = os.path.join(static_dir, "index.html")
    if os.path.isfile(index):
        return send_from_directory(static_dir, "index.html")
    return jsonify({
        "message": "Plant Disease Detection API is running.",
        "endpoints": [
            "POST /api/predict",
            "GET  /api/classes",
            "GET  /api/model-status",
            "GET  /api/pesticides",
            "GET  /api/stats",
        ],
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
