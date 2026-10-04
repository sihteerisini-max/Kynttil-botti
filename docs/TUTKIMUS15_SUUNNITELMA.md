# Tutkimus 15M: K- ja J-signaalit 15 minuutin kynttilöillä – ennakkoon lukittu suunnitelma

**Lukittu 4.10.2026** ennen kuin testijakson dataa on ladattu tai katsottu. Tätä suunnitelmaa ei
muuteta tulosten perusteella. Lukituksen tunniste on tämän tiedoston sisältävä git-commit.
Mahdollinen muutos tehdään uutena versiona, ja se arvioidaan uudella aineistolla.

* **Erillinen tutkimus.** Se ei muuta livebottia, sen sääntöjä, paperitilejä eikä vaiheen 1 lukittua
  toistojaksoa (2.–30.10.2026). Vaiheen 1 toiston aikaväliä ei käytetä tässä tutkimuksessa.
* **Vain tutkimusta ja paperilaskentaa.** Toimeksiantoja ei lähetetä.
* **Toteutus:**
  * Koodi on hakemistossa `tutkimus15/`, ja se ajetaan omana Railway-palvelunaan, jolla on oma
    Volume.
  * Botin palvelu ei käynnisty uudelleen.
  * Signaalien tunnistus- ja sääntökoodi on tavukopio botin koodista (`tutkimus15/kynttilatulkki/`),
    ja sen samuus tarkistetaan testillä.

## 1. Kysymykset

1. **Ajoitus (vaihe 1, ilman kuluja):** ennustavatko K- ja J-signaalit hinnan suuntaa 15 minuutin
   kynttilöillä paremmin kuin satunnaiset avaushetket? Vertailuhetket otetaan samalta markkinalta,
   samaan suuntaan ja samalta UTC-päivältä.
2. **Liikkeiden koko suhteessa kuluihin (kuvaileva, aina):** kuinka suuri tyypillinen ±1·A-liike on
   verrattuna edestakaisiin kuluihin? Mikä tavoiteosuus vaadittaisiin kannattavuusrajaan?
3. **Kannattavuus (vaihe 2, ehdollinen):** ajetaan vain niille signaaliryhmille, joille vaiheen 1
   ennalta määritelty näyttö ajoitusedusta täyttyy.

## 2. Aineisto ja aikajaksot

| Jakso | Aika (UTC) | Käyttö |
|---|---|---|
| Markkinavalinta | 1.10.2024 00:00 – 1.1.2025 00:00 | vain likviditeettimittarit, ei signaaleja eikä tuloksia |
| Lämmittely | 29.12.2024 00:00 – 1.1.2025 00:00 | kontekstin historia (≥ 20 kynttilää), ei signaaleja |
| **TESTIJAKSO** | **1.1.2025 00:00 – 1.7.2026 00:00** (546 vrk) | signaalikynttilät tältä väliltä |
| Jälkidata | 1.7.2026 00:00 – 06:00 | vain jakson viimeisten signaalien lopputulosten laskentaan |
| Puoliskot | 1.1.2025 – 1.10.2025 ja 1.10.2025 – 1.7.2026 | johdonmukaisuusehto |

* Mitään näistä jaksoista ei ole käytetty sääntöjen kehittämiseen, raja-arvojen valintaan eikä
  aiempiin testeihin.
* Aiemmat aineistot alkoivat aikaisintaan 14.7.2026: vaiheen 1 historia 15.7.–15.9.2026, jakso A
  22.9.2026 alkaen ja toisto 2.10.2026 alkaen.
* Tässä tutkimuksessa ei tarkastella dataa 1.7.2026 jälkeen.
* **Lähde:** Kraken Derivatives charts API, `trade`-kynttilät, resoluutio 15m. 1m-dataa käytetään
  vain markkinavalinnan kattavuusmittariin ja eheystarkistukseen.
* Dataa on saatavilla vuodesta 2024 alkaen. Tämä tarkistettiin 4.10.2026 hakemalla yksittäisiä
  päiviä, joiden hintoja ei analysoitu.

## 3. Markkinavalinta (objektiivinen, ennen testijaksoa)

Valinta tehdään automaattisesti tällä säännöllä. Tulos kirjataan repoon
(`tutkimus15/tulokset/valinta.md`) ennen kuin yhtään signaalia tai lopputulosta lasketaan.

