# Markkinavaihto 30.9.2026 klo 20.10 (17:10 UTC)

**Paperikauppaa.** Tilejä ei nollattu, eikä muita sääntöjä muutettu. Testijakson alku (15:21 UTC)
ja loppu (28.10. 15:21 UTC) pysyvät ennallaan.

| | Markkinat |
|---|---|
| ennen (15:21–17:10 UTC) | PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_ZECUSD, PF_XRPUSD |
| jälkeen (17:10 UTC alkaen) | **PF_SUIUSD, PF_ZECUSD, PF_XRPUSD, PF_DOGEUSD, PF_SOLUSD** |

* Botin loki: `MARKKINAT VAIHDETTU 2026-09-30 17:10 UTC`.
* Tapahtuma `markkinat_vaihdettu` tallentui tiedostoihin `tapahtumat_<versio>.jsonl`.
* Vaihto tehtiin koodilla, commit 4c7a749.
* Ennen vaihtoa kummallakaan tilillä ei ollut kauppoja eikä avoimia positioita (pääoma 10 000 USD).
* Tulokset raportoidaan erikseen avausajan mukaan: ennen vaihtoa ja vaihdon jälkeen. Kaupankäyntikohteet
  muuttuivat, joten osia ei yhdistetä.

## Valintaperuste (Jessen pyyntö: enemmän suhteellista 1 min vaihtelua)

Sama markkina ja instrumentti kuin ennen: Kraken Derivatives, PF-perpetualit. Mukana olivat
25 vaihdetuinta kryptoa; kulta, öljy ja osakeperpetualit jätettiin pois. Data haettiin 30.9.2026:

* 1 min kynttilät 27.9. 17:03 – 30.9. 17:03 UTC (72 h)
* spread 6 tickerinäytteestä ja orderbook 3 näytteestä klo 17:03–17:06 UTC.

**Ehdot:**

1. kauppoja vähintään 95 %:ssa minuuteista
2. volyymi 72 tunnissa vähintään 40 M$ (noin 13 M$ vuorokaudessa)
3. spreadin mediaani enintään 8 bp
4. orderbookissa vähintään 150 k$ ±0,25 %:n sisällä heikommalla puolella (mediaani).

**Järjestys:** ehdot täyttävistä valittiin viisi, joiden 1 min vaihteluvälin (high − low) / close
mediaani oli suurin. Mediaani ei reagoi yksittäisiin piikkeihin.

| Markkina | Aktiiviset min | 1 min vaihteluväli, mediaani | 1 min tuottojen keskihajonta | Volyymi / 24 h | Spread | Syvyys ±0,25 % | Tulos |
|---|---|---|---|---|---|---|---|
| SUI | 100 % | 20,5 bp | 18,8 bp | 19,8 M$ | 4,19 bp | 0,19 M$ | valittu |
| ZEC | 97 % | 14,3 bp | 16,9 bp | 43,7 M$ | 6,19 bp | 0,70 M$ | valittu |
| XRP | 99 % | 11,1 bp | 11,6 bp | 49,0 M$ | 3,31 bp | 1,47 M$ | valittu |
| DOGE | 97 % | 9,7 bp | 11,6 bp | 15,6 M$ | 1,05 bp | 0,38 M$ | valittu |
| SOL | 99 % | 9,3 bp | 9,5 bp | 74,4 M$ | 0,83 bp | 2,76 M$ | valittu |
| ETH | 100 % | 6,2 bp | 6,6 bp | 111,5 M$ | 0,37 bp | 12,1 M$ | poistui (vaihtelu pienempi) |
| XBT | 100 % | 5,1 bp | 5,3 bp | 475,8 M$ | 0,12 bp | 27,9 M$ | poistui (vaihtelu pienempi) |
| NEAR | 95 % | 23,4 bp | 25,9 bp | 23,7 M$ | 17,4 bp | 0,10 M$ | karsittu: spread, syvyys |
| LINK | 97 % | 13,3 bp | 15,9 bp | 12,7 M$ | 6,24 bp | 0,21 M$ | karsittu: volyymi (38 M$ / 72 h) |
| ADA | 96 % | 13,2 bp | 14,9 bp | 7,4 M$ | 4,82 bp | 0,22 M$ | karsittu: volyymi |
| HYPE | 82 % | 7,1 bp | 10,0 bp | 19,7 M$ | 5,82 bp | 0,88 M$ | karsittu: kauppattomia minuutteja |

AVAX, UNI, TAO, PUMP ja muut karsiutuivat kauppattomien minuuttien osuuden (yli 5 %) tai
spreadin vuoksi. Vaihtelun mediaani oli uusilla viidellä keskimäärin 13,0 bp ja vanhoilla 9,2 bp.

**Huomio:** uusien markkinoiden spread on suurempi (SUI 4,2 bp ja ZEC 6,2 bp, kun XBT:llä se oli
0,1 bp), ja orderbook on ohuempi. Kulusuodatin ja kulumalli ottavat reaaliaikaisen spreadin
huomioon samoilla säännöillä kuin ennen.
