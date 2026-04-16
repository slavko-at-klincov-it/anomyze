# Anomyze — Praesentation fuer Entscheidungstraeger

Slide-Inhalte fuer PowerPoint / Keynote / Google Slides.
Jede Folie hat: Titel, Inhalt, und Sprechnotizen (kursiv).

---

## Folie 1 — Titel

**Anomyze**

Souveraene Anonymisierung fuer die oesterreichische KI-Verwaltung

anomyze.it | Open Source (MIT)

*Sprechnotizen: Anomyze ist eine Softwareloesung, die wir im Rahmen der Public-AI-Initiative entwickelt haben. Sie schuetzt personenbezogene Daten in KI-generierten Texten der Bundesverwaltung. Vollstaendig lokal, vollstaendig oesterreichisch.*

---

## Folie 2 — Die Ausgangslage

**Die Verwaltung setzt KI ein. Die Daten muessen geschuetzt bleiben.**

- GovGPT beantwortet Anfragen von Bediensteten
- ELAK-KI unterstuetzt die Aktenverwaltung
- KAPA recherchiert fuer parlamentarische Anfragen

Diese Werkzeuge arbeiten mit echten personenbezogenen Daten — weil sie diese Daten brauchen, um sinnvolle Antworten zu geben.

*Sprechnotizen: Die KI-Werkzeuge der Bundesverwaltung sind leistungsfaehig. Aber sie arbeiten mit Klarnamen, Sozialversicherungsnummern, Adressen, Gesundheitsdaten. Das ist fuer die interne Verarbeitung notwendig. Kritisch wird es erst, wenn der Output das System verlaesst.*

---

## Folie 3 — Das Risiko

**Was passiert, wenn KI-Output ungefiltert das System verlaesst?**

Beispiel — ein KI-generierter Bescheid-Entwurf:

> Sehr geehrte Frau Mag. Maria Huber,
> Ihre Sozialversicherungsnummer 1237 010180
> und IBAN AT61 1904 3002 3457 3201
> liegen dem Akt bei.
> Diagnose: F32.1 (mittelgradige depressive Episode).

Name, Bankverbindung, Gesundheitsdaten — alles in einem Dokument.
Bei Weiterleitung oder Veroeffentlichung: DSGVO-Verstoss.

*Sprechnotizen: Stellen Sie sich vor, dieser Text wird auf data.gv.at veroeffentlicht oder in einer parlamentarischen Beantwortung zitiert. Name, Kontonummer, eine psychiatrische Diagnose — offen einsehbar. Das ist nicht hypothetisch, das ist das Risiko bei jedem ungefilterten KI-Output.*

---

## Folie 4 — Die Loesung

**Anomyze filtert den Output, bevor er das System verlaesst.**

Derselbe Text, nach Anomyze:

> Sehr geehrte Frau Mag. [PERSON_1],
> Ihre Sozialversicherungsnummer [SVNR_1]
> und IBAN [IBAN_1]
> liegen dem Akt [AKTENZAHL_1] bei.
> Diagnose: [GESUNDHEIT_1] (mittelgradige depressive Episode).

Alle personenbezogenen Daten erkannt und ersetzt.
Die KI-Werkzeuge selbst muessen nicht angepasst werden.

*Sprechnotizen: Anomyze sitzt als letzte Schicht zwischen dem KI-Werkzeug und dem Ausgang. Es erkennt automatisch ueber 20 Kategorien personenbezogener Daten — und ersetzt sie. Die KI-Werkzeuge bemerken davon nichts, sie muessen nicht umgebaut werden. Anomyze ist eine eigenstaendige Sicherheitsschicht.*

---

## Folie 5 — Drei Kanaele fuer drei Szenarien

**Jeder Anwendungsfall hat eigene Datenschutz-Anforderungen.**

| | GovGPT | IFG | KAPA |
|---|---|---|---|
| **Einsatz** | Interne Weiterleitung | Veroeffentlichung (data.gv.at) | Parlamentarische Anfragen |
| **Schwaerzung** | Umkehrbar (fuer Berechtigte) | Unwiderruflich | Umkehrbar + Pruefprotokoll |
| **Audit-Trail** | Nein | Schwaerzungsprotokoll | Vollstaendige Nachvollziehbarkeit |
| **Manuelle Pruefung** | Nein | Nein | Ja, bei unsicheren Erkennungen |

