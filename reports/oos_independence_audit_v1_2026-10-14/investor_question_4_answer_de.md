# Investorenfrage 4: Gesperrter Out-of-Sample-Datensatz und Auswertungs-Gate

- Stand: 14.10.2026
- Status: Entwurf zur internen Prüfung. Keine Weitergabe ohne menschliche Freigabe.

## Gesamtstatus

**C. Unabhängigkeit oder Gate nicht nachgewiesen.**

## Kurzantwort

Für die Handelsstrategie gibt es keinen nachweisbar gesperrten und unberührten Out-of-Sample-Datensatz. Ein vorab festgelegtes Auswertungs-Gate mit numerischen Schwellen ist für die Handelsstrategie nicht belegt. Eine Vorregistrierung mit nachprüfbarem Hash besteht für eine andere Forschungslinie (RX-CAPTURE-1). Diese Linie verwendet jedoch denselben Datensatz wie andere Forschungslinien und ist deshalb nicht unabhängig.

## 1. Wann wurde der Datensatz eingefroren?

- **Handelsstrategie, Grenze 21.05.2026:** nicht nachweisbar. Die früheste Angabe im Repository steht in einem Artefakt vom 15.07.2026, 16:52 UTC, das bereits Ergebnisse für den Zeitraum nach dieser Grenze enthält.
- **Separater Holdout für Fundamental- und Nachrichtenfaktoren, 09.06. bis 30.06.2026:** Zeitstempel 05.08.2026, 11:31 UTC. Dieser Zeitstempel wurde vom Skript selbst geschrieben und nicht über die Versionsverwaltung gesichert.
- **RX-CAPTURE-1, Vorregistrierung:** Eintrag im Entscheidungsprotokoll vom 22.09.2026 mit Hash-Wert, der mit der aktuellen Datei übereinstimmt. Die erste Speicherung in der Versionsverwaltung erfolgte am 23.09.2026.

## 2. Was belegt das Einfrieren?

- Dateihashes und Einträge im Entscheidungsprotokoll: nur für RX-CAPTURE-1 bestätigt.
- Dateizeitstempel und Zeitstempel innerhalb von Dateien, die vom Skript selbst geschrieben wurden, belegen allein kein Einfrieren.

## 3. Wurde der Testzeitraum bereits verwendet?

**Ja.** Der Zeitraum nach dem 21.05.2026 wurde am 15.07.2026 ausgewertet (44 bzw. 62 Beobachtungen je nach Auswahl). Ab dem 26.06.2026 wurden im September 2026 mehrere weitere Auswertungen mit 17.149 bis 18.909 Beobachtungen durchgeführt. Der Testzeitraum ist daher nicht unberührt. Der Holdout für Fundamental- und Nachrichtenfaktoren überschneidet sich mit diesen Zeiträumen.

## 4. War das Gate vor der Auswertung festgelegt?

- **Handelsstrategie:** nicht nachgewiesen. Die Testplanung wurde im selben Commit gespeichert wie die Ergebnisse vom selben Tag.
- **Dokumentierte Schwellen (mit Einschränkungen):**
  - Der Vorteil gegenüber der Zufallsbasis (Lift) muss über 1 liegen, oder die Erwartung nach Kosten muss positiv sein. Eine Zufallsbasis mit numerischem Wert ist nicht festgelegt.
  - Das Konfidenzintervall darf nicht vollständig unter der Zufallsbasis liegen.
  - Das gleiche Vorzeichen muss in mindestens drei Zeitabschnitten auftreten.
  - Bei negativem Median darf das Ergebnis nicht allein auf dem Mittelwert beruhen.
- **Forschungsläufe mit festen Haltezeiten:** Schwelle für den FDR-Test 0,05, deflatierter Sharpe-Quotient mindestens 0,95, mindestens 50 Beobachtungen je Zeitraum, Mittelwert und Median der Nettorendite positiv in Training und Validierung. Diese Werte wurden am 06.08.2026 im Code gespeichert, nach dem Lauf vom 05.08.2026.
- **Numerische Schwelle für den Holdout:** nicht vorhanden.
- **RX-CAPTURE-1 (vorregistriert):** Primärgröße ist der Median der Nettoerfassung. Dieser Median ist für die geprüften Kandidaten degeneriert, weil die meisten Beobachtungen die feste Zielmarke sofort erreichen. Die Schwellen sind unverändert dokumentiert, aber nur eingeschränkt aussagekräftig.

## 5. Was lässt sich nicht unabhängig prüfen?

- Zugriffsprotokolle für den Testdatensatz existieren nicht. Die Freigabe des Holdouts ist technisch nicht erzwungen; die Schutzklasse wird nur in Tests verwendet.
- Ob Schwellen nach Kenntnis der Ergebnisse gewählt wurden, lässt sich aus dem Repository nicht ausschließen.
- Die Produktionsrangfolge ist nicht vollständig rekonstruiert. Die getestete Bewertungsmethode ist eine Näherung und nicht dieselbe wie in der Produktion.
- Es gibt mehrere Versionen der Eingangsdaten, darunter eine Sicherungskopie vom 15.07.2026, die vor einer Korrektur angelegt wurde.
- Die Vorregistrierung für den ökonomischen Review von RX-CAPTURE-1 kann nicht über den gespeicherten Hash-Wert belegt werden; ihre Version ist daher nicht nachweisbar festgelegt.

## 6. Ist die Auswertung bereit?

**Nein.** Für eine belastbare Auswertung sind erforderlich:

1. Ein neues Protokoll mit numerischen Erfolgs-, Misserfolgs- und Unentschieden-Kriterien, das vor dem Zugriff mit Hash-Wert gespeichert wird.
2. Ein Testzeitraum, dessen Daten erst nach dem Einfrieren entstehen und in keiner früheren Auswertung verwendet wurden.
3. Eine dokumentierte Freigabe durch eine verantwortliche Person.
4. Ein Zugriffsprotokoll und eine technisch erzwungene Einmalöffnung.

## Zusammenfassung

Wir können dokumentieren, welche Auswertungen durchgeführt wurden. Wir können nicht nachweisen, dass ein unabhängiger, vorab gesperrter Testzeitraum eingehalten wurde. Eine Aussage über die Out-of-Sample-Validierung der Handelsstrategie ist daher nicht möglich.
