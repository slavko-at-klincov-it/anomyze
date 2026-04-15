"""Tests for the synthetic AT benchmark generator."""

from anomyze.benchmark.generators.at import generate
from stdnum import iban as stdnum_iban
from stdnum.at import uid as stdnum_uid
from stdnum.at import vnr as stdnum_vnr


class TestGenerate:
    def test_count_returned(self) -> None:
        samples = generate(20, seed=0)
        assert len(samples) == 20

    def test_deterministic(self) -> None:
        a = generate(10, seed=42)
        b = generate(10, seed=42)
        assert a == b

    def test_different_seeds_diverge(self) -> None:
        a = generate(10, seed=0)
        b = generate(10, seed=1)
        assert a != b

    def test_spans_align(self) -> None:
        for sample in generate(40, seed=7):
            for entity in sample["entities"]:
                slice_ = sample["text"][entity["start"]:entity["end"]]
                assert slice_, f"empty slice in {sample['id']}"

    def test_checksums_valid(self) -> None:
        # Every IBAN/SVNR/UID emitted by the generator must pass its
        # canonical checksum — that's the whole point of generating
        # them via stdnum.
        for sample in generate(40, seed=11):
            for entity in sample["entities"]:
                slice_ = sample["text"][entity["start"]:entity["end"]]
                if entity["type"] == "IBAN":
                    assert stdnum_iban.is_valid(slice_), slice_
                elif entity["type"] == "SVN":
                    assert stdnum_vnr.is_valid(slice_), slice_
                elif entity["type"] == "UID":
                    assert stdnum_uid.is_valid(slice_), slice_
