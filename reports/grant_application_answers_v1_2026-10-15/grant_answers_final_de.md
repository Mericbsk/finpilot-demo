# Antworten auf die Fragen (Entwurf v2, Stand 15.10.2026)

- Status: Entwurf für die finale Prüfung. Noch nicht einreichungsfertig: Felder mit [OFFEN] müssen vor Einreichung geschlossen werden.
- Interne Hinweise am Ende der Datei sind nicht zur Einreichung bestimmt.

## Frage 1: Struktur, Team und Zeitplan

Das Vorhaben läuft über 24 Monate in sechs Arbeitspaketen mit drei Entscheidungskriterien (Gates). Der Gründer arbeitet in Wien in Vollzeit. Ab Monat 4 kommen ein bis zwei Teilzeit-Entwickler und ein Berater für Quant- und ML-Fragen hinzu. [OFFEN: Stunden, Vertragsform und Vertragspartner ergänzen.] Weitere Mittel werden erst nach einem bestandenen Gate freigegeben.

| Arbeitspaket | Monate | Ergebnis |
|---|---|---|
| AP1 Daten und Infrastruktur | 1–12 | Datenpipeline, lokale KI-Hardware, Messung von Spread und Slippage |
| AP2 Forschung und Validierung | 1–15 | Vorab-Registrierung, Schattentest, prospektive Testphase mit vorab festgelegtem Protokoll; Auswertung in Gate 1 (Monat 9) |
| AP3 Produkt und Plattform | 4–24 | MVP (Monat 6), geschlossene Beta (Monat 7–15), Marktstart (Monat 17) |
| AP4 Lokale Modelle | 4–18 | Fine-Tuning und Erklärbarkeit auf eigener Hardware |
| AP5 Recht und Compliance | 1–9, 13–15 | Gründung, Rechtsgutachten, DSGVO, KI-Verordnung |
| AP6 Markteintritt und Finanzen | 13–24 | B2B-Pilotkunden, Preistest, CAC-Messung, Folgefinanzierung |

| Gate | Zeitpunkt | Entscheidung |
|---|---|---|
| Start | Monat 3 | Unternehmen gegründet, Protokoll versioniert und mit Hash gesichert, Erfassung von Kosten und Ausführung vorbereitet |
| Gate 1 | Monat 9 | Auswertung des vorab gesperrten Prospektivfensters (einmalig): weiter, Richtungswechsel oder Stopp |
| Gate 2 | Monat 16 | Marktstart nur bei Beta-Daten und rechtlicher Klarheit |
| Gate 3 | Monat 21 | Umsatz- und CAC-Nachweis für die Folgefinanzierung |
| Abschluss | Monat 24 | Abschlussbericht; Entscheidung über Live-Kapital oder regulierte Produkte |

Bestehende Datensätze gelten nicht als unabhängiges Out-of-Sample (siehe Frage 4). Die Auswertung in Gate 1 nutzt ausschließlich Daten, die nach der Protokollsperre entstehen. [OFFEN: Prüfen, ob in Monat 3 bis 9 genügend Signale mit abgeschlossenem Ergebnis entstehen.]

## Frage 2: Budget

Beantragt wird ein Gesamtbudget von 300.000 € für 24 Monate Betriebs-Runway. Live-Handelskapital ist darin nicht enthalten. Bereits aufgewendete Eigenmittel von rund 35.000 € (Datensätze, Server; Stand 14.10.2026) liegen außerhalb dieses Budgets. [OFFEN: Eigenmittel belegen.]

| Posten | 24 Monate (T€) | Anteil |
|---|---|---|
| Gründergehalt | 112,4 | 37,5 % |
| Teilzeit-Entwickler und Berater | 62,0 | 20,7 % |
| Lokale KI-Hardware | 33,0 | 11,0 % |
| Cloud, API und Daten | 27,0 | 9,0 % |
| Reserve | 27,3 | 9,1 % |
| Recht, Buchhaltung, Verwaltung | 25,0 | 8,3 % |
| Büro | 13,3 | 4,4 % |
| **Summe** | **300,0** | **100 %** |

Gehalts- und Lohnnebenkosten sind Schätzwerte und werden mit dem Steuerberater abgestimmt. Hardware ist inklusive USt. angesetzt.

## Frage 3: Erwarteter Nettogewinn pro Trade

