# VITA – tilanneraportti 8.10.2026

**Tilanne 8.10.2026 klo 12:57 UTC (15:57 Suomen aikaa).**

Raporttia varten ei muutettu sääntöjä, ei käynnistetty kokeita eikä keskeytetty testejä.
Lukitun toistojakson (2.–30.10.2026) tuloksia ei ole avattu. Siitä raportoidaan vain aikataulu,
toiminta ja tiedonkeruun laatu.

**Lähteet:**
* Railwayn deploy- ja ajolokit sekä Volume-tiedot
* botin omat lokit (`kaupat_*.jsonl`, `tapahtumat_*.jsonl`), haettu 8.10. klo 12:57 UTC
* seurantapalvelun `/api/tila`, `/api/kaaviot` ja `/api/toisto`
* repositorion tallennetut tulokset (`results/`, `tutkimus/tulokset/`, `tutkimus15/tulokset/`)
* edellinen raportti `RAPORTTI_kaikki_testit_2026-10-04.md`

Merkinnät: **puuttuu** = tietoa ei ole. **tarkistamaton** = tietoa ei ole todennettu tässä
raportissa.

---

## Tilannekuva

1. **Kynttiläbotin molemmat paperitilit ovat pysähtyneet** 10 %:n pudotusrajaan:
   * K 3.10. klo 01:16 UTC
   * J 4.10. klo 00:26 UTC

   Botti on käynnissä ja kirjaa signaaleja normaalisti (K noin 200 ja J noin 140 vuorokaudessa),
   mutta ei avaa kauppoja. Uusia kauppoja ei ole tullut edellisen raportin jälkeen.
2. **Vahvistava 1 minuutin toistotesti on käynnissä**, päivä 7/28 (päättyy 30.10. klo 00:00 UTC).
   Tiedonkeruussa ei ole puutteita eikä virheitä. Tuloksia ei ole avattu.
3. **15 minuutin tutkimus (Tutkimus 15M) valmistui 4.10.:** ajoitusetua ei löytynyt yhdessäkään
   neljästä ryhmästä (K/J × long/short). Kannattavuusvaihetta ei ajettu.
4. **⚠ Sini-trader-palvelu (VITA-sivusto ja funding-carry-paperivalidointi) on kaatunut**
   6.10. klo 01:00 UTC lähtien, koska sen 1 GB:n Volume on täynnä (990/1000 MB, `ENOSPC`).
   * Palvelu ei käynnisty.
   * Funding-carry-vaihe 4:n paperivalidoinnin keruu on ollut poikki noin 2,5 vuorokautta.
   * Tätä ei korjattu raporttia varten, koska se vaatii päätöksesi (ks. luku 1.3).
5. **Kokonaiskuva:**
   * Kaikki kynttiläsignaalien kaupankäyntitestit ovat olleet tappiollisia kulujen jälkeen.
   * Kahdessa riittävän suuressa satunnaisvertailussa signaalien ajoitus ei ollut satunnaista
     parempi (1 min historia SOL:lla ja 15 min historia kuudella markkinalla 18 kuukauden ajalta).
   * Kulut ovat tällä signaalityypillä rakenteellinen este: 15 minuutin kynttilöilläkin
     kannattavuus vaatisi 68–85 %:n tavoiteosuuden, kun toteutunut oli 45–51 %.

---

## Vertailutaulukko: kaikki testit

Sääntöversioita, markkinalistoja sekä historia- ja livetestejä ei ole yhdistetty.
* **"Hintaliike"** = tulos viitehinnoin ennen spreadia, liukumaa, palkkioita ja fundingia.
* **"D"** = signaalin pisteet − satunnaisten vertailuhetkien pisteet. D > 0 tarkoittaa satunnaista
  parempaa ajoitusta.

