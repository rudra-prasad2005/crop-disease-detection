"""Top-level pipeline orchestrator.

Run any combination of: train -> evaluate -> explain -> predict from a single
entry point. Useful for reproducing the full pipeline on a fresh checkout.

Examples:
    python main.py all                       # train + evaluate + explain
    python main.py train                     # train only
    python main.py train evaluate            # train, then evaluate
    python main.py evaluate explain          # skip training (uses existing model)
    python main.py predict path/to/leaf.jpg  # single-image inference
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


# Make `src` importable when running `python main.py ...` from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _run(stage: str, args: list[str]) -> None:
    if stage == "train":
        from src.train import main as train_main
        train_main()
    elif stage == "evaluate":
        from src.evaluate import main as eval_main
        eval_main()
    elif stage == "explain":
        from src.explain import main as explain_main
        explain_main()
    elif stage == "predict":
        # Forward remaining CLI args (image path + --top-k) into predict.main.
        from src.predict import main as predict_main
        sys.argv = ["src.predict", *args]
        predict_main()
    elif stage == "all":
        for s in ("train", "evaluate", "explain"):
            _run(s, args)
    else:
        raise SystemExit(f"Unknown stage: {stage}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plant disease classification pipeline orchestrator.",
    )
    parser.add_argument(
        "stages", nargs="+",
        help="One or more of: train, evaluate, explain, predict, all. "
             "If 'predict' is included, additional arguments (image path, "
             "--top-k) are passed through.",
    )
    args = parser.parse_args()

    # If 'predict' is one of the stages, the image path follows it. Split the
    # list into the stages and the passthrough args.
    stages = list(args.stages)
    passthrough: list[str] = []
    if "predict" in stages:
        idx = stages.index("predict")
        passthrough = stages[idx + 1:]
        stages = stages[:idx + 1]

    for stage in stages:
        print(f"\n========== {stage.upper()} ==========")
        _run(stage, passthrough)


if __name__ == "__main__":
    main()
