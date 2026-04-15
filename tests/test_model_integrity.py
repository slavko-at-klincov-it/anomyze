"""Tests for the model-integrity manifest check."""

import hashlib
import json
from pathlib import Path

from anomyze.pipeline.model_integrity import load_manifest, verify_model


def _make_snapshot(tmp_path: Path, model_id: str, files: dict[str, bytes]) -> Path:
    safe = model_id.replace("/", "--")
    snap = tmp_path / f"models--{safe}" / "snapshots" / "abc123"
    snap.mkdir(parents=True)
    for name, content in files.items():
        (snap / name).write_bytes(content)
    return snap


class TestLoadManifest:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert load_manifest(tmp_path / "nope.json") == {}

    def test_loads_json(self, tmp_path: Path) -> None:
        p = tmp_path / "m.json"
        p.write_text('{"x/y": {"a.bin": "deadbeef"}}')
        assert load_manifest(p) == {"x/y": {"a.bin": "deadbeef"}}


class TestVerifyModel:
    def test_no_manifest_entry_passes(self, tmp_path: Path) -> None:
        ok, problems = verify_model("foo/bar", {}, tmp_path)
        assert ok and problems == []

    def test_matching_checksums(self, tmp_path: Path) -> None:
        files = {"config.json": b"hello"}
        sha = hashlib.sha256(b"hello").hexdigest()
        _make_snapshot(tmp_path, "foo/bar", files)
        manifest = {"foo/bar": {"config.json": sha}}
        ok, problems = verify_model("foo/bar", manifest, tmp_path)
        assert ok
        assert problems == []

    def test_mismatch(self, tmp_path: Path) -> None:
        files = {"config.json": b"hello"}
        _make_snapshot(tmp_path, "foo/bar", files)
        manifest = {"foo/bar": {"config.json": "wrong"}}
        ok, problems = verify_model("foo/bar", manifest, tmp_path)
        assert not ok
        assert any("mismatch" in p for p in problems)

    def test_missing_snapshot(self, tmp_path: Path) -> None:
        manifest = {"foo/bar": {"config.json": "x"}}
        ok, problems = verify_model("foo/bar", manifest, tmp_path)
        assert not ok
        assert any("snapshot dir not found" in p for p in problems)
