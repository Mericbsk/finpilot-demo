# Investorenfrage 5: Ergebnis ohne die oberen 1 % und 5 % sowie Ausführbarkeit

- Stand: 14.10.2026
- Status: Entwurf zur internen Prüfung. Keine Weitergabe ohne menschliche Freigabe.
- Grundlage: [outlier_dependence_baseline.md](outlier_dependence_baseline.md), [top_1pct_top_5pct_sensitivity.md](top_1pct_top_5pct_sensitivity.md), [execution_feasibility_audit.md](execution_feasibility_audit.md), [liquidity_and_cost_sensitivity.md](liquidity_and_cost_sensitivity.md)

## Gesamtergebnis

**2. Die Ergebnisse reagieren empfindlich auf Ausreißer und Ausführungsannahmen.**

Die Ausführbarkeit zur beabsichtigten Positionsgröße ist nicht belegt.

## Kurzantwort

Das Ergebnis ist nicht robust gegenüber den stärksten Einzelsignalen. Der Mittelwert der Bruttorendite von +0,40 % sinkt nach Ausschluss der oberen 1 % auf +0,19 % und nach Ausschluss der oberen 5 % auf −0,16 %. Ob die Signale zur beabsichtigten Positionsgröße ausführbar waren, ist nicht belegt. Spread und Orderbuch wurden nicht gemessen, und eine beabsichtigte Positionsgröße ist nicht festgelegt.

## Grundlage

- 5.206 entschiedene Signale aus der Archivtabelle `signals_archive`.
- Rendite je Signal: gespeichertes Barriere-Ergebnis, brutto, ohne Kosten, ohne Positionsgröße, mit idealer Ausführung an den Kursschranken.
- Es handelt sich um simulierte Ergebnisse, nicht um realisierte Handelsgeschäfte.

## A. Basis

- Mittelwert: +0,40 %
- Median: −0,64 %
- Trefferquote: 30,06 %
- 95-%-Intervall des Mittelwerts, nach Handelstag geclustert: +0,06 % bis +0,56 %

## B. Nach Ausschluss der oberen 1 % (52 Signale)

- Mittelwert: +0,19 % (Veränderung um −0,21 Prozentpunkte)
- Median: −0,65 %
- Trefferquote: 29,36 %

## C. Nach Ausschluss der oberen 5 % (260 Signale)

- Mittelwert: −0,16 %. Das Vorzeichen kehrt sich um.
- Median: −0,68 %
- Trefferquote: 26,38 %
- 95-%-Intervall des Mittelwerts: −0,42 % bis +0,05 %

## D. Anteil der Spitzen am Ergebnis

- Die oberen 1 % tragen 52,9 % des Nettoergebnisses.
- Die oberen 5 % tragen 138,5 % des Nettoergebnisses. Ohne sie ist die Summe negativ.
- Zwei Handelstage (01.03.2026 und 03.03.2026) enthalten 48 der 52 Signale der oberen 1 %. Ohne diese zwei Tage beträgt der Mittelwert +0,13 %, der Median −0,54 %.

## E. Ausführbarkeit zur beabsichtigten Positionsgröße

**Nicht belegt.**

- Eine beabsichtigte Positionsgröße ist nicht festgelegt. Im Code sind Obergrenzen hinterlegt (15 % bzw. 20 % des Kapitals, je nach Datei). In der Forschung wurde mit 1.000 USD je Signal gerechnet.
- Bei 1.000 USD liegt der Auftrag bei 95,2 % der Signale unter 0,1 % des 20-Tage-Dollarvolumens. Bei den oberen 1 % liegen 10 von 52 Signalen (19,2 %) über 5 %.
- 17 der 52 Signale der oberen 1 % betreffen Aktien unter 1 USD.
- Der Einstiegspreis entspricht dem Schlusskurs des Signaltags. Ob dieser Kurs zum Signalzeitpunkt handelbar war, ist nicht belegt. Der Eröffnungskurs des Folgetags lag bei den oberen 1 % im Median 2,0 % und bei den oberen 5 % 4,0 % über dem Einstiegspreis.

## F. Gemessen oder nicht gemessen

- Tagesvolumen: gemessen, historisch, aus Tageskursen. Vollständigkeit bei wenig gehandelten Werten nicht geprüft.
- Spread, Geld- und Briefkurse, Orderbuch: nicht gemessen.
- Intraday-Kurse: nicht vorhanden.

## G. Auswirkung der Kosten und Ausführungsannahmen

Pauschale Kosten je Signal:

| Annahme | Gesamt | Ohne obere 5 % |
|---|---|---|
| keine | +0,40 % | −0,16 % |
| 0,20 Prozentpunkte | +0,20 % | −0,36 % |
| 0,55 Prozentpunkte | −0,15 % | −0,71 % |
| 1,00 Prozentpunkte | −0,60 % | −1,16 % |

Weitere Sensitivitäten auf den 4.631 Signalen, deren Ergebnis sich aus den Tageskursen reproduzieren lässt:

- Ausstieg zum Eröffnungskurs, wenn der Kurs Stopp oder Ziel überspringt: Mittelwert von +0,44 % auf −0,06 %.
- Stopp zuerst, wenn Stopp und Ziel am selben Tag berührt werden: Mittelwert +0,32 %.

Die Kostenszenarien sind keine Spread- oder Marktauswirkungsmodelle. Sie zeigen die Größenordnung.

## H. Was unverifiziert bleibt

- Spread und Ausführung zum Signalzeitpunkt.
- Zeitzone der Signalzeitstempel. Die häufigsten Uhrzeiten sind 09:00 und 21:45. Ohne Zeitzone ist die Handelbarkeit des Einstiegskurses nicht prüfbar.
- Reproduktion: 575 von 5.206 Ergebnissen (11,0 %) lassen sich mit den gespeicherten Tageskursen nicht reproduzieren. Die Ursache ist nicht geklärt.
- Ob die Signale vom 01.03.2026 (Sonntag) und 03.03.2026 zum Signalzeitpunkt geschrieben oder nachträglich eingetragen wurden.
- Survivorship des Universums.

## Konklusion

Die Aussage, das Ergebnis sei robust und die Positionen seien ausführbar, kann nicht gemacht werden. Das Ergebnis hängt von wenigen Spitzen, von einer Konzentration auf zwei Handelstage und von Ausführungsannahmen ab. Eine Nettorendite wird nicht genannt, da Kosten, Spread und Ausführung nicht gemessen sind.
