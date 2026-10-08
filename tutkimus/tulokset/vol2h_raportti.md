# Kehitystesti VOL2H – tulokset (KEHITYSDATA, ei näyttöä)

Suunnitelma `docs/KEHITYSTESTI_VOL2H_SUUNNITELMA.md` (lukittu ennen laskentaa). Jakso 2026-07-15T00:00 – 2026-09-15T00:00 UTC (62 vrk), 1m-kynttilät, markkinat PF_DOGEUSD, PF_SOLUSD, PF_SUIUSD, PF_XRPUSD, PF_ZECUSD. Tilikohtaiset tappiorajat pois kaikista malleista. ½ spread: DOGE 0.0123%, SOL 0.0100%, SUI 0.0150%, XRP 0.0100%, ZEC 0.0269%.


## Tili K (aj1-kaanto, kääntymissignaalit)

| Malli | Suunta | Kauppoja | Kauppoja/pv | Osuma (netto > 0) | Tavoite / stop / aika / epäselvä | Keskim. voitto | Keskim. tappio | Kulut/kauppa | Netto/kauppa | Netto/kauppa (riskiyks.) | Netto yht. | Netto yht. vakiopääoma | Suurin pudotus (vakiopääoma) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NYKYINEN | kaikki | 9714 | 156.7 | 4.2% | 2939 / 5321 / 1377 / 77 | +0.79 $ | -1.11 $ | 1.04 $ | -1.03 $ | -0.612 | -10,000 $ | -297,393 $ | 297,393 $ (2973.9%) |
| NYKYINEN | long | 4886 | 78.8 | 4.2% | 1465 / 2723 / 658 / 40 | +0.98 $ | -1.09 $ | 1.05 $ | -1.00 $ | -0.620 | -4,896 $ | -151,512 $ | 151,512 $ (1515.1%) |
| NYKYINEN | short | 4828 | 77.9 | 4.1% | 1474 / 2598 / 719 / 37 | +0.60 $ | -1.13 $ | 1.03 $ | -1.06 $ | -0.604 | -5,104 $ | -145,881 $ | 145,885 $ (1458.9%) |
| V1 | kaikki | 1195 | 19.3 | 40.5% | 413 / 480 / 302 / 0 | +9.30 $ | -18.28 $ | 6.34 $ | -7.11 $ | -0.315 | -8,493 $ | -18,824 $ | 18,850 $ (188.5%) |
| V1 | long | 606 | 9.8 | 39.4% | 198 / 260 / 148 / 0 | +9.34 $ | -17.90 $ | 6.29 $ | -7.15 $ | -0.346 | -4,335 $ | -10,475 $ | 10,482 $ (104.8%) |
| V1 | short | 589 | 9.5 | 41.6% | 215 / 220 / 154 / 0 | +9.26 $ | -18.69 $ | 6.40 $ | -7.06 $ | -0.283 | -4,158 $ | -8,348 $ | 8,381 $ (83.8%) |
| V2 | kaikki | 120 | 1.9 | 61.7% | 72 / 32 / 15 / 1 | +11.18 $ | -38.33 $ | 8.04 $ | -7.80 $ | -0.163 | -936 $ | -978 $ | 978 $ (9.8%) |
| V2 | long | 60 | 1.0 | 56.7% | 33 / 17 / 9 / 1 | +10.82 $ | -37.63 $ | 8.26 $ | -10.18 $ | -0.213 | -611 $ | -639 $ | 639 $ (6.4%) |
| V2 | short | 60 | 1.0 | 66.7% | 39 / 15 / 6 / 0 | +11.49 $ | -39.25 $ | 7.82 $ | -5.42 $ | -0.113 | -325 $ | -339 $ | 388 $ (3.9%) |

**Tilaisuudet ja ohitukset (K):**

| Malli | Signaaleja/pv | Avattu/pv | Ohitettu: kulusuodatin | Ohitettu: markkinassa jo positio | Ohitettu: 3 positiota auki | Muut ohitukset |
|---|---|---|---|---|---|---|
| NYKYINEN | 214.0 | 156.7 | 0 | 1094 | 262 | 2196 |
| V1 | 214.0 | 19.3 | 11814 | 234 | 23 | 0 |
| V2 | 214.0 | 1.9 | 13128 | 18 | 0 | 0 |

**Arviointi (K):**

| Malli | Netto/kauppa riskiyksikköinä, 95 % LV | Puoliskot | K2: tukeeko suurempaa kauppamäärää | Päiväero vs NYKYINEN (riskiyks./pv), 95 % LV | K1: parantaako nettotulosta |
|---|---|---|---|---|---|
| NYKYINEN | -0.612 (-0.633 … -0.590) | -0.652 / -0.563 | **EI TUE** | – | **–** |
| V1 | -0.315 (-0.357 … -0.277) | -0.374 / -0.310 | **EI TUE** | +89.86 (+82.15 … +97.14) | **PARANTAA** |
| V2 | -0.163 (-0.302 … -0.056) | -0.525 / -0.160 | **EI TUE** | +95.62 (+89.43 … +101.87) | **PARANTAA** |

## Tili J (aj1-jatko, jatkumissignaalit)

