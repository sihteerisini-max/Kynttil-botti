# Sääntöversiot v1.1 ja v2 – paperivertailu

Tila: **LUKITTU 29.9.2026** ennen testijakson B alkua (lukituscommit näkyy git-historiassa).
Koodissa: `kynttilatulkki/strategy.py` → `RULESETS["v1.1"]`, `RULESETS["v2"]`, `estimate_costs()`,
`size_position()`.

Molemmat noudattavat kaikilta muilta osin sääntöjä v1 (`docs/SAANNOT_v1.md`):
signaaliehdot, avaus, stop, 1,5 R -tavoite, 15 min pitoaika, 0,5 % riskibudjetti ja
tappiorajat (−2 %/päivä, 4 tappion putki → 60 min tauko, −10 % huipusta → pysäytys).

| Versio | Kulumalli | Kulusuodatin | Muuta |
|---|---|---|---|
| v1 | alkuperäinen (virheellinen, ks. kohta 2) | R ≥ 2 × kulut | säilytetään jakson A toistettavuuden vuoksi |
| **v1.1** | **korjattu** | R ≥ 2 × C | = v1 + kulukorjaus + kokorajat |
| **v2** | **korjattu** | **R ≥ 4 × C** | ainoa ero v1.1:een on suodatin |

## 1. Määritelmät

* **Hintariski R** (per yksikkö) = |toteutunut avaushinta − stop|. R ei sisällä kuluja. Koska se
  mitataan toteutuneesta avaushinnasta, avauksen spread ja liukuma ovat jo mukana hinnassa.
* **Kokonaistappio stopissa L** (per yksikkö, mallin oletuksilla) = R + sulun spread ja
  stop-liukuma + palkkiot molempiin suuntiin + funding-varaus.
* **Riskibudjetti** = 0,5 % pääomasta (USD). Positiokoko: määrä = budjetti / L, pyöristettynä
  alaspäin (kohta 4). **Kun stop toteutuu mallin oletuksilla, nettotappio vastaa riskibudjettia.
  Todellinen toteutus voi ylittää sen**, jos hinta avautuu stopin yli (hintakuilu), spread on
  mallia leveämpi, liukuma on suurempi tai funding on varausta suurempi.
* **Stop-skenaarion kustannusarvio C** (per yksikkö) = avauksen spread ja liukuma + sulun spread
  ja stop-liukuma + palkkiot + funding-varaus. C on ennakkoarvio stopilla päättyvän kaupan
  kitkasta. Sitä käytetään vain kulusuodattimessa.
* **Kulusuodatin**: kauppa avataan vain, jos R ≥ k × C (v1.1: k = 2, v2: k = 4).
* **Funding-varaus Fu** on ennakkoarvio (0,00125 %/h × 15 min aina omaa positiota vastaan), jota
  käytetään vain koon ja suodattimen laskennassa. **Toteutunut funding** kirjataan kaupan sulussa
  todellisella pitoajalla ja korolla (live: Krakenin tickerin tuntikorko; historiatesti:
  historiallinen tuntikorko tai varaus-korko, jos historiaa ei saada). Kauppalokissa kenttä
  `funding` on toteutunut funding.
* Raportissa on kaksi mittaria: *R-kerroin* = netto / (määrä × R) ja
  *budjettikerroin* = netto / riskibudjetti. Arvioinnin päämittari on budjettikerroin.

## 2. Kulukaava

Merkinnät: P = avauskynttilän avaushinta, S = stop, h = puolikas spread, s = liukuma 0,02 %,
s_stop = stop-liukuma 0,05 %, f = taker-palkkio 0,05 %, φ = funding-varauksen korko 0,00125 %/h,
H = maksimipitoaika 15 min.

```
                    LONG                         SHORT
avaushinta      E = P × (1 + h + s)          E = P × (1 − h − s)
stop-toteutus   X = S × (1 − h − s_stop)     X = S × (1 + h + s_stop)
hintariski      R = E − S                    R = S − E
avauksen kitka  Ke = P × (h + s)                 (sisältyy jo E:hen)
sulun kitka     Kx = S × (h + s_stop)
palkkiot        F  = f × (E + X)
funding-varaus  Fu = E × φ × H/60
kustannusarvio  C  = Ke + Kx + F + Fu            (suodatin)
kokonaistappio  L  = R + Kx + F + Fu = |E − X| + F + Fu
```

**Mitä korjattiin (v1 → v1.1)**: v1 arvioi kulut kaavalla `2f + 2(h + s)`. Se (a) laski
avauksen spreadin ja liukuman toiseen kertaan, vaikka ne ovat jo R:ssä, ja (b) oletti sulkuun
0,02 %:n liukuman, vaikka stop toteutetaan 0,05 %:n liukumalla. Jaksolla A virheet sattuivat
lähes kumoamaan toisensa, mutta siihen ei luoteta, vaan molemmat on korjattu.