| Testi | Tyyppi | Jakso (UTC) | Markkinat | Säännöt | Kauppoja (long/short) | Hintaliike | Kulut | Netto | Suurin pudotus | Satunnaisvertailu |
|---|---|---|---|---|---|---|---|---|---|---|
| Historiatesti v1, jakso A | historia | 22.–29.9.2026 | XBT, ETH, SOL, ZEC, XRP | v1: T1, K-kuviot, 1,5 R, kulusuodatin 2× | 42 (16/26) | −441,87 $ | 592,47 $ | **−1 034,33 $** | 10,34 % (pysäytys) | ei tehty |
| T2-testi v1.1-T2 (arkistoitu) | live | 30.9. 15:21–17:39 | vaihtui 17:10 | T2, 1,5 R, kulusuodatin 2× | 1 (1/0) | −33,07 $ | 17,79 $ | **−50,85 $** | 0,51 % | ei tehty |
| T2-testi v2-T2 (arkistoitu) | live | sama | sama | T2, 1,5 R, kulusuodatin 4× | 0 | – | – | 0 $ | 0 % | ei tehty |
| **Ajoitustesti 1, K** | live | 30.9. 17:39 → (28.10.) | SUI, ZEC, XRP, DOGE, SOL | aj1-kaanto: 1 R / 1 R / 15 min, ei kulusuodatinta | 31 (9/22) | −75,19 $ | 934,18 $ | **−1 009,37 $** | 10,09 %, pysäytetty 3.10. | ei tehty livekaupoille |
| **Ajoitustesti 1, J** | live | sama | sama | aj1-jatko: 1 R / 1 R / 15 min | 42 (23/19) | −54,50 $ | 981,57 $ | **−1 036,07 $** | 10,36 %, pysäytetty 4.10. | ei tehty livekaupoille |
| Vaihe 1 historia, K | historia, ei kuluja | 15.7.–15.9.2026, 1 min | vain SOL täytti kattavuuden | aj1-kaanto-signaalit, ±1·A, 15 min | 2 449 signaalia (1 217/1 232) | – | – | – | – | **D −0,012** (LV −0,056…+0,033), ei näyttöä |
| Vaihe 1 historia, J | sama | sama | sama | aj1-jatko-signaalit | 1 816 (976/840) | – | – | – | – | **D −0,064** (Holm-p 0,009), satunnaista huonompi mutta ei johdonmukainen (1 markkina) |
| **Tutkimus 15M, K** | historia, ei kuluja | 1.1.2025–1.7.2026, 15 min | XBT, ETH, SOL, DOGE, XRP, PEPE | aj1-kaanto, ±1·A, 4 h | 7 594 signaalia (3 947/3 647) | – | – | – | – | long **+0,025**, short **+0,039**, ei näyttöä (Holm-p 0,53 / 0,26) |
| **Tutkimus 15M, J** | sama | sama | sama | aj1-jatko, ±1·A, 4 h | 5 562 (2 680/2 882) | – | – | – | – | long **−0,043**, short **−0,022**, ei näyttöä (Holm-p 0,26 / 0,53) |
| Vaihe 1 toisto | historia, eteenpäin kerätty | 2.–30.10.2026, 1 min | SUI, ZEC, XRP, DOGE, SOL | lukitut aj1-signaalit | **ei avattu** | – | – | – | – | tulokset 30.10. jälkeen |

---

## 1. Mitä nyt on ajossa?

### 1.1 Palvelut ja koodiversiot (Railway, 8.10. klo 12:57 UTC)

| Projekti / palvelu | Tila | Koodiversio (aktiivinen deploy) | Tehtävä |
|---|---|---|---|
| giving-integrity / **Kynttil-botti** | käynnissä | **b4a92ff** (30.9. 17:38). Kaikki myöhemmät pushit on ohitettu (watch paths), eikä uudelleenkäynnistyksiä ole näkyvissä säilyneissä lokeissa. | Ajoitustesti 1:n paperitilit K ja J (molemmat pysäytetty) sekä arkistoidut T2-tilit (eivät käy kauppaa) |
| giving-integrity / **Seuranta** | käynnissä | **7be58aa** (1.10. 17:43) | Vain lukeva seurantasivu ja kaaviot sekä toistojakson tiedonkeruu (`/data/keruu`) |
| giving-integrity / **Tutkimus15** | käynnissä, joutilaana | **0054dab** (4.10. 08:01) | 15M-tutkimuksen raakadata (109 MB). Ei tee mitään. |
| motivated-playfulness / **Sini-trader** (VITA-sivusto) | **KAATUNUT** 6.10. 01:00 UTC lähtien | ded1b59 (29.9. 16:19) | Funding-carry-vaihe 4 (XBT, ETH) ja muut Sini-traderin toiminnot. Syy: Volume täynnä 990/1000 MB (`ENOSPC`). |
| kind-cooperation / Sini-Server | aktiivinen deploy afcc2e0 (18.9.) | – | Puhelinassistentti. Ei kuulu kaupankäyntitesteihin. Toimintaa ei tarkistettu (**tarkistamaton**). |

