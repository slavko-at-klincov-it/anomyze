"""
Austrian first and last name data resources.

Small curated dictionaries of common Austrian given and family names
used as an additional signal for PII detection and entity resolution.
Includes a pre-computed Kölner Phonetik index for fuzzy matching.

Sources: Statistik Austria name ranking (common Austrian first/last names).
Not exhaustive — used as confidence boost, never as hard allow/block list.
"""

from anomyze.pipeline.phonetic import cologne_phonetic

# Common Austrian first names (male + female, historical + modern).
AT_FIRST_NAMES: frozenset[str] = frozenset(map(str.lower, {
    # Male — common
    "Karl", "Johann", "Franz", "Josef", "Michael", "Thomas", "Stefan",
    "Christian", "Markus", "Andreas", "Martin", "Peter", "Wolfgang",
    "Robert", "Christoph", "Gerhard", "Manfred", "Friedrich", "Hans",
    "Werner", "Klaus", "Alexander", "Daniel", "David", "Lukas",
    "Maximilian", "Tobias", "Jakob", "Leon", "Elias", "Florian",
    "Sebastian", "Matthias", "Patrick", "Philipp", "Simon", "Raphael",
    "Felix", "Niklas", "Paul", "Jonas", "Moritz", "Benjamin", "Leo",
    "Fabian", "Dominik", "Marcel", "Julian", "Samuel", "Herbert",
    "Rudolf", "Walter", "Gottfried", "Helmut", "Ernst", "Kurt", "Leopold",
    # Female — common
    "Maria", "Anna", "Johanna", "Elisabeth", "Barbara", "Brigitte",
    "Helga", "Christine", "Gertrude", "Erika", "Ingrid", "Gabriele",
    "Ursula", "Monika", "Renate", "Sonja", "Andrea", "Sabine", "Karin",
    "Daniela", "Martina", "Sandra", "Katrin", "Melanie", "Julia", "Lisa",
    "Sarah", "Laura", "Lena", "Hannah", "Emma", "Sophie", "Marie", "Lea",
    "Emilia", "Mia", "Lina", "Nina", "Theresa", "Magdalena", "Nora",
    "Valentina", "Elena", "Katharina", "Eva", "Susanne", "Silvia",
    "Petra", "Heidi", "Angela", "Claudia", "Ulrike", "Irene", "Beate",
    "Waltraud", "Margarete", "Hildegard", "Hermine", "Franziska",
}))

# Common Austrian last names.
AT_LAST_NAMES: frozenset[str] = frozenset(map(str.lower, {
    "Gruber", "Huber", "Bauer", "Wagner", "Müller", "Pichler", "Steiner",
    "Moser", "Mayer", "Hofer", "Leitner", "Berger", "Fuchs", "Eder",
    "Fischer", "Schmidt", "Weber", "Winkler", "Schwarz", "Maier",
    "Reiter", "Schuster", "Lang", "Baumgartner", "Wolf", "Haas",
    "Brunner", "Lehner", "Stadler", "Egger", "Auer", "Strasser",
    "Koller", "Ebner", "Aigner", "Schneider", "Wimmer", "Binder",
    "Lackner", "Hauser", "Graf", "Fellner", "Lindner", "Riedl",
    "Zimmermann", "Schwaiger", "Köck", "Koch", "Prinz", "Seidl",
    "Schachner", "Payer", "Pöll", "Zauner", "Jäger", "Bachler",
    "Bichler", "Neumann", "Meier", "Meyer", "Heinzl", "Kern",
    "Puchner", "Weiß", "Pachler", "Klammer", "Raab", "Pfeifer",
    "Resch", "Ortner", "Mitterer", "Zehetner", "Reisinger",
    "Kogler", "Schreiner", "Weissenbacher", "Langer", "Zechmeister",
    "Holzer", "Buchner", "Rieder", "Gartner", "Höfer", "Kraus",
    "Herzog", "Unger", "Neuhold", "Wastl", "Schober", "Gasser",
    "Pucher", "Grill", "Hofbauer", "Rauch", "Aumayr",
}))


def _build_phonetic_index(names: frozenset[str]) -> dict[str, frozenset[str]]:
    """Build {phonetic_code: names} mapping for fuzzy lookup."""
    index: dict[str, set[str]] = {}
    for name in names:
        code = cologne_phonetic(name)
        if code:
            index.setdefault(code, set()).add(name)
    return {k: frozenset(v) for k, v in index.items()}


_FIRST_NAME_PHONETIC = _build_phonetic_index(AT_FIRST_NAMES)
_LAST_NAME_PHONETIC = _build_phonetic_index(AT_LAST_NAMES)


def is_at_firstname(name: str) -> bool:
    """Return True if `name` matches an AT first name (case-insensitive)."""
    return name.lower().strip() in AT_FIRST_NAMES


def is_at_lastname(name: str) -> bool:
    """Return True if `name` matches an AT last name (case-insensitive)."""
    return name.lower().strip() in AT_LAST_NAMES


def phonetic_match_firstname(name: str) -> frozenset[str]:
    """Return AT first names with the same Kölner Phonetik code as `name`.

    Useful for matching misspellings or locale variants
    (e.g. "Mueller" matches "Müller" via the same phonetic code).
    """
    code = cologne_phonetic(name)
    if not code:
        return frozenset()
    return _FIRST_NAME_PHONETIC.get(code, frozenset())


def phonetic_match_lastname(name: str) -> frozenset[str]:
    """Return AT last names with the same Kölner Phonetik code as `name`."""
    code = cologne_phonetic(name)
    if not code:
        return frozenset()
    return _LAST_NAME_PHONETIC.get(code, frozenset())


def is_at_name(name: str) -> bool:
    """Return True if `name` matches either an AT first or last name."""
    return is_at_firstname(name) or is_at_lastname(name)