## 3. Numeeriset esimerkit

**Long** (jakso A: PF_ETHUSD 23.9. 14:10), P = 2 699,00, S = 2 689,63, h = 0,010 %,
riskibudjetti 50,00 USD:

| Suure | Arvo |
|---|---|
| E / X / R | 2 699,8097 / 2 688,0162 / 10,1797 |
| Ke / Kx / F / Fu | 0,8097 / 1,6138 / 2,6939 / 0,0084 |
| C / L / R ÷ C | 5,1258 / 14,4958 / **1,99** |

* Määrä 50,00 / 14,4958 = 3,44927 → ETH:n askel 0,001 → **3,449 ETH**. Nimellisarvo 9 311,7 USD,
  riskibudjetti pyöristyksen jälkeen 49,996 USD.
* v1 avasi tämän kaupan. v1.1 ei avaa (1,99 < 2), eikä v2 avaa (1,99 < 4).

**Short** (testattu yksikkötestillä `test_kaava_short_numeerinen`), P = 100, S = 101, h = 0,010 %:

| Suure | Laskenta | Arvo |
|---|---|---|
| E | 100 × (1 − 0,0003) | 99,97 |
| X | 101 × (1 + 0,0006) | 101,0606 |
| R | 101 − 99,97 | 1,03 |
| Ke | 100 × 0,0003 | 0,03 |
| Kx | 101 × 0,0006 | 0,0606 |
| F | 0,0005 × (99,97 + 101,0606) | 0,1005153 |
| Fu | 99,97 × 0,0000125 × 0,25 | 0,000312406 |
| C | Ke + Kx + F + Fu | 0,191427706 |
| L | X − E + F + Fu | 1,191427706 |

Moottorissa stopilla suljettu short tuottaa −50,00 USD + käyttämätön funding-varaus
(`test_short_stop_moottorissa`). Hintakuilussa tappio ylittää budjetin
(`test_hintakuilu_ylittaa_budjetin`).

## 4. Positiokoko ja rajat (v1.1 ja v2)

Järjestys (`size_position()`):

1. q = riskibudjetti / L
2. q rajataan pienimpään seuraavista:
   * **nimellisarvo per positio** ≤ 3 × pääoma
   * **avoin nimellisarvo yhteensä** ≤ 5 × pääoma
   * **alkumarginaali yhteensä** ≤ 50 % pääomasta. Alkumarginaali = max(Krakenin porrastettu
     alkumarginaali positiokoon mukaan, 1/10). 1/10 vastaa EEA:n 10×:n vipukattoa.
   * **Krakenin maxPositionSize**
3. **Pyöristys alaspäin** sallittuun kokoaskeleeseen (10^−contractValueTradePrecision; esim.
   BTC 0,0001, ETH 0,001, SOL 0,01, XRP 1). Jos tulos on alle yhden askeleen, kauppaa ei avata.
4. Riskibudjetti kirjataan toteutuneella koolla (q × L ≤ 0,5 % pääomasta).

Sopimustiedot haetaan Krakenin instruments-rajapinnasta ajon alussa (live ja historiatesti).
Jos markkinan tietoja ei saada, markkinassa ei avata kauppoja. Avoimia positioita on enintään
3, yksi per markkina.

## 5. Miksi v1.1:llä oli jaksolla A 49 kauppaa ja v1:llä 42

Tapahtumalokien vertailu (sama data, samat tappiorajat):

* Yhteisiä kauppoja 27. Vain v1:ssä 15, vain v1.1:ssä 22 → 42 − 15 + 22 = 49.
* **15 kauppaa vain v1:ssä**:
  * 14 hylkäsi v1.1:n kulusuodatin. Korjattu C on suurempi kuin v1:n arvio, koska stop-sulun
    liukuma on 0,05 % eikä 0,02 %. Suodatin on siksi tiukempi.
  * 1 osui v1.1:ssä tappioputken taukoon.
* **22 kauppaa vain v1.1:ssä**: v1 ei voinut avata niitä tappiorajojensa vuoksi.
  * 13 kertaa v1:n päivän tappioraja oli täynnä.
  * 9 kauppaa sijoittui v1:n maksimipudotuspysäytyksen (28.9. 12:11 UTC) jälkeen.
  * v1.1 hävisi alussa vähemmän, joten se ei osunut samoihin rajoihin.
* Kauppamäärän kasvu ei siis johdu löysemmästä suodattimesta, vaan siitä, että tiukempi suodatin
  vähensi tappioita ja tappiorajat laukesivat harvemmin.