Volumet:
* kynttil-botti 336/5 000 MB
* seuranta 195/5 000 MB
* tutkimus15 109/5 000 MB
* sini-trader 990/1 000 MB (täynnä)

### 1.2 Kynttiläbotin säännöt (Ajoitustesti 1, `docs/AJOITUSTESTI_1.md`)

* **Markkinat:** PF_SUIUSD, PF_ZECUSD, PF_XRPUSD, PF_DOGEUSD ja PF_SOLUSD, Kraken Derivatives,
  1 minuutin kynttilät.
* **Signaalit:**
  * **K** (`aj1-kaanto`): T2-kääntymiskuviot, eli vasara, käänteinen vasara, peittävät kuviot,
    tähdenlento ja hirttäytyjä. Vaatimukset: pisteet ≥ 2, volyymi ≥ 1,2 ×, kuvion vaatima
    edeltävä trendi ±1,5·A ja koko ≥ 0,6·A.
  * **J** (`aj1-jatko`): jatkumissignaali. Vaatimukset: trendi ±1,5·A, kynttilän suunta, runko
    ≥ 0,5, koko ≥ 1,0·A, päätös uloimmassa 25 %:ssa, uusi 10 kynttilän ääripää ja volyymi
    ≥ 1,2 ×.
* **Avaus:** seuraavan kynttilän avaushinta + ½ spread + liukuma 0,02 %. Ei kulusuodatinta.
* **Sulku:**
  * stop on kuvion ääripää ± 0,1·A
  * tavoite on 1 R toteutuneesta avaushinnasta
  * aikaraja 15 kynttilää
  * jos stop ja tavoite osuvat samaan kynttilään, tapaus on epäselvä ja kirjataan stoppina
  * hintakuilussa täyttö tehdään avaushintaan.
* **Kulumalli:**
  * taker 0,05 % kummassakin päässä
  * ½ havaittu spread avauksessa
  * liukuma 0,02 % (stopissa 0,05 %)
  * funding pitoajalta.
* **Riskirajat:**
  * riskibudjetti 0,5 % pääomasta
  * enintään 3 × pääoma per positio ja 5 × yhteensä
  * enintään 3 positiota, marginaali enintään 50 %, vipu enintään 10 ×
  * päivän tappioraja 2 % ja 4 tappion jälkeen 60 minuutin tauko
  * **10 %:n pudotus pysäyttää tilin pysyvästi.** Nollausta ei tehdä.

### 1.3 Paperitilit

| Tili | Tila | Pääoma | Viimeinen kauppa |
|---|---|---|---|
| aj1-kaanto (K) | **PYSÄYTETTY** (pudotus 10,09 %) | 8 990,63 $ | 3.10. 01:16 UTC |
| aj1-jatko (J) | **PYSÄYTETTY** (pudotus 10,36 %) | 8 963,93 $ | 4.10. 00:26 UTC |
| v1.1-T2, v2-T2 | arkistoitu 30.9. | 9 949,15 $ / 10 000 $ | 30.9. 17:38 |
| Sini-trader funding-carry, vaihe 4 (XBT, ETH) | **keskeytynyt palvelun kaatumisen vuoksi** 6.10. 01:00 UTC | **puuttuu** (tilaa ei voi lukea kaatuneesta palvelusta) | **puuttuu** |

**Sini-traderin kaatuminen, tarkemmin (lokeista):**
* Viimeiset normaalit rivit olivat 6.10. klo 00:54 UTC. Ne olivat basis-hälytyksiä
  `carry_basis PF_XBTUSD: −200…−216 bps`.
* Hälytykset ovat poikkeuksellisen suuria (noin −2 %), ja ne saattavat viitata datavirheeseen. Tätä
  ei ole tarkistettu (**tarkistamaton**).
* Klo 01:00:15 alkaen jokainen käynnistys kaatui, koska `CarryEngine._restore` → `store.append`
  ei voi kirjoittaa täyteen levyyn.
* Korjaus vaatii joko Volumen kasvattamisen tai vanhan datan siivoamisen. Molemmat ovat muutoksia
  lukittuun validointiin, joten ne vaativat päätöksesi.
