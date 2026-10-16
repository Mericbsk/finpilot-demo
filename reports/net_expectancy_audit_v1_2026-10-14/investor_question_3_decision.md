# Investorenfrage 3: Netto-Erwartung pro Trade

- Stand: 14.10.2026
- Status: Entwurf zur internen Prüfung. Keine Weitergabe ohne menschliche Freigabe.

## Entscheidung

**Mit der vorhandenen Evidenz nicht zuverlässig bestimmbar.**

## Kurzantwort

Die Erwartung pro Trade nach Spread, Slippage und Gebühren lässt sich mit der vorhandenen Evidenz nicht zuverlässig bestimmen. Eine gemessene Netto-Kennzahl liegt nicht vor. Die in internen Unterlagen genannte Kennzahl von +0,40 % ist eine Brutto-Kennzahl aus archivierten Barriere-Ergebnissen ohne Transaktionskosten.

## 1. Gemessene Fakten

- Die Kennzahl wurde aus 5.206 entschiedenen Signalen reproduziert. Der Zeitraum reicht vom 12.09.2025 bis zum 09.09.2026.
- Trefferquote: 30,1 %. Durchschnittlicher Gewinn: +4,28 %. Durchschnittlicher Verlust: −1,27 %. Brutto-Erwartung: +0,40 % je Signal.
- Der Median der Ergebnisse ist negativ (−0,64 %). Die positive Erwartung hängt daher wesentlich von einer kleinen Zahl großer Ergebnisse ab.
- Ohne die obersten 5 % der Ergebnisse ist die Erwartung negativ (−0,16 %).
- Die Signale überlappen sich: 5.748 archivierte Zeilen entsprechen 4.318 verschiedenen Symbol-Tagen.
- Im März 2026 liegen 48 % der entschiedenen Signale.
- Es liegen keine ausgeführten Trades vor. Im Broker-Protokoll stehen 11 Orders, aber keine Ausführung.

## 2. Modellierte und annahmebasierte Größen

- Die Ergebnisse beruhen auf Tageskursen. Der Einstieg erfolgt zum Signalpreis, der Ausstieg zum Take-Profit- oder Stop-Loss-Niveau. Diese Ausführungen sind ideal und nicht beobachtet.
- Wird an einem Tag sowohl der Take-Profit als auch der Stop-Loss berührt, wird der Take-Profit angenommen.
- Die Transaktionskosten von 0,20 %, 0,55 % und 1,00 % je Trade sind Szenarioannahmen und keine Messungen. Je nach Annahme wechselt das Vorzeichen der Netto-Erwartung.

## 3. Unbekannt oder nicht vorhanden

- Gemessene Geld-Brief-Spannen (Spreads) und Slippage
- Gebühren laut Broker-Abrechnung sowie Börsen- und Aufsichtsgebühren
- Leihekosten, Währungsumrechnung und Marktauswirkung
- Positionsgrößen und Kapazität je Wert
- Eine unberührte Out-of-Sample-Periode mit vorab festgelegten Schwellen (siehe Frage 4)

## 4. Nicht behauptet werden darf

- Eine Netto-Rendite pro Trade
- Dass die Kennzahl realisierten Handelsergebnissen entspricht
- Dass die Kennzahl unter Berücksichtigung von Kosten validiert ist
- Dass automatisierte oder Paper-Trades das Ergebnis belegen

## 5. Minimal notwendige nächste Schritte

1. Prüfung der Kursreihen: Bereinigung um Splits und Dividenden sowie Ausreißer, insbesondere am 01.03. und 03.03.2026.
2. Ausführungsnahe Protokollierung von Geld- und Briefkurs, Füllzeitpunkt, Preis und Gebühren in einer klar definierten Umgebung.
3. Ein einheitliches, dokumentiertes Kostenmodell mit einer Quelle je Kostenart.
4. Eine vorregistrierte, bis zur Auswertung unberührte Testperiode mit festgelegten Schwellen.
5. Abgleich mit Broker-Abrechnungen, sofern tatsächlich Trades ausgeführt wurden.

## Interner Vermerk (nicht zur Weitergabe)

Die Kennzahl +0,40 % erscheint auf öffentlichen Oberflächen als Erwartung, ohne Hinweis darauf, dass sie brutto berechnet ist und Ideal-Ausführungen unterstellt. Eine Änderung dieser Darstellung ist eine menschliche Entscheidung (Level C) und wird durch diesen Bericht nicht umgesetzt.