*Sprechnotizen: Es gibt drei Kanaele, weil die Anforderungen unterschiedlich sind. Bei interner Weiterleitung an Bedienstete genuegt ein umkehrbarer Platzhalter — die Sachbearbeiterin kann bei Bedarf nachsehen, wer PERSON_1 ist. Bei Veroeffentlichung auf data.gv.at wird unwiderruflich geschwaerzt — niemand kann die Originaldaten zurueckgewinnen. Bei parlamentarischen Anfragen kommt ein lueckenloses Pruefprotokoll dazu: wer hat wann was erkannt, mit welcher Sicherheit, und wer hat die unsicheren Faelle kontrolliert.*

---

## Folie 6 — Oesterreich-spezifisch

**Anomyze kennt oesterreichische Datenformate.**

Generische Werkzeuge erkennen Namen und E-Mail-Adressen. Anomyze erkennt zusaetzlich:

- Sozialversicherungsnummern (mit Pruefziffern-Validierung)
- UID-Nummern (ATU...)
- KFZ-Kennzeichen (alle Bezirkscodes: W, G, L, IL, KB ...)
- Geschaeftszahlen (GZ 2024/4567-III/2)
- Gerichtsaktenzeichen (3 Ob 123/45)
- Firmenbuchnummern (FN 12345a)
- ICD-10-Diagnosecodes (Gesundheitsdaten — besondere DSGVO-Kategorie)
- Oesterreichische Vor- und Nachnamen (phonetischer Abgleich)

Gesetzestitel (ASVG, StGB) und Behoerdennamen (BMI, VfGH) werden bewusst *nicht* geschwaerzt.

*Sprechnotizen: Das ist der entscheidende Unterschied zu internationalen Anonymisierungswerkzeugen. Die kennen keine oesterreichischen Sozialversicherungsnummern, keine Geschaeftszahlen im Format der Bundesverwaltung, keine Bezirkscodes auf Kennzeichen. Anomyze wurde speziell fuer oesterreichische Behoerdendokumente entwickelt. Gleichzeitig weiss es, dass "ASVG" kein Name ist, sondern ein Gesetz — und schwaerzt es nicht.*

---

## Folie 7 — DSGVO und besondere Kategorien

**Gesundheitsdaten, Religion, Herkunft — hoechste Schutzstufe.**

DSGVO Artikel 9 schuetzt "besondere Kategorien" personenbezogener Daten:

- Gesundheit (Diagnosen, Medikamente)
- Religion, Weltanschauung
- Ethnische Herkunft
- Politische Meinung
- Gewerkschaftszugehoerigkeit
- Sexuelle Orientierung

Anomyze-Verhalten bei besonderen Kategorien:

- **IFG-Kanal:** Nicht einmal die Kategorie wird veroeffentlicht — nur "[GESCHWAERZT: BESONDERE KATEGORIE]"
- **KAPA-Kanal:** Jede Erkennung wird zwingend zur manuellen Pruefung vorgelegt, unabhaengig von der Erkennungssicherheit

*Sprechnotizen: Artikel 9 der DSGVO stellt bestimmte Datenkategorien unter besonderen Schutz. Anomyze traegt dem Rechnung. Im IFG-Kanal — also bei Veroeffentlichungen — wird nicht einmal die Art der besonderen Kategorie preisgegeben. Man sieht nicht, ob es eine Diagnose oder eine Religionszugehoerigkeit war. Im KAPA-Kanal wird jede Erkennung einer besonderen Kategorie zwingend einem Menschen vorgelegt. Auch wenn die automatische Erkennung 99 Prozent sicher ist — bei Gesundheitsdaten entscheidet immer ein Mensch.*

---

## Folie 8 — Datensouveraenitaet

**Kein Byte verlaesst die Infrastruktur der Behoerde.**

- Alle KI-Modelle laufen lokal (keine Cloud-API, kein externer Dienst)
- Keine Internetverbindung im Betrieb erforderlich
- Gehaeerteter Container (nur-lesen, minimale Berechtigungen, kein Root-Zugriff)
- Automatische Datenloeschung nach konfigurierbaren Fristen
- Recht auf Vergessenwerden (Art. 17 DSGVO) technisch umgesetzt

Deploybar auf bestehender Behoerden-Infrastruktur. Keine Beschaffung externer Cloud-Dienste notwendig.