* Validoinnissa on nyt aukko 6.10. klo 01:00 UTC alkaen, ja se pitää kirjata poikkeamaksi.

---

## 2. Mitä on tehty edellisen raportin (4.10. klo 06:15 UTC) jälkeen?

**Tehty:**
1. **Tutkimus 15M** (4.10. klo 06:30–08:07 UTC):
   * Suunnitelma ja koodi lukittiin ennen dataa (commitit 0bf9c88 ja d00622a).
   * Tutkimukselle tehtiin erillinen Railway-palvelu.
   * **Poikkeama 1:** alkuperäinen markkinavalinta (≥ 99 % kauppaminuutteja 1m-datasta) hylkäsi
     kaikki markkinat, myös XBT:n (98,6 %). Ehto mitattiin uudelleen 15m-kynttilöistä (muutos 1.1,
     30b589d) ennen kuin testidataa oli ladattu.
   * **Poikkeama 2:** A:n laskennan liukulukuvirhe korjattiin ajon 1 jälkeen (0054dab). Se koski 2
     signaalia 13 156:sta. Ensisijaiset päätökset olivat samat, ja ajo 1 on säilytetty.
   * Tulokset: `tutkimus15/tulokset/` (YHTEENVETO, raportti, valinta, eheys).
2. **Ei muita muutoksia** bottiin, seurantaan, sääntöihin tai testeihin. Repossa ei ole committeja
   4.10. klo 08:07 UTC jälkeen.
3. **Sini-trader kaatui** 6.10. levyn täyttymisen takia. Se ei johtunut tämän projektin
   muutoksista.

**Suunniteltu mutta tekemättä:**
* **K-signaalien 4 tunnin pitoajasta ei ole tehty erillistä tutkimusta.**
  * Havainto on 15M-tutkimuksen eksploratiivisista mittareista: K-signaalin jälkeinen suunnattu
    tuotto 16 kynttilän (4 h) kohdalla oli +0,29…+0,32 A (BH-q 0,013–0,016).
  * Samassa tutkimuksessa K:n ensisijainen tavoite/stop-mittari ei ollut merkitsevä.
  * Havainto on hypoteesi, ei näyttöä. Sitä ei voi vahvistaa samalla datalla.
* Uusia hypoteeseja (K:n volatiliteettihavainto, 1 tunnin kynttilät) ei ole lukittu eikä testattu.
* Tutkimus15-palvelun poisto odottaa päätöstäsi.
* Ajoitustesti 1:n loppuarviointi on ajastettu 28.10. klo 18:05 UTC, ja toistojakson analyysi
  30.10. klo 01:10 UTC. Molemmat ovat ajastettuja tehtäviä tässä istunnossa, ja ne tarvitsevat
  koneesi verkkoon.

---

## 3. Mitä tulokset osoittavat?

### 3.1 Historiatestit (ajoitus satunnaisvertailulla, ilman kuluja)

**1 minuutti, 15.7.–15.9.2026, vain SOL (muut alle 95 %:n kattavuuden):**

| | Signaaleja | D | 95 % LV | Holm-p | Long (eksploratiivinen) | Short (eksploratiivinen) |
|---|---|---|---|---|---|---|
| K | 2 449 | −0,012 | −0,056 … +0,033 | 0,61 | −0,029 | +0,004 |
| J | 1 816 | −0,064 | −0,111 … −0,019 | 0,009 | −0,023 | **−0,112** (q < 0,001) |

**15 minuuttia, 1.1.2025–1.7.2026, 6 markkinaa, seuranta-aika 4 h:**

| Ryhmä | Signaaleja | D | 95 % LV | Holm-p | Tavoiteosuus: signaalit / satunnaiset | Päätös |
|---|---|---|---|---|---|---|
| K long | 3 947 | +0,025 | −0,018 … +0,068 | 0,53 | 47,5 % / 46,0 % | ei näyttöä |
| K short | 3 647 | +0,039 | −0,003 … +0,082 | 0,26 | 50,8 % / 48,8 % | ei näyttöä (puoliskot +0,10 / −0,03) |
| J long | 2 680 | −0,043 | −0,091 … +0,006 | 0,26 | 45,3 % / 48,5 % | ei näyttöä |
| J short | 2 882 | −0,022 | −0,077 … +0,035 | 0,53 | 47,8 % / 49,9 % | ei näyttöä |

