# Sääntöversiot v1.1 ja v2

Tila: **ODOTTAA HYVÄKSYNTÄÄ** – lukitaan ennen testijakson B alkua.
Koodissa: `kynttilatulkki/strategy.py` → `RULESETS["v1.1"]`, `RULESETS["v2"]`, `estimate_costs()`.

Molemmat noudattavat kaikilta muilta osin sääntöjä v1 (`docs/SAANNOT_v1.md`):
signaaliehdot, avaus, stop, 1,5 R -tavoite, 15 min pitoaika, 0,5 % riskibudjetti, positiokatot ja
tappiorajat (−2 %/päivä, 4 tappion putki → 60 min tauko, −10 % huipusta → pysäytys).

| Versio | Kulumalli | Kulusuodatin | Muuta |
|---|---|---|---|
| v1 | alkuperäinen (virheellinen, ks. alla) | R ≥ 2 × kulut | säilytetään jakson A toistettavuuden vuoksi |
| **v1.1** | **korjattu** | R ≥ 2 × kulut | = v1 + kulukorjaus |
| **v2** | **korjattu** | **R ≥ 4 × kulut** | ainoa ero v1.1:een on suodatin |

## 1. Määritelmät

* **Hintariski R** (per yksikkö) = |toteutunut avaushinta − stop|. R ei sisällä kuluja. Koska se
  mitataan toteutuneesta avaushinnasta, avauksen spread ja liukuma ovat jo mukana hinnassa.
* **Kokonaistappio stopissa L** (per yksikkö) = R + sulun spread ja stop-liukuma + palkkiot
  molempiin suuntiin + funding-arvio.
* **Riskibudjetti** = 0,5 % pääomasta (USD) = määrä × L. Positiokoko: määrä = budjetti / L.
  Kun stop toteutuu suunnitellusti, nettotappio on siis −1,00 × riskibudjetti. Hintakuilussa tai
  osittaisella funding-kulutuksella tappio voi poiketa tästä.
* **Kulut C** (per yksikkö, suodatinta varten) = avauksen spread ja liukuma + sulun spread ja
  stop-liukuma + palkkiot + funding-arvio. C sisältää koko kaupan kitkan.
* **Kulusuodatin**: kauppa avataan vain, jos R ≥ k × C (v1.1: k = 2, v2: k = 4).
* Raportissa on kaksi mittaria: *R-kerroin* = netto / (määrä × R) ja
  *budjettikerroin* = netto / riskibudjetti. Arvioinnin päämittari on budjettikerroin.

## 2. Kulukaava

Merkinnät: P = avauskynttilän avaushinta, S = stop, h = puolikas spread, s = liukuma 0,02 %,
s_stop = stop-liukuma 0,05 %, f = taker-palkkio 0,05 %, φ = funding-varaus 0,00125 %/h,
H = maksimipitoaika 15 min.

Long (short peilikuvana):

```
avaushinta          E  = P × (1 + h + s)
stop-toteutus       X  = S × (1 − h − s_stop)
hintariski          R  = E − S
avauksen kitka      Ke = P × (h + s)                    (sisältyy jo E:hen)
sulun kitka         Kx = S × (h + s_stop)
palkkiot            F  = f × (E + X)
funding-varaus      Fu = E × φ × H/60
kulut               C  = Ke + Kx + F + Fu
kokonaistappio      L  = R + Kx + F + Fu  =  (E − X) + F + Fu
määrä               q  = riskibudjetti / L
```

**Mitä korjattiin (v1 → v1.1)**: v1 arvioi kulut kaavalla `2f + 2(h + s)`. Se (a) laski
avauksen spreadin ja liukuman toiseen kertaan, vaikka ne ovat jo R:ssä, ja (b) oletti sulkuun
0,02 % liukuman, vaikka stop toteutetaan 0,05 %:n liukumalla. Jaksolla A virheet sattuivat
lähes kumoamaan toisensa (varattu 0,391 R, toteutunut 0,376 R), mutta siihen ei voi luottaa.

## 3. Numeerinen esimerkki (jakso A: PF_ETHUSD long 23.9. 14:10)

P = 2 699,00, S = 2 689,63, h = 0,010 %, pääoma 10 000 USD → riskibudjetti 50,00 USD

| Suure | Arvo per yksikkö |
|---|---|
| E = 2 699,00 × 1,0003 | 2 699,8097 |
| X = 2 689,63 × (1 − 0,0006) | 2 688,0162 |
| R = E − S | 10,1797 |
| Ke = 2 699,00 × 0,0003 | 0,8097 |
| Kx = 2 689,63 × 0,0006 | 1,6138 |
| F = 0,0005 × (E + X) | 2,6939 |
| Fu = E × 0,0000125 × 0,25 | 0,0084 |
| **C** = Ke + Kx + F + Fu | **5,1258** |
| **L** = R + Kx + F + Fu | **14,4958** |
| R / C | **1,99** |

