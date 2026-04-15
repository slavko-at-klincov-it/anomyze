"""Synthetic Austrian benchmark-sample generator.

Produces JSON samples in the schema consumed by
``anomyze.benchmark.loader`` — a flat list of ``{id, text, entities}``
objects where each entity carries ``{start, end, type}``.

Design notes
------------

We intentionally avoid pulling in ``faker`` as a runtime dependency:
the Austrian PII types we care about (SVNR with real check digits,
UID with MOD-11 check digit, KFZ with valid district prefixes,
Geschäftszahl / Aktenzahl in the shape that Behörden actually use)
are not available in ``faker[de_AT]`` out of the box. Implementing
them here keeps the dependency surface small and lets the generator
fall back on :mod:`stdnum` for checksum-valid identifiers.

The generator is deterministic by default (``seed=0``) so benchmark
regressions are reproducible.

CLI:

    python -m anomyze.benchmark.generators.at --out smoke.json --count 50
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

from stdnum import iban as stdnum_iban
from stdnum.at import uid as stdnum_uid
from stdnum.at import vnr as stdnum_vnr

from anomyze.patterns.at_names import AT_FIRST_NAMES, AT_LAST_NAMES

# Austrian KFZ prefixes — subset of the official list. Keep it short
# for the generator; the recognizer covers the full list separately.
_KFZ_PREFIXES = ("W", "G", "L", "S", "IL", "KB", "SL", "LI", "BR", "VB")

_AT_CITIES = (
    ("Wien", "1010"), ("Wien", "1070"), ("Wien", "1120"),
    ("Graz", "8010"), ("Linz", "4020"), ("Salzburg", "5020"),
    ("Innsbruck", "6020"), ("Klagenfurt", "9020"), ("Bregenz", "6900"),
    ("Eisenstadt", "7000"), ("St. Pölten", "3100"),
)

_AT_STREETS = (
    "Hauptstraße", "Mariahilferstraße", "Ringstraße", "Bahnhofstraße",
    "Landstraße", "Kärntner Straße", "Herrengasse", "Schottengasse",
    "Opernring", "Burggasse",
)


def _random_svnr(rng: random.Random) -> str:
    """Return a checksum-valid 10-digit AT SVNR (``NNNN DDMMYY``)."""
    while True:
        day = rng.randint(1, 28)
        month = rng.randint(1, 12)
        year = rng.randint(40, 99)
        date_part = f"{day:02d}{month:02d}{year:02d}"
        for running in range(10000):
            cand = f"{running:04d}{date_part}"
            if stdnum_vnr.is_valid(cand):
                return f"{cand[:4]} {cand[4:]}"


def _random_iban(rng: random.Random) -> str:
    """Return a checksum-valid AT IBAN with a random BBAN."""
    bban_digits = ''.join(str(rng.randint(0, 9)) for _ in range(16))
    for cd in range(100):
        cand = f"AT{cd:02d}{bban_digits}"
        if stdnum_iban.is_valid(cand):
            return (
                f"AT{cd:02d} {bban_digits[:4]} {bban_digits[4:8]} "
                f"{bban_digits[8:12]} {bban_digits[12:]}"
            )
    raise RuntimeError("no valid IBAN found")


def _random_uid(rng: random.Random) -> str:
    """Return a checksum-valid AT UID (``ATU`` + 8 digits)."""
    while True:
        body = ''.join(str(rng.randint(0, 9)) for _ in range(8))
        cand = f"ATU{body}"
        if stdnum_uid.is_valid(cand):
            return cand


def _random_kfz(rng: random.Random) -> str:
    prefix = rng.choice(_KFZ_PREFIXES)
    digits = rng.randint(1, 9999)
    suffix = ''.join(rng.choice("ABCDEFGHJKLMNOPRSTUVWX") for _ in range(rng.randint(1, 3)))
    return f"{prefix}-{digits}{suffix}"


def _random_name(rng: random.Random) -> tuple[str, str]:
    first = rng.choice(sorted(AT_FIRST_NAMES)).title()
    last = rng.choice(sorted(AT_LAST_NAMES)).title()
    return first, last


def _random_address(rng: random.Random) -> str:
    street = rng.choice(_AT_STREETS)
    nr = rng.randint(1, 199)
    city, plz = rng.choice(_AT_CITIES)
    return f"{street} {nr}, {plz} {city}"


def _random_gz(rng: random.Random) -> str:
    dept = rng.choice(["BMI", "BMF", "BMJ", "BKA"])
    year = rng.randint(2018, 2025)
    num = rng.randint(100, 9999)
    sub = rng.choice(["I", "II", "III", "IV", "V"])
    sub_num = rng.randint(1, 20)
    return f"GZ {year}/{num}-{sub}/{sub_num}"


@dataclass
class _Sample:
    id: str
    text: str
    entities: list[dict]

    def to_dict(self) -> dict:
        return {"id": self.id, "text": self.text, "entities": self.entities}


def _emit(prefix: str, text: str, spans: list[tuple[str, str]]) -> _Sample:
    """Build a sample by scanning spans in render order."""
    entities: list[dict] = []
    cursor = 0
    for value, etype in spans:
        idx = text.find(value, cursor)
        if idx == -1:
            raise RuntimeError(f"Span {value!r} not found in rendered text")
        entities.append({"start": idx, "end": idx + len(value), "type": etype})
        cursor = idx + len(value)
    return _Sample(id=prefix, text=text, entities=entities)


def _tmpl_bescheid(rng: random.Random, i: int) -> _Sample:
    first, last = _random_name(rng)
    name = f"{first} {last}"
    gz = _random_gz(rng)
    addr = _random_address(rng)
    svnr = _random_svnr(rng)
    iban = _random_iban(rng)
    text = (
        f"BESCHEID, Geschäftszahl {gz}.\n"
        f"Sehr geehrte Frau {name}, wohnhaft {addr}.\n"
        f"Ihre Sozialversicherungsnummer {svnr} und Konto {iban} wurden vermerkt."
    )
    return _emit(
        f"gen-bescheid-{i:04d}",
        text,
        [(gz, "AKTENZAHL"), (name, "PER"), (addr, "ADRESSE"),
         (svnr, "SVN"), (iban, "IBAN")],
    )


def _tmpl_ladung(rng: random.Random, i: int) -> _Sample:
    first, last = _random_name(rng)
    name = f"{first} {last}"
    gz = _random_gz(rng)
    addr = _random_address(rng)
    kfz = _random_kfz(rng)
    text = (
        f"LADUNG zur Geschäftszahl {gz}. Herr {name}, {addr}, "
        f"wird als Beschuldigter vorgeladen. Fahrzeug {kfz} wurde sichergestellt."
    )
    return _emit(
        f"gen-ladung-{i:04d}",
        text,
        [(gz, "AKTENZAHL"), (name, "PER"), (addr, "ADRESSE"), (kfz, "KFZ")],
    )


def _tmpl_rechnung(rng: random.Random, i: int) -> _Sample:
    first, last = _random_name(rng)
    name = f"{first} {last}"
    uid = _random_uid(rng)
    iban = _random_iban(rng)
    email = f"{first.lower()}.{last.lower()}@example.at"
    text = (
        f"Rechnung an {name} (UID: {uid}).\n"
        f"Bitte überweisen auf {iban}. Rückfragen: {email}."
    )
    return _emit(
        f"gen-rechnung-{i:04d}",
        text,
        [(name, "PER"), (uid, "UID"), (iban, "IBAN"), (email, "EMAIL")],
    )


def _tmpl_protokoll(rng: random.Random, i: int) -> _Sample:
    first1, last1 = _random_name(rng)
    first2, last2 = _random_name(rng)
    name1 = f"{first1} {last1}"
    name2 = f"{first2} {last2}"
    addr = _random_address(rng)
    svnr = _random_svnr(rng)
    phone = f"+43 {rng.choice([664, 676, 660, 699])} {rng.randint(1000000, 9999999)}"
    text = (
        f"PROTOKOLL: Vernehmungsleiter {name1}. Zeugin: {name2}, wohnhaft {addr}, "
        f"SVNR {svnr}, erreichbar unter {phone}."
    )
    return _emit(
        f"gen-protokoll-{i:04d}",
        text,
        [(name1, "PER"), (name2, "PER"), (addr, "ADRESSE"),
         (svnr, "SVN"), (phone, "TELEFON")],
    )


_TEMPLATES = (_tmpl_bescheid, _tmpl_ladung, _tmpl_rechnung, _tmpl_protokoll)


def generate(count: int, seed: int = 0) -> list[dict]:
    """Return ``count`` synthetic samples (round-robin templates)."""
    rng = random.Random(seed)
    samples: list[dict] = []
    for i in range(count):
        template = _TEMPLATES[i % len(_TEMPLATES)]
        samples.append(template(rng, i).to_dict())
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic AT benchmark samples",
    )
    parser.add_argument("--out", type=Path, required=True,
                        help="Output JSON path")
    parser.add_argument("--count", type=int, default=50,
                        help="Number of samples (default: 50)")
    parser.add_argument("--seed", type=int, default=0,
                        help="Random seed (default: 0)")
    args = parser.parse_args()

    samples = generate(args.count, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(samples, ensure_ascii=False, indent=2))
    print(f"Wrote {len(samples)} samples to {args.out}")


if __name__ == "__main__":  # pragma: no cover
    main()