*Sprechnotizen: Das ist ein zentraler Punkt. Anomyze laeuft vollstaendig lokal — auf einem Server in der Behoerde, ohne Internetverbindung. Es gibt keinen Datenabfluss an Google, Microsoft, OpenAI oder andere Dritte. Die Daten bleiben unter der Kontrolle der Republik. Der Container ist gehaertet: nur-lesen-Dateisystem, keine Administrator-Rechte, keine unnoetige Software. Und es gibt ein eingebautes Loeschkonzept — personenbezogene Daten im Audit-Log werden nach sieben Tagen automatisch unkenntlich gemacht, nach sieben Jahren geloescht.*

---

## Folie 9 — Qualitaetssicherung

**Messbare Erkennungsqualitaet. Automatische Regressionspruefung.**

- Benchmark-Framework mit oesterreichischen Testdokumenten (Bescheide, Niederschriften, Ladungen, Protokolle)
- Misst Genauigkeit (Precision), Vollstaendigkeit (Recall) und deren Zusammenspiel (F1-Score) pro Datenkategorie
- Automatische Pruefung bei jeder neuen Version: die Erkennungsqualitaet darf nicht sinken
- Abschlusskontrolle jedes anonymisierten Dokuments auf durchgerutschte Reste

*Sprechnotizen: Anonymisierung ist nur so gut wie ihre Erkennungsrate. Deshalb messen wir die Qualitaet systematisch — auf realitaetsnahen oesterreichischen Behoerdentexten, nicht auf englischen Beispieldaten. Wenn ein Entwickler eine Aenderung macht, prueft ein automatischer Gate-Check, dass die Erkennung insgesamt nicht schlechter wird. Und jedes einzelne Dokument wird nach der Anonymisierung nochmals geprueft: haben wir etwas uebersehen?*

---

## Folie 10 — Status und naechste Schritte

**Anomyze ist einsatzbereit. Der naechste Schritt ist der Pilotbetrieb.**

Aktueller Stand:
- Open Source, MIT-Lizenz
- Ueber 450 automatisierte Tests, CI/CD-Pipeline
- Docker-Container gehhaertet und verifiziert
- DSGVO-Compliance-Vorlagen (Datenschutz-Folgenabschaetzung, Auftragsverarbeitungsvertrag, Loeschkonzept) liegen bei
- Deploy-Vorlagen fuer Behoerden-Infrastruktur (Reverse-Proxy, Authentifizierung, Backup)

Naechste Schritte:
- Pilotbetrieb mit einem Ressort (Echtdaten, begleitete Evaluierung)
- Freigabe durch Datenschutzbeauftragte (DPIA-Finalisierung)
- Integration in bestehende KI-Infrastruktur (GovGPT / ELAK-KI / KAPA)

*Sprechnotizen: Die Software ist technisch fertig und getestet. Was jetzt folgt, ist der Schritt in die Praxis: ein Pilotbetrieb mit einem Ressort, begleitet von der Datenschutzbehoerde. Die Compliance-Vorlagen — Datenschutz-Folgenabschaetzung, Auftragsverarbeitungsvertrag, Loeschkonzept — sind vorbereitet und muessen von der Rechtsabteilung finalisiert werden. Technisch kann Anomyze auf bestehender Behoerden-Infrastruktur betrieben werden, ohne neue Hardware-Beschaffung.*

---

## Folie 11 — Kontakt

**Anomyze**

anomyze.it

GitHub: github.com/slavko-at-klincov-it/anomyze

Lizenz: MIT (frei nutzbar, auch kommerziell)

---

## Design-Hinweise fuer die Umsetzung

- **Farben:** Weiss/Hellgrau-Hintergrund, Dunkelblau fuer Ueberschriften, Rot nur fuer Akzente (z.B. das "Vorher"-Beispiel). Oesterreich-Rot (#ED2939) sparsam.
- **Schrift:** Serifenlos (z.B. Inter, Source Sans Pro, oder die Hausschrift des Bundeskanzleramts falls vorhanden)
- **Wenig Text:** Maximal 5-6 Zeilen pro Folie. Die Sprechnotizen tragen die Details.
- **Vorher/Nachher (Folie 3+4):** Monospace-Schrift fuer die Textbeispiele, "Vorher" mit rotem Rand, "Nachher" mit gruenem Rand.
- **Tabelle (Folie 5):** Minimalistisch, keine schweren Rahmen. Headerzeile farbig hinterlegt.
- **Folie 8 (Datensouveraenitaet):** Grafik eines Servers mit Schloss-Symbol, "100% lokal" als grosser Claim.
- **Kein Logo-Overkill.** Ein Anomyze-Logo oben rechts (klein), Bundeskanzleramt-Wappen nur wenn offiziell freigegeben.
