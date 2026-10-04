# Tutkimus 15M – tulokset

Suunnitelma `docs/TUTKIMUS15_SUUNNITELMA.md` (lukittu ennen dataa). Testijakso 2025-01-01 00:00 – 2026-07-01 00:00 UTC, 15m-kynttilät, seuranta-aika 16 kynttilää (4 h), rajat ±1·A, siemen 20261004. Ei kuluja vaiheessa 1.

Markkinat: PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_DOGEUSD, PF_XRPUSD, PF_PEPEUSD. Mukana analyysissa (kattavuus ja eheys): **PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_DOGEUSD, PF_XRPUSD, PF_PEPEUSD** (6).

## Vaihe 1: ajoitus (ensisijainen, Holm 4 testille)

| Ryhmä | Signaaleja | Päiviä | Signaali ka | Vertailu ka | D | 95 % LV | p | p (Holm) | 1. puolisko | 2. puolisko | Markkinoita D > 0 | Päätös |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K long | 3947 | 533 | -0.0246 | -0.0499 | **+0.0253** | -0.0176 … +0.0680 | 0.2636 | 0.5272 | +0.0096 | +0.0397 | 5/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |
| K short | 3647 | 534 | +0.0418 | +0.0026 | **+0.0392** | -0.0029 … +0.0821 | 0.0660 | 0.2640 | +0.1004 | -0.0314 | 6/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |
| J long | 2680 | 477 | -0.0458 | -0.0032 | **-0.0426** | -0.0914 … +0.0056 | 0.0850 | 0.2640 | -0.0385 | -0.0478 | 1/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |
| J short | 2882 | 472 | +0.0032 | +0.0251 | **-0.0219** | -0.0771 … +0.0350 | 0.4552 | 0.5272 | -0.0167 | -0.0277 | 3/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |

D = signaalin pisteet − 50 satunnaisen vertailuhetken keskiarvo (sama markkina, suunta ja UTC-päivä). Epävarmuus päiväklusteribootstrapilla. D = +0,10 ≈ 55 % tavoiteosuus 50 %:n sijaan.

### Markkinakohtaiset tulokset (ensisijainen mittari, ei erillistä päätöstä)

| Ryhmä | Markkina | Signaaleja | D | 95 % LV | p (korjaamaton) |
|---|---|---|---|---|---|
| K long | PF_DOGEUSD | 682 | +0.0316 | -0.0450 … +0.1065 | 0.4212 |
| K long | PF_ETHUSD | 614 | +0.0290 | -0.0548 … +0.1113 | 0.4916 |
| K long | PF_PEPEUSD | 661 | +0.0071 | -0.0746 … +0.0886 | 0.8468 |
| K long | PF_SOLUSD | 619 | -0.0364 | -0.1208 … +0.0481 | 0.3910 |
| K long | PF_XBTUSD | 687 | +0.0556 | -0.0226 … +0.1363 | 0.1640 |
| K long | PF_XRPUSD | 684 | +0.0587 | -0.0211 … +0.1386 | 0.1484 |
| K short | PF_DOGEUSD | 618 | +0.0098 | -0.0770 … +0.0974 | 0.8302 |
| K short | PF_ETHUSD | 594 | +0.0001 | -0.0861 … +0.0857 | 0.9870 |
| K short | PF_PEPEUSD | 656 | +0.0278 | -0.0618 … +0.1147 | 0.5416 |
| K short | PF_SOLUSD | 621 | +0.0876 | +0.0072 … +0.1654 | 0.0340 |
| K short | PF_XBTUSD | 581 | +0.0653 | -0.0216 … +0.1539 | 0.1432 |
| K short | PF_XRPUSD | 577 | +0.0456 | -0.0448 … +0.1346 | 0.3244 |
| J long | PF_DOGEUSD | 437 | -0.0676 | -0.1735 … +0.0332 | 0.1874 |
| J long | PF_ETHUSD | 386 | -0.0076 | -0.1028 … +0.0842 | 0.8700 |
| J long | PF_PEPEUSD | 490 | -0.0313 | -0.1262 … +0.0621 | 0.4994 |
| J long | PF_SOLUSD | 440 | +0.0330 | -0.0645 … +0.1282 | 0.5348 |
| J long | PF_XBTUSD | 478 | -0.1025 | -0.1981 … -0.0100 | 0.0300 |
| J long | PF_XRPUSD | 449 | -0.0710 | -0.1666 … +0.0253 | 0.1468 |
| J short | PF_DOGEUSD | 483 | -0.0165 | -0.1076 … +0.0734 | 0.7212 |
| J short | PF_ETHUSD | 445 | +0.0214 | -0.0672 … +0.1120 | 0.6316 |
| J short | PF_PEPEUSD | 461 | +0.0300 | -0.0674 … +0.1286 | 0.5572 |
| J short | PF_SOLUSD | 473 | +0.0032 | -0.0944 … +0.0976 | 0.9796 |
| J short | PF_XBTUSD | 552 | -0.0331 | -0.1246 … +0.0585 | 0.4810 |
| J short | PF_XRPUSD | 468 | -0.1317 | -0.2267 … -0.0334 | 0.0078 |