**Historiatestin v1 kaupat** (jakso A, 1 min, kulujen kanssa): 42 kauppaa (long 16, short 26),
hintaliike −441,87 $, kulut 592,47 $, netto −1 034,33 $ ja pudotus 10,34 %. Satunnaisvertailua ei
tehty.

### 3.2 Livetestit (paperi)

| Tili | Suunta | Kauppoja | Tavoite / stop / aikaraja / epäselvä | Hintaliike | Kulut | Netto | Netto/kauppa |
|---|---|---|---|---|---|---|---|
| K | long | 9 | 3 / 5 / 1 / 0 | +46,93 $ | 265,84 $ | −218,91 $ | −24,32 $ |
| K | short | 22 | 5 / 16 / 1 / 0 | −122,12 $ | 668,34 $ | −790,46 $ | −35,93 $ |
| **K** | yht. | **31** | 8 / 21 / 2 / 0 | **−75,19 $** | **934,18 $** | **−1 009,37 $** | −32,56 $ |
| J | long | 23 | 11 / 9 / 3 / 0 | +126,06 $ | 525,46 $ | −399,40 $ | −17,37 $ |
| J | short | 19 | 4 / 14 / 1 / 0 | −180,56 $ | 456,11 $ | −636,67 $ | −33,51 $ |
| **J** | yht. | **42** | 15 / 23 / 4 / 0 | **−54,50 $** | **981,57 $** | **−1 036,07 $** | −24,67 $ |

* Suurin pudotus oli K 10,09 % ja J 10,36 %, minkä jälkeen tilit pysäytettiin.
* **Livekauppoja ei ole verrattu satunnaisiin hetkiin.** Otos on pieni (31 + 42) ja valikoitunut:
  päivän tappioraja rajasi avatut kaupat lähes kokonaan klo 00–03 UTC:hen. Lisäksi 2.10. jälkeiset
  livekaupat osuvat lukitun toistojakson sisään.
* T2-testi (arkistoitu): 1 kauppa, netto −50,85 $. Aineisto ei riitä mihinkään.

### 3.3 Mitä tämä yhteensä osoittaa

* **Osoitettu:** nykyisillä säännöillä kaikki kynttiläkaupankäynti on ollut tappiollista kulujen
  jälkeen. Jo ennen kuluja hintaliike on ollut lähellä nollaa tai negatiivinen.
* **Osoitettu kahdella riittävän suurella aineistolla:** K-signaalien ajoitus ei ole satunnaista
  parempi. J-signaalit ovat nolla tai heikompia kuin satunnaiset hetket.
* **Ei osoitettu:** yhdenkään signaaliryhmän etua missään testissä. K:n pieni positiivinen ero 15
  minuutin kynttilöillä (+0,03, eli noin 1,5 prosenttiyksikköä tavoiteosuudessa) ei ole tilastollisesti
  merkitsevä. Se on myös aivan liian pieni kuluihin nähden.

---

## 4. Toimiiko tiedonkeruu ja seuranta?

**Toistojakson tiedonkeruu** (seurantapalvelu, 8.10. klo 12:57 UTC; vain laatu, ei tuloksia):

| Markkina | Minuutteja tallessa / odotettu | Puuttuu | Kauppaminuutteja | Nollaminuutteja tarkistettu | Niissä kauppoja |
|---|---|---|---|---|---|
| SUI | 9 415 / 9 415 | 0 | 98,95 % | 99 | 0 |
| ZEC | 9 415 / 9 415 | 0 | 95,35 % | 438 | 0 |
| XRP | 9 415 / 9 415 | 0 | 95,10 % | 461 | 0 |
| DOGE | 9 415 / 9 415 | 0 | 93,31 % | 630 | 0 |
| SOL | 9 415 / 9 415 | 0 | 97,27 % | 257 | 0 |

* **Keruu toimii:**
  * 9 792 kierrosta 1.10. klo 17:43 alkaen, ilman yhtään virhettä.
  * Viimeisin onnistunut kierros oli 8.10. klo 12:57.
  * Yhtään minuuttia ei puutu.
* **Kaupaton aika:** kaikki 1 885 jakson nollaminuuttia tarkistettiin Krakenin kauppahistoriasta, ja
  jokainen oli aidosti kaupaton. Datavirheitä ei siis ole.
