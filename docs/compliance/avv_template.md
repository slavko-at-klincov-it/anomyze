# AVV-Template (Anomyze)

Vorlage für einen Auftragsverarbeitungsvertrag gemäß Art. 28 DSGVO.
Ergänzen durch die rechtliche Vertretung der verantwortlichen Stelle.

## Parteien

- **Verantwortliche** (Auftraggeber): _Behörde / Bundesministerium_.
- **Auftragsverarbeiter:** _Betreiber der Anomyze-Infrastruktur_
  (i.d.R. die eigene IT-Abteilung — kein externer Cloud-Anbieter
  zulässig wegen der Datensouveränitätsanforderung).

## Gegenstand

Filterung KI-generierter Texte vor deren Weitergabe / Veröffentlichung
durch die Anomyze-Pipeline (Versionsangabe siehe `pyproject.toml`).

## Dauer

_Beginn / Ende der Verarbeitung; Mindest-/Höchstdauer der Speicherung._

## Art und Zweck

Vollständig im DPIA dokumentiert (`dpia.md`).

## Datenkategorien und Kreis der Betroffenen

Siehe DPIA-Abschnitt 1.

## Pflichten des Auftragsverarbeiters

- Verarbeitung ausschließlich auf dokumentierte Weisung.
- Sicherstellung der Vertraulichkeit (Art. 28 Abs. 3 lit. b).
- Technische und organisatorische Maßnahmen (TOMs) gemäß Anlage 1.
- Unterstützung bei Betroffenenrechten (Art. 12-22).
- Meldung von Datenschutzverletzungen innerhalb von 24 Stunden.
- Löschung / Rückgabe nach Vertragsende.

## TOMs (Anlage 1)

| Bereich | Maßnahme | Anomyze-Umsetzung |
|---|---|---|
| Pseudonymisierung | Reversible Platzhalter im GovGPT-Kanal | `anomyze/channels/govgpt.py` |
| Verschlüsselung | Transport via HTTPS, Storage je nach Kanal | (extern) |
| Vertraulichkeit | Audit-Log-Zugriff Rollen-basiert | (extern) |
| Integrität | Modell-Pinning per SHA, Integrity-Check | `anomyze/pipeline/model_integrity.py` |
| Verfügbarkeit | Lokal-Betrieb, kein Cloud-Lock-in | Architektur |
| Belastbarkeit | Container-Isolation (read_only, cap_drop) | `docker-compose.yml` |
| Wiederherstellung | Mapping-/Audit-Persistenz konfigurierbar | `Settings.audit_log_path` |
| Evaluierung | Benchmark-CI mit Regression-Gate | `.github/workflows/benchmark.yml` |

## Unterauftragsverarbeitung

Keine zulässig — Anomyze läuft ausschließlich On-Premise.
