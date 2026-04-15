#!/usr/bin/env python3
"""Pre-fetch all Anomyze HuggingFace models into the local HF cache.

Intended to run as a Docker init-container or before air-gapping a
deployment. Honours the same ``ANOMYZE_*_MODEL`` and
``ANOMYZE_*_MODEL_REVISION`` environment variables as the runtime.
"""

from __future__ import annotations

import sys

from huggingface_hub import snapshot_download

from anomyze.config.settings import Settings


def fetch(settings: Settings) -> int:
    targets = [
        (settings.pii_model, settings.pii_model_revision),
        (settings.org_model, settings.org_model_revision),
        (settings.mlm_model, settings.mlm_model_revision),
    ]
    if settings.use_gliner:
        targets.append((settings.gliner_model, settings.gliner_model_revision))

    failures = 0
    for model_id, revision in targets:
        rev = revision or None
        print(f"Fetching {model_id}@{rev or 'latest'} ...")
        try:
            snapshot_download(repo_id=model_id, revision=rev)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {exc}", file=sys.stderr)
            failures += 1

    return failures


def main() -> int:
    settings = Settings.from_env()
    return fetch(settings)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
