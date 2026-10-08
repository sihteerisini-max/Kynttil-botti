# Tutkimus K4H: 15 minuutin K-kääntymissignaalit ja kiinteä 4 tunnin pitoaika – ennakkoon lukittu suunnitelma

**Lukittu 8.10.2026** ennen kuin tämän tutkimuksen laskelmia on tehty millään datalla. Tätä
suunnitelmaa ei muuteta tulosten perusteella. Lukituksen tunniste on tämän tiedoston sisältävä
git-commit.

* **Erillinen tutkimus.** Se ei muuta livebottia, paperitilejä eikä lukittua lokakuun toistotestia
  (2.–30.10.2026), eikä se käytä toiston dataa.
* **Vain tutkimusta ja paperilaskentaa.** Oikean rahan kaupankäyntiä ei ole.
* **Toteutus:** hakemisto `tutkimus_k4h/`, oma Railway-palvelu ja oma Volume. Signaalikoodi on
  tavukopio botin koodista.

## 1. Kysymys

Tutkimus 15M:n eksploratiivinen havainto:
* 15 minuutin K-signaalin jälkeen suunnattu hintamuutos 16 kynttilän (4 h) kohdalla oli satunnaisia
  vertailuhetkiä suurempi: K long +0,32 A ja K short +0,29 A, BH-q 0,013–0,016.
* Havainto tehtiin jo käytetyllä datalla (1.1.2025–1.7.2026), joten se ei ole näyttöä.

**Tutkimuskysymykset:**
* **H1:** säilyykö suuntavaikutus uudella datalla?
* **H2:** kattaako se kaupankäynnin kulut, kun K-signaalilla käydään kauppaa kiinteällä
  4 tunnin pitoajalla?

## 2. Aineistot

| Aineisto | Aika (UTC) | Käyttö |
|---|---|---|
| **KEHITYS** | 1.1.2025 00:00 – 1.7.2026 00:00 (lämmittely 29.12.2024 alkaen) | Jo käytetty Tutkimus 15M:ssä. Laskelmat esitetään **vain kehitysanalyysinä**, eivät näyttönä. Sääntöihin ei tehdä muutoksia niiden perusteella. |
| **VAHVISTUS** | **1.1.2024 00:00 – 1.10.2024 00:00** (274 vrk; lämmittely 29.12.2023 alkaen, jälkidata 1.10.2024 klo 06:00 asti) | Riippumaton vahvistus. Jaksoa ei ole käytetty missään aiemmassa analyysissä. Tutkimus 15M:n markkinavalinta käytti vain 1.10.–31.12.2024 likviditeettiä, ei signaaleja eikä hintakehitystä. |
| Vahvistuksen puoliskot | 1.1.–17.5.2024 ja 17.5.–1.10.2024 (137 vrk kumpikin) | johdonmukaisuusehto |

**Ajojärjestys:**
1. Suunnitelma ja koodi lukitaan.
2. Kehitysanalyysi ajetaan.
3. **Vahvistus ajetaan vasta Jessen hyväksynnän jälkeen.** Kehitystuloksen perusteella ei muuteta
   mitään. Ainoa vaihtoehto on jättää vahvistus kokonaan ajamatta.
4. Jos vahvistus on myönteinen, seuraava vaihe on eteenpäin kerättävä paperitesti 30.10.2026
   jälkeisellä datalla. Siitä tehdään oma suunnitelma.

**Markkinat** (kiinteät, samat kuin Tutkimus 15M): PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_DOGEUSD,
PF_XRPUSD ja PF_PEPEUSD. Kaikilla on 15m-dataa 28.12.2023 alkaen (tarkistettu 8.10.2026).
* **Rajoitus:** markkinat on valittu vuoden 2024 lopun likviditeetin perusteella, siis
  vahvistusjakson jälkeen. Valinta ei käyttänyt signaali- tai tuottotietoa.

## 3. Signaali (ennallaan)

* **K** = botin lukittu `aj1-kaanto` (T2-kääntymiskuviot) 15m-kynttilöillä täsmälleen kuten
  Tutkimus 15M:ssä. Kaikki ikkunat on mitattu kynttilämäärinä.
* Signaali syntyy signaalikynttilän sulkeutuessa. Se tuotetaan botin omalla koodilla, ja avaukset
  on estetty.
* Sekä long- että short-signaalit tutkitaan, ja ne raportoidaan erikseen.

## 4. Kaupankäyntisäännöt (paperi)

* **Avaus:** signaalikynttilän i jälkeisen kynttilän (i+1) avaushinta, eli ensimmäinen hinta
  signaalin valmistumisen jälkeen.
* **Sulku:** kiinteä pitoaika, **täsmälleen 16 kynttilää = 4 h**. Sulku tehdään kynttilän i+17
  avaushintaan. **Ei stoppia eikä tavoitetta.**
* **Päällekkäiset signaalit:**
  * Kullakin markkinalla voi olla enintään yksi avoin positio.
  * Jos markkinalla on avoin positio, uusi K-signaali (samaan tai vastakkaiseen suuntaan) ohitetaan
    ja kirjataan ohitetuksi. Positiota ei käännetä eikä pidennetä.
  * Eri markkinoilla voi olla positio yhtä aikaa (enintään 6).
  * Uusi signaali voi avata position aikaisintaan sulkukynttilän avauksessa, kun edellinen positio
    on suljettu.
* **Koko:** kiinteä nimellisarvo N jokaiselle kaupalle. Tulokset ilmoitetaan prosentteina
  nimellisarvosta. Dollariesimerkeissä N = 1 000 $ ja vertailupääoma 6 × N = 6 000 $.
  Vipua ei rajoiteta.

