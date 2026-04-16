"""
Post-anonymization quality check.

Verifies the anonymized output before it leaves the system:
- No regex-detectable PII (emails, IBANs, phone numbers, etc.) outside placeholders
- No anonymized entity words remaining in the output
- All placeholders follow the expected format

The check is a reporting gate — it flags issues but does not modify
the output. Callers decide whether to block, warn, or reprocess.
"""

import re
from dataclasses import dataclass, field

from anomyze.patterns import (
    find_emails_regex,
    find_ibans_regex,
    find_id_card_regex,
    find_license_plate_regex,
    find_passport_regex,
    find_phone_regex,
    find_svnr_regex,
    find_tax_number_regex,
)
from anomyze.patterns.at_names import is_at_firstname, is_at_lastname
from anomyze.pipeline import DetectedEntity

# Capitalised word of 3+ characters — token candidate for the AT name
# dictionary rescan. We only scan capitalised runs so common nouns
# like "Bank" don't flood the report.
_CAPITALISED_WORD = re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]{2,}\b")

# Matches any [...] placeholder in output
_PLACEHOLDER_RE = re.compile(r'\[[^\]]+\]')

# Valid placeholder formats:
# [TYPE_N]                — GovGPT/KAPA regular
# [PRÜFEN:TYPE_N]         — KAPA review flag
# [GESCHWÄRZT:TYPE]       — IFG (no numbering)
_VALID_PLACEHOLDER = re.compile(
    r'^\['
    r'(?:'
    r'GESCHWÄRZT:[A-ZÄÖÜ_]+'
    r'|PRÜFEN:[A-ZÄÖÜ_]+_\d+'
    r'|[A-ZÄÖÜ_]+_\d+'
    r')\]$'
)


@dataclass
class QualityIssue:
    """A single issue detected by the quality check.

    Attributes:
        type: Category of issue ("leak" or "format").
        pii_type: PII category (EMAIL, IBAN, PLACEHOLDER, etc.).
        position: Character offset in the output text.
        snippet: The offending text fragment.
        description: Human-readable description.
    """

    type: str
    pii_type: str
    position: int
    snippet: str
    description: str

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type,
            "pii_type": self.pii_type,
            "position": self.position,
            "snippet": self.snippet,
            "description": self.description,
        }


@dataclass
class QualityReport:
    """Result of a quality check on anonymized output.

    Attributes:
        passed: True if no issues were found.
        issues: All detected issues.
        leak_count: Number of leak-type issues (residual PII).
    """

    passed: bool
    issues: list[QualityIssue] = field(default_factory=list)
    leak_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "passed": self.passed,
            "leak_count": self.leak_count,
            "issues": [i.to_dict() for i in self.issues],
        }


# (pii_type, finder_fn) pairs used for regex-based leak detection
_LEAK_FINDERS = (
    ('EMAIL', find_emails_regex),
    ('IBAN', find_ibans_regex),
    ('SVN', find_svnr_regex),
    ('STEUERNUMMER', find_tax_number_regex),
    ('TELEFON', find_phone_regex),
    ('REISEPASS', find_passport_regex),
    ('PERSONALAUSWEIS', find_id_card_regex),
    ('KFZ', find_license_plate_regex),
)


def _placeholder_spans(text: str) -> list[tuple[int, int]]:
    """Return [(start, end), ...] for every [...] placeholder in text."""
    return [(m.start(), m.end()) for m in _PLACEHOLDER_RE.finditer(text)]