## 6. Kehitysloki – jakso A on kehitysaineistoa

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

Korjatulla kulumallilla ja v1:n tappiorajoilla (jakso A, ilman sopimuskohtaista pyöristystä):

| Versio | Kauppoja | Voittoja | Netto USD | Ennen kuluja USD | ka budjettikerroin | Stop-tappio ka | Pudotus |
|---|---|---|---|---|---|---|---|
| v1 (vanha malli) | 42 | 7 | −1 035 | −442 | −0,52 | −0,99 | 10,3 % (pysäytys) |
| v1.1 | 49 | 12 | −955 | −321 | −0,41 | −1,00 | 9,6 % |
| v2 | 5 | 1 | −97 | −72 | −0,39 | −1,00 | 1,0 % |

v2 valittiin testattavaksi ennen yllä olevia kulukorjattuja lukuja. Perusteena oli jakson A
tarkistus (`results/jakso_A_tarkistus.md`): suotuisan liikkeen mediaani (≈ 0,33 R) jäi
pienemmäksi kuin kaupan kulut (≈ 0,38 R). Viisi kauppaa ei kerro v2:sta mitään.

## 7. Testijakso B

* Molemmat versiot ajetaan **samassa prosessissa ja samasta datavirrasta** erillisillä
  10 000 USD:n paperitileillä. Kummallakin tilillä on oma tilatiedostonsa
  (`STATE_DIR/paper_v1.1.pkl`, `paper_v2.pkl`), joka säilyy uudelleenkäynnistysten yli, sekä
  omat kauppalokinsa.
* **Jakso B alkaa vasta tilien todellisesta käynnistyshetkestä.** Hetki on se, jolloin
  lämmittely on valmis ja live-silmukka alkaa. Se tallentuu kummankin tilin tilaan
  (`started_at`) ja lokiin riville `JAKSO B – tilien todellinen aloitushetki`. Jos hetket
  eroavat, loki varoittaa, eikä vertailua pidetä samalta jaksolta tehtynä.
* Markkinat: 5 vaihdetuinta PF-perpetualia käynnistyshetkellä, sama lista molemmille tileille.
  1 min kynttilät.
* **Ensimmäinen arviointi, kun käynnistyksestä on kulunut 4 viikkoa.**
* Sääntöjä ei muuteta jakson B aikana.

## 8. Arviointi (lukittu etukäteen)

Työkalu: `python -m kynttilatulkki.evaluate`.

* **Päämittari**: nettotulos / riskibudjetti per kauppa, kaikki toteutuneet kulut mukana.
* **Ajallinen riippuvuus**: kaupat eivät ole riippumattomia. Saman päivän kaupat syntyvät samasta
  markkinatilasta, ja tappiorajat kytkevät peräkkäiset kaupat toisiinsa. Luottamusvälit
  lasketaan siksi **lohkobootstrapilla**:
  * ensisijaisesti **päivälohkot**: kaikki jakson kalenteripäivät, myös kauppattomat,
    3 päivän peräkkäisinä lohkoina. Keskiarvo lasketaan muodossa Σ tulos / Σ kaupat.
  * toissijaisesti **kauppajono** aikajärjestyksessä, lohkon pituus ⌈n^(1/3)⌉.
  * Tulkintaan käytetään näistä **varovaisempaa (leveämpää)** väliä.
  * Wilsonin väli voittoprosentille raportoidaan vain suuntaa antavana, koska se olettaa
    riippumattomuuden.
* **30 kauppaa ei ole itsessään riittävä näyttö.** Se on vain alaraja, jota pienemmästä
  aineistosta ei tehdä tulkintaa.
* Tulkinta per versio:
  * n < 30 tai kauppapäiviä < 10 → **keskeneräinen näyttö**.
  * varovaisen välin yläraja < 0 → **näyttö tappiollisuudesta**.
  * **Alustava näyttö voitollisuudesta** edellyttää kaikkia seuraavia: varovaisen välin alaraja
    > 0, jakson molemmat puoliskot erikseen positiivisia ja yksikään päivä ei tuota yli 50 %
    nettotuloksesta. Tämäkään **ei ole hyväksyntä**, vaan tulos pitää toistaa uudella jaksolla.
  * muuten → **ei näyttöä suuntaan tai toiseen**.
* **Versioiden ero** lasketaan paritettuna päivälohkobootstrapilla (samat päivät). Eroa ei
  todeta, jos jommallakummalla n < 30 tai eron väli sisältää nollan.
* **Ristiintarkistus**: sama jakso ajetaan historiatestinä (`--backtest-start`). Poikkeamat
  live-tulokseen selvitetään (mitattu vs. oletettu spread, katkot, pyöristys).
