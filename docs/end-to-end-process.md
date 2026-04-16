# End-to-End-Prozess: Vom Buergerantrag zum anonymisierten Dokument

Dieses Dokument beschreibt den Gesamtprozess, in dem Anomyze als
automatische Anonymisierungsschicht eingebettet ist. Die Vision ist
ein durchgehend automatisierter Ablauf, bei dem der Mensch erst am
Ende als Prüfinstanz eingreift — nicht als Bearbeiter, sondern als
Kontrolleur.

---

## Prozessueberblick

```
    BUERGERIN / BUERGER
          |
          | 1. Anfrage ueber Web-Portal
          |    (z.B. Auskunftsbegehren, Antrag, Beschwerde)
          v
  +------------------+
  |   WEB-PORTAL     |
  |   (data.gv.at,   |
  |    oesterreich.   |
  |    gv.at, ...)    |
  +------------------+
          |
          | 2. Automatische Identifikation
          |    - Wer stellt die Anfrage? (Authentifizierung via ID Austria)
          |    - Was wird angefragt? (Kategorisierung des Anliegens)
          |    - Welche Daten werden benoetigt? (Regelwerk)
          v
  +------------------+
  |   ORCHESTRIERUNG |
  |   (Workflow-      |
  |    Engine)        |
  +------------------+
          |
          | 3. Automatische Datenbeschaffung
          |    - Relevante Akten aus dem ELAK
          |    - Registerdaten (ZMR, Firmenbuch, Grundbuch, ...)
          |    - Vorherige Bescheide, Protokolle, Gutachten
          |    Alles automatisch, anhand des kategorisierten Anliegens.
          v
  +------------------+
  |   KI-VERARBEITUNG|
  |   (GovGPT /      |
  |    ELAK-KI /      |
  |    KAPA)          |
  +------------------+
          |
          | 4. KI generiert den Dokument-Entwurf
          |    - Bescheid, Auskunft, Beantwortung, Stellungnahme
          |    - Auf Basis der gesammelten Daten
          |    - Inhaltlich vollstaendig, aber mit personenbezogenen Daten
          v
  +------------------+
  |                  |
  |    A N O M Y Z E |  <-- Automatische Anonymisierung
  |                  |
  +------------------+
          |
          | 5. Anomyze filtert den KI-Output
          |    - Erkennt alle personenbezogenen Daten (20+ Kategorien)
          |    - Ersetzt sie durch Platzhalter
          |    - Flaggt unsichere Erkennungen
          |    - Flaggt besondere Kategorien (Gesundheit, Religion, ...)
          |    - Erzeugt Pruefprotokoll (Audit-Trail)
          |    - Fuehrt Abschlusskontrolle durch (Quality-Check)
          v
  +------------------+
  |   PRUEF-QUEUE    |
  |   (Aufgaben-     |
  |    verwaltung)   |
  +------------------+
          |
          | 6. Sachbearbeiterin wird benachrichtigt
          |    "Ein Dokument wartet auf Ihre Freigabe."
          |    - Per E-Mail, Dashboard, oder Aufgabenliste
          v
  +------------------+
  |   HUMAN-IN-THE-  |
  |   LOOP           |
  |   (Sachbear-     |
  |    beiterin)     |
  +------------------+
          |
          | 7. Pruefung und Freigabe
          |    - Sachbearbeiterin oeffnet das anonymisierte Dokument
          |    - Sieht markierte Stellen: [PERSON_1], [SVNR_1], ...
          |    - Sieht Warnungen: [PRUEFEN:GESUNDHEIT_1]
          |    - Kann bei Bedarf das Mapping einsehen (wer ist PERSON_1?)
          |    - Entscheidet:
          |        [Freigeben]  →  Dokument wird verschickt
          |        [Zurueck]    →  Zur Nachbearbeitung
          v
  +------------------+
  |   VERSAND        |
  +------------------+
          |
          | 8. Dokument wird zugestellt
          |    - Per Zustellservice (MeinPostfach, RSa-Brief, E-Mail)
          |    - An die Buergerin / den Buerger
          |    - Audit-Eintrag wird geschlossen
          v
    BUERGERIN / BUERGER
    erhaelt das Dokument
```

---

## Die Rolle von Anomyze im Gesamtprozess

Anomyze ist **Schritt 5** — die automatische Anonymisierungsschicht
zwischen der KI-Verarbeitung und der menschlichen Kontrolle.

Was Anomyze in diesem Prozess leistet:

| Funktion | Beschreibung |
|----------|-------------|
| **Erkennung** | Identifiziert automatisch alle personenbezogenen Daten im KI-generierten Dokument — Namen, Adressen, Kontonummern, Sozialversicherungsnummern, Gesundheitsdaten, und 20+ weitere oesterreich-spezifische Kategorien. |
| **Anonymisierung** | Ersetzt erkannte Daten durch Platzhalter. Je nach Kanal reversibel (fuer die Sachbearbeiterin einsehbar) oder unwiderruflich (fuer Veroeffentlichungen). |
| **Risiko-Flagging** | Markiert unsichere Erkennungen und besonders sensible Daten (DSGVO Art. 9) fuer die manuelle Pruefung. Die Sachbearbeiterin sieht auf einen Blick, wo sie genauer hinsehen muss. |
| **Audit-Trail** | Protokolliert jede Erkennung mit Zeitstempel, Sicherheit und Quelle — fuer parlamentarische Nachvollziehbarkeit und interne Revision. |
| **Qualitaetskontrolle** | Prueft das anonymisierte Dokument nochmals auf durchgerutschte Reste, bevor es in die Pruef-Queue gelangt. |