**Mit der vorhandenen Evidenz nicht zuverlässig bestimmbar.** Es liegt keine gemessene Netto-Kennzahl vor.

Gemessene Fakten (5.206 archivierte Signale mit abgeschlossenem Ergebnis, 12.09.2025 bis 22.05.2026):

- Trefferquote 30,1 %. Durchschnittlicher Gewinn +4,28 %, durchschnittlicher Verlust −1,27 %. Brutto-Erwartung +0,40 % je Signal.
- Der Median ist negativ (−0,64 %). Ohne die oberen 5 % der Ergebnisse ist die Erwartung negativ (−0,16 %).
- Das gesamte Archiv umfasst 5.748 Zeilen einschließlich offener Signale, verteilt auf 4.318 Symbol-Tage. Signale überlappen sich. 48 % der abgeschlossenen Signale stammen aus März 2026.
- Es liegen keine ausgeführten Trades vor. Das Broker-Protokoll enthält 11 Orders ohne Ausführung.

Annahmen: Die Ergebnisse beruhen auf Tageskursen und idealer Ausführung (Einstieg zum Signalpreis, Ausstieg am Take-Profit- oder Stop-Loss-Niveau). Die Kosten von 0,20, 0,55 und 1,00 Prozentpunkten sind Szenarien, keine Messungen. Je nach Szenario liegt die Erwartung bei +0,20 %, −0,15 % bzw. −0,60 %.

Nicht gemessen: Spreads und Slippage, Gebühren laut Broker-Abrechnung, Leihekosten, Währungsumrechnung, Marktauswirkung, Positionsgrößen und Kapazität je Wert.

Nächste Schritte (AP1): ausführungsnahe Protokollierung von Geld- und Briefkurs, Füllzeitpunkt, Preis und Gebühren; ein dokumentiertes Kostenmodell mit einer Quelle je Kostenart; eine vorregistrierte, unberührte Testperiode (Frage 4); Abgleich mit Broker-Abrechnungen.

## Frage 4: Gesperrter Out-of-Sample-Datensatz und Auswertungs-Gate

**Unabhängigkeit oder Gate nicht nachgewiesen.** Für die Handelsstrategie gibt es keinen nachweisbar gesperrten und unberührten Out-of-Sample-Datensatz. Ein vorab festgelegtes Auswertungs-Gate mit numerischen Schwellen ist nicht belegt. Wir treffen daher keine Aussage zur Out-of-Sample-Validierung der Handelsstrategie.

Stand im Einzelnen (Ortszeit MESZ):

- Der Einfrierzeitpunkt der Handelsstrategie (Grenze 21.05.2026) ist nicht nachweisbar. Der Testplan mit dieser Grenze liegt im lokalen Arbeitsverlauf ab 15.07.2026, 16:09 MESZ. Eine Fassung mit der Grenze ist ab 15.07.2026, 18:07 MESZ dokumentiert. Ergebnisse nach der Grenze stammen aus Artefakten vom 15.07.2026, 18:52 MESZ. Die Versionsverwaltung enthält die Grenze ab 15.07.2026, 20:18 MESZ. Eine Zugriffsprotokollierung existiert nicht.
- Der Testzeitraum wurde bereits verwendet: am 15.07.2026 (44 bzw. 62 Beobachtungen) und im September 2026 mit 17.149 bis 18.909 Beobachtungen.
- Die Schwellen für Forschungsläufe liegen im Code-Stand vom 04.08.2026 und wurden am 06.08.2026 versioniert. Für den Lauf vom 05.08.2026 ist die Zuordnung zum Code-Stand nicht vollständig belegt.
- Für den separaten Holdout gibt es keine numerische Erfolgsschwelle. Die Sperre ist technisch nicht erzwungen.
- RX-CAPTURE-1: Die Vorregistrierung vom 22.09.2026 ist über den im Entscheidungsprotokoll hinterlegten Hash verifiziert. Diese Linie nutzt denselben Datensatz wie andere Forschungslinien und ist daher nicht unabhängig.
- RX-CAPTURE-1-ECON: Der im Entscheidungsprotokoll hinterlegte Sperr-Hash vom 23.09.2026 ist aus dem lokalen Arbeitsverlauf reproduzierbar (23.09.2026, 14:49 MESZ). Die Fassung ist nicht in der Versionsverwaltung abgelegt.

