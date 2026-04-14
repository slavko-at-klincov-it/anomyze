"""
Recognizer abstraction inspired by Microsoft Presidio's PatternRecognizer.

Provides a Presidio-compatible API without depending on the
presidio-analyzer package, allowing future migration to actual
Presidio if needed.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Pattern:
    """A single regex pattern with name and base score.

    Mirrors presidio_analyzer.Pattern.

    Attributes:
        name: Identifier for this pattern (for debugging).
        regex: The regex string.
        score: Base confidence (0.0–1.0) when this pattern matches.
    """

    name: str
    regex: str
    score: float


@dataclass
class RecognizerResult:
    """Result of pattern matching by a recognizer.

    Mirrors presidio_analyzer.RecognizerResult.

    Attributes:
        entity_type: The PII type detected (e.g., "AT_SVNR").
        start: Start offset in the source text.
        end: End offset in the source text.
        score: Final confidence (after context boost).
        text: The matched text fragment.
        recognizer_name: Class name of the recognizer that produced this.
    """

    entity_type: str
    start: int
    end: int
    score: float
    text: str
    recognizer_name: str = ""


class PatternRecognizer:
    """Base class for pattern-based recognizers.

    Subclasses set:
        supported_entity: PII type this recognizer detects.
        patterns: List of Pattern objects (regexes with base scores).
        context: Words that, when nearby, boost the confidence score.
        context_boost: How much to boost score when context is found.
        context_window: Characters around match to scan for context.

    Subclasses may override _is_valid_match for post-pattern validation
    (e.g., checksum, date validity).
    """

    supported_entity: str = ""
    patterns: list[Pattern] = []
    context: list[str] = []
    context_boost: float = 0.2
    context_window: int = 50

    def __init__(self) -> None:
        self._compiled: list[tuple[re.Pattern[str], Pattern]] = [
            (re.compile(p.regex, re.IGNORECASE), p) for p in self.patterns
        ]

    def analyze(self, text: str) -> list[RecognizerResult]:
        """Apply all patterns and return matches with confidence scores.

        Args:
            text: The input text to scan.

        Returns:
            One RecognizerResult per valid match.
        """
        results: list[RecognizerResult] = []
        for compiled, pattern in self._compiled:
            for match in compiled.finditer(text):
                matched = match.group()
                if not self._is_valid_match(matched, text, match.start(), match.end()):
                    continue

                score = pattern.score
                if self._has_context(text, match.start(), match.end()):
                    score = min(1.0, score + self.context_boost)

                results.append(RecognizerResult(
                    entity_type=self.supported_entity,
                    start=match.start(),
                    end=match.end(),
                    score=score,
                    text=matched,
                    recognizer_name=type(self).__name__,
                ))
        return results

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        """Override to add post-pattern validation. Default: accept."""
        return True

    def _has_context(self, text: str, start: int, end: int) -> bool:
        """Check whether any context word appears near the match."""
        if not self.context:
            return False
        win_start = max(0, start - self.context_window)
        win_end = min(len(text), end + self.context_window)
        window = text[win_start:win_end].lower()
        return any(c.lower() in window for c in self.context)
