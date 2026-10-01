# Vaihe 1: ennustavatko signaalit suuntaa ja ajoitusta sattumaa paremmin? (ilman kuluja)

**Lukittu 1.10.2026 ennen arviointiaineiston lataamista.** Tätä suunnitelmaa, mittareita,
aineistoa ja päätössääntöjä ei muuteta tulosten perusteella. Mahdollinen muutos tehdään uutena
versiona ja arvioidaan uudella aineistolla.

Tutkimus ei muuta livebottia, sen sääntöjä eikä paperitilejä. Skripti on `tutkimus/ajoitus.py`, ja
se on botin Railway-palvelun ulkopuolella, joten botti ei käynnisty uudelleen.

## 1. Kysymys ja rajaus

Ennustavatko botin signaalit hinnan suuntaa signaalihetkellä paremmin kuin satunnainen hetki samalla
markkinalla, samassa suunnassa ja samana päivänä, kun **kuluja ei huomioida**?

* Tutkimus mittaa **ajoitusta**.
* **Kannattavuus** kulujen jälkeen on eri kysymys (vaihe 2), ja sitä arvioidaan vasta, jos vaihe 1
  osoittaa etua.

## 2. Signaalit

* Tutkittavat signaalityypit:
  * **K** = `aj1-kaanto`: T2-kääntymiskuviot
  * **J** = `aj1-jatko`: jatkumissignaali.
* Säännöt ovat samat kuin livebotissa (`docs/AJOITUSTESTI_1.md`).
* Signaalit tuotetaan **botin omalla koodilla**: `PaperEngine.on_bar_close` → `on_signal`, ja
  avaukset on estetty. Tulos on siten sama koodipolku kuin live-ajossa.
* **Kaikki signaalit** otetaan mukaan riippumatta paperitilien tappiorajoista, positiorajoista,
  avoimista positioista tai samanaikaisista signaaleista.
* Markkinat: PF_SUIUSD, PF_ZECUSD, PF_XRPUSD, PF_DOGEUSD ja PF_SOLUSD (1 min kynttilät).
  Kauppattomat minuutit täytetään kuten livebotissa.

## 3. Kokeellinen kauppa (sama signaaleille ja vertailuille)

* **Avaus:** signaalikynttilän jälkeisen kynttilän avaushinta. Se on ensimmäinen hinta signaalin
  valmistumisen jälkeen, eikä siihen lisätä kuluja.
* **Volatiliteettiyksikkö A:** 20 signaalikynttilää edeltävän suljetun kynttilän keskimääräinen
  vaihteluväli. Tämä on sama luku kuin botin kontekstissa, ja skripti tarkistaa, että ne ovat
  samat. A:ssa ei ole signaalikynttilän tai myöhempää tietoa.
* **Poistumissäännöt** ovat symmetriset ja mitataan markkinahinnasta:
  * tavoite = avaus + k·A ja stop = avaus − k·A (shortilla päinvastoin)
  * ensisijaisesti **k = 1,0**, täydentävästi k = 2,0
  * aikaraja 15 kynttilää (16. kynttilän avaus, kuten botissa)
  * hintakuilu kynttilän avauksessa lasketaan osumaksi.
* **Pisteet:** +1, jos tavoite osuu ensin, ja −1, jos stop osuu ensin. Aikarajalla pisteet ovat
  suunnattu muutos / (k·A) rajattuna välille [−1, +1].
* **Sama kynttilä osuu sekä tavoitteeseen että stoppiin:** järjestystä ei voi 1 min datasta
  tietää. Tapaus merkitään **epäselväksi**, ja sen pisteet ovat ensisijaisessa mittarissa **0**.
  Herkkyysanalyysi raportoi tuloksen myös, jos kaikki epäselvät olisivat +1 ja jos kaikki olisivat
  −1. Sama sääntö koskee vertailuja.

## 4. Satunnaisvertailu

Jokaiselle signaalille arvotaan **50 vertailuhetkeä**:

* sama markkina, sama suunta ja sama UTC-päivä
* vähintään 15 minuutin päässä signaalista
* sama kokeellinen kauppa, ja A lasketaan vertailuhetken omasta edeltävästä historiasta.

Vertailu käyttää samoja historiallisia hintoja. Se poistaa päivän trendin, markkinan ja
volatiliteettitason vaikutuksen, joten jäljelle jää se, tuoko **juuri signaalin hetki** jotain
lisää. Satunnaisuuden siemen on lukittu (20261001).

## 5. Ensisijainen mittari (yksi per signaalityyppi)

**D = signaalin pisteet − sen 50 vertailun keskiarvo**, keskiarvona kaikista signaaleista, k = 1,0.

* **Riippuvuus:** samanaikaiset signaalit eri markkinoilla ja päällekkäiset aikaikkunat korreloivat.
  Siksi epävarmuus lasketaan **päiväklusteribootstrapilla** (10 000 otosta), jossa koko UTC-päivän
  signaalit arvotaan yhdessä.
* **Useat testit:** ensisijaisia testejä on kaksi (K ja J), ja niille tehdään **Holm-korjaus**
  (α = 0,05). Kaikki muut mittarit ovat täydentäviä, ja niille raportoidaan Benjamini–Hochberg-
  q-arvot. Niistä ei tehdä päätelmiä yksinään.

**Päätössääntö** kullekin tyypille, lukittu:

