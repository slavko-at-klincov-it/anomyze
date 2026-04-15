"""Tests for the benchmark regression gate."""

from anomyze.benchmark.regression_check import compare


def _report(overall_f1: float, **cats: dict) -> dict:
    by_category: dict[str, dict] = {}
    for name, payload in cats.items():
        by_category[name] = payload
    return {
        "num_samples": 1,
        "overall": {"f1": overall_f1, "precision": overall_f1, "recall": overall_f1,
                    "tp": 0, "fp": 0, "fn": 0},
        "by_category": by_category,
        "by_layer": {},
    }


class TestCompare:
    def _full_cats(self, recall: float = 0.99) -> dict:
        payload = {"recall": recall, "precision": recall, "f1": recall,
                   "tp": 1, "fp": 0, "fn": 0}
        return {"SVN": dict(payload), "IBAN": dict(payload), "EMAIL": dict(payload)}

    def test_no_change_passes(self) -> None:
        base = _report(0.9, **self._full_cats())
        cur = _report(0.9, **self._full_cats())
        ok, problems = compare(base, cur)
        assert ok and problems == []

    def test_abs_drop_fails(self) -> None:
        base = _report(0.9, **self._full_cats())
        cur = _report(0.85, **self._full_cats())
        ok, problems = compare(base, cur, abs_drop=0.02)
        assert not ok
        assert any("F1 dropped" in p for p in problems)

    def test_critical_recall_fail(self) -> None:
        base = _report(0.9, **self._full_cats())
        cats = self._full_cats()
        cats["IBAN"]["recall"] = 0.5
        cur = _report(0.9, **cats)
        ok, problems = compare(base, cur)
        assert not ok
        assert any("IBAN" in p for p in problems)

    def test_custom_critical_list(self) -> None:
        base = _report(0.9)
        cur = _report(0.9, FOO={"recall": 0.5, "precision": 0.5, "f1": 0.5,
                                 "tp": 0, "fp": 0, "fn": 0})
        ok, problems = compare(base, cur, critical=("FOO",))
        assert not ok