Geplant für Gate 1. Das Protokoll wird vor Testbeginn mit Hash und Commit gesichert:

1. Strategie- und Codeversion, eingefroren bei Protokollsperre. Es wird der Produktionsstand verwendet, nicht ein Proxy. [OFFEN: Produktionsstand gegen Proxy abgleichen.]
2. Ein Testfenster, das nach der Protokollsperre entsteht und in keiner früheren Auswertung verwendet wurde.
3. Numerische Erfolgs-, Misserfolgs- und Unentschieden-Kriterien, vor Testbeginn festgelegt.
4. Eine dokumentierte Freigabe durch eine verantwortliche Person sowie ein Zugriffsprotokoll mit technisch erzwungener Einmalöffnung.

Vorgeschlagene Kriterien (Werte werden vor Protokollsperre festgelegt):

- Ergebnis nach dokumentierten Kosten positiv; Sensitivität mit 1,00 Prozentpunkten Kosten.
- Mittelwert nach Ausschluss der oberen 1 % und 5 % der Ergebnisse positiv.
- Untere Grenze des 95-%-Intervalls, nach Handelstag geclustert, über null.
- Kein einzelner Handelstag trägt mehr als 25 % des Ergebnisses.
- Gleiches Vorzeichen in mindestens drei Zeitabschnitten.

## Frage 5: Ausreißer und Umsetzbarkeit

**Die Ergebnisse reagieren empfindlich auf Ausreißer und Ausführungsannahmen.** Die Umsetzbarkeit zur beabsichtigten Positionsgröße ist nicht belegt. Grundlage sind 5.206 abgeschlossene Signale aus dem Archiv: simuliert, brutto, ohne Kosten, mit idealer Ausführung an den Kursschranken.

| Szenario | Mittelwert | Median | Trefferquote |
|---|---|---|---|
| Alle Signale | +0,40 % | −0,64 % | 30,06 % |
| Ohne obere 1 % (52) | +0,19 % | −0,65 % | 29,36 % |
| Ohne obere 5 % (260) | −0,16 % | −0,68 % | 26,38 % |

Nach Ausschluss der oberen 5 % kehrt sich das Vorzeichen um. Das 95-%-Intervall des Mittelwerts (nach Handelstag geclustert) reicht für alle Signale von +0,06 % bis +0,56 %, ohne die oberen 5 % von −0,42 % bis +0,05 %.

Konzentration: Die oberen 1 % tragen 52,9 % des Ergebnisses, die oberen 5 % 138,5 %. 48 der 52 Signale der oberen 1 % stammen von zwei Handelstagen (01.03. und 03.03.2026). Ohne diese Tage beträgt der Mittelwert +0,13 % und der Median −0,54 %.

Kosten (pauschal je Signal):

| Annahme | Alle Signale | Ohne obere 5 % |
|---|---|---|
| 0,20 Prozentpunkte | +0,20 % | −0,36 % |
| 0,55 Prozentpunkte | −0,15 % | −0,71 % |
| 1,00 Prozentpunkte | −0,60 % | −1,16 % |

Umsetzbarkeit: Eine beabsichtigte Positionsgröße ist nicht festgelegt. Die Forschung rechnete mit 1.000 USD je Signal. Dabei liegt der Auftrag bei 95,2 % der Signale unter 0,1 % des 20-Tage-Dollarvolumens. Bei den oberen 1 % liegen jedoch 10 von 52 Signalen (19,2 %) über 5 %, und 17 von 52 betreffen Aktien unter 1 USD. Der Einstieg erfolgt zum Schlusskurs des Signaltags. Die Eröffnung des Folgetags lag bei den oberen 1 % im Median 2,0 % und bei den oberen 5 % 4,0 % darüber. Springt der Kurs über Stopp oder Ziel und wird zur Eröffnung ausgestiegen, fällt der Mittelwert der 4.631 reproduzierbaren Signale von +0,44 % auf −0,06 %.

Nicht gemessen: Spread, Geld- und Briefkurse, Orderbuch, Intraday-Kurse. Unverifiziert: die Zeitzone der Signalzeitstempel; 575 von 5.206 Ergebnissen (11,0 %) lassen sich aus den gespeicherten Tageskursen nicht reproduzieren; ob die Signale vom 01. und 03.03.2026 zeitnah oder nachträglich eingetragen wurden; Survivorship des Universums.

