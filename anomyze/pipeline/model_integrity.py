"""Model integrity checks.

Verifies that the model files actually loaded from the HuggingFace
cache match a hard-coded expected SHA256 manifest. This protects
against silent supply-chain swaps when ``ANOMYZE_*_MODEL_REVISION`` is
left unpinned.

Manifest format
---------------

``config/model_hashes.json`` maps a HuggingFace model id to a dict of
``relative_path -> sha256``::

    {
      "HuggingLil/pii-sensitive-ner-german": {
        "config.json": "abcd...",
        "pytorch_model.bin": "ef01..."
      }
    }

Empty manifests are accepted (logging only) so deployments that do not
yet maintain a checksum file can still boot.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _model_dir(cache_root: Path, model_id: str) -> Path | None:
    """Return the local snapshot directory for a HF model id, if any."""
    safe = model_id.replace("/", "--")
    candidates = list(cache_root.glob(f"models--{safe}/snapshots/*"))
    return candidates[0] if candidates else None


def load_manifest(manifest_path: Path) -> dict[str, dict[str, str]]:
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text())


def verify_model(
    model_id: str,
    manifest: dict[str, dict[str, str]],
    cache_root: Path,
) -> tuple[bool, list[str]]:
    """Verify the on-disk files for ``model_id`` against the manifest.

    Returns a ``(ok, problems)`` pair. ``ok`` is True when every file
    listed in the manifest matches; ``problems`` lists the offending
    files (missing or mismatched). Models not in the manifest return
    ``(True, [])`` and are logged so operators notice.
    """
    expected = manifest.get(model_id)
    if not expected:
        logger.info("Model %s not in integrity manifest, skipping check", model_id)
        return True, []

    snapshot = _model_dir(cache_root, model_id)
    if snapshot is None:
        return False, [f"snapshot dir not found for {model_id}"]

    problems: list[str] = []
    for rel_path, want_sha in expected.items():
        full = snapshot / rel_path
        if not full.exists():
            problems.append(f"missing: {rel_path}")
            continue
        got = _sha256(full)
        if got != want_sha:
            problems.append(
                f"checksum mismatch for {rel_path}: expected {want_sha[:12]}…, got {got[:12]}…"
            )
    return not problems, problems


__all__ = ["load_manifest", "verify_model"]