* Määrä q = 50,00 / 14,4958 = 3,449 ETH, nimellisarvo ≈ 9 312 USD.
* Hintariski q × R = 35,11 USD. Kulut stopissa q × (Kx + F + Fu) = 14,89 USD. Yhteensä 50,00 USD.
* **v1.1**: R / C = 1,99 < 2 → **ei avata** (v1 avasi tämän kaupan). **v2**: < 4 → ei avata.

## 4. Kehitysloki – jakso A on kehitysaineistoa

Jakso A (22.–29.9.2026) on katsottu ja sitä on käytetty kehitykseen. Sen tuloksia **ei käytetä
kannattavuuden todisteena** millekään versiolle.

Kokeillut yksittäiset muutokset v1:een (vanha kulumalli, tappiorajat pois vertailua varten):

| # | Muutos | Kauppoja | Netto USD | Ennen kuluja USD | ka R-kerroin |
|---|---|---|---|---|---|
| – | v1 ennallaan | 85 | −1 632 | −464 | −0,58 |
| 1 | tavoite 1,0 R | 87 | −1 664 | −472 | −0,58 |
| 2 | tavoite 0,75 R | 87 | −1 615 | −418 | −0,56 |
| 3 | stop-puskuri 0,5 ATR | 156 | −2 195 | −110 | −0,44 |
| 4 | kulusuodatin 4 × | 8 | −144 | −83 | −0,42 |
| 5 | pitoaika 5 min | 88 | −1 492 | −322 | −0,51 |
| 6 | volyymiehto pois | 149 | −2 292 | −303 | −0,49 |

Korjatulla kulumallilla ja v1:n tappiorajoilla (jakso A):

| Versio | Kauppoja | Voittoja | Netto USD | Ennen kuluja USD | ka budjettikerroin | Stop-tappio ka | Pudotus |
|---|---|---|---|---|---|---|---|
| v1 (vanha malli) | 42 | 7 | −1 035 | −442 | −0,52 | −0,99 | 10,3 % (pysäytys) |
| v1.1 | 49 | 12 | −955 | −321 | −0,41 | −1,00 | 9,6 % |
| v2 | 5 | 1 | −97 | −72 | −0,39 | −1,00 | 1,0 % |

v2 valittiin testattavaksi ennen yllä olevia kulukorjattuja lukuja. Perusteena oli jakson A
tarkistus (`results/jakso_A_tarkistus.md`): suotuisan liikkeen mediaani (≈ 0,33 R) jäi
pienemmäksi kuin kaupan kulut (≈ 0,38 R). Viisi kauppaa ei kerro v2:sta mitään.

## 5. Testijakso B

* Alkaa, kun live-paperikauppa käynnistyy Railwayssä muuttujalla `RULES=v1.1,v2`. Alkuhetki
  kirjautuu lokiin ja tilatiedostoihin (`started_at`) ja merkitään tiedostoon
  `results/TESTIJAKSOT.md`.
* Molemmat versiot ajetaan **samassa prosessissa, samasta datasta ja samasta hetkestä**
  erillisillä 10 000 USD:n paperitileillä. Markkinat: 5 vaihdetuinta PF-perpetualia
  käynnistyshetkellä, sama lista molemmille tileille.
* 1 min kynttilät.
* **Ensimmäinen arviointi 4 viikon kuluttua käynnistyksestä** (tavoite 27.10.2026).

## 6. Arviointi (lukittu etukäteen)

Työkalu: `python -m kynttilatulkki.evaluate`.

* Päämittari: nettotulos / riskibudjetti per kauppa, kaikki kulut mukana.
* Epävarmuus: 95 %:n bootstrap-luottamusväli keskiarvolle (10 000 otosta), Wilsonin väli
  voittoprosentille ja versioiden erolle bootstrap-väli.
* Tulkinta per versio:
  * n < 30 → **keskeneräinen näyttö**: ei johtopäätöksiä eikä hyväksyntää.
  * n ≥ 30 ja välin alaraja > 0 → **alustava näyttö voitollisuudesta**. Tämä ei vielä ole
    hyväksyntä, vaan vaatii toiston uudella jaksolla.
  * n ≥ 30 ja välin yläraja < 0 → **näyttö tappiollisuudesta**.
  * muuten → **ei näyttöä suuntaan tai toiseen**.
* Versioiden ero todetaan vain, jos molemmilla n ≥ 30 ja eron luottamusväli ei sisällä nollaa.
* Ristiintarkistus: sama jakso historiatestinä (`--backtest-start`). Poikkeamat live-tulokseen
  selvitetään (spread mitattu vs. oletettu, katkot).
* Sääntöjä ei muuteta jakson B aikana.