## Täydentävät mittarit (eksploratiivisia, Benjamini–Hochberg)

| Mittari | n | Päiviä | Ero (signaali − vertailu) | 95 % LV | p | q (BH) |
|---|---|---|---|---|---|---|
| K yhteensä (±1·A) | 7594 | 546 | +0.0320 | +0.0012 … +0.0620 | 0.0398 | 0.0862 |
| K long ±2·A | 3947 | 533 | +0.0349 | -0.0101 … +0.0788 | 0.1266 | 0.2194 |
| K long tuotto 1 kynttilä (A) | 3947 | 533 | +0.0020 | -0.0366 … +0.0391 | 0.9214 | 0.9214 |
| K long tuotto 4 kynttilää (A) | 3947 | 533 | +0.0650 | -0.0298 … +0.1636 | 0.1780 | 0.2722 |
| K long tuotto 16 kynttilää (A) | 3947 | 533 | +0.3183 | +0.0848 … +0.5642 | 0.0066 | 0.0156 |
| K long MFE (A) | 3947 | 533 | +0.4327 | +0.2503 … +0.6512 | 0.0000 | 0.0000 |
| K long MAE (A) | 3947 | 533 | +0.2235 | +0.0687 … +0.3910 | 0.0044 | 0.0127 |
| K short ±2·A | 3647 | 534 | +0.0440 | -0.0001 … +0.0884 | 0.0508 | 0.1016 |
| K short tuotto 1 kynttilä (A) | 3647 | 534 | +0.0225 | -0.0173 … +0.0617 | 0.2632 | 0.3802 |
| K short tuotto 4 kynttilää (A) | 3647 | 534 | +0.0338 | -0.0527 … +0.1214 | 0.4346 | 0.5650 |
| K short tuotto 16 kynttilää (A) | 3647 | 534 | +0.2889 | +0.0879 … +0.4840 | 0.0050 | 0.0130 |
| K short MFE (A) | 3647 | 534 | +0.4943 | +0.3455 … +0.6474 | 0.0000 | 0.0000 |
| K short MAE (A) | 3647 | 534 | +0.2781 | +0.1312 … +0.4274 | 0.0000 | 0.0000 |
| J yhteensä (±1·A) | 5562 | 543 | -0.0319 | -0.0690 … +0.0049 | 0.0880 | 0.1634 |
| J long ±2·A | 2680 | 477 | -0.0186 | -0.0736 … +0.0361 | 0.4940 | 0.5838 |
| J long tuotto 1 kynttilä (A) | 2680 | 477 | -0.0453 | -0.1055 … +0.0170 | 0.1520 | 0.2470 |
| J long tuotto 4 kynttilää (A) | 2680 | 477 | -0.0530 | -0.2057 … +0.1012 | 0.4816 | 0.5838 |
| J long tuotto 16 kynttilää (A) | 2680 | 477 | -0.4842 | -0.7570 … -0.2104 | 0.0006 | 0.0019 |
| J long MFE (A) | 2680 | 477 | +0.5132 | +0.3074 … +0.7260 | 0.0000 | 0.0000 |
| J long MAE (A) | 2680 | 477 | +0.7272 | +0.5443 … +0.9259 | 0.0000 | 0.0000 |
| J short ±2·A | 2882 | 472 | -0.0268 | -0.0864 … +0.0335 | 0.3860 | 0.5282 |
| J short tuotto 1 kynttilä (A) | 2882 | 472 | -0.0164 | -0.0931 … +0.0605 | 0.6566 | 0.7113 |
| J short tuotto 4 kynttilää (A) | 2882 | 472 | -0.0102 | -0.1484 … +0.1319 | 0.8608 | 0.8952 |
| J short tuotto 16 kynttilää (A) | 2882 | 472 | -0.0940 | -0.4474 … +0.2561 | 0.6050 | 0.6839 |
| J short MFE (A) | 2882 | 472 | +0.8125 | +0.5328 … +1.1125 | 0.0000 | 0.0000 |
| J short MAE (A) | 2882 | 472 | +0.6609 | +0.4417 … +0.9085 | 0.0000 | 0.0000 |