def _is_inside(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    """Check whether a range is contained in any placeholder span."""
    return any(ps <= start and end <= pe for ps, pe in spans)


def check_output(
    text: str,
    entities: list[DetectedEntity],
) -> QualityReport:
    """Run post-anonymization quality checks.

    Args:
        text: The anonymized output text (with placeholders).
        entities: All detection entities; used to check that
            anonymized words (those with .placeholder set) do not
            still appear in the output.

    Returns:
        QualityReport with any issues found.
    """
    issues: list[QualityIssue] = []
    spans = _placeholder_spans(text)

    # 1. Regex-based leak detection (outside placeholders)
    for leak_type, finder in _LEAK_FINDERS:
        for ent in finder(text):
            if _is_inside(ent.start, ent.end, spans):
                continue
            issues.append(QualityIssue(
                type='leak',
                pii_type=leak_type,
                position=ent.start,
                snippet=ent.word,
                description=f"{leak_type} still present in output",
            ))

    # 2. Anonymized entity word presence check
    seen: set[str] = set()
    for ent in entities:
        if not ent.placeholder:
            continue
        word = ent.word.strip()
        if not word or word.lower() in seen:
            continue
        seen.add(word.lower())

        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        for m in pattern.finditer(text):
            if _is_inside(m.start(), m.end(), spans):
                continue
            issues.append(QualityIssue(
                type='leak',
                pii_type=ent.entity_group,
                position=m.start(),
                snippet=m.group(),
                description=f"Anonymized entity '{word}' remains in output",
            ))
            break  # One issue per unique entity word is enough

    # 3. Placeholder format validation
    for ps, pe in spans:
        placeholder = text[ps:pe]
        if not _VALID_PLACEHOLDER.match(placeholder):
            issues.append(QualityIssue(
                type='format',
                pii_type='PLACEHOLDER',
                position=ps,
                snippet=placeholder,
                description=f"Malformed placeholder: {placeholder}",
            ))

    # 4. Name-dictionary rescan — catches residual names that slipped
    # through ML layers and are not yet in the anonymized-entity set
    # (e.g., introduced by post-anonymization smoothing). Only runs
    # when at least one placeholder is present; otherwise no
    # anonymization took place and the ordinary entity-word check
    # already covers pre-anonymization input.
    anonymization_happened = bool(spans) or any(e.placeholder for e in entities)
    if anonymization_happened:
        issues.extend(_check_name_dict_leakage(text, spans))

    leak_count = sum(1 for i in issues if i.type == 'leak')
    return QualityReport(
        passed=len(issues) == 0,
        issues=issues,
        leak_count=leak_count,
    )


def _check_name_dict_leakage(
    text: str,
    spans: list[tuple[int, int]],
) -> list[QualityIssue]:
    """Flag capitalised tokens that match the AT name dictionary.

    Strategy:

    * ``leak``: two consecutive tokens where the first is an AT
      first-name and the second an AT last-name (or vice-versa) —
      this is an unambiguous personal identifier.
    * ``warn``: a single token that is in both lists (ambiguous
      name / surname) or a token that is a surname only. Surfaced
      so reviewers can look but not counted as a hard leak.
    """
    issues: list[QualityIssue] = []
    matches = list(_CAPITALISED_WORD.finditer(text))
    tagged: list[tuple[int, int, str, bool, bool]] = []
    for match in matches:
        if _is_inside(match.start(), match.end(), spans):
            continue
        word = match.group()
        is_first = is_at_firstname(word)
        is_last = is_at_lastname(word)
        if not (is_first or is_last):
            continue
        tagged.append((match.start(), match.end(), word, is_first, is_last))

    flagged_positions: set[int] = set()

    # Pairwise scan: adjacent (first, last) or (last, first) → leak.
    for i, (start, end, word, is_f, is_l) in enumerate(tagged):
        if i + 1 >= len(tagged):
            continue
        n_start, n_end, n_word, n_f, n_l = tagged[i + 1]
        if n_start - end > 3:  # only truly adjacent tokens
            continue
        pair_is_leak = (is_f and n_l) or (is_l and n_f)
        if pair_is_leak:
            issues.append(QualityIssue(
                type="leak",
                pii_type="PER_DICT",
                position=start,
                snippet=f"{word} {n_word}",
                description=(
                    f"AT name dictionary match in output: "
                    f"'{word} {n_word}'"
                ),
            ))
            flagged_positions.add(start)
            flagged_positions.add(n_start)

    # Single-token warnings (not counted as leaks).
    for start, _end, word, is_f, is_l in tagged:
        if start in flagged_positions:
            continue
        # Last-name alone is a stronger signal than first-name alone.
        if is_l and not is_f:
            issues.append(QualityIssue(
                type="warn",
                pii_type="PER_DICT",
                position=start,
                snippet=word,
                description=f"Possible AT surname in output: '{word}'",
            ))

    return issues
