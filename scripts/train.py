"""Train the sentiment model and persist it to disk.

Run with: python -m scripts.train
This is invoked during environment `install` so a model artifact is ready
before the API server starts.
"""

from __future__ import annotations

from app import model as model_module


def main() -> None:
    print("Training sentiment model on bundled dataset...")
    pipeline = model_module.train()
    path = model_module.save(pipeline)
    print(f"Model trained and saved to {path}")

    # Quick sanity check so training failures surface immediately.
    sample = "I really love this, it is fantastic"
    prediction = model_module.predict(pipeline, sample)
    print(f"Sanity check: {sample!r} -> {prediction.label} ({prediction.confidence:.3f})")


if __name__ == "__main__":
    main()
