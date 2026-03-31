"""
Entity processing utilities for the Anomyze pipeline.

Provides shared utility functions used by all pipeline layers
for word boundary expansion, entity cleaning, normalization,
and overlap detection.
"""



def expand_to_word_boundaries(text: str, start: int, end: int) -> tuple[int, int]:
    """Expand start/end to cover the full word, not just a subword token.

    Args:
        text: The full source text.
        start: Current start position.
        end: Current end position.

    Returns:
        Tuple of (expanded_start, expanded_end).
    """
    while start > 0 and text[start - 1].isalnum():
        start -= 1
    while end < len(text) and text[end].isalnum():
        end += 1
    return start, end


def clean_entity_word(word: str, text: str, start: int, end: int) -> tuple[str, int, int]:
    """Fix subword tokens and clean up entity boundaries.

    Expands to full word boundaries, strips whitespace, removes leading
    articles and common German prefix words, and removes trailing punctuation.

    Args:
        word: The detected entity word.
        text: The full source text.
        start: Start position in text.
        end: End position in text.

    Returns:
        Tuple of (cleaned_word, new_start, new_end).
    """
    # Always expand to full word boundaries
    new_start, new_end = expand_to_word_boundaries(text, start, end)
    expanded_word = text[new_start:new_end]

    # If expanded word is different and longer, use it
    if len(expanded_word) > len(word.strip()) and expanded_word.strip():
        word = expanded_word
        start = new_start
        end = new_end

    # Strip leading/trailing whitespace and adjust positions
    original_word = word
    word = word.strip()
    if word != original_word:
        # Find actual start position of stripped word in text
        offset = original_word.index(word) if word in original_word else 0
        start = start + offset
        end = start + len(word)

    # Remove leading articles and common prefix words
    prefixes_to_remove = [
        'der ', 'die ', 'das ', 'dem ', 'den ', 'von ', 'vom ', 'unter ',
        'ist ', 'sind ', 'war ', 'waren ', 'wird ', 'werden ',
        'hat ', 'haben ', 'hatte ', 'hatten ',
        'und ', 'oder ', 'aber ', 'auch ',
        'herrn ', 'frau ', 'herr ',
        'kollegen ', 'kollegin ', 'kollege ',
        'ehemaligen ', 'ehemaliger ', 'ehemalige ',
        'unseren ', 'unsere ', 'unser ', 'unserem ',
    ]

    changed = True
    while changed:
        changed = False
        for prefix in prefixes_to_remove:
            if word.lower().startswith(prefix):
                word = word[len(prefix):]
                start = start + len(prefix)
                changed = True
                break

    # Remove trailing punctuation that got included
    while word and word[-1] in '.,;:!?)':
        word = word[:-1]
        end -= 1

    return word, start, end


def normalize_entity(word: str) -> str:
    """Normalize entity for deduplication (lowercase, stripped)."""
    return word.lower().strip()


def entities_overlap(e1_start: int, e1_end: int, e2_start: int, e2_end: int) -> bool:
    """Check if two entity spans overlap.

    Args:
        e1_start: Start of first entity.
        e1_end: End of first entity.
        e2_start: Start of second entity.
        e2_end: End of second entity.

    Returns:
        True if the spans overlap.
    """
    return not (e1_end <= e2_start or e1_start >= e2_end)