* **Kattavuus:** välitilanteessa 4/5 markkinaa ylittää 95 %:n rajan (DOGE ei). Tämä on datan
  laatua, ei tulos. Lopullinen kattavuus ratkeaa 30.10.

**Botin signaalikirjaus:**
* Kirjaus jatkuu pysäytyksen jälkeen: jokainen signaali kirjataan ohitettuna syineen.
* Signaaleja on kirjattu yhteensä:
  * K: 1 620 (long 868, short 752), joista 903 edellisen raportin jälkeen
  * J: 1 116 (long 541, short 575), joista 617 edellisen raportin jälkeen.
* Pysäytyksen jälkeen K-signaaleja on ohitettu 1 164 ja J-signaaleja 646.
* Viimeisimmät signaalit: K 8.10. klo 12:56 ja J klo 12:49 UTC.
* Signaaleja kertyy päivittäin tasaisesti: K 173–234 ja J 127–167 täyteen vuorokauteen (1.–7.10.).
* Uudelleenkäynnistyksiä ei ole säilyneissä lokeissa, joten kiinnikurontajaksoja, joilta signaaleja
  ei kirjattaisi, ei ole.

**Häiriöt** (botin lokit):
* Krakenin huoltokatko 6.10. klo 07:00–07:07 UTC: noteerausten haku epäonnistui 135 kertaa. Botti
  ei avaa kauppoja, joten vaikutusta ei ole.
* 8.10. klo 01:27: yksi aikakatkaisu.

**Seurantasivun kaaviot:**
* Sivu ja rajapinnat vastaavat, botti näkyy vastaavana ja virhelistat ovat tyhjät.
* **Avaus- ja sulkumerkit:** pysäytyksen jälkeen kauppoja ei ole, joten uusia avaus- tai
  sulkumerkkejä ei synny.
* Kaavioikkuna on enintään 24 h. Vanhat kaupat (viimeisin 4.10.) eivät siksi enää näy kaavioissa,
  mutta ne ovat seurantasivun kauppataulukoissa (73 kauppaa).
* **Avaamatta jääneet signaalit** näkyvät kaavioissa merkkeinä, kun valinta "Näytä tunnistetut,
  avaamatta jääneet signaalit" on päällä (oletuksena päällä): 340 merkkiä viimeisen 24 h:n aikana.
* Viimeisin signaali tai hylkäyssyy näkyy jokaisen kaavion yhteydessä.

**Havaitut, tarkistamattomat poikkeamat:**
* Seurannan lokissa on `BrokenPipeError`-rivejä. Ne syntyvät, kun selain sulkee yhteyden kesken
  vastauksen, eivätkä ne vaikuta dataan (**tarkistamaton**, mutta tyypillinen syy).
* Kaavion selityspaneelissa näkyi SUI:lle trendiarvo −68 × A, mikä on epätodennäköisen suuri.
  Syytä ei ole selvitetty (**tarkistamaton**). Se ei koske botin kirjauksia eikä toistodataa.

---

## 5. Mikä estää voitollisuuden?

