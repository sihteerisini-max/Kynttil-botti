# Vaihe 1 – ajoitustutkimus (ARVIOINTI-aineisto)

Aineisto 2026-07-15T00:00 – 2026-09-15T00:00 UTC · suunnitelma docs/VAIHE1_AJOITUSTUTKIMUS.md · ei kuluja · siemen 20261001

## Markkinat ja kattavuus

| Markkina | Kauppaminuutteja | Minuutteja | Mukana |
|---|---|---|---|
| PF_DOGEUSD | 86.3% | 89280 | EI (kattavuus tai historia) |
| PF_SOLUSD | 95.9% | 89280 | kyllä |
| PF_SUIUSD | 84.0% | 89280 | EI (kattavuus tai historia) |
| PF_XRPUSD | 86.3% | 89280 | EI (kattavuus tai historia) |
| PF_ZECUSD | 88.3% | 89280 | EI (kattavuus tai historia) |

## Ensisijainen mittari

Signaalin pisteet − saman markkinan, suunnan ja UTC-päivän 50 satunnaisen hetken keskiarvo (±1,0·A, 15 min). Epävarmuus: päiväklusteribootstrap. Holm-korjaus kahdelle testille (K, J).

| Tyyppi | Signaaleja | Päiviä | Signaali ka | Vertailu ka | Ero | 95 % LV | p | p (Holm) |
|---|---|---|---|---|---|---|---|---|
| K | 2449 | 62 | -0.0116 | +0.0005 | **-0.0121** | -0.0557 … +0.0330 | 0.6138 | 0.6138 |
| J | 1816 | 62 | -0.0659 | -0.0019 | **-0.0640** | -0.1111 … -0.0185 | 0.0046 | 0.0092 |

## Päätös (ennakkoon lukittu sääntö)

* **K**: EI NÄYTTÖÄ AJOITUSEDUSTA. Puoliskot +0.0267 / -0.0427; markkinoita, joissa ero > 0: 0/1.
* **J**: TILASTOLLINEN ERO, MUTTA EI JOHDONMUKAINEN (puoliskot tai markkinat ristiriidassa) – ei osoitettu. Puoliskot -0.0862 / -0.0371; markkinoita, joissa ero > 0: 0/1.

## Täydentävät mittarit (eksploratiivisia, Benjamini–Hochberg)

| Mittari | n | Päiviä | Ero (signaali − vertailu) | 95 % LV | p | q (BH) |
|---|---|---|---|---|---|---|
| K long | 1217 | 62 | -0.0287 | -0.0836 … +0.0303 | 0.3368 | 0.5880 |
| K short | 1232 | 62 | +0.0044 | -0.0628 … +0.0721 | 0.9026 | 0.9026 |
| K ±2·A | 2449 | 62 | +0.0046 | -0.0391 … +0.0501 | 0.8520 | 0.9021 |
| K tuotto 1 min (A) | 2449 | 62 | -0.0457 | -0.0938 … +0.0028 | 0.0630 | 0.1620 |
| K tuotto 5 min (A) | 2449 | 62 | -0.0234 | -0.1391 … +0.0967 | 0.6774 | 0.7621 |
| K tuotto 15 min (A) | 2449 | 62 | -0.1058 | -0.3398 … +0.1204 | 0.3612 | 0.5880 |
| K MFE (A) | 2449 | 62 | +0.0677 | -0.0745 … +0.2188 | 0.3674 | 0.5880 |
| K MAE (A) | 2449 | 62 | +0.4743 | +0.2746 … +0.6972 | 0.0000 | 0.0000 |
| K PF_SOLUSD | 2449 | 62 | -0.0121 | -0.0572 … +0.0332 | 0.6002 | 0.7380 |
| J long | 976 | 62 | -0.0228 | -0.0994 … +0.0490 | 0.5550 | 0.7380 |
| J short | 840 | 62 | -0.1120 | -0.1758 … -0.0496 | 0.0000 | 0.0000 |
| J ±2·A | 1816 | 62 | -0.0358 | -0.0919 … +0.0185 | 0.2000 | 0.4500 |
| J tuotto 1 min (A) | 1816 | 62 | -0.1901 | -0.2636 … -0.1201 | 0.0000 | 0.0000 |
| J tuotto 5 min (A) | 1816 | 62 | -0.0818 | -0.2623 … +0.1028 | 0.3920 | 0.5880 |
| J tuotto 15 min (A) | 1816 | 62 | +0.1110 | -0.2780 … +0.5407 | 0.6150 | 0.7380 |
| J MFE (A) | 1816 | 62 | +1.2605 | +0.8515 … +1.7148 | 0.0000 | 0.0000 |
| J MAE (A) | 1816 | 62 | +0.4929 | +0.3223 … +0.6629 | 0.0000 | 0.0000 |
| J PF_SOLUSD | 1816 | 62 | -0.0640 | -0.1112 … -0.0185 | 0.0064 | 0.0192 |

## Saman kynttilän osumat (epäselvä) ja herkkyys

| Tyyppi | Epäselviä (signaalit) | Vertailujen epäselvä-osuus | Ero, jos epäselvä = +1 | Ero, jos epäselvä = −1 |
|---|---|---|---|---|
| K | 28 (1.1%) | 1.5% | -0.0152 | -0.0089 |
| J | 79 (4.4%) | 1.3% | -0.0335 | -0.0946 |

## Lopputulosten jakauma (±1·A)

| Tyyppi | tavoite | stop | aikaraja | epäselvä | vertailun tavoiteosuus |
|---|---|---|---|---|---|
| K | 1194 | 1223 | 4 | 28 | 49.0% |
| J | 808 | 928 | 1 | 79 | 49.0% |

Tulokset kertovat vain ajoituksesta ennen kuluja. Kannattavuus kulujen jälkeen arvioidaan erikseen (vaihe 2).