Wir treffen keine Aussage zur Belastbarkeit des Ergebnisses oder zur Umsetzbarkeit der Positionen und nennen keine Netto-Kennzahl.

## Frage 6: Türkei

Ein Teil unserer externen Unterstützung (Beratung und IT-Sicherheit) kommt von Dienstleistern aus der Türkei; diese Zusammenarbeit besteht fort. Eine Aufsichts- oder sonstige Behörde in der Türkei wurde nicht informiert. Es gibt weder einen Antrag (z. B. bei der SPK) noch schriftliche Korrespondenz. [OFFEN: Angaben bestätigen.] Gespräche mit Institutionen waren informell und mündlich, ohne offiziellen Charakter und ohne Verbindlichkeit.

Greifen türkische Dienstleister auf personenbezogene Daten aus der EU zu, werden geeignete Schutzmaßnahmen nach DSGVO vereinbart. Für die Türkei liegt kein Angemessenheitsbeschluss der EU vor. [OFFEN: vertragliche Grundlage festlegen.]

Unternehmenssitz ist Wien. Zielmärkte sind die USA und Europa. Die Türkei ist nicht Teil des Marktplans. Vor einem Markteintritt würde die lokale Regulierung rechtlich geprüft.

## Frage 7: Regulierung

**Eigener Handel:** Der Handelsteil ist experimentell. Handelslogik und Code sind dem Gründer vorbehalten. [OFFEN: Zugriffsbeschränkung belegen.]

**Plattform:** FinSense ist eine Plattform für Finanzkompetenz (IT-Dienstleistung, SaaS für Bildung und Analyse). Eigene KI-Modelle erklären anhand realer, nachträglich ausgewerteter Beispiele, warum eine Auswahl getroffen wurde und weshalb Entscheidungen gelungen oder misslungen sind. Es gibt keine persönliche Anlageberatung. [OFFEN: Produktbeschreibung mit dem tatsächlichen Produktstand abgleichen.]

**Weitergabe von Handelssignalen:** [OFFEN – BLOCKIEREND: Die Aussage zur Weitergabe von Kauf- oder Verkaufssignalen darf erst nach rechtlicher Prüfung der bestehenden Verteilung von Scanner-Ergebnissen formuliert werden. Siehe interne Hinweise, Punkt 7.]

**Einschätzung:** Nach derzeitigem Verständnis erfordert das Modell keine Konzession. Ein Rechtsgutachten wird vor Marktstart eingeholt (Budgetposten Recht, AP5).

**Später:** Sollten Signal- oder Portfoliomodelle für Endkunden folgen, geschieht dies nicht unter eigener Lizenz, sondern unter dem Haftungsdach eines MiFID-II-lizenzierten Partners und erst nach rechtlicher Prüfung.

## Frage 8: Erlösmodell, Kunden, CAC

**B2C:** Drei Mitgliedschaftsstufen zu 19 €, 29 € und 59 € pro Monat, inklusive USt.

**B2B:** Unternehmenslizenz für Analyse- und Portfolio-Software, die lizenzierte Institutionen einsetzen: 10.000 € pro Jahr oder 5.000 € einmalig, je nach Leistungsumfang. [OFFEN: Netto- oder Bruttopreis festlegen; Abgrenzung der beiden Modelle festlegen.]

**Kunden und CAC:** Derzeit gibt es keine zahlenden Kunden; die Kundenakquisitionskosten (CAC) sind noch nicht gemessen. Umsätze beginnen mit dem Marktstart nach Gate 2 (ab Monat 17). B2B-Pilotkunden sind schon in der Betaphase möglich. CAC und Kundenwert messen wir ab Marktstart und prüfen sie in Gate 3 (Monat 21).

**Rechenbeispiel (keine Prognose):** Die durchschnittliche Budgetrate beträgt rund 12.500 € pro Monat. Der Nettoerlös je Abo nach 20 % österreichischer Umsatzsteuer beträgt 15,83 € (19 €), 24,17 € (29 €) bzw. 49,17 € (59 €). Zur Deckung von 12.500 € netto pro Monat wären ohne Kündigungen und ohne Akquisitionskosten rund 790, 517 bzw. 254 zahlende Kunden nötig. Bei B2B-Lizenzen zu 10.000 € netto pro Jahr (833 € pro Monat, Annahme) wären rund 15 Kunden nötig. Das Rechenbeispiel berücksichtigt weder Akquisitionskosten noch Abwanderung. Die Erlöse beginnen erst ab Monat 17.