| Tekijä | Osoitettu vai hypoteesi | Perustelu |
|---|---|---|
| **Kulut suhteessa liikkeen kokoon** | **OSOITETTU** (tärkein) | 1m-livekaupoissa kulut olivat mediaanina 1,8 × R (K) ja 0,95 × R (J). 6/8 K:n tavoitekaupasta oli tappiollisia kulujen jälkeen. 15 minuutin kynttilöillä kulut ovat 0,37–0,69 × A, jolloin kannattavuusraja on 68–85 % tavoiteosumia, kun toteutunut oli 45–51 %. Livetesteissä kulut olivat 934–982 $, kun hintaliike oli −55…−75 $. |
| **Signaalin suuntaetu** | **OSOITETTU, ettei sitä löytynyt** | K ei ole satunnaista parempi 1 minuutin kynttilöillä (SOL) eikä 15 minuutin kynttilöillä (6 markkinaa). J on nolla tai negatiivinen. |
| **Ajoitus** (avaushetki) | **OSOITETTU, ettei etua löytynyt** testatuilla asetelmilla | Satunnaisvertailu kontrolloi markkinan, suunnan, päivän ja volatiliteetin. Mittarina on tavoite tai stop ensin. |
| **Sulkusäännöt** (1 R / 1 R / 15 min) | **HYPOTEESI**, ei testattu erikseen | Symmetrinen 1:1-sulku vaatii yli 50 %:n osumatarkkuuden ennen kuluja. Eksploratiivinen havainto: K-signaalin jälkeen liike laajenee molempiin suuntiin, ja 4 h:n tuotto oli positiivinen. Sulkutavan muuttaminen voisi teoriassa muuttaa tulosta, mutta tätä ei ole testattu, eikä samaa dataa voi käyttää. |
| **Likviditeetti** | **OSITTAIN OSOITETTU** | 1m-altcoineilla on paljon kaupattomia minuutteja: historiassa 84–96 % kauppaminuutteja, ja jopa XBT:llä 98,6 % vuonna 2024. PEPEn puolikas spread on 0,05 %, kun XBT:llä se on 0,0006 %. Livekaupat valikoituivat yötunneille, jolloin spreadit ovat suhteessa leveimmät. Likviditeetti nostaa kuluja, mutta likvideimmilläkään markkinoilla ei löytynyt etua 15 minuutin kynttilöillä. |
| **Position koko** | **OSOITETTU, ettei se ole syy** | Kaikki kulut ovat suhteessa nimellisarvoon, joten kulut/R ei riipu positiokoosta. Riskibudjetti 0,5 % kertoo vain tappion dollarimäärän, ei kannattavuutta. Positiokoko vaikuttaa pudotuksen nopeuteen, mutta ei odotusarvon etumerkkiin. |
| **Riskirajat** | **OSOITETTU** vaikutus otokseen, ei kannattavuuteen | Päivän tappioraja ja pysäytys rajasivat livekaupat 4–8 %:iin signaaleista. Tämä vaikeuttaa livetestien tulkintaa, mutta ei selitä tappiota. |
| **Taker-toimeksiannot** | **HYPOTEESI** | Maker-palkkio on pienempi, mutta täyttyminen ei ole varmaa, ja täyttyvät maker-toimeksiannot ovat usein epäedullisesti valikoituneita. Tätä ei ole testattu. |

**Yhteenveto:** voitollisuuden estää ensisijaisesti se, ettei signaaleilla ole osoitettua
suuntaetua. Etu pitäisi olla suuri, koska kulut vievät lyhyellä aikavälillä merkittävän osan
liikkeestä. Pelkkä parametrien säätäminen samalla signaalityypillä ei korjaa kumpaakaan.

---

## 6. Enintään kolme perusteltua seuraavaa kehityskokeilua (ei toteutettu)

Kaikissa kolmessa:
* suunnitelma lukitaan ennen dataa
* käytetään vain käyttämätöntä dataa
* tehdään satunnaisvertailu
* raportoidaan myös epäonnistunut tulos
* kannattavuusraja lasketaan etukäteen.

Käytetty data, jota ei enää käytetä todisteena:
* 1m: 15.7.–15.9.2026 ja 22.9.2026 alkaen
* 15m: 1.10.2024–1.7.2026 kuudella markkinalla.

### Kokeilu 1: Kulukynnys ensin – millä aikavälillä liikkeet ylipäätään kantavat kulut?

* **Perustelu:** kulut ovat osoitettu este. Ennen uusia signaalitestejä kannattaa selvittää ilman
  signaaleja, millä aikavälillä ja markkinoilla tyypillinen liike on riittävän suuri. Näin vältetään
  signaalitestit asetelmissa, joissa voitto on mahdoton.
* **Data:** Krakenin 1h- ja 4h-kynttilät XBT:lle, ETH:lle ja SOL:lle. Lisäksi 24 tunnin kulun
  arvio nykyisistä spreadeista ja palkkioista.
* **Ennalta määriteltävä ehto:** aikaväli kelpaa signaalitestiin vain, jos C/A-mediaani ≤ 0,15, eli
  kannattavuusraja p\* ≤ 57,5 %. Jos mikään aikaväli ei täytä ehtoa, lyhyen aikavälin
  kynttiläkaupasta luovutaan taker-kuluilla.
* **Huom:** tämä on kuvaileva laskelma, ei kannattavuustesti, eikä se vaadi signaalituloksia. Se
  voidaan tehdä myös 2024–2026 datalle, koska suunnan tuloksia ei katsota.

### Kokeilu 2: K-signaalit 1 tunnin kynttilöillä tai K-signaali volatiliteetin ennustajana