## Lopputulosten jakauma ja epäselvien herkkyys (±1·A)

| Ryhmä | tavoite | stop | aikaraja | epäselvä | Signaalien tavoiteosuus | Vertailujen tavoiteosuus | D, jos epäselvä = +1 | D, jos epäselvä = −1 |
|---|---|---|---|---|---|---|---|---|
| K long | 1876 | 1976 | 26 | 69 | 47.5% | 46.0% | +0.0335 | +0.0171 |
| K short | 1853 | 1701 | 17 | 76 | 50.8% | 48.8% | +0.0521 | +0.0263 |
| J long | 1214 | 1335 | 17 | 114 | 45.3% | 48.5% | -0.0076 | -0.0776 |
| J short | 1379 | 1369 | 6 | 128 | 47.8% | 49.9% | +0.0147 | -0.0584 |

## Liikkeiden koko suhteessa kuluihin (kuvaileva, ei päätöstä)

Kulumalli: taker 0.05% × 2, liukuma 0.02% avaus + 0.05% stop, puolikas spread × 2 (nykyinen mitattu 2026-10-04 07:49 UTC, vähintään 0.005%). C = edestakainen kulu stop-skenaariossa. p* = ½ + C/(2A) on tavoiteosuus, jolla symmetrinen ±1·A-kauppa olisi kulujen jälkeen nollatuloksessa.

| Markkina | Puolikas spread | C (% hinnasta) | A mediaani (% hinnasta) | C/A mediaani | p* mediaani | Signaaleja, joissa p* > 100 % |
|---|---|---|---|---|---|---|
| PF_XBTUSD | 0.0050% | 0.180% | 0.260% | 0.69 | 84.7% | 23.1% |
| PF_ETHUSD | 0.0050% | 0.180% | 0.438% | 0.41 | 70.6% | 3.7% |
| PF_SOLUSD | 0.0050% | 0.180% | 0.492% | 0.37 | 68.3% | 1.1% |
| PF_DOGEUSD | 0.0054% | 0.181% | 0.494% | 0.37 | 68.3% | 1.1% |
| PF_XRPUSD | 0.0050% | 0.180% | 0.448% | 0.40 | 70.1% | 3.3% |
| PF_PEPEUSD | 0.0502% | 0.270% | 0.592% | 0.46 | 72.8% | 6.4% |

| Ryhmä | Signaalien tavoiteosuus | p* keskiarvo | Ero (tavoiteosuus − p*) |
|---|---|---|---|
| K long | 47.5% | 74.5% | -27.0% |
| K short | 50.8% | 75.7% | -24.9% |
| J long | 45.3% | 76.6% | -31.3% |
| J short | 47.8% | 74.7% | -26.9% |

## Vaihe 2: kannattavuus kulujen jälkeen (ehdollinen)

* **K long:** vaihetta 2 ei ajettu – vaiheen 1 päätös: EI NÄYTTÖÄ AJOITUSEDUSTA.
* **K short:** vaihetta 2 ei ajettu – vaiheen 1 päätös: EI NÄYTTÖÄ AJOITUSEDUSTA.
* **J long:** vaihetta 2 ei ajettu – vaiheen 1 päätös: EI NÄYTTÖÄ AJOITUSEDUSTA.
* **J short:** vaihetta 2 ei ajettu – vaiheen 1 päätös: EI NÄYTTÖÄ AJOITUSEDUSTA.

Vaihetta 2 ei ajettu yhdellekään ryhmälle, koska ajoitusetua ei osoitettu suunnitelman mukaisesti.

Kaikki luvut ovat paperilaskentaa historiadatalla. Toimeksiantoja ei lähetetty.