1. **Ehdokkaat:**
   * Krakenin nykyinen instrumenttilista: `PF_*USD`, `type = flexible_futures`,
     `tradeable = true` ja `tradfi = false`.
   * Markkinan `openingDate` on viimeistään 1.10.2024.
   * Lisäksi 15m-data alkaa viimeistään 2.10.2024.
2. **Likviditeetti:** valintajakson UTC-päivien mediaani päivän nimellisvolyymista. Päivän
   nimellisvolyymi on 15m-kynttilöiden Σ volyymi × päätöshinta.
3. **Kymmenen suurinta** ehdokasta otetaan jatkoon. Niille lasketaan valintajakson 1m-kynttilöistä
   kauppaminuuttien osuus (volyymi > 0).
4. **Kattavuusehto:** kauppaminuutteja on vähintään 99,0 %.
5. **Lopulliset markkinat:** kuusi likvideintä kattavuusehdon täyttävää. Jos ehdon täyttää alle
   neljä markkinaa, tutkimusta ei ajeta, ja syy raportoidaan.

**Rajoitus:** lista on nykyinen. Vuoden 2024 jälkeen poistetut markkinat eivät ole ehdokkaina.
Valinta ei käytä testijakson dataa.

## 4. Puuttuva data vs. aidosti kaupaton aika

* **Kynttilätyypit:**
  * **Kaupaton kynttilä:** API palauttaa tasaisen kynttilän (o = h = l = c) volyymilla 0. Tällainen
    kynttilä on pörssin vastaus "ei kauppoja", ei puuttuva rivi.
  * **Puuttuva rivi:** jokin 15 minuutin aikaväli puuttuu API:n vastauksesta. Kyseinen vuorokausi
    haetaan uudelleen kerran.
  * Jos rivi puuttuu edelleen, se merkitään **puuttuvaksi**. Se täytetään edellisellä
    päätöskurssilla volyymilla 0, jotta aika etenee tasaisesti. Puuttuva rivi lasketaan
    kaupattomaksi ja raportoidaan erikseen.
* **Eheystarkistus jokaiselle markkinalle**, siemen 20261004:
  1. **Satunnaisotos:** 200 testijakson 15m-kynttilää. Kunkin kynttilän 15 minuutin
     1m-kynttilät haetaan, ja niistä kootaan OHLCV: avaus = 1. avaus, ylin = max, alin = min,
     päätös = viimeinen päätös ja volyymi = summa. Koottua verrataan 15m-kynttilään.
     **Hyväksytään**, jos ≥ 99 % otoksesta täsmää (hinnat suhteellisesti 1e-9 ja volyymi 1e-6).
     Tarkistus todentaa samalla aikaleimojen kohdistuksen.
  2. **Kaupattomat kynttilät:** kaikki testijakson nollavolyymin 15m-kynttilät, enintään 300
     satunnaista. Niiden kaikkien 1m-kynttilöiden volyymin pitää olla 0. Jos 1m-datassa on kauppoja,
     kyse on **datavirheestä**.
* **Markkina on mukana analyysissa**, jos kaikki seuraavat ehdot täyttyvät:
  * testijakson 15m-kynttilöistä vähintään 98,0 % on kaupallisia
  * puuttuvia rivejä on enintään 0,5 %
  * eheystarkistus hyväksytään.
* **Kokonaispäätös:** jos mukana on **alle 4 markkinaa**, kokonaispäätös on AVOIN, ja
  markkinakohtaiset tulokset raportoidaan erikseen.

## 5. Signaalit (rakenne säilytetty, mitoitettu 15m-kynttilöihin)

* Signaalit tuotetaan botin lukitulla koodilla ilman muutoksia:
  * **K** = `aj1-kaanto` (T2-kääntymiskuviot, pisteet ≥ 2, volyymi ≥ 1,2 ×, kuvion vaatima
    edeltävä trendi)
  * **J** = `aj1-jatko` (jatkumissignaali).
  * Koodipolku on `PaperEngine.on_bar_close` → `on_signal`, ja avaukset on estetty.