| Ehto | Tulos |
|---|---|
| n < 300 signaalia tai < 14 päivää | AINEISTO EI RIITÄ |
| Holm-p < 0,05 **ja** D > 0 **ja** molemmat jakson puoliskot > 0 **ja** D > 0 vähintään 3/5 markkinalla | AJOITUSETU OSOITETTU (ennen kuluja) |
| Holm-p < 0,05 **ja** D < 0 samoin ehdoin | SIGNAALIT SATTUMAA HUONOMPIA |
| Holm-p < 0,05, mutta puoliskot tai markkinat ristiriidassa | EI OSOITETTU (epäjohdonmukainen) |
| muuten | EI NÄYTTÖÄ AJOITUSEDUSTA |

**Tulkinta-apu:** D = +0,10 vastaa suunnilleen 55 %:n tavoiteosuutta 50 %:n sijaan symmetrisillä
rajoilla.

## 6. Täydentävät mittarit (eksploratiivisia)

* long ja short erikseen
* k = 2,0
* suunnattu tuotto 1, 5 ja 15 minuutissa A-yksiköinä
* suotuisin ja epäsuotuisin liike (MFE ja MAE) A-yksiköinä
* markkinakohtaiset erot
* tulosten jakauma: tavoite, stop, aikaraja ja epäselvä
* vertailun tavoiteosuus
* epäselvien osuus.

## 7. Aineistot

| Aineisto | Aika (UTC) | Käyttö |
|---|---|---|
| **Kehitys** | 22.9.2026 18:43 – 2.10.2026 00:00 (jakso A, sarjojen B/C data, ajoitustesti 1:n live-kaupat) | Vain skriptin testaukseen. Jo nähty, ei näyttöä. |
| **ARVIOINTI (ensisijainen)** | **15.7.2026 00:00 – 15.9.2026 00:00** (62 vrk), lisäksi 14.7. lämmittelyyn | Ei ole käytetty sääntöjen, rajojen tai markkinoiden valintaan, eikä signaaleja ole katsottu. |
| Toisto (myöhemmin) | 2.10.2026 00:00 – 30.10.2026 00:00 | Raportoidaan erikseen, jos ensisijainen tulos osoittaa etua. |

* Arviointiaineistoa ei ole ladattu ennen lukitusta.
* Markkina jätetään pois vain ennalta määritellyn kattavuussäännön perusteella: kauppoja alle 95 %
  minuuteista tai alle 1 vrk lämmittelyhistoriaa. Tuloksilla ei ole tässä merkitystä.
* Väli 15.9.–22.9. jätetään puskuriksi kehitysaineistoon.
* Skripti on ajettu kehitysaineistolla vain toimivuuden tarkistamiseksi. Sen tuloksia ei käytetä
  eikä raportoida näyttönä.

## 8. Tulevan tiedon esto (testattu: `tests/test_tutkimus_ajoitus.py`)

* Signaalit ja A ovat samat, vaikka data katkaistaisiin signaalin kohdalta.
* Avaus tehdään vasta signaalin jälkeisen kynttilän avauksessa, ja lopputulos lasketaan vain sen
  jälkeisistä kynttilöistä.
* Vertailuhetkien A lasketaan vain niitä edeltävistä kynttilöistä.

## 9. Ajo-ohjeet (Windows, PowerShell, repon kansiossa)

```
git pull
python -m kynttilatulkki.lataa --start 2026-07-14T00:00 --end 2026-09-15T00:00 --symbols PF_SUIUSD,PF_ZECUSD,PF_XRPUSD,PF_DOGEUSD,PF_SOLUSD
python -m tutkimus.ajoitus --data-glob "data/PF_*_2026-07-14T0000_2026-09-15T0000.csv" --alku 2026-07-15T00:00 --loppu 2026-09-15T00:00 --tulos tutkimus/tulokset/arviointi --aineisto ARVIOINTI
```

* Lataus kestää muutamia minuutteja, ja analyysi muutaman minuutin.
* Tulokset ovat tiedostoissa `tutkimus/tulokset/arviointi_raportti.md` ja
  `tutkimus/tulokset/arviointi_signaalit.csv`. Lähetä molemmat.
* Jos lataus katkeaa, aja sama komento uudelleen.

## 10. Täsmennys aiempaan raporttiin: kannattavuus kaupoittain vs. koko strategia

Laskettu ajoitustesti 1:n 35 kaupasta samalla kulumallilla. Jokaiselle kaupalle laskettiin netto
siinä tapauksessa, että se olisi päättynyt tavoitteeseen, ja siinä tapauksessa, että se olisi
päättynyt stoppiin.

* **Yksittäiset kaupat:**
  * K: **10/16** kauppaa olisi ollut tappiollisia, vaikka tavoite olisi osunut. Niissä tavoitteen
    hintaliike ei kata edestakaisia kuluja.
  * J: 1/19 kauppaa.
* **Koko strategia:** odotettu nettotulos on p × Σ(netto tavoitteessa) − (1 − p) × Σ(tappio
  stopissa), kun aikarajasulut jätetään huomiotta.
  * K: vaikka **kaikki 16** kauppaa olisivat osuneet tavoitteeseen, summa olisi −93,34 $. Tällä
    kulujen ja R:n suhteella kannattavuusrajaa ei siis voi saavuttaa millään osumatarkkuudella.
  * J: kaikki tavoitteessa yhteensä +233,25 $ ja kaikki stopissa −932,64 $. Kannattavuusraja
    on **p* ≈ 80 %** tavoiteosumia, kun satunnaisvertailun taso on noin 40–45 %.
* **Aiemman raportin korjaus:** aiemmin mainitut "11/16" ja "87–92 %" olivat karkeita arvioita
  mediaaneista. Kaupoittain lasketut luvut ovat 10/16 ja noin 80 %.
* **Yleistys:** väite "mahdoton" koskee nykyistä kulumallia (taker molemmissa päissä, ½ spread ja
  liukuma) ja tämän otoksen R-jakaumaa. Se ei ole väite signaalien ajoituksesta.