* **Perustelu:** K oli ainoa signaali, jonka ero oli positiivinen 15 minuutin kynttilöillä
  (ei-merkitsevä). Sen jälkeen liike laajeni molempiin suuntiin (MFE +0,43–0,49 A ja
  MAE +0,22–0,28 A). Tämä on eksploratiivinen hypoteesi. Kaksi vaihtoehtoista testiä, joista
  valitaan yksi ennen dataa:
  * **2a:** K-signaali sellaisenaan aikavälillä, jonka kokeilu 1 hyväksyy (esim. 1 h), ±1·A ja
    seuranta-aika ennalta (esim. 8 kynttilää).
  * **2b:** suuntaneutraali hypoteesi: K-signaalia seuraavan 4 tunnin vaihteluväli on suurempi kuin
    satunnaisilla hetkillä.
* **Data:** käyttämätön jakso, esimerkiksi 1.1.–30.9.2024 15m- tai 1h-kynttilöinä samoille
  likvideille markkinoille, tai eteenpäin kerättävä data toistojakson päättymisen (30.10.2026)
  jälkeen. Jakso 1.7.2026–30.10.2026 ei kelpaa, koska se on osin jo käytetty.
* **Ennalta määriteltävä ehto:**
  * 2a: ensisijainen D > 0 Holm-korjattuna, molemmat puoliskot ja vähintään 2/3 markkinoista. Sen
    lisäksi toteutuneen tavoiteosuuden alarajan pitää ylittää p\*.
  * 2b: vaihteluvälisuhde > 1 luottamusvälin alarajalla.
  * **Hylkäys**, jos ehto ei täyty. Silloin K-signaaleista luovutaan.
* **Huom:** 2b ei suoraan tuota kauppaa ilman optioita. Se kertoo vain, mihin signaali reagoi.

### Kokeilu 3: Eri tuottolähde – trendi tai momentum pidemmällä aikavälillä

* **Perustelu:** linjasi on, että epäonnistuneen testin jälkeen siirrytään eri tuottolähteeseen eikä
  säädetä samaa. Kynttiläkuviot ovat lyhyen aikavälin kääntymis- ja jatkumishypoteeseja.
  Aikasarjamomentum (aiempi 1–4 viikon tuotto ennustaa seuraavaa) on eri ilmiö. Se käy harvemmin
  kauppaa, joten kulut ovat pienempi osa liikkeestä.
* **Data:** Krakenin päivä- tai 4h-kynttilät XBT:lle, ETH:lle ja SOL:lle mahdollisimman pitkältä
  ajalta. Kehitys tehdään 2022–2024 datalla ja testi lukitaan 2025–2026 datalle (momentumia ei ole testattu millään jaksolla; K- ja J-signaalit testattiin 2025–2026 15m-datalla, mutta kyse on eri hypoteesista). Lisäksi funding-historia.
* **Ennalta määriteltävä ehto:**
  * nettotuotto kulujen ja fundingin jälkeen > 0 testijaksolla
  * luottamusvälin alaraja > 0 tai ennalta määritelty vähimmäis-Sharpe
  * suurin pudotus alle ennalta asetetun rajan
  * tulos johdonmukainen molemmilla puoliskoilla.
  * Muuten hylkäys.

**Erillinen päätös, ei kehityskokeilu:** Sini-traderin funding-carry-vaihe 4 on keskeytynyt levyn
täyttymisen takia. Jatketaanko sitä (Volumen kasvatus tai siivous ja aukon kirjaus poikkeamaksi) vai
päätetäänkö se? Se on jo eri tuottolähde (carry), joten se on luonteva vertailukohta kokeilulle 3.

---

## Liite: tiedon tila

| Tieto | Tila |
|---|---|
| Kynttiläbotin lokit, kauppojen ja signaalien määrät | tarkistettu 8.10. 12:57 UTC |
| Livekauppojen tulokset | ennallaan 4.10. jälkeen (ei uusia kauppoja), luvut edellisestä raportista |
| Toistojakson tulokset | **ei avattu** (lukittu 30.10. asti) |
| Sini-traderin tila | kaatunut (Railway-lokit ja Volume). Funding-carry-tulokset **puuttuvat** tästä raportista, eikä niitä ole luettu. |
| Sini-traderin basis-hälytys −2 % | **tarkistamaton** |
| Sini-Serverin toiminta | **tarkistamaton** (ei kuulu kaupankäyntiin) |
