# Tutkimus 15M – markkinavalinta, suunnitelman versio 1.0 (ajettu 4.10.2026 klo 06:48 UTC)

> Tallennettu sellaisenaan. Lukitun version 1.0 sääntö **ei valinnut yhtään markkinaa**, joten
> tutkimusta ei olisi ajettu. Suunnitelmaan tehtiin muutos 1.1 ennen kuin testijakson dataa ladattiin
> (`docs/TUTKIMUS15_SUUNNITELMA.md`, luku 13).

Valintajakso on 2024-10-01 00:00 – 2025-01-01 00:00 UTC, eli ennen testijaksoa. Ehdokkaita oli 114
(PF_*USD, flexible_futures, tradeable, ei tradfi, avattu viimeistään 1.10.2024).

**Valitut markkinat:** – Vain 0 markkinaa täytti ehdot (< 4), joten tutkimusta ei ajettu.

API palautti kaikilla kymmenellä markkinalla kaikki valintajakson minuutit (132 480/132 480), eikä
yhtään riviä puuttunut. Puuttuvat kauppaminuutit ovat siis API:n palauttamia nollavolyymin minuutteja
eli aidosti kaupattomia minuutteja, eivät hakuvirheitä.

| # | Markkina | Päivän nimellisvolyymin mediaani (USD) | 15m data alkaa | Kauppaminuutteja (1m) | Tulos |
|---|---|---|---|---|---|
| 1 | PF_XBTUSD | 446,999,380 | 2024-10-01 00:00 | 98.63% | kauppaminuutit < 99 % |
| 2 | PF_ETHUSD | 88,742,249 | 2024-10-01 00:00 | 96.90% | kauppaminuutit < 99 % |
| 3 | PF_SOLUSD | 67,712,677 | 2024-10-01 00:00 | 94.16% | kauppaminuutit < 99 % |
| 4 | PF_DOGEUSD | 37,772,648 | 2024-10-01 00:00 | 91.63% | kauppaminuutit < 99 % |
| 5 | PF_XRPUSD | 25,316,558 | 2024-10-01 00:00 | 88.71% | kauppaminuutit < 99 % |
| 6 | PF_PEPEUSD | 13,549,412 | 2024-10-01 00:00 | 86.94% | kauppaminuutit < 99 % |
| 7 | PF_WIFUSD | 12,646,974 | 2024-10-01 00:00 | 84.05% | kauppaminuutit < 99 % |
| 8 | PF_SUIUSD | 9,034,461 | 2024-10-01 00:00 | 79.48% | kauppaminuutit < 99 % |
| 9 | PF_ADAUSD | 8,049,998 | 2024-10-01 00:00 | 79.95% | kauppaminuutit < 99 % |
| 10 | PF_POPCATUSD | 4,420,042 | 2024-10-01 00:00 | 67.42% | kauppaminuutit < 99 % |
| 11–30 | (LINK, DOT, UNI, TAO, NEAR, AVAX, LTC, BONK, BNB, SHIB, CRV, INJ, WLD, AAVE, ARB, TIA, ATOM, RUNE, FIL, APT) | 4,216,125 … 934,794 | 2024-10-01 00:00 | – | ei 10 likvideimmän joukossa |
