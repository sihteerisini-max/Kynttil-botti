# Tutkimus K4H – KEHITYS

Suunnitelma `docs/TUTKIMUS_K4H_SUUNNITELMA.md` (lukittu ennen laskelmia). Jakso 2025-01-01 00:00 – 2026-07-01 00:00 UTC, 15m K-signaalit (aj1-kaanto), pitoaika 16 kynttilää (4 h), ei stoppia/tavoitetta, yksi positio per markkina, siemen 20261008.

> **KEHITYSANALYYSI – ei näyttöä.** Data on jo käytetty Tutkimus 15M:ssä, jossa 4 h -havainto tehtiin. Päätössääntöjen tulokset alla ovat vain kuvaus siitä, miltä lukittu sääntö näyttää kehitysdatalla.

Mukana: **PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_DOGEUSD, PF_XRPUSD, PF_PEPEUSD** (6/6). Spreadit mitattu 2026-10-08 17:34 UTC.

## Ensisijaiset testit

| Ryhmä | Signaaleja | D16 (A) | 95 % LV | Holm-p | Puoliskot | Markkinoita > 0 | H1 | Kauppoja | Netto/kauppa | 95 % LV | Holm-p (yksisuunt.) | Puoliskot | Markkinoita > 0 | H2 | **Päätös** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K long | 3947 | +0.3034 | +0.0721 … +0.5547 | 0.0128 | +0.475 / +0.146 | 6/6 | kyllä | 2756 | -0.2278% | -0.3591% … -0.0914% | 1.0000 | -0.1525% / -0.2965% | 0/6 | ei | **SUUNTAVAIKUTUS SÄILYI, MUTTA EI KATA KULUJA – hylätään kaupankäyntistrategiana** |
| K short | 3647 | +0.2889 | +0.0850 … +0.4870 | 0.0128 | +0.418 / +0.139 | 5/6 | kyllä | 2583 | -0.2031% | -0.3046% … -0.0988% | 1.0000 | -0.1581% / -0.2549% | 0/6 | ei | **SUUNTAVAIKUTUS SÄILYI, MUTTA EI KATA KULUJA – hylätään kaupankäyntistrategiana** |

Vaadittu markkinamäärä ⌈2m/3⌉ = 4. D16 = signaalin suunnattu 4 h muutos − 50 satunnaisen hetken keskiarvo (A-yksiköissä, ei kuluja). Netto = tuotto % nimellisarvosta kaikkien kulujen jälkeen (toteutetut kaupat).

## Kulut ja bruttotuotto (kuvaileva)

| Ryhmä | Kauppoja | Brutto ka (ennen kuluja) | Spread + liukuma | Palkkiot | Funding | Netto ka | Netto, funding = 0 | Osuma (netto > 0) | Funding todellinen / varovainen |
|---|---|---|---|---|---|---|---|---|---|
| K long | 2756 | -0.0431% | 0.0804% | 0.0999% | +0.0043% | -0.2278% | -0.2235% | 42.4% | 1413 / 1343 |
| K short | 2583 | -0.0176% | 0.0800% | 0.1000% | +0.0054% | -0.2031% | -0.1977% | 43.7% | 1172 / 1411 |

| Markkina | ½ spread | Kauppoja | Brutto ka | Netto ka |
|---|---|---|---|---|
| PF_XBTUSD | 0.0050% | 887 | +0.0360% | -0.1191% |
| PF_ETHUSD | 0.0050% | 829 | -0.0860% | -0.2410% |
| PF_SOLUSD | 0.0094% | 871 | -0.0015% | -0.1651% |
| PF_DOGEUSD | 0.0122% | 926 | -0.0908% | -0.2597% |
| PF_XRPUSD | 0.0188% | 894 | -0.0271% | -0.2098% |
| PF_PEPEUSD | 0.0672% | 932 | -0.0164% | -0.2950% |

## Salkku (N = 1,000 $ per kauppa, vertailupääoma 6 × N = 6,000 $)

* Kauppoja 5339 (long 2756, short 2583); päällekkäisyyden vuoksi ohitettuja signaaleja 2255.
* Brutto -1,643.69 $, kulut 9,878.84 $, **netto -11,522.53 $**.
* Suurin pudotus 11,747.85 $ (195.80% vertailupääomasta) – 2026-06-25 17:15.
* Kauppoja, joiden pidossa kaupattomia/puuttuvia 15m-kynttilöitä: 74.

Kaikki luvut ovat paperilaskentaa historiadatalla. Toimeksiantoja ei lähetetty.
