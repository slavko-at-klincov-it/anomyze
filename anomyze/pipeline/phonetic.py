"""
Cologne Phonetic (Kölner Phonetik) — phonetic encoding for German.

Designed by Hans Joachim Postel (1969). More accurate than Soundex
for German-language PII matching. Returns a short digit string such
that similar-sounding German words produce the same or similar codes.

Examples:
    Meier, Mayer, Maier, Meyer → "67"
    Müller               → "657"
    Schmidt              → "862"
"""


def cologne_phonetic(text: str) -> str:
    """Encode a string using the Kölner Phonetik algorithm.

    Args:
        text: The input string (typically a name).

    Returns:
        Phonetic code (digits only). Empty string for empty/non-letter input.
    """
    if not text:
        return ""

    # Normalize umlauts and ß for the letter-by-letter rules
    s = (
        text.upper()
        .replace("Ä", "A")
        .replace("Ö", "O")
        .replace("Ü", "U")
        .replace("ß", "S")
    )

    # Keep only A-Z
    chars = [c for c in s if "A" <= c <= "Z"]
    n = len(chars)
    if n == 0:
        return ""

    codes: list[str] = []
    i = 0
    while i < n:
        c = chars[i]
        prev = chars[i - 1] if i > 0 else ""
        nxt = chars[i + 1] if i < n - 1 else ""

        # Helper membership tests use `len == 1` guards because Python's
        # `"" in "XYZ"` evaluates to True (empty string is a substring).
        if c in "AEIJOUY":
            codes.append("0")
        elif c == "H":
            pass  # silent
        elif c == "B":
            codes.append("1")
        elif c == "P":
            if nxt == "H":
                codes.append("3")
                i += 1  # consume the silent H
            else:
                codes.append("1")
        elif c in "DT":
            codes.append("8" if (nxt and nxt in "CSZ") else "2")
        elif c in "FVW":
            codes.append("3")
        elif c in "GKQ":
            codes.append("4")
        elif c == "C":
            if i == 0:
                codes.append("4" if (nxt and nxt in "AHKLOQRUX") else "8")
            else:
                if prev in "SZ":
                    codes.append("8")
                else:
                    codes.append("4" if (nxt and nxt in "AHKOQUX") else "8")
        elif c == "X":
            codes.append("8" if (prev and prev in "CKQ") else "48")
        elif c == "L":
            codes.append("5")
        elif c in "MN":
            codes.append("6")
        elif c == "R":
            codes.append("7")
        elif c in "SZ":
            codes.append("8")

        i += 1

    # Flatten to digit string
    digits = "".join(codes)
    if not digits:
        return ""

    # Collapse consecutive duplicate digits
    collapsed = [digits[0]]
    for d in digits[1:]:
        if d != collapsed[-1]:
            collapsed.append(d)

    # Remove all '0' except at the very start
    head, *rest = collapsed
    result = [head] + [d for d in rest if d != "0"]

    return "".join(result)


def phonetic_equal(a: str, b: str) -> bool:
    """Return True if two strings encode to the same Cologne phonetic code."""
    return cologne_phonetic(a) == cologne_phonetic(b)
