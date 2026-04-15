"""
Dataset loader for benchmark framework.

Reads JSON files with annotated PII samples and returns typed
Sample/GroundTruthEntity records for consumption by the evaluator.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GroundTruthEntity:
    """A single annotated PII span in a benchmark sample.

    Attributes:
        start: Character offset of the entity start in the sample text.
        end: Character offset of the entity end (exclusive).
        type: Entity category (EMAIL, IBAN, SVN, PER, ADRESSE, ...).
    """

    start: int
    end: int
    type: str


@dataclass
class Sample:
    """A benchmark sample with text and ground-truth annotations.

    Attributes:
        id: Unique identifier of the sample.
        text: The sample text.
        entities: List of annotated PII spans.
    """

    id: str
    text: str
    entities: list[GroundTruthEntity]


class DatasetLoadError(ValueError):
    """Raised when a dataset file has an invalid schema."""


def _validate_entity(raw: object, sample_id: str, text_len: int) -> GroundTruthEntity:
    if not isinstance(raw, dict):
        raise DatasetLoadError(
            f"Sample {sample_id!r}: entity must be an object, got {type(raw).__name__}"
        )

    missing = {"start", "end", "type"} - raw.keys()
    if missing:
        raise DatasetLoadError(
            f"Sample {sample_id!r}: entity missing fields: {sorted(missing)}"
        )

    start = raw["start"]
    end = raw["end"]
    etype = raw["type"]

    if not isinstance(start, int) or not isinstance(end, int):
        raise DatasetLoadError(
            f"Sample {sample_id!r}: entity start/end must be int"
        )
    if not isinstance(etype, str) or not etype:
        raise DatasetLoadError(
            f"Sample {sample_id!r}: entity type must be a non-empty string"
        )
    if start < 0 or end > text_len or start >= end:
        raise DatasetLoadError(
            f"Sample {sample_id!r}: invalid span [{start}:{end}] "
            f"for text of length {text_len}"
        )

    return GroundTruthEntity(start=start, end=end, type=etype)


def _validate_sample(raw: object) -> Sample:
    if not isinstance(raw, dict):
        raise DatasetLoadError(
            f"Sample entry must be an object, got {type(raw).__name__}"
        )

    missing = {"id", "text", "entities"} - raw.keys()
    if missing:
        raise DatasetLoadError(f"Sample missing fields: {sorted(missing)}")

    sample_id = raw["id"]
    text = raw["text"]
    entities_raw = raw["entities"]

    if not isinstance(sample_id, str) or not sample_id:
        raise DatasetLoadError("Sample id must be a non-empty string")
    if not isinstance(text, str):
        raise DatasetLoadError(f"Sample {sample_id!r}: text must be a string")
    if not isinstance(entities_raw, list):
        raise DatasetLoadError(
            f"Sample {sample_id!r}: entities must be a list"
        )

    entities = [_validate_entity(e, sample_id, len(text)) for e in entities_raw]
    return Sample(id=sample_id, text=text, entities=entities)


def load_dataset(path: Path | str) -> list[Sample]:
    """Load a benchmark dataset from a JSON file.

    Args:
        path: Path to the dataset JSON file.

    Returns:
        List of parsed Sample records.

    Raises:
        DatasetLoadError: If the file does not follow the schema.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    if not isinstance(raw, list):
        raise DatasetLoadError(
            f"Dataset root must be a JSON list, got {type(raw).__name__}"
        )

    return [_validate_sample(entry) for entry in raw]
