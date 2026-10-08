# Kehitystesti VOL2H: tavoite ja stop kahden tunnin hintavaihtelun mukaan – ennakkoon lukittu suunnitelma

**Lukittu 8.10.2026** ennen laskentaa. Lukituksen tunniste on tämän tiedoston sisältävä git-commit.

* **Kyseessä on kehitystesti jo käytetyllä datalla.** Tulokset eivät ole näyttöä.
* **Käyttämätöntä vahvistusaineistoa ei käytetä.** Se säästetään siihen asti, että jatkosta on
  päätetty.
* **Uusia kaupankäyntisääntöjä ei julkaista.** Livebottia, paperitilejä ja lukittua lokakuun
  toistotestia ei muuteta.

## 1. Kysymykset

1. Parantaako kahden tunnin vaihteluun mukautuva tavoite- ja stop-malli nettotulosta verrattuna
   nykyiseen malliin samoilla signaaleilla?
2. Tukeeko aineisto suurempaa kauppamäärää? Toisin sanoen, onko mallin nettotuotto per kauppa
   positiivinen niin, että useampi kauppa tarkoittaisi enemmän voittoa eikä enemmän tappiota?
3. Montako kelvollista tilaisuutta nykyiset signaalit tuottavat päivässä?

## 2. Aineisto (kehitys, jo käytetty)

* 1 minuutin kynttilät **15.7.2026 00:00 – 15.9.2026 00:00 UTC** (62 vrk), lämmittely 14.7. alkaen.
* Markkinat PF_SUIUSD, PF_ZECUSD, PF_XRPUSD, PF_DOGEUSD ja PF_SOLUSD, eli samat kuin nykyisessä
  botissa.
* Data on samaa vaiheen 1 historia-aineistoa kuin aiemmin (ladattu 1.10.2026, Jessen koneella).
* Kauppattomat minuutit täytetään kuten botissa.
* Puoliskot ovat 15.7.–15.8. ja 15.8.–15.9.2026.

## 3. Signaalit (ennallaan)

* **K** = `aj1-kaanto` ja **J** = `aj1-jatko`, botin koodi ilman muutoksia.
* Molemmat suunnat ovat mukana.
* Kummallekin signaalityypille on oma paperitili (alkupääoma 10 000 $), kuten livebotissa.

## 4. Mallit

Kaikissa malleissa ovat samat:
* botin oma paperimoottori (`PaperEngine`)
* täyttömalli ja kulut
* positiorajat: 1 positio per markkina, enintään 3 avointa, nimellisarvo ≤ 3 × pääoma per positio ja
  ≤ 5 × yhteensä, marginaali ≤ 50 %
* riskibudjetti 0,5 % pääomasta, ja mitoitus jakaa sen stopin etäisyydellä ja arvioiduilla kuluilla.
  Positiota ei suurenneta minkään dollarivoiton takia.
* aikaraja 15 kynttilää.

Tilikohtaiset tappiorajat (päiväraja 2 %, 4 tappion tauko, 10 %:n pysäytys) on **poistettu
kaikista malleista**, jotta vertailu kattaa koko jakson.

| Malli | Stop | Tavoite | Kulusuodatin |
|---|---|---|---|
| **NYKYINEN** (aj1) | signaalikynttilän ääripää ± 0,1·A | 1 R toteutuneesta avaushinnasta | ei |
| **V1** | avaus ∓ 1,0·M | avaus ± min(1,0·M; 0,5·R2) | tavoite ≥ 2 × arvioidut kulut |
| **V2** | avaus ∓ 1,0·M | avaus ± min(0,5·M; 0,5·R2) | tavoite ≥ 2 × arvioidut kulut |

Mallien määritelmät:
* **W:** 120 viimeistä suljettua 1m-kynttilää, eli 2 tuntia, signaalikynttilä mukaan lukien. Mitään
  ei lasketa avauksen jälkeisestä datasta.
* **R2** = W:n korkein hinta − W:n matalin hinta (kahden tunnin vaihteluväli).
* **M** = W:n sisällä laskettu 15 minuutin päätöskurssimuutosten |close(k) − close(k−15)|
  mediaani (105 liukuvaa havaintoa). M on tyypillinen liike pitoajan (15 min) mittaisella
  ikkunalla, joten pitoaika on mukana säännössä.
* **"Avaus"** = signaalia seuraavan kynttilän avaushinta markkinahintana. Stop ja tavoite asetetaan
  siitä symmetrisesti markkinahinnassa.
