# Anomyze Compliance-Dokumente

Dieses Verzeichnis enthält Vorlagen-Skelette für die DSGVO-konforme
Inbetriebnahme von Anomyze in einer österreichischen Behörde. Sie sind
**keine rechtsverbindliche Beratung**, sondern Ausgangspunkte, die
durch die Datenschutzbeauftragte (DSB) und die Rechtsabteilung der
betreibenden Stelle ergänzt und freigegeben werden müssen.

## Inhaltsübersicht

| Datei | Zweck | DSGVO-Bezug |
|---|---|---|
| [dpia.md](dpia.md) | Datenschutz-Folgenabschätzung | Art. 35 |
| [avv_template.md](avv_template.md) | Auftragsverarbeitungsvertrag | Art. 28 |
| [retention_policy.md](retention_policy.md) | Aufbewahrungs- und Löschfristen | Art. 5 (1) e |
| [loeschkonzept.md](loeschkonzept.md) | Operatives Löschkonzept | Art. 17 |
| [ropa.md](ropa.md) | Verzeichnis von Verarbeitungstätigkeiten | Art. 30 |

## Gültigkeitsbereich

Anomyze verarbeitet personenbezogene Daten **nicht zu eigenen Zwecken**
sondern als Output-Filter für KI-generierte Antworten. Die behördliche
Nutzung erfordert:

1. eine eigenständige Rechtsgrundlage für die KI-Anwendung selbst,
2. einen AVV mit dem Betreiber der Modell-Infrastruktur,
3. eine DPIA, sobald die KI-Anwendung neue Risiken für Betroffene
   einführt (regelmäßig der Fall bei Sprachmodellen).

## Pflege

Diese Dokumente sind versioniert. Substanzielle Änderungen werden im
[CHANGELOG.md](../../CHANGELOG.md) im Wurzelverzeichnis vermerkt und
sollten von der DSB gegengezeichnet werden.