* **Mitoitus:** kaikki botin aikaikkunat on määritelty **kynttilämäärinä**, joten 15m-kynttilöillä
  ne skaalautuvat sellaisinaan:

  | Ikkuna | 1m-botissa | Tässä tutkimuksessa |
  |---|---|---|
  | Keskimääräinen vaihteluväli ja volyymi | 20 kynttilää = 20 min | 20 kynttilää = 5 h |
  | Edeltävä trendi | 10 kynttilää = 10 min | 10 kynttilää = 2,5 h |
  | J:n murtoehto | 10 edellisen kynttilän ääripää | 10 × 15 min = 2,5 h |
  | Historian vähimmäispituus | 20 kynttilää | 20 kynttilää |

  Raja-arvot ovat ennallaan: trendi ±1,5·A, T2-koko ≥ 0,6·A, J:n runko ≥ 0,5, J:n koko ≥ 1,0·A,
  päätös uloimmassa 25 %:ssa ja volyymi ≥ 1,2 ×. Kynttilämäärämitoitus on ainoa skaalausvaihtoehto,
  jota käytetään. Muita vaihtoehtoja ei kokeilla.
* **Kaikki signaalit** otetaan mukaan riippumatta tappiorajoista, positiorajoista tai päällekkäisistä
  signaaleista.

## 6. Kokeellinen kauppa (sama signaaleille ja vertailuille)

* **Avaus:** signaalikynttilän jälkeisen 15m-kynttilän avaushinta, eli ensimmäinen hinta signaalin
  valmistumisen jälkeen.
* **A:** 20 signaalikynttilää edeltävän 15m-kynttilän keskimääräinen vaihteluväli. Tämä on sama
  luku kuin botin kontekstissa, ja skripti tarkistaa sen.
* **Tavoite ja stop:** ensisijaisesti avaus ± **1,0·A** markkinahinnasta symmetrisesti, ja
  täydentävästi ± 2,0·A.
* **Seuranta-aika: 16 kynttilää = 4 tuntia.** Aikaraja on 17. kynttilän avaus, eli 16
  kokonaisen kynttilän jälkeen.
  * Arvo on asetettu erikseen tälle tutkimukselle, eikä 1m-botin 15 minuutin sulkurajaa ole
    siirretty.
  * Perustelu: kynttilämäärä on suunnilleen sama kuin 1m-botissa (15–16 kynttilää). Neljä tuntia
    on pyöreä aika, joka riittää ±1·A-rajojen ratkeamiseen (vaiheen 1 historiassa vain 0,2 %
    tapauksista päättyi aikarajaan).
  * Muita seuranta-aikoja ei testata.
* **Pisteet:**
  * +1, jos tavoite osuu ensin, ja −1, jos stop osuu ensin.
  * Aikarajalla pisteet ovat suunnattu muutos / (k·A) rajattuna välille [−1, +1].
  * Hintakuilu kynttilän avauksessa lasketaan osumaksi.
  * Jos sama 15m-kynttilä osuu sekä tavoitteeseen että stoppiin, tapaus on **epäselvä**, ja sen
    pisteet ovat 0. Herkkyysanalyysi laskee tuloksen myös olettamalla kaikki epäselvät +1:ksi ja
    −1:ksi.

## 7. Satunnaisvertailu

* Jokaiselle signaalille arvotaan **50 vertailuhetkeä**:
  * sama markkina, sama suunta ja sama UTC-päivä
  * vähintään 16 kynttilän päässä signaalista, eli seuranta-ajan pituuden verran
  * sama kokeellinen kauppa, ja A lasketaan vertailuhetken omasta edeltävästä historiasta.
* Siemen on **20261004**.

## 8. Ensisijaiset mittarit, testit ja päätössääntö (vaihe 1)

* **Ensisijaiset ryhmät (4):** K long, K short, J long ja J short.
* **Mittari D** = signaalin pisteet − sen 50 vertailun keskiarvo, keskiarvona ryhmän signaaleista
  (±1,0·A, 16 kynttilää).
* **Epävarmuus:** päiväklusteribootstrap (UTC-päivä), 10 000 otosta, 95 %:n luottamusväli ja
  kaksisuuntainen p.
* **Useat testit:** neljälle ensisijaiselle testille tehdään **Holm-korjaus** (α = 0,05).
* **Täydentävät mittarit:**
  * K ja J yhdistettyinä
  * ±2·A
  * suunnattu tuotto 1, 4 ja 16 kynttilän jälkeen (A-yksiköissä)
  * MFE ja MAE
  * markkinakohtaiset tulokset.
  * Täydentäville mittareille raportoidaan Benjamini–Hochberg-q. Niistä ei tehdä päätelmiä
    yksinään.