Was Anomyze **nicht** leistet (und auch nicht soll):

| Abgrenzung | Verantwortlich |
|------------|---------------|
| Authentifizierung der Buergerin | ID Austria / Web-Portal |
| Kategorisierung des Anliegens | Workflow-Engine / Fachapplikation |
| Datenbeschaffung aus Registern | ELAK / Register-Schnittstellen |
| Inhaltliche Erstellung des Dokuments | KI-Werkzeug (GovGPT, ELAK-KI, KAPA) |
| Finale inhaltliche Pruefung | Sachbearbeiterin (Human-in-the-Loop) |
| Zustellung an die Buergerin | Zustellservice (MeinPostfach, RSa) |

---

## Der Mensch als Prüfinstanz, nicht als Bearbeiter

Der zentrale Gedanke dieses Prozesses: **Der Mensch prueft, er
erstellt nicht.** Die gesamte Kette — von der Anfrage ueber die
Datenbeschaffung, KI-Verarbeitung bis zur Anonymisierung — laeuft
automatisch. Der Mensch kommt erst am Ende, als Kontrollinstanz.

Das hat drei Vorteile:

1. **Geschwindigkeit.** Ein Vorgang der heute Tage dauert (Akt suchen,
   Daten zusammenstellen, Entwurf schreiben, anonymisieren) kann in
   Minuten durchlaufen. Der Mensch prueft nur noch das Ergebnis.

2. **Konsistenz.** Automatische Anonymisierung ist konsistenter als
   manuelle. Ein Mensch uebersieht eine Sozialversicherungsnummer in
   einem langen Dokument. Anomyze nicht.

3. **Nachvollziehbarkeit.** Jeder Schritt ist dokumentiert. Bei einer
   Beschwerde oder parlamentarischen Anfrage kann lueckenlos
   nachgewiesen werden: welche Daten wurden erkannt, mit welcher
   Sicherheit, wer hat kontrolliert, wann wurde freigegeben.

---

## Beispiel: Auskunftsbegehren nach Informationsfreiheitsgesetz

```
Montag, 09:12 — Buergerin stellt Anfrage auf data.gv.at
                "Ich ersuche um Auskunft zu den Erhebungen
                 im Verfahren GZ 2024/4567."

Montag, 09:12 — System identifiziert: IFG-Anfrage, GZ 2024/4567,
                Ressort BMI.

Montag, 09:13 — Automatischer Abruf der Akte GZ 2024/4567 aus dem
                ELAK. 14 Dokumente, 23 Seiten.

Montag, 09:14 — KI (GovGPT) erstellt eine Zusammenfassung der
                relevanten Aktenstuecke fuer die Auskunft.
                Zusammenfassung enthaelt: 3 Namen, 2 Adressen,
                1 Sozialversicherungsnummer, 1 Diagnose.

Montag, 09:14 — Anomyze anonymisiert die Zusammenfassung.
                IFG-Kanal: unwiderrufliche Schwaerzung.
                1 Warnung: Diagnose (Art. 9) → BESONDERE KATEGORIE.
                Quality-Check: bestanden, keine Reste.

Montag, 09:15 — Sachbearbeiterin Dr. Koller erhaelt Benachrichtigung:
                "IFG-Auskunft zu GZ 2024/4567 bereit zur Freigabe."

Montag, 09:22 — Dr. Koller oeffnet das Dokument, prueft die
                Schwaerzungen, bestaetigt die besondere Kategorie.
                Klickt [Freigeben].

Montag, 09:22 — Dokument wird an das MeinPostfach der Buergerin
                zugestellt. Audit-Eintrag wird geschlossen.
```

Gesamtdauer Eingang bis Zustellung: **10 Minuten.**
Davon manuell: **7 Minuten** (Pruefung durch Dr. Koller).

---

## Einbettung in die Praesentationsfolien

Dieser Prozess kann als **Folie 7a** (nach "Drei Kanaele", vor
"Oesterreich-spezifisch") in die Praesentation eingefuegt werden.

Empfohlene Darstellung:

- Vertikaler Prozessfluss, 8 Schritte
- Jeder Schritt eine Zeile mit Icon + Kurzbeschreibung
- Anomyze-Schritt farblich hervorgehoben (z.B. blaue Box)
- Human-in-the-Loop-Schritt mit Person-Icon
- Timeline-Beispiel (10 Minuten) als Fusszeile

Alternativ als **zwei Folien:**
- Folie A: Der Gesamtprozess (8 Schritte, schematisch)
- Folie B: Das konkrete Beispiel (IFG-Anfrage, Zeitverlauf)