* **Arvioidut kulut C** (tavoiteskenaario) = avaushinta × (2 × 0,05 % palkkio + 2 × (½ spread +
  0,02 %)). Kauppa ohitetaan, jos tavoitteen etäisyys < 2 × C.
* Jos M = 0 tai historiaa on alle 120 kynttilää, kauppa ohitetaan.
* **V2** on ainoa vaihtoehto V1:lle. Se vastaa ajatukseen "pienempiä voittoja": puolet tyypillisestä
  liikkeestä tavoitteena, stop ennallaan. Muita versioita ei kokeilla.

**Täyttö ja kulut** (botin moottori, sama kaikille malleille):
* Avaus: seuraavan kynttilän avaushinta ± (½ spread + 0,02 %), taker.
* Stop: stop-hinta ∓ (½ spread + 0,05 %).
* Tavoite: tavoitehinta ∓ (½ spread + 0,02 %), taker kosketuksesta.
* Aikaraja: 16. kynttilän avaushinta ∓ (½ spread + 0,02 %).
* Hintakuilussa täyttö tehdään avaushintaan.
* **Jos sama kynttilä osuu tavoitteeseen ja stoppiin, tapaus kirjataan stopiksi** ja merkitään
  epäselväksi (varovainen).
* Palkkio on 0,05 % avauksen ja sulun nimellisarvosta.
* ½ spread on markkinakohtainen nykyinen mitattu mediaani (20 havaintoa 15 s välein), vähintään
  0,01 % (botin historiatestin alaraja).
* Funding: Krakenin historialliset tuntikorot markkinoittain päiväkeskiarvona × pitoaika, long maksaa
  positiivisella korolla.

## 5. Mittarit ja arviointikriteerit

**Raportoidaan jokaiselle mallille, tilille (K, J) ja suunnalle (long, short):**
* signaaleja päivässä, kulusuodattimen läpäisseitä päivässä ja avattuja kauppoja päivässä
* ohitussyyt
* osumaprosentti (netto > 0) ja tavoite / stop / aikaraja / epäselvä
* keskimääräinen voitto ja tappio ($ ja riskiyksikköinä)
* kulut per kauppa eriteltyinä
* nettotuotto per kauppa
* kokonaisnetto
* suurin pääoman pudotus.

**Vertailukelpoisuus:**
* Nettotulos ilmoitetaan myös **riskiyksikköinä**: netto / riskibudjetti per kauppa.
* Lisäksi lasketaan **vakiopääomavastine** = riskiyksiköt × 50 $ (0,5 % × 10 000 $). Se poistaa
  pääoman korkoa korolle -vaikutuksen.
* Suurin pudotus lasketaan vakiopääomavastineen kertymästä, suhteessa 10 000 $:iin.

**Kriteerit kullekin tilille (K, J) ja mallille V1 ja V2:**
* **K1, parantaako nettotulosta:**
  * kriteeri: päiväkohtainen ero Σ riskiyksiköt(V) − Σ riskiyksiköt(NYKYINEN)
  * päiväklusteribootstrap (10 000 otosta, siemen 20261008)
  * **PARANTAA**, jos keskiarvo > 0 ja 95 %:n luottamusvälin alaraja > 0
  * muuten **EI OSOITETTU PARANNUSTA**.
* **K2, tukeeko suurempaa kauppamäärää:**
  * kriteeri: nettotuotto per kauppa riskiyksiköinä
  * **TUKEE**, jos keskiarvo > 0, 95 %:n luottamusvälin alaraja > 0 ja molemmat puoliskot > 0
  * muuten **EI TUE**, koska negatiivisella odotusarvolla useampi kauppa lisää tappiota.

Tulokset ovat kehitysanalyysiä. Myönteinenkään tulos ei ole näyttöä ilman vahvistusta
käyttämättömällä datalla.

## 6. Tarkistus

Nykyisen mallin laskenta tehdään samalla moottorilla kuin livebotissa (vain tappiorajat pois).
V-mallit ovat moottorin aliluokka, joka muuttaa vain stopin, tavoitteen ja kulusuodattimen.
Testit varmistavat:
* M ja R2 käyttävät vain signaalikynttilää ja sitä edeltäviä kynttilöitä
* stopin ja tavoitteen sijainti
* kulusuodatin
* saman kynttilän stop-ensin-käsittely.
