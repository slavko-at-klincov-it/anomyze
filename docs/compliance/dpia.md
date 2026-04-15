# Datenschutz-Folgenabschätzung (DPIA) — Anomyze

Vorlage gemäß Art. 35 DSGVO. Auszufüllen durch die verantwortliche
Stelle vor produktiver Inbetriebnahme.

## 1. Beschreibung der Verarbeitung

- **Verantwortliche Stelle:** _Behörde, Geschäftsbereich, Adresse_
- **Verarbeitungstätigkeit:** Filterung KI-generierter Texte zur
  Entfernung personenbezogener Daten vor Weiterleitung an Bedienstete
  (GovGPT), Veröffentlichung (IFG) oder parlamentarischer Verwendung
  (KAPA).
- **Zweck:** Schutz der Betroffenen vor unbeabsichtigter Offenlegung
  durch generative KI; Ermöglichung souveräner KI-Nutzung durch die
  Bundesverwaltung.
- **Rechtsgrundlage:** _Art. 6 (1) e DSGVO i.V.m. § __ AVG / fachgesetz._
- **Datenarten:** Name, Adresse, Geburtsdatum, SVNR, IBAN, BIC, UID,
  KFZ-Kennzeichen, Aktenzahlen, Reisepass, ZMR-Kennzahl, sowie
  besondere Kategorien (Gesundheit, Religion, Ethnie, Politik,
  Gewerkschaft, sexuelle Orientierung, Biometrie) — letztere mit
  obligatorischer manueller Prüfung im KAPA-Kanal.
- **Betroffene:** Auskunftssuchende, Bedienstete, Dritte, deren Daten
  in den Eingabetexten vorkommen.
- **Datenflüsse:** Eingabetext → Anomyze (lokal, On-Premise) →
  anonymisierter Text. Originaltext und Mapping werden je nach Kanal
  unterschiedlich behandelt (siehe `retention_policy.md`).

## 2. Notwendigkeit und Verhältnismäßigkeit

- _Begründung, warum kein milderes Mittel verfügbar ist._
- _Beurteilung der Datenminimierung (z.B. IFG-Kanal aggregiert
  besondere Kategorien zu BESONDERE_KATEGORIE)._

## 3. Risikoanalyse

| Risiko | Auswirkung | Eintrittswahrscheinlichkeit | Bewertung |
|---|---|---|---|
| Re-Identifikation über Quasi-Identifikatoren | hoch | mittel | hoch |
| Fehlende Erkennung (False Negative) bei Art. 9-Daten | sehr hoch | niedrig | mittel |
| Adversariale Eingaben (Homoglyphen, RTL-Override, Leetspeak) | hoch | niedrig | mittel |
| Ungewolltes Persistieren von Original-PII im Audit-Log | hoch | niedrig | mittel |

## 4. Abhilfemaßnahmen

- Mehrschichtige Detektion (Regex + NER + Presidio-kompatibel + GLiNER).
- Adversariale Normalisierung in `anomyze/pipeline/normalizer.py`.
- Re-Identifikations-Detektor in `anomyze/pipeline/reidentification.py`
  mit konfigurierbarem Fenster (`ANOMYZE_QUASI_ID_WINDOW`).
- Audit-Log-Retention mit automatischer PII-Redaktion nach 7 Tagen
  (siehe `retention_policy.md`).
- Manuelle Prüfung jeder Art. 9-Erkennung im KAPA-Kanal
  (`flagged_for_review`).
- Whitelist für Gesetzestitel und Behörden in
  `anomyze/patterns/whitelist.py` minimiert False Positives in
  Bescheid-Texten.

## 5. Restrisiko

_Bewertung durch DSB. Bei verbleibendem hohen Risiko: Konsultation
der Datenschutzbehörde gemäß Art. 36 DSGVO._

## 6. Freigabe

| Rolle | Name | Datum | Unterschrift |
|---|---|---|---|
| Datenschutzbeauftragte | | | |
| Verantwortliche Leitung | | | |
| Informationssicherheit | | | |
