# Tutkimus 15M – ajo 1 (4.10.2026 klo 07:53 UTC): VIRHEELLINEN, säilytetty sellaisenaan

> **Miksi tämä on virheellinen:** A laskettiin juoksevalla summalla. Kahdessa 13 156 signaalista
> (PEPE 1.11.2025 klo 08:45 ja 09:15) vertailujoukkoon osui hetki pitkältä kaupattomalta jaksolta.
> Sen oikea A on 0, mutta laskettuna siihen jäi liukulukujäännös. Suunnitelman mukaan tällaiset
> hetket jätetään pois (A = 0).
>
> Virhe näkyy täydentävien mittareiden mahdottomina arvoina (esim. −692 751 869 A). Ensisijaisiin
> pisteisiin, jotka on rajattu välille [−1, +1], vaikutus on hyvin pieni.
>
> Korjattu ajo: `raportti.md`. Ensisijaiset taulukot ovat alla sellaisenaan. Täydentävät taulukot
> ovat Tutkimus15-palvelun ajon 1 tiedostossa (Railway-volume `/data/t15`), ja niiden
> virheettömät versiot ovat korjatussa raportissa.

## Vaihe 1: ajoitus (ensisijainen, Holm 4 testille) – ajo 1

| Ryhmä | Signaaleja | Päiviä | Signaali ka | Vertailu ka | D | 95 % LV | p | p (Holm) | 1. puolisko | 2. puolisko | Markkinoita D > 0 | Päätös |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K long | 3947 | 533 | -0.0246 | -0.0474 | **+0.0228** | -0.0199 … +0.0651 | 0.3078 | 0.6156 | +0.0062 | +0.0380 | 5/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |
| K short | 3647 | 534 | +0.0418 | +0.0015 | **+0.0403** | -0.0021 … +0.0835 | 0.0614 | 0.2456 | +0.1041 | -0.0332 | 6/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |
| J long | 2680 | 477 | -0.0458 | -0.0060 | **-0.0398** | -0.0888 … +0.0086 | 0.1090 | 0.3270 | -0.0387 | -0.0411 | 1/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |
| J short | 2882 | 472 | +0.0032 | +0.0248 | **-0.0217** | -0.0759 … +0.0348 | 0.4542 | 0.6156 | -0.0187 | -0.0250 | 3/6 (vaad. 4) | **EI NÄYTTÖÄ AJOITUSEDUSTA** |

## Lopputulosten jakauma (±1·A) – ajo 1

| Ryhmä | tavoite | stop | aikaraja | epäselvä | Signaalien tavoiteosuus | Vertailujen tavoiteosuus | D, jos epäselvä = +1 | D, jos epäselvä = −1 |
|---|---|---|---|---|---|---|---|---|
| K long | 1876 | 1976 | 26 | 69 | 47.5% | 46.2% | +0.0310 | +0.0146 |
| K short | 1853 | 1701 | 17 | 76 | 50.8% | 48.8% | +0.0531 | +0.0276 |
| J long | 1214 | 1335 | 17 | 114 | 45.3% | 48.4% | -0.0045 | -0.0751 |
| J short | 1379 | 1369 | 6 | 128 | 47.8% | 49.9% | +0.0149 | -0.0582 |

Vaihe 2: ei ajettu yhdellekään ryhmälle (ajoitusetua ei osoitettu).