**Päätössääntö kullekin ensisijaiselle ryhmälle** (m = mukana olevien markkinoiden määrä,
vaadittu = ⌈2m/3⌉):

| Ehto | Tulos |
|---|---|
| mukana alle 4 markkinaa | KOKONAISPÄÄTÖS AVOIN (markkinakohtaiset tulokset erikseen) |
| n < 300 signaalia tai < 60 päivää | AINEISTO EI RIITÄ |
| Holm-p < 0,05 **ja** D > 0 **ja** D > 0 molemmilla puoliskoilla **ja** D > 0 vähintään ⌈2m/3⌉ markkinalla | **AJOITUSETU OSOITETTU (ennen kuluja)** |
| Holm-p < 0,05 **ja** D < 0 samoin ehdoin | SIGNAALIT SATTUMAA HUONOMPIA |
| Holm-p < 0,05, mutta puoliskot tai markkinat ristiriidassa | TILASTOLLINEN ERO, EI JOHDONMUKAINEN – ei osoitettu |
| muuten | EI NÄYTTÖÄ AJOITUSEDUSTA |

* **Tulkinta-apu:** D = +0,10 vastaa suunnilleen 55 %:n tavoiteosuutta 50 %:n sijaan.
* Pelkkä voittoprosentti ei ole näyttöä.

## 9. Liikkeiden koko suhteessa kuluihin (kuvaileva, raportoidaan aina)

**Kulumalli (paperi):**
* taker-palkkio 0,05 % kummassakin päässä
* liukuma 0,02 % avauksessa sekä tavoite- ja aikarajasulussa, 0,05 % stopissa
* puolikas spread = max(nykyinen mitattu puolikas spread, 0,005 %). Spread mitataan tutkimuksen
  ajohetkellä Krakenin tickeristä: mediaani 20 havainnosta 15 sekunnin välein.

**Rajoitus:** historiallisia bid/ask-hintoja ei ole saatavilla, joten nykyinen spread on arvio
vuosien 2025–2026 spreadista.

**Raportoidaan markkinoittain ja ryhmittäin:**
* A prosentteina hinnasta (mediaani)
* edestakainen kulu C prosentteina hinnasta (stop-skenaario)
* C/A
* **kannattavuusrajan tavoiteosuus p\* = ½ + C/(2A)** symmetrisillä ±1·A-rajoilla, verrattuna
  signaalien ja vertailujen toteutuneeseen tavoiteosuuteen.

Tämä on kuvaus. Siitä ei tehdä kannattavuuspäätöstä.

## 10. Vaihe 2: kannattavuus (vain jos vaiheen 1 ryhmä on "AJOITUSETU OSOITETTU")

* **Ajetaan** vain niille ensisijaisille ryhmille, joiden vaiheen 1 tulos on AJOITUSETU OSOITETTU.
  Muille kirjataan "vaihetta 2 ei ajettu, koska ajoitusetua ei osoitettu".
* **Kauppa:** jokainen ryhmän signaali käydään kauppana sellaisenaan.
  * Avaus on seuraavan kynttilän avaus ± (puolikas spread + 0,02 %).
  * Tavoite ja stop ovat samat ±1·A-rajat markkinahinnasta.
  * Sulkuhinta on raja ∓ (puolikas spread + liukuma). Hintakuilussa käytetään avaushintaa.
  * Aikaraja on 16 kynttilää.
  * **Epäselvä tapaus on stop.** Tämä on varovainen oletus, ja herkkyysanalyysissa epäselvä on
    tavoite.
  * Palkkio on 0,05 % avauksen ja sulun nimellisarvosta.
  * Funding lasketaan Krakenin historiallisista tuntikoroista pitoajalle suhteessa. Long maksaa
    positiivisella korolla.
* **Mittari:** nettotuotto % nimellisarvosta per kauppa. Riskiä, positiokokoa ja päällekkäisyyttä ei
  simuloida, joten tulos on signaalikohtainen odotusarvo.
