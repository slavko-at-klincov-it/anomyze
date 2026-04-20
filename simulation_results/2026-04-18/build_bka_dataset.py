"""Generate 5 synthetic BKA documents for the IFG simulation.

Pure stdnum + Python — no anomyze imports, safe to run alongside pytest.
Outputs benchmarks/datasets/bka_ifg_simulation.json with exact character
offsets validated by the loader's _validate_entity check.

Synthetic PII only:
- SVNR / IBAN / UID generated via stdnum with valid checksums.
- Names are obviously fictitious.
- Addresses, GZ-Aktenzahlen, KFZ etc. constructed to be format-valid but
  not corresponding to real persons or filings.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from stdnum import iban as stdnum_iban
from stdnum.at import uid as stdnum_uid
from stdnum.at import vnr as stdnum_vnr


def make_svnr(rng: random.Random) -> str:
    while True:
        d = rng.randint(1, 28); m = rng.randint(1, 12); y = rng.randint(50, 95)
        date_part = f"{d:02d}{m:02d}{y:02d}"
        for running in range(10000):
            cand = f"{running:04d}{date_part}"
            if stdnum_vnr.is_valid(cand):
                return f"{cand[:4]} {cand[4:]}"


def make_iban(rng: random.Random) -> str:
    bban = "".join(str(rng.randint(0, 9)) for _ in range(16))
    for cd in range(100):
        cand = f"AT{cd:02d}{bban}"
        if stdnum_iban.is_valid(cand):
            return f"AT{cd:02d} {bban[:4]} {bban[4:8]} {bban[8:12]} {bban[12:]}"
    raise RuntimeError("no valid IBAN")


def make_uid(rng: random.Random) -> str:
    while True:
        body = "".join(str(rng.randint(0, 9)) for _ in range(8))
        cand = f"ATU{body}"
        if stdnum_uid.is_valid(cand):
            return cand


class Builder:
    """Concatenate text segments while tracking entity offsets."""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.entities: list[dict] = []
        self.cursor = 0

    def add(self, text: str) -> None:
        self.parts.append(text)
        self.cursor += len(text)

    def add_entity(self, text: str, etype: str) -> None:
        start = self.cursor
        self.parts.append(text)
        self.cursor += len(text)
        self.entities.append({"start": start, "end": self.cursor, "type": etype})

    @property
    def text(self) -> str:
        return "".join(self.parts)

    def build(self, doc_id: str) -> dict:
        return {"id": doc_id, "text": self.text, "entities": self.entities}


def doc_001_bescheid(rng: random.Random) -> dict:
    """IFG-Antrag-Bescheid from BKA-Verfassungsdienst."""
    b = Builder()
    b.add("BESCHEID\n\nDes Bundeskanzleramts, Sektion ")
    b.add_entity("BKA-Verfassungsdienst", "ORG")
    b.add(", betreffend den Antrag gemäß § 4 IFG vom 03.03.2026.\n\nGeschäftszahl: ")
    b.add_entity("GZ 2026/0142-VD/3", "AKTENZAHL")
    b.add("\nDatum: 18.04.2026\n\nIn der Verwaltungssache der Antragstellerin Frau ")
    b.add_entity("Ingrid Falschnamerl", "PER")
    b.add(", geboren am 14.05.1981, wohnhaft ")
    b.add_entity("Donaufelder Straße 247, 1220 Wien", "ADRESSE")
    b.add(", Sozialversicherungsnummer ")
    b.add_entity(make_svnr(rng), "SVN")
    b.add(", ergeht folgender Bescheid: Dem Antrag auf Akteneinsicht in das Konvolut zur "
          "interministeriellen Abstimmung wird teilweise stattgegeben.\n\n"
          "Für Rückfragen steht die zuständige Sachbearbeiterin "
          "Mag.a ")
    b.add_entity("Roswitha Erfunderl", "PER")
    b.add(" unter der Adresse ")
    b.add_entity("roswitha.erfunderl@bka.gv.at", "EMAIL")
    b.add(" zur Verfügung.")
    return b.build("bka-ifg-001-bescheid-verfassungsdienst")


def doc_002_ministerratsvortrag(rng: random.Random) -> dict:
    """Vortrag an den Ministerrat with multi-ministry context."""
    b = Builder()
    b.add("VORTRAG AN DEN MINISTERRAT\n\nGeschäftszahl: ")
    b.add_entity("GZ 2026/0089-MRV/1", "AKTENZAHL")
    b.add("\nEingebracht von ")
    b.add_entity("Bundeskanzler Karl Phantasie", "PER")
    b.add(" im Einvernehmen mit dem ")
    b.add_entity("Bundesministerium für Finanzen", "ORG")
    b.add(" und dem ")
    b.add_entity("Bundesministerium für Inneres", "ORG")
    b.add(".\n\nGegenstand: Förderzuwendung an die ")
    b.add_entity("Erfundene Forschungsstiftung GmbH", "ORG")
    b.add(", eingetragen unter der Firmenbuchnummer ")
    b.add_entity("FN 482910 t", "FIRMENBUCH")
    b.add(", Auszahlung auf das Konto ")
    b.add_entity(make_iban(rng), "IBAN")
    b.add(". Die zentrale Melderegister-Zahl der Geschäftsführerin ist ZMR-Zahl ")
    b.add_entity("123 456 789 012", "ZMR")
    b.add(". Verantwortlich gezeichnet: Sektionschefin ")
    b.add_entity("Dr.in Brigitte Niemand", "PER")
    b.add(".")
    return b.build("bka-ifg-002-ministerratsvortrag")


def doc_003_buergeranfrage(rng: random.Random) -> dict:
    """IFG-Antwortschreiben to a citizen with KFZ + Führerschein context."""
    b = Builder()
    b.add("Antwortschreiben gem. § 8 IFG\n\nSehr geehrter Herr ")
    b.add_entity("Hubert Niefürwahr", "PER")
    b.add(",\n\nbezugnehmend auf Ihre Anfrage vom 02.04.2026, wohnhaft ")
    b.add_entity("Mariahilfer Straße 318/14, 1150 Wien", "ADRESSE")
    b.add(", erreichbar unter ")
    b.add_entity("+43 660 1234567", "TELEFON")
    b.add(" oder ")
    b.add_entity("h.niefuerwahr@example.at", "EMAIL")
    b.add(", übermitteln wir Ihnen die angeforderte Auskunft.\n\n"
          "Das von Ihnen gemeldete Fahrzeug mit Kennzeichen ")
    b.add_entity("W-12345BX", "KFZ")
    b.add(" wurde im aktuellen Verfahren erwähnt. Ihre Führerschein-Nummer ")
    b.add_entity("87654321", "FUEHRERSCHEIN")
    b.add(" ist im Akt vermerkt; weitere Daten werden nicht offengelegt.\n\n"
          "Mit freundlichen Grüßen, das Bundeskanzleramt.")
    return b.build("bka-ifg-003-buergeranfrage-antwort")


def doc_004_mitteilung(rng: random.Random) -> dict:
    """Inter-ministerial Mitteilung with UID + BIC + ICD-10 (Art. 9)."""
    b = Builder()
    b.add("INTERMINISTERIELLE MITTEILUNG\n\nVom ")
    b.add_entity("Bundesministerium für Inneres", "ORG")
    b.add(" an das ")
    b.add_entity("Bundeskanzleramt", "ORG")
    b.add(", Sektion Personal.\n\nBetrifft: Dienstunfähigkeit des Beamten ")
    b.add_entity("Dr. Wolfgang Hirngespinst", "PER")
    b.add(", UID-Nummer der bezugsauszahlenden Stelle ")
    b.add_entity(make_uid(rng), "UID")
    b.add(", Bankverbindung BIC ")
    b.add_entity("GIBAATWWXXX", "BIC")
    b.add(".\n\nAufgrund der ärztlich attestierten Diagnose ")
    b.add_entity("F32.1", "HEALTH_DIAGNOSIS")
    b.add(" (mittelgradige depressive Episode) wird die vorzeitige Ruhestandsversetzung "
          "beantragt. Die Glaubensgemeinschaft des Beamten – Religion: ")
    b.add_entity("römisch-katholisch", "RELIGION")
    b.add(" – ist für die seelsorgerische Betreuung im Krankenstand vermerkt.")
    return b.build("bka-ifg-004-interministerielle-mitteilung")


def doc_005_parlamentarische_anfrage(rng: random.Random) -> dict:
    """§90 GOG-NR Anfrage to the Bundeskanzler."""
    b = Builder()
    b.add("PARLAMENTARISCHE ANFRAGE\ngemäß § 90 Abs. 1 GOG-NR\n\nder Abgeordneten ")
    b.add_entity("Sabine Trugschluss", "PER")
    b.add(" und Genoss:innen an den ")
    b.add_entity("Bundeskanzler", "ORG")
    b.add(" betreffend das Verfahren zur Geschäftszahl ")
    b.add_entity("Zl 2026/0312-IV", "AKTENZAHL")
    b.add(" gegen die ")
    b.add_entity("Beispielhafte Beratungs GmbH", "ORG")
    b.add(".\n\nIm Rahmen der Erhebungen wurde ")
    b.add_entity("Mag. Klaus Niegelebt", "PER")
    b.add(" als Auskunftsperson herangezogen. Förderzahlungen erfolgten auf das Konto ")
    b.add_entity(make_iban(rng), "IBAN")
    b.add(". Wir ersuchen um schriftliche Beantwortung gemäß § 91 GOG-NR.")
    return b.build("bka-ifg-005-parlamentarische-anfrage")


def main() -> None:
    rng = random.Random(20260418)
    docs = [
        doc_001_bescheid(rng),
        doc_002_ministerratsvortrag(rng),
        doc_003_buergeranfrage(rng),
        doc_004_mitteilung(rng),
        doc_005_parlamentarische_anfrage(rng),
    ]

    # Self-check: verify every entity span matches text[start:end].
    for d in docs:
        for ent in d["entities"]:
            slice_ = d["text"][ent["start"]:ent["end"]]
            assert len(slice_) == ent["end"] - ent["start"], (d["id"], ent)

    out = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "datasets" / "bka_ifg_simulation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(docs, ensure_ascii=False, indent=2))
    print(f"wrote {len(docs)} docs to {out}")
    for d in docs:
        print(f"  {d['id']}: {len(d['text'])} chars, {len(d['entities'])} entities")


if __name__ == "__main__":
    main()
