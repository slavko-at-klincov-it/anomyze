#!/usr/bin/env python3
"""Generate ``config/model_hashes.json`` from the current HF cache.

Walks the local HuggingFace snapshot directories for every model in
``Settings`` and emits SHA256 hashes for the weight / config / tokenizer
files. The resulting manifest is consumed by
``anomyze.pipeline.model_integrity.verify_model``.

Run after ``scripts/prefetch_models.py`` or after a model revision bump.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from huggingface_hub.constants import HF_HUB_CACHE

from anomyze.config.settings import Settings

# Only hash files that actually influence the loaded model; skip
# markdown / example / gitattributes to keep the manifest stable.
_HASHABLE_SUFFIXES = frozenset({
    ".json", ".bin", ".safetensors", ".txt", ".model", ".spm",
})


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_dir(cache_root: Path, model_id: str) -> Path | None:
    safe = model_id.replace("/", "--")
    snapshots = list(cache_root.glob(f"models--{safe}/snapshots/*"))
    return snapshots[0] if snapshots else None


def build(settings: Settings, cache_root: Path) -> dict[str, dict[str, str]]:
    ids = [settings.pii_model, settings.org_model, settings.mlm_model]
    if settings.use_gliner:
        ids.append(settings.gliner_model)

    manifest: dict[str, dict[str, str]] = {}
    for model_id in ids:
        snap = _snapshot_dir(cache_root, model_id)
        if snap is None:
            print(f"  SKIP: {model_id} (snapshot not in cache)", file=sys.stderr)
            continue
        entries: dict[str, str] = {}
        for f in snap.rglob("*"):
            # HF cache stores snapshots as symlinks into ../../blobs/;
            # follow them rather than skipping. The blob contents are
            # what we actually care about for the integrity check.
            target = f.resolve()
            if not target.is_file():
                continue
            if f.suffix.lower() not in _HASHABLE_SUFFIXES:
                continue
            entries[str(f.relative_to(snap))] = _sha256(target)
        manifest[model_id] = entries
        print(f"  {model_id}: {len(entries)} files hashed")
    return manifest


def main() -> int:
    settings = Settings.from_env()
    cache_root = Path(HF_HUB_CACHE)
    if not cache_root.exists():
        print(f"HF cache not found at {cache_root}", file=sys.stderr)
        return 1
    manifest = build(settings, cache_root)
    if not manifest:
        print("no models found in cache — run prefetch_models first", file=sys.stderr)
        return 1
    out = Path("config/model_hashes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"wrote {out} ({sum(len(v) for v in manifest.values())} entries total)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
