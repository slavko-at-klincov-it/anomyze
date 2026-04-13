"""
Ensemble aggregation for multi-source entity detection.

When multiple detection layers (regex, NER, GLiNER) find overlapping
entities in the same text span, the ensemble merges them into a single
entity with a combined confidence score.

Aggregation: score = 1 - product(1 - score_i)
Each source is treated as an independent detector.
"""

from anomyze.pipeline import DetectedEntity


def merge_entities(
    entities: list[DetectedEntity], text: str
) -> list[DetectedEntity]:
    """Merge overlapping entities from multiple detection sources.

    Groups entities by overlapping text spans, then merges each group
    into a single entity with aggregated confidence.

    Args:
        entities: All detected entities from all pipeline layers.
        text: The original source text (used to extract words for
            merged spans).

    Returns:
        Deduplicated entities with ensemble confidence scores.
    """
    if not entities:
        return []

    # Sort by start position, then widest span first
    sorted_ents = sorted(
        entities, key=lambda e: (e.start, -(e.end - e.start))
    )

    # Group overlapping entities (sweep-line)
    groups: list[list[DetectedEntity]] = []
    current_group: list[DetectedEntity] = [sorted_ents[0]]
    current_end = sorted_ents[0].end

    for entity in sorted_ents[1:]:
        if entity.start < current_end:
            current_group.append(entity)
            current_end = max(current_end, entity.end)
        else:
            groups.append(current_group)
            current_group = [entity]
            current_end = entity.end
    groups.append(current_group)

    return [_merge_group(group, text) for group in groups]


def _merge_group(
    group: list[DetectedEntity], text: str
) -> DetectedEntity:
    """Merge a group of overlapping entities into one.

    Uses the union span for boundaries, highest-scoring entity's
    label, and combines confidence via 1 - product(1 - score_i).

    Args:
        group: Overlapping entities to merge.
        text: The original source text.

    Returns:
        Single merged entity.
    """
    if len(group) == 1:
        ent = group[0]
        return DetectedEntity(
            word=ent.word,
            entity_group=ent.entity_group,
            score=ent.score,
            start=ent.start,
            end=ent.end,
            source=ent.source,
            sources=(ent.source,),
            context=ent.context,
            anomaly_score=ent.anomaly_score,
        )

    # Combined confidence: 1 - product(1 - score_i)
    complement = 1.0
    for ent in group:
        complement *= 1.0 - ent.score
    combined_score = 1.0 - complement

    # Entity group: from highest individual score
    best = max(group, key=lambda e: e.score)

    # Span: union of all overlapping spans
    start = min(e.start for e in group)
    end = max(e.end for e in group)
    word = text[start:end]

    # All contributing sources (deduplicated, order-preserving)
    all_sources = tuple(dict.fromkeys(e.source for e in group))

    # Context/anomaly: preserve if any entity has it
    context = ""
    anomaly_score = 0.0
    for ent in group:
        if ent.context:
            context = ent.context
        if ent.anomaly_score > anomaly_score:
            anomaly_score = ent.anomaly_score

    return DetectedEntity(
        word=word,
        entity_group=best.entity_group,
        score=combined_score,
        start=start,
        end=end,
        source="ensemble" if len(all_sources) > 1 else all_sources[0],
        sources=all_sources,
        context=context,
        anomaly_score=anomaly_score,
    )