* **Epävarmuus:** päiväklusteribootstrap.
* **Päätös:** **KANNATTAVA ENNEN PAPERITESTIÄ**, jos kaikki seuraavat täyttyvät:
  * ka > 0
  * 95 %:n luottamusvälin alaraja > 0
  * molempien puoliskojen ka > 0
  * ka > 0 vähintään ⌈2m/3⌉ markkinalla.

  Muuten tulos on **EI KANNATTAVA**.
* **Jatko:** vaikka tulos olisi kannattava, seuraava askel on eteenpäin kerättävä paperitesti, ei
  oikea kaupankäynti.

## 11. Tulevan tiedon esto (testataan `tests/test_tutkimus15.py`)

* Signaalit ja A eivät muutu, vaikka data katkaistaan signaalikynttilän kohdalta.
* Avaus tehdään vasta signaalin jälkeisen kynttilän avauksessa, ja lopputulos lasketaan vain sen
  jälkeisistä kynttilöistä.
* Vertailuhetkien A lasketaan vain niitä edeltävistä kynttilöistä.
* Markkinavalinta käyttää vain testijaksoa edeltävää dataa.

## 12. Ajon vaiheet ja kirjaukset

1. **Lukitus:** tämä suunnitelma ja koodi commitoidaan ennen dataa.
2. **Valinta:** markkinat valitaan, ja tulos commitoidaan (`tutkimus15/tulokset/valinta.md`).
3. **Lataus ja eheys:** testijakson data ladataan, ja eheysraportti commitoidaan
   (`tutkimus15/tulokset/eheys.md`).
4. **Analyysi:** vaihe 1 ja kuvaileva kulusuhde ajetaan, ja vaihe 2 ehdollisesti
   (`tutkimus15/tulokset/raportti.md`, `signaalit.csv`).
5. **Raportointi:** tulos raportoidaan sellaisenaan, myös epäonnistunut tai epäselvä. Rajoja ei
   säädetä, eikä vaihtoehtoja kokeilla samalla datalla.

## 13. Muutos 1.1 (4.10.2026 klo 07:00 UTC, ennen testijakson datan latausta)

**Mitä tapahtui:**
* Version 1.0 markkinavalinta (luku 3) ajettiin 4.10.2026 klo 06:48 UTC.
* Yksikään markkina ei täyttänyt 1m-kattavuusehtoa (≥ 99 % kauppaminuutteja). Esimerkiksi PF_XBTUSD
  sai 98,63 % ja PF_ETHUSD 96,90 % (`tutkimus15/tulokset/valinta_v1_0.md`).
* API palautti kaikki minuutit, joten kyse on aidosti kaupattomista minuuteista eikä puuttuvasta
  datasta.
* Version 1.0 mukaan tutkimusta ei olisi ajettu.

**Muutos:** luvun 3 kohdat 3–4 korvataan seuraavasti:

3. Kymmenelle likvideimmälle lasketaan valintajakson **15m-kynttilöistä** kauppakynttilöiden
   osuus (volyymi > 0, odotettu määrä 8 832). 1m-kauppaminuuttien osuus raportoidaan vain
   tiedoksi.
4. **Kattavuusehto:** kauppakynttilöitä (15m) on vähintään 99,0 %.

Kohta 5 (kuusi likvideintä, vähintään 4) ja kaikki muut luvut pysyvät ennallaan. Erityisesti
testijakson kattavuus- ja eheysehdot (luku 4) eivät muutu.

**Perustelu:**
* Tutkimus käyttää 15m-kynttilöitä. Kattavuus mitataan nyt samalla resoluutiolla kuin
  analyysissa ja testijakson ehdossa (luku 4).
* 1m-ehto oli asetettu tuntematta Krakenin futuurien tavanomaista minuuttitason kaupattomuutta.
* Raja (99 %) ja kaikki muut säännöt ovat ennallaan.
* **Muutos tehtiin ennen kuin testijakson dataa ladattiin.** Signaaleja tai lopputuloksia ei ollut
  laskettu, joten muutos ei voi perustua tuloksiin.
* Valintajakson likviditeettijärjestys oli nähty. Muutos ei kuitenkaan valitse markkinoita
  nimeltä, vaan sama sääntö koskee kaikkia ehdokkaita.

Raportissa tämä muutos ilmoitetaan poikkeamana alkuperäisestä lukitusta suunnitelmasta.