---

## Interne Hinweise (nicht zur Einreichung)

Bu notlar Türkçedir. Değişikliklerin gerekçelerini ve açık noktaları içerir.

1. Soru 3, Forschungshinweis kaldırıldı. Gerekçe: n = 19.607 ve net +%0,90 değerleri repoda eşleşmedi (5 Ağustos kopyasında n = 15.795, validation boş). Kural 3.120 yapılandırmanın en iyisi olarak seçildi; White Reality Check ve SPA (p = 0,28 / 0,29) seçim şansını dışlamıyor. Bunun yatırımcıya performans olarak sunulması Level C kararıdır. Geri eklenecekse kaynak doğrulaması, "doğrulanmamış hipotez" etiketi ve onay gerekir.
2. Soru 3, tarih düzeltildi. Veritabanı sorgusu: 5.206 sonuçlanmış sinyal 12.09.2025 ile 22.05.2026 arasında. 09.09.2026 tarihi tüm arşivin (5.748 satır) son tarihi. 5.748 / 4.318 örtüşme ifadesi artık tüm arşive ait.
3. Soru 2, "Einzelposten 299.982 €" cümlesi kaldırıldı. T€ tablosu tam olarak 300,0'a toplanıyor; birim değerler belgelenmediği için bu cümle doğrulanamıyordu.
4. Soru 1, "gesperrten OOS-Zeitraums" ifadesi yeni bir prospektif pencereyle değiştirildi. Mevcut setler Durum C nedeniyle bağımsız OOS olarak kullanılamaz. Açık risk: 3–9. aylarda yeterli sayıda sonuçlanmış sinyal oluşup oluşmayacağı.
5. Soru 4, kronoloji düzeltildi (Remediation raporu: oos_status_c_remediation_v1_2026-10-15). "15.07. 16:52 UTC en eski kayıt" ifadesi eksik; yerel çalışma geçmişinde sınır 18:07 MESZ'de görünüyor. ECON hash'i yeniden üretilebiliyor; "belgelenemez" ifadesi artık yanlış. Eşikler 04.08.2026 kod sürümünde bulunuyor.
6. Soru 4, "gemessene Kosten" ifadesi "dokumentierte Kosten" olarak değiştirildi; çünkü hiçbir maliyet ölçülmedi.
7. Soru 7, BLOKE EDİCİ. "Üçüncü kişilere alım-satım sinyali verilmiyor" ifadesi repo kanıtlarıyla desteklenmiyor: 09.10.2026'da insan onaylı bir Telegram teslimatı kayıtlı; web yayın zinciri mevcut; scanner adayları (ör. NVAX, NTLA) önizleme olarak hazırlanmış. Hukuki değerlendirme olmadan bu ifade kullanılmamalı. Kamuya açık yüzeylerdeki +%0,40 düzeltmesi Level C kararıdır.
8. Soru 8, KDV: Avusturya normal oranı %20 varsayım olarak belirtildi. Müşteri sayıları 790 / 517 / 254 / 15 olarak düzeltildi (önce 520 ve 255). "50 € tek seferlik" iç referansı kaldırıldı. Churn ve CAC'in hesapta olmadığı belirtildi.
9. Soru 6, veri koruma: Türkiye'nin AB yeterlilik kararı yok. AB kişisel verilerine erişim varsa standart sözleşme maddeleri veya başka bir dayanak gerekir.

Göndermeden önce açık noktalar:

- Bloke edici: 7. madde (sinyal dağıtımının hukuki incelemesi); 3–9. aylarda Gate 1 örneklemi (4. madde); Forschungshinweis kararı (1. madde, varsayılan: kaldırıldı).
- Belgeler: 35.000 € öz kaynak; saatler ve sözleşme tarafları; işlem kısmındaki erişim kısıtı; FinSense ürün açıklaması.
- Hukuki: Türk hizmet sağlayıcılar için veri koruma sözleşme dayanağı; kurumsal bilgilerin teyidi; B2B fiyatının net mi brüt mü olduğu.
- Şirket türü ve sözleşme tarafı (1. soru).
- Fiyat, abonelik ve müşteri sayıları teyit edilene kadar varsayımdır.

Öneri: Bloke edici maddeler kapanmadan göndermeyin.
