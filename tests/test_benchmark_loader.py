"""Unit tests for benchmark dataset loader."""

import json
from pathlib import Path

import pytest

from anomyze.benchmark.loader import DatasetLoadError, load_dataset


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_loads_valid_dataset(tmp_path: Path) -> None:
    data = [
        {
            "id": "s1",
            "text": "Kontakt: a@b.at",
            "entities": [{"start": 9, "end": 15, "type": "EMAIL"}],
        },
        {"id": "s2", "text": "Hallo", "entities": []},
    ]
    path = _write(tmp_path, data)

    samples = load_dataset(path)

    assert len(samples) == 2
    assert samples[0].id == "s1"
    assert samples[0].text == "Kontakt: a@b.at"
    assert len(samples[0].entities) == 1
    assert samples[0].entities[0].start == 9
    assert samples[0].entities[0].end == 15
    assert samples[0].entities[0].type == "EMAIL"
    assert samples[1].entities == []


def test_empty_dataset_yields_empty_list(tmp_path: Path) -> None:
    path = _write(tmp_path, [])
    assert load_dataset(path) == []


def test_rejects_non_list_root(tmp_path: Path) -> None:
    path = _write(tmp_path, {"id": "s1"})
    with pytest.raises(DatasetLoadError):
        load_dataset(path)


def test_rejects_missing_sample_fields(tmp_path: Path) -> None:
    path = _write(tmp_path, [{"id": "s1", "text": "x"}])
    with pytest.raises(DatasetLoadError):
        load_dataset(path)


def test_rejects_out_of_range_span(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        [
            {
                "id": "s1",
                "text": "abc",
                "entities": [{"start": 0, "end": 99, "type": "EMAIL"}],
            }
        ],
    )
    with pytest.raises(DatasetLoadError):
        load_dataset(path)


def test_rejects_inverted_span(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        [
            {
                "id": "s1",
                "text": "abcdef",
                "entities": [{"start": 5, "end": 2, "type": "EMAIL"}],
            }
        ],
    )
    with pytest.raises(DatasetLoadError):
        load_dataset(path)


def test_rejects_empty_type(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        [
            {
                "id": "s1",
                "text": "abcdef",
                "entities": [{"start": 0, "end": 3, "type": ""}],
            }
        ],
    )
    with pytest.raises(DatasetLoadError):
        load_dataset(path)