| Malli | Suunta | Kauppoja | Kauppoja/pv | Osuma (netto > 0) | Tavoite / stop / aika / epäselvä | Keskim. voitto | Keskim. tappio | Kulut/kauppa | Netto/kauppa | Netto/kauppa (riskiyks.) | Netto yht. | Netto yht. vakiopääoma | Suurin pudotus (vakiopääoma) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NYKYINEN | kaikki | 8080 | 130.3 | 7.2% | 2419 / 4265 / 1385 / 11 | +1.04 $ | -1.41 $ | 1.20 $ | -1.24 $ | -0.575 | -10,000 $ | -232,378 $ | 232,378 $ (2323.8%) |
| NYKYINEN | long | 4129 | 66.6 | 6.7% | 1226 / 2189 / 709 / 5 | +0.89 $ | -1.41 $ | 1.14 $ | -1.26 $ | -0.571 | -5,191 $ | -117,940 $ | 117,940 $ (1179.4%) |
| NYKYINEN | short | 3951 | 63.7 | 7.7% | 1193 / 2076 / 676 / 6 | +1.18 $ | -1.42 $ | 1.26 $ | -1.22 $ | -0.579 | -4,809 $ | -114,438 $ | 114,438 $ (1144.4%) |
| V1 | kaikki | 755 | 12.2 | 41.3% | 282 / 313 / 152 / 8 | +10.89 $ | -23.75 $ | 7.76 $ | -9.44 $ | -0.329 | -7,125 $ | -12,401 $ | 12,425 $ (124.2%) |
| V1 | long | 380 | 6.1 | 43.9% | 147 / 140 / 92 / 1 | +11.00 $ | -23.36 $ | 7.98 $ | -8.26 $ | -0.276 | -3,139 $ | -5,240 $ | 5,303 $ (53.0%) |
| V1 | short | 375 | 6.0 | 38.7% | 135 / 173 / 60 / 7 | +10.76 $ | -24.11 $ | 7.55 $ | -10.63 $ | -0.382 | -3,986 $ | -7,161 $ | 7,161 $ (71.6%) |
| V2 | kaikki | 87 | 1.4 | 59.8% | 48 / 22 / 13 / 4 | +10.88 $ | -41.03 $ | 7.98 $ | -10.00 $ | -0.208 | -870 $ | -905 $ | 972 $ (9.7%) |
| V2 | long | 46 | 0.7 | 65.2% | 29 / 13 / 4 / 0 | +11.09 $ | -42.27 $ | 8.02 $ | -7.47 $ | -0.154 | -344 $ | -355 $ | 458 $ (4.6%) |
| V2 | short | 41 | 0.7 | 53.7% | 19 / 9 / 9 / 4 | +10.61 $ | -39.98 $ | 7.92 $ | -12.84 $ | -0.268 | -526 $ | -550 $ | 561 $ (5.6%) |

**Tilaisuudet ja ohitukset (J):**

| Malli | Signaaleja/pv | Avattu/pv | Ohitettu: kulusuodatin | Ohitettu: markkinassa jo positio | Ohitettu: 3 positiota auki | Muut ohitukset |
|---|---|---|---|---|---|---|
| NYKYINEN | 163.0 | 130.3 | 0 | 1519 | 315 | 193 |
| V1 | 163.0 | 12.2 | 9228 | 105 | 20 | 0 |
| V2 | 163.0 | 1.4 | 10014 | 7 | 0 | 0 |

**Arviointi (J):**

| Malli | Netto/kauppa riskiyksikköinä, 95 % LV | Puoliskot | K2: tukeeko suurempaa kauppamäärää | Päiväero vs NYKYINEN (riskiyks./pv), 95 % LV | K1: parantaako nettotulosta |
|---|---|---|---|---|---|
| NYKYINEN | -0.575 (-0.599 … -0.549) | -0.617 / -0.521 | **EI TUE** | – | **–** |
| V1 | -0.329 (-0.384 … -0.275) | -0.403 / -0.321 | **EI TUE** | +70.96 (+64.16 … +77.74) | **PARANTAA** |
| V2 | -0.208 (-0.297 … -0.012) | +nan / -0.208 | **EI TUE** | +74.67 (+68.84 … +80.56) | **PARANTAA** |

## V-mallien tavoite- ja stopetäisyydet (avatut kaupat, % hinnasta)

| Tili | Malli | M mediaani | Tavoite mediaani | Stop mediaani | Arvioidut kulut mediaani | Tavoite / kulut mediaani |
|---|---|---|---|---|---|---|
| K | V1 | 0.443% | 0.443% | 0.443% | 0.170% | 2.51 |
| K | V2 | 0.848% | 0.424% | 0.848% | 0.165% | 2.39 |
| J | V1 | 0.434% | 0.434% | 0.434% | 0.170% | 2.49 |
| J | V2 | 0.851% | 0.426% | 0.851% | 0.165% | 2.51 |

Riskiyksikkö = nettotulos / kaupan riskibudjetti (−1 = suunniteltu täysi tappio). Vakiopääomavastine = riskiyksiköt × 50 $ (0,5 % × 10 000 $), jolloin korkoa korolle ei vääristä vertailua. Kaikki luvut ovat paperilaskentaa jo käytetyllä kehitysdatalla.
