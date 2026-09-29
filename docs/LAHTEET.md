# Kuvioiden lähteet ja omat numeeriset oletukset

Kirjallisuuden määritelmät ovat sanallisia. Lähes kaikki numeeriset raja-arvot ovat tämän botin
omia oletuksia, eivätkä ne tule lähteistä. Poikkeus on Bulkowskin vasaran ja tähdenlennon
"varjo vähintään 2 × runko".

## Lähteet

* **[SC]** StockCharts ChartSchool: *Candlestick Pattern Dictionary*.
  https://chartschool.stockcharts.com/table-of-contents/chart-analysis/candlestick-charts/candlestick-pattern-dictionary
* **[TB]** Thomas N. Bulkowski, ThePatternSite.com (tunnistusohjeet, "Identification Guidelines").
  Sivut: Hammer.html, HangingMan.html, HammerInv.html, ShootingStar.html, BullEngulfing.html,
  Dragonfly.html, Gravestone.html, LongLegDoji.html, WhiteMarubozu.html. Bulkowskin kirja
  *Encyclopedia of Candlestick Charts* (Wiley 2008) käyttää samoja ohjeita. Kirjaa itseään ei ole
  tässä tarkistettu.
* Investopedia estyi hakutyökalussa, eikä sitä ole käytetty.

## Kuvioittain: lähteen määritelmä | oma numeerinen oletus

| Kuvio | Muoto lähteen mukaan | Tausta lähteen mukaan | Oma numeerinen oletus (botti) |
|---|---|---|---|
| Doji | Avaus ja päätös "käytännössä yhtä suuret" [SC], "muutaman sentin sisällä" [TB] | Ei trendivaatimusta [SC, TB] | runko ≤ 10 % vaihteluvälistä; koko ≥ 0,3 × 20 ed. keskim. |
| Sudenkorento-doji | Avaus ja päätös huipussa [SC]; pitkä alavarjo, pieni runko [TB] | "None required" [TB] | doji + yläsvarjo ≤ 10 % + alavarjo ≥ 60 % |
| Hautakivi-doji | Doji pohjassa [SC]; pitkä yläsvarjo, vähän tai ei alavarjoa [TB] | "None required" [TB] | doji + alavarjo ≤ 10 % + yläsvarjo ≥ 60 % |
| Pitkäjalkainen doji | Pitkät ylä- ja alavarjot, doji keskellä [SC, TB] | Ei [TB] | doji + molemmat varjot ≥ 30 % + koko ≥ 1,0 × keskim. |
| Vasara | Pitkä alavarjo "vähintään 2–3 × runko", vähän tai ei yläsvarjoa [TB] | Muodostuu laskussa [SC, TB] | alavarjo ≥ 2 × runko ja ≥ 60 % R, yläsvarjo ≤ 15 % R, runko > 10 % R; lasku = 10 min regressioliike ≤ −1,5 × keskim. R |
| Hirttäytyjä | Pieni runko pitkän alavarjon päällä [TB] | Nousussa [SC, TB] | kuten vasara; nousu ≥ +1,5 × keskim. R |
| Käänteinen vasara | Pieni runko alhaalla, pitkä yläsvarjo, ei doji [SC, TB] | Laskussa [SC, TB] | yläsvarjo ≥ 2 × runko ja ≥ 60 % R, alavarjo ≤ 15 % R. **Ero:** [TB] määrittelee kuvion kahden kynttilän kuvioksi (ensin pitkä laskeva kynttilä, avaus sen päätöksen alapuolella). Botti käyttää yhden kynttilän muotoa kuten [SC]. |
| Tähdenlento | Pieni runko (ei doji), vähän tai ei alavarjoa, yläsvarjo "vähintään 2 × runko" [TB] | Nousussa [SC, TB] | kuten käänteinen vasara; nousu ≥ +1,5 |
| Nouseva peittävä | Laskevaa kynttilää seuraa nouseva, jonka runko peittää edellisen rungon; varjoilla ei väliä [SC, TB]; "open below the prior close" [TB] | Laskun lopussa [SC, TB] | avaus ≤ ed. päätös (**yhtäsuuruus sallittu**, koska krypto käy tauotta ja avaus on lähes aina edellinen päätös); päätös > ed. avaus; runko > ed. runko; ed. runko > 10 % ed. R |
| Laskeva peittävä | Peilikuva [SC] | Nousun lopussa [SC] | peilikuva |
| Marubozu | Ei varjoja [SC]; "tall … with no upper or lower shadows" [TB] | "None required" [TB]; pitkä kynttilä [TB] | runko ≥ 90 % R; koko ≥ 1,2 × keskim. R |

Yhteiset oletukset: 1 min kynttilät, keskiarvot 20 edeltävästä suljetusta kynttilästä, trendi-ikkuna
10 kynttilää. Kynttilää ei tulkita, jos sen vaihteluväli on alle 0,3 × keskiarvo. Trendi- ja
kokoehdot ovat **taustaehtoja**, muut **muotoehtoja** (`kynttilatulkki/komponentit.py`).

## Tiedossa olevat erot lähteisiin

1. Peittävä kuvio: [TB] vaatii avauksen edellisen päätöksen alapuolelle. Botti sallii
   yhtäsuuruuden. Jatkuvasti käyvässä kryptossa avaus on lähes aina täsmälleen edellinen päätös,
   joten tiukka ehto hylkäisi lähes kaikki. Tämä on oma oletus, ja se kirjataan erikseen.
2. Käänteinen vasara: [TB] kahden kynttilän kuvio, botti ja [SC] yksi kynttilä.
3. Kaikki prosenttirajat ovat omia oletuksia.

Määritelmää ei kiristetä pelkän esiintymistiheyden perusteella. Muutoksen perusteena on
käytettävä luokiteltuja arvioita (`validointi/arviointi`).