**Kulut** (kaikki suhteessa nimellisarvoon):

| Kulu | Sääntö |
|---|---|
| Palkkio | taker 0,05 % avauksen ja sulun nimellisarvosta |
| Spread | avaus = avaushinta × (1 ± (½ spread + liukuma)), sulku = sulkuhinta × (1 ∓ (½ spread + liukuma)) |
| ½ spread | markkinakohtainen nykyinen mitattu mediaani (20 havaintoa 15 s välein ajon alussa), vähintään 0,005 % |
| Liukuma | 0,02 % kummassakin päässä |
| Funding | Krakenin historialliset tuntikorot, kun ne ovat saatavilla (6.10.2025 alkaen). Pitoajan funding = Σ korko × nimellisarvo; long maksaa positiivisella korolla. Kun historiaa ei ole (koko vahvistusjakso ja kehitysjakson alku), käytetään varovaista kiinteää kulua **0,01 % per kauppa** suunnasta riippumatta. Herkkyysanalyysissa funding on 0. |

## 5. Mittarit ja päätössääntö

Ryhmät ovat **K long** ja **K short**. Kummallekin tehdään kaksi ensisijaista testiä, ja
Holm-korjaus tehdään testityypeittäin kahdelle ryhmälle.

* **H1 – suuntavaikutus** (kaikki signaalit, ei kuluja):
  * **D16** = signaalin suunnattu muutos avauksesta sulkuun A-yksiköissä (A = 20 edeltävän 15m-kynttilän
    keskimääräinen vaihteluväli) − 50 satunnaisen vertailuhetken saman mittarin keskiarvo.
  * Vertailuhetket otetaan samalta markkinalta, samaan suuntaan ja samalta UTC-päivältä, vähintään
    16 kynttilän päästä signaalista. Hetket, joilla A = 0, jätetään pois. Siemen 20261008.
  * Päiväklusteribootstrap (10 000 otosta) ja kaksisuuntainen p.
* **H2 – kannattavuus** (toteutetut kaupat päällekkäisyyssäännön jälkeen, kaikki kulut):
  * nettotuotto % nimellisarvosta per kauppa
  * päiväklusteribootstrap (10 000 otosta) ja yksisuuntainen p (H0: ka ≤ 0).

**Ehdot kullekin ryhmälle** (m = mukana olevat markkinat, vaadittu = ⌈2m/3⌉):

| Ehto | Tulos |
|---|---|
| mukana alle 4 markkinaa | AVOIN |
| toteutettuja kauppoja < 300 tai päiviä < 60 | AINEISTO EI RIITÄ |
| **H1:** Holm-p < 0,05 **ja** D16 > 0 **ja** molemmat puoliskot > 0 **ja** D16 > 0 vähintään vaaditulla määrällä markkinoita | SUUNTAVAIKUTUS SÄILYI |
| **H2:** Holm-p < 0,05 **ja** nettoka > 0 **ja** 95 % LV:n alaraja > 0 **ja** molemmat puoliskot > 0 **ja** nettoka > 0 vähintään vaaditulla määrällä markkinoita | KATTAA KULUT |

**Lopullinen päätös kullekin ryhmälle:**
* **H1 ja H2 täyttyvät:** JATKOON ETEENPÄIN KERÄTTÄVÄÄN PAPERITESTIIN. Tämä ei ole lupa oikeaan
  kaupankäyntiin.
* **Vain H1 täyttyy:** SUUNTAVAIKUTUS SÄILYI, MUTTA EI KATA KULUJA. Ryhmä hylätään
  kaupankäyntistrategiana.
* **H1 ei täyty:** EI NÄYTTÖÄ. Ryhmä hylätään.

**Kuvailevat mittarit** (aina, ei päätöksiä):
* bruttotuotto ennen kuluja
* kulut eriteltyinä
* kannattavuusraja eli tarvittava bruttotuotto
* osumaosuus
* markkinakohtaiset tulokset
* salkun pääomakäyrä ja suurin pudotus N = 1 000 $ per kauppa
* kaikkien signaalien versio ilman päällekkäisyyssääntöä
* funding-herkkyys (0 vs. 0,01 %)
* signaalien ja ohitusten määrät.

## 6. Datan laatu

Säännöt ovat samat kuin Tutkimus 15M:ssä (`docs/TUTKIMUS15_SUUNNITELMA.md`, luku 4):
* puuttuvat rivit erotellaan kaupattomista ja haetaan uudelleen
* markkina on mukana, jos ≥ 98 % 15m-kynttilöistä on kaupallisia, puuttuvia rivejä on ≤ 0,5 % ja
  1m-otostarkistus (200 + enintään 300 kaupatonta) täsmää vähintään 99-prosenttisesti.

Kaupat, joiden pitoajalla on puuttuvia rivejä, lasketaan mukaan, ja niiden määrä raportoidaan.

## 7. Tulevan tiedon esto

* Signaali ja A lasketaan vain signaalikynttilästä ja sitä edeltävistä kynttilöistä. Tämä
  tarkistetaan testillä, joka katkaisee datan.
* Avaus tehdään vasta seuraavan kynttilän avauksessa, ja sulku tehdään sitä myöhemmin.
* Päällekkäisyyssääntö käyttää vain ennen signaalia avattujen positioiden tietoja.
* Spread mitataan ajohetkellä. Tämä on rajoitus (historiallista bid/askia ei ole), mutta se ei
  käytä tulevaa hintatietoa.
