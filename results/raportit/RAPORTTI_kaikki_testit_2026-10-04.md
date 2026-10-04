# Kynttiläbotti – raportti kaikista testeistä

**Tilanne 4.10.2026 klo 06:15 UTC (09:15 Suomen aikaa).** Kaikki testit ovat paperikauppaa:
oikeita toimeksiantoja ei ole lähetetty. Raportin laatiminen ei muuttanut sääntöjä, tilejä eikä
käynnissä olevia testejä.

**Lähteet:**
* botin omat lokit Railwayn Volumesta (`kaupat_*.jsonl`, `tapahtumat_*.jsonl`), haettu 4.10.2026
  06:15 UTC
* Railwayn deploy- ja ajolokit
* seurantapalvelun tiedonkeruu (`/keruu`)
* repositorion tallennetut tulokset: `results/`, `validointi/`, `tutkimus/tulokset/`

Puuttuva tieto on merkitty sanalla **puuttuu**.

---

## Yhteenveto

**1. Tunnistaako botti long- ja short-paikat oikeaan aikaan? Ei ole näyttöä siitä.**
* Ainoa riittävän suuri vertailu satunnaisiin avaushetkiin on vaiheen 1 historiallinen tutkimus
  (15.7.–15.9.2026). Siinä kattavuusehdon täytti vain SOL.
* Kääntymissignaalit (K) eivät eronneet satunnaisista hetkistä: ero −0,012, 95 % LV
  −0,056 … +0,033.
* Jatkumissignaalit (J) olivat tilastollisesti **huonompia** kuin satunnaiset hetket: ero −0,064,
  Holm-p 0,009. Koska tulos tuli vain yhdeltä markkinalta, se ei lukitun säännön mukaan ole
  johdonmukainen.
* Long- tai short-suunnassa ei ollut näyttöä edusta kummallakaan signaalityypillä.
* Vahvistava toistojakso 2.–30.10.2026 on kesken. Sen tuloksia ei katsota ennen jakson loppua.

**2. Jääkö kaupankäynnistä voittoa kulujen jälkeen? Ei.**
* Jokainen kaupankäyntitesti on ollut tappiollinen kulujen jälkeen.
* Jo ennen kuluja hintaliike on ollut nollan tuntumassa tai negatiivinen.
* Kulut ovat moninkertaiset hintaliikkeeseen verrattuna. Käynnissä olevassa ajoitustestissä
  kulut olivat keskimäärin 23–30 $ kauppaa kohden, kun hintaliike ennen kuluja oli −1 … −2 $
  kauppaa kohden.

**3. Molemmat ajoitustestin paperitilit on pysäytetty.**
* Kumpikin tili on ylittänyt 10 %:n pudotusrajan:
  * K: 3.10. klo 01:16 UTC, pudotus 10,09 %
  * J: 4.10. klo 00:26 UTC, pudotus 10,36 %
* Tilit eivät avaa uusia kauppoja, koska pysäytys vaatii käsin nollauksen, eikä tilejä nollata.
* Signaalien kirjaus jatkuu (viimeisimmät signaalit 4.10. klo 06:11 ja 05:43 UTC).

**4. Kuvioiden tunnistus on eri kysymys.**
* Kuvioiden muoto vastaa sanallisia määritelmiä hyvin (sarjat A–C).
* Arviointi ei ole riippumaton, eikä se kerro ajoituksesta tai kannattavuudesta mitään.

**5. Voittoprosentti ei ole näyttöä edusta.**
* Tavoite ja stop ovat 1 R:n päässä toteutuneesta avaushinnasta. Avaushintaan sisältyy jo
  puolikas spread ja liukuma.
* Markkinahinnasta katsottuna tavoite on siksi kauempana kuin stop, ja satunnainenkin kauppa osuu
  stoppiin useammin.

---

## Vertailutaulukko

Eri sääntöversioita, markkinalistoja ja historia- ja livetestejä **ei ole yhdistetty**.
"Hintaliike" = tulos viitehinnoin ennen spreadia, liukumaa, palkkioita ja fundingia.
"Kulut" = palkkiot + spread ja liukuma + funding.

| Vaihe | Tyyppi | Jakso (UTC) | Markkinat | Säännöt | Signaaleja | Avattu / suljettu | Long / short (kaupat) | Tavoite / stop / aikaraja / epäselvä | Hintaliike | Kulut | Netto | Netto / kauppa | Suurin pudotus | Satunnaisvertailu |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Historiatesti v1, jakso A | historia | 22.9. 18:43 – 29.9. 18:43 | XBT, ETH, SOL, ZEC, XRP | v1: T1, K-kuviot, tavoite 1,5 R, kulusuodatin 2× | 1 534 | 42 / 42 | 16 / 26 | 1 / 22 / 19 / ei eroteltu | −441,87 $ | 592,47 $ | **−1 034,33 $** | −24,63 $ | 10,34 % (pysäytys 28.9.) | ei tehty |
| T2-testi v1.1-T2 (arkistoitu) | live | 30.9. 15:21 – 17:39 | vaihtui 17:10 (ks. luku 3) | T2, tavoite 1,5 R, kulusuodatin 2× | 20 | 1 / 1 | 1 / 0 | 0 / 1 / 0 / 0 | −33,07 $ (johdettu: brutto + spread ja liukuma) | 17,79 $ | **−50,85 $** | −50,85 $ | 0,51 % | ei tehty |
| T2-testi v2-T2 (arkistoitu) | live | 30.9. 15:21 – 17:39 | sama | T2, tavoite 1,5 R, kulusuodatin 4× | 20 | 0 / 0 | – | – | – | – | 0 $ | – | 0 % | ei tehty |
| **Ajoitustesti 1, K** (käynnissä, tili pysäytetty) | live | 30.9. 17:39 → (28.10. 17:39) | SUI, ZEC, XRP, DOGE, SOL | aj1-kaanto: T2-kääntyminen, 1 R / 1 R / 15 min, ei kulusuodatinta | 716 | 31 / 31 | 9 / 22 | 8 / 21 / 2 / 0 | −75,19 $ | 934,18 $ | **−1 009,37 $** | −32,56 $ | 10,09 % (pysäytys 3.10.) | ei tehty livekaupoille |
| **Ajoitustesti 1, J** (käynnissä, tili pysäytetty) | live | 30.9. 17:39 → (28.10. 17:39) | SUI, ZEC, XRP, DOGE, SOL | aj1-jatko: jatkumissignaali, 1 R / 1 R / 15 min | 499 | 42 / 42 | 23 / 19 | 15 / 23 / 4 / 0 | −54,50 $ | 981,57 $ | **−1 036,07 $** | −24,67 $ | 10,36 % (pysäytys 4.10.) | ei tehty livekaupoille |
| Vaihe 1 historiallinen, K | historia, ilman kuluja | 15.7. – 15.9. | vain SOL täytti kattavuuden | aj1-kaanto-signaalit, symmetriset ±1·A, 15 min | 2 449 | – (ei kauppoja) | signaaleja 1 217 / 1 232 | 1 194 / 1 223 / 4 / 28 | – | – | – | – | – | **ero −0,012**, ei näyttöä |
| Vaihe 1 historiallinen, J | historia, ilman kuluja | 15.7. – 15.9. | vain SOL | aj1-jatko-signaalit | 1 816 | – | signaaleja 976 / 840 | 808 / 928 / 1 / 79 | – | – | – | – | – | **ero −0,064** (Holm-p 0,009), sattumaa huonompi mutta ei johdonmukainen |
| Vaihe 1 toisto | historia, eteenpäin kerätty | 2.10. – 30.10. (päivä 3/28) | SUI, ZEC, XRP, DOGE, SOL | samat lukitut säännöt | ei katsottu | – | – | – | – | – | – | – | – | tulokset 30.10. jälkeen |

---

## 0. Kuvioiden tunnistuksen validointi (ei ajoitus- eikä kannattavuustesti)

Sokkoarvioinneissa kysyttiin, kuvaako botti kynttilät samoin kuin kirjallisuuden sanallinen
määritelmä. Arvioitavana oli vain kynttilä ja sitä edeltävä historia, ei myöhempää hintaa.

| Sarja | Data | Arvioija | Muoto | Tausta / koko | Riippumaton? |
|---|---|---|---|---|---|
| A (T1) | jakso A | Jesse ChatGPT:n avustamana, kuva | 33 oikein, 1 väärä hälytys (näytön pyöristys), 0 löytämättä, 29 oikein hylätty, 3 epäselvää | Tausta: 9 väärää hälytystä, kaikki pieniä kynttilöitä → muutos **T2** (koon alaraja 0,3 → 0,6 ×) | ei (muutos johdettiin tästä) |
| B (T2) | 29.9. 18:43 – 30.9. 14:23 | ChatGPT, numerot | 0 erimielisyyttä, 3 epäselvää | Koko: T2 0 erimielisyyttä, T1 21 | **ei** (oli nähnyt 0,6:n rajan) |
| C (T2) | sama jakso, eri kynttilät | ChatGPT, numerot | 0 erimielisyyttä, 3 epäselvää | Koko: T2 4 väärää hälytystä, T1 21 | **ei täysin** (aiempi yhteenveto välittyi) |

* **Tukee:** botti laskee muodot ja suhteet oikein. Laskennassa ei löytynyt virheitä (perusteluiden
  luvut täsmäsivät 0,01–0,05:n tarkkuudella).
* **Ei osoita:** tunnistus ei kerro, ennustaako kuvio hintaa. Edeltävän liikkeen tulkinnassa
  arvioija ja botin regressiotrendi erosivat useimmin, kun suunta vaihtui.
* **Rajoitukset:**
  * Arvioijia oli yksi, tapauksia 66 sarjaa kohden ja jakso noin 20 h.
  * Arvioija on kielimalli, eikä arviointi ole riippumaton.

## 1. Historiatesti v1, jakso A (22.–29.9.2026)

* **Säännöt:** v1, eli T1-tunnistus, K-tyyppiset kääntymiskuviot, tavoite 1,5 R, stop kuvion
  ääripäässä, aikaraja 15 min ja kulusuodatin (R ≥ 2 × kulut).
* **Markkinat:** PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_ZECUSD ja PF_XRPUSD.
* **Muutokset kesken jakson:** ei.
* **Signaalit:** 1 534, joista avattiin 42 ja ohitettiin 1 492:
  * kulusuodatin 932
  * päivän tappioraja 265
  * pudotuspysäytys 227
  * tauko 4 tappion jälkeen 55
  * markkinassa jo positio 9
  * 3 positiota auki 4
* **Kaupat:** voitollisia 7/42.

| | Kauppoja | Voittoja | Tavoite / stop / aikaraja | Hintaliike | Netto |
|---|---|---|---|---|---|
| Long | 16 | 3 | 1 / 7 / 8 | −106,24 $ | −336,93 $ |
| Short | 26 | 4 | 0 / 15 / 11 | −335,62 $ | −697,41 $ |
| **Yhteensä** | 42 | 7 | 1 / 22 / 19 | **−441,87 $** | **−1 034,33 $** |

* **Tulos ja kulut:**
  * brutto täyttöhinnoin −721,59 $
  * palkkiot 313,18 $
  * spread ja liukuma 279,72 $
  * funding +0,43 $ (tuloa)
  * netto −1 034,33 $, eli −24,63 $ kauppaa kohden (−0,72 R)
* **Suurin pudotus:** 10,34 %. Tili pysäytettiin 28.9. viimeisen kaupan jälkeen (klo 12:10), ja
  sen jälkeen pysäytyksen vuoksi ohitettiin 227 signaalia.
* **Epäselvät tapaukset** (stop ja tavoite samassa kynttilässä) eivät erotu tämän version lokissa.
  Merkintä lisättiin myöhemmin, joten niiden määrä **puuttuu**.
* **Satunnaisvertailu:** ei tehty.
* **Muuta:** jakso on katsottua kehitysdataa. Myöhemmissä kehityskokeissa (muutos kerrallaan,
  `results/jakso_A_tarkistus.md`) mikään muutos ei ollut kannattava. Näitä kokeita ei käytetä
  näyttönä.

## 2. Suunniteltu jakso B

Jakso B oli tarkoitettu v1.1:n ja v2:n live-paperivertailuksi. Sitä **ei käynnistetty**
(Jessen päätös 30.9.).

## 3. T2-kannattavuustesti (arkistoitu 30.9.2026 klo 17:39 UTC)

* **Säännöt:**
  * `v1.1-T2`: T2-tunnistus, tavoite 1,5 R, kulusuodatin 2×
  * `v2-T2`: sama, mutta kulusuodatin 4×
  * Molemmilla oli oma 10 000 $:n tili.
* **Jakso:** 30.9. 15:21–17:39 UTC, eli noin 2 h 18 min. Testi lopetettiin, kun ajoitustesti 1
  alkoi.
* **Muutokset kesken jakson:**
  * 15:26:57–15:27:00 tapahtui uudelleenkäynnistys, kun dokumenttimuutos pushattiin. Koodi oli
    identtinen, ja tila jatkui tallennuksesta.
  * **Markkinavaihto klo 17:10:** XBT, ETH, SOL, ZEC, XRP → SUI, ZEC, XRP, DOGE, SOL.
* **Ennen vaihtoa:**
  * kummallakin versiolla 17 signaalia (long 7, short 10)
  * kaikki ohitettiin kulusuodattimen takia
  * 0 kauppaa
* **Vaihdon jälkeen:**
  * `v1.1-T2`: 3 signaalia. Niistä 1 avattiin (ZEC long 17:28, suljettiin stoppiin 17:38, netto
    −50,85 $). Kulusuodatin ohitti 2.
  * `v2-T2`: 3 signaalia, jotka kulusuodatin ohitti kaikki.
  * Kulusuodatin oli ainoa ohitussyy.
* **Johtopäätös:** aineisto ei riitä mihinkään.

## 4. Ajoitustesti 1 – live-paperitesti (käynnissä, molemmat tilit pysäytetty)

* **Jakso:** 30.9.2026 klo 17:39 UTC – 28.10.2026 klo 17:39 UTC (28 vrk). Raportin hetkellä
  menossa päivä 4/28.
* **Markkinat:** PF_SUIUSD, PF_ZECUSD, PF_XRPUSD, PF_DOGEUSD ja PF_SOLUSD, 1 min kynttilät.
* **Säännöt (`docs/AJOITUSTESTI_1.md`):**
  * K (`aj1-kaanto`): T2-kääntymiskuviot.
  * J (`aj1-jatko`): jatkumissignaali.
  * Yhteistä: ei kulusuodatinta (kulut kirjataan), tavoite 1 R, stop 1 R, aikaraja 15 min.
  * Riskiraja: riskibudjetti 0,5 %, päivän tappioraja 2 %, 4 peräkkäisen tappion jälkeen 60 min
    tauko ja 10 %:n pudotus pysäyttää tilin.
  * Kummallakin on erillinen 10 000 $:n tili.
* **Muutokset kesken jakson:**
  * Ei sääntö-, markkina- tai koodimuutoksia.
  * Railwayssa on vain yksi onnistunut deploy (commit b4a92ff, 30.9. 17:38). Kaikki myöhemmät
    pushit ohitettiin (watch paths).
  * Lokissa on yksi `TESTIJAKSO`-käynnistysrivi, joten uudelleenkäynnistyksiä ei ollut.
    Kiinnikurontajaksoja, joissa signaaleja ei kirjattaisi, ei siten ole.

### 4.1 Signaalit ja avaamatta jääneet

| | K | J |
|---|---|---|
| Signaaleja yhteensä (avattu + ohitettu) | **716** (long 379, short 337) | **499** (long 251, short 248) |
| Avattu / suljettu / auki nyt | 31 / 31 / 0 | 42 / 42 / 0 |
| Ohitettu: päivän tappioraja 2 % | 378 | 408 |
| Ohitettu: tili pysäytetty (pudotus ≥ 10 %) | 260 | 29 |
| Ohitettu: tauko 4 tappion jälkeen | 46 | 10 |
| Ohitettu: markkinassa jo positio | 1 | 7 |
| Ohitettu: 3 positiota jo auki | 0 | 3 |
| Avattujen osuus signaaleista | 4,3 % | 8,4 % |

**Signaalit päivittäin (UTC):**

| Päivä | K signaaleja / avattu | K:n pääasiallinen ohitussyy | J signaaleja / avattu | J:n pääasiallinen ohitussyy |
|---|---|---|---|---|
| 30.9. (alk. 17:39) | 59 / 7 | päiväraja 40, tauko 12 | 39 / 11 | päiväraja 27 |
| 1.10. | 173 / 9 | päiväraja 153 | 127 / 8 | päiväraja 112 |
| 2.10. | 205 / 10 | päiväraja 185 | 131 / 7 | päiväraja 115 |
| 3.10. | 213 / 5 | pysäytys 194 | 167 / 12 | päiväraja 154 |
| 4.10. (klo 06:15 asti) | 66 / 0 | pysäytys 66 | 35 / 4 | pysäytys 29 |

**Tärkeä valintavinouma.** Päivän tappioraja täyttyi joka UTC-päivä yleensä parin ensimmäisen
tunnin aikana. Siksi lähes kaikki avatut kaupat ovat yöltä:
* K: 23/31 kauppaa avattiin klo 00–03 UTC (03–06 Suomen aikaa).
* J: 30/42 kauppaa avattiin samaan aikaan.
* Klo 06–18 UTC ei avattu yhtään kauppaa.

Kaupat eivät siis edusta kaikkia signaaleja. Ne ovat vuorokauden hiljaisimman jakson signaaleja,
jolloin spreadit ovat suhteessa leveimmät.

### 4.2 Tulokset: long ja short, K ja J erikseen

| Tili | Suunta | Kauppoja | Voittoja | Tavoite / stop / aikaraja / epäselvä | Hintaliike | Palkkiot | Spread + liukuma | Funding | Kulut yht. | Netto | Netto / kauppa |
|---|---|---|---|---|---|---|---|---|---|---|---|
| K | long | 9 | 1 | 3 / 5 / 1 / 0 | +46,93 $ | 145,00 $ | 120,82 $ | 0,02 $ | 265,84 $ | −218,91 $ | −24,32 $ |
| K | short | 22 | 1 | 5 / 16 / 1 / 0 | −122,12 $ | 356,16 $ | 312,24 $ | −0,06 $ | 668,34 $ | −790,46 $ | −35,93 $ |
| **K** | **yht.** | **31** | **2** | **8 / 21 / 2 / 0** | **−75,19 $** | 501,16 $ | 433,06 $ | −0,04 $ | **934,18 $** | **−1 009,37 $** | **−32,56 $** |
| J | long | 23 | 10 | 11 / 9 / 3 / 0 | +126,06 $ | 291,62 $ | 233,72 $ | 0,12 $ | 525,46 $ | −399,40 $ | −17,37 $ |
| J | short | 19 | 4 | 4 / 14 / 1 / 0 | −180,56 $ | 236,64 $ | 219,54 $ | −0,07 $ | 456,11 $ | −636,67 $ | −33,51 $ |
| **J** | **yht.** | **42** | **14** | **15 / 23 / 4 / 0** | **−54,50 $** | 528,26 $ | 453,26 $ | 0,05 $ | **981,57 $** | **−1 036,07 $** | **−24,67 $** |

Taulukon selitykset:
* K:n stopeista yksi täyttyi hintakuilussa avauksessa.
* Epäselviä tapauksia (stop ja tavoite samassa kynttilässä) ei ollut yhtään. Tämä versio
  merkitsee ne lokiin.
* Täsmäytys: hintaliike − spread ja liukuma = brutto täyttöhinnoin, ja brutto − palkkiot − funding
  = netto. Molemmat täsmäävät senttiin. Tilien loppupääoma 8 990,63 $ (K) ja 8 963,93 $ (J) on
  10 000 $ + netto.

**Tavoitteeseen päättyneet kaupat:**
* K: keskimäärin −3,53 $ netto, ja 6/8 tavoitekauppaa oli **tappiollisia kulujen jälkeen**.
* J: keskimäärin +7,82 $, ja 2/15 oli tappiollisia.

**Stoppiin päättyneet kaupat:** keskimäärin −45,29 $ (K) ja −46,89 $ (J).

**Kulujen suhde R:ään avaushetkellä:**
* K: mediaani 1,80 (vaihteluväli 0,52–6,21). Tyypillisessä K-kaupassa kulut ovat siis
  suuremmat kuin koko tavoiteliike.
* J: mediaani 0,95 (0,45–2,48).

**Epävarmuus kauppaa kohden** (karkea, kaupat oletettu riippumattomiksi, mikä ei pidä täysin):

| | Netto / kauppa, 95 % LV | Hintaliike ennen kuluja R-yksiköissä / kauppa, 95 % LV |
|---|---|---|
| K | −32,56 $ (−39,84 … −25,28) | −0,08 R (−0,40 … +0,24) |
| J | −24,67 $ (−32,91 … −16,43) | −0,03 R (−0,32 … +0,27) |
| J long | – | +0,25 R (−0,17 … +0,66) |
| J short | – | −0,37 R (−0,74 … +0,01) |

* Nettotappio on selvä.
* Hintaliikkeessä ennen kuluja ei ole erottuvaa etua eikä haittaa. Otos on liian pieni ja valikoitu
  (ks. 4.1).
* J:n short-puoli oli heikompi, ja sama suunta näkyi historiallisessa tutkimuksessa
  (eksploratiivinen mittari). Tämä on **hypoteesi** tulevaa ennakkoon lukittua testiä varten, ei
  näyttöä eikä peruste muuttaa sääntöjä nyt.

**Markkinoittain:**

| Markkina | K kauppoja | K hintaliike | K netto | J kauppoja | J hintaliike | J netto |
|---|---|---|---|---|---|---|
| DOGE | 10 | −16,74 $ | −322,19 $ | 10 | −83,51 $ | −336,51 $ |
| SOL | 8 | −45,35 $ | −317,04 $ | 7 | +73,72 $ | −95,21 $ |
| SUI | 4 | −32,42 $ | −112,18 $ | 8 | −93,22 $ | −250,81 $ |
| ZEC | 6 | −28,61 $ | −207,50 $ | 11 | +17,17 $ | −227,66 $ |
| XRP | 3 | +47,93 $ | −50,47 $ | 6 | +31,35 $ | −125,88 $ |

**Jako toistojakson alun mukaan.** Kaupat jaettiin avausajan mukaan ennen 2.10. klo 00:00 UTC ja
sen jälkeen. Tämä on vain tiedoksi, koska 2.10. jälkeiset kaupat sattuvat vaiheen 1 toistojakson
sisään (ks. luku 6).

| | K ennen 2.10. | K 2.10. alkaen | J ennen 2.10. | J 2.10. alkaen |
|---|---|---|---|---|
| Kauppoja | 16 | 15 | 19 | 23 |
| Hintaliike | +59,71 $ | −134,90 $ | −33,40 $ | −21,09 $ |
| Netto | −450,65 $ | −558,72 $ | −460,80 $ | −575,27 $ |

### 4.3 Riskirajat ja jatkunut signaaliseuranta

* **Päivän tappioraja (2 %)** täyttyi kummallakin tilillä joka UTC-päivä 30.9.–3.10.
* **4 tappion tauko (60 min)**, johdettu kauppalokista:
  * K: 7 kertaa, alkaen 30.9. 18:23, 1.10. 00:16 ja 01:31, 2.10. 00:21 ja 02:06 sekä 3.10. 00:10
    ja 01:16.
  * J: 3 kertaa, alkaen 1.10. 02:23, 2.10. 00:33 ja 3.10. 01:05.
* **Pudotuspysäytys (10 %):**
  * K pysäytettiin 3.10. klo 01:16 UTC (10,09 %). Ensimmäinen pysäytyksen vuoksi ohitettu signaali
    oli klo 01:18.
  * J pysäytettiin 4.10. klo 00:26 UTC (10,36 %), ja ensimmäinen ohitus oli klo 00:54.
* Pysäytys on pysyvä, kunnes tili nollataan käsin. Nollausta ei tehdä.
* **Signaaliseuranta jatkuu pysäytyksen jälkeen:** jokainen signaali kirjataan ohitettuna syineen.
  Pysäytyksen jälkeen kirjattiin 260 K-signaalia ja 29 J-signaalia, ja viimeisimmät olivat
  4.10. klo 06:11 (K) ja 05:43 (J) UTC.
* **Seuraus:** ajoitustesti 1 ei enää tuota uusia kauppoja. Kannattavuudesta ei tule tästä testistä
  lisätietoa ennen 28.10. Signaalien ajoitusta arvioidaan vaiheen 1 toistossa (luku 6).

### 4.4 Data ja virheet

* **Krakenin huoltokatko 1.10. klo 07:00:55–07:15:46 UTC:** noteerausten haku epäonnistui 283
  kertaa. Katkon aikana ei ollut signaaleja eikä avauksia, joten tuloksiin ei ollut vaikutusta.
* **2.10. klo 04:24 UTC** yksi DOGE-kynttilöiden haku epäonnistui. Saman minuutin DOGE-signaali
  kirjattiin, joten seuraava haku onnistui.
* Kauppattomat minuutit täytetään edellisellä päätöskurssilla volyymilla 0, kuten historiatestissä.
* Kulumalli on paperimalli:
  * Taker-palkkio 0,05 % kummassakin päässä.
  * Spreadina käytetään puolikasta havaittua spreadia avaushetkellä.
  * Liukumaksi oletetaan 0,02 %, ja stopissa 0,05 %.
  * Funding lasketaan.
  * Todellisia täyttöjä ei ole, joten todelliset kulut voivat olla suuremmat tai pienemmät.
* Lokit ovat täydelliset: avausten ja sulkujen määrät täsmäävät, eikä uudelleenkäynnistyksiä ollut.

## 5. Vaihe 1: historiallinen ajoitustutkimus satunnaisvertailulla (15.7.–15.9.2026)

* **Kysymys:** ennustavatko signaalit hinnan suuntaa paremmin kuin satunnainen hetki samalla
  markkinalla, samaan suuntaan ja samana UTC-päivänä? Kuluja ei huomioida.
* Suunnitelma ja analyysi lukittiin 1.10. ennen datan lataamista (`docs/VAIHE1_AJOITUSTUTKIMUS.md`).
* **Menetelmä:**
  * Signaalit tuotettiin botin omalla koodilla, ja ne ovat kaikki signaalit riskirajoista
    riippumatta.
  * Jokaiselle signaalille on 50 satunnaista vertailuhetkeä.
  * Rajat ovat symmetriset ±1·A markkinahinnasta, ja aikaraja on 15 min.
  * Kun stop ja tavoite osuvat samaan kynttilään, tapaus on epäselvä ja saa 0 pistettä.
  * Epävarmuus arvioitiin päiväklusteribootstrapilla, ja Holm-korjaus tehtiin K:lle ja J:lle.
* **Kattavuus:**
  * Vain SOL täytti ehdon (95,9 %).
  * Muut jäivät alle 95 %: DOGE 86,3 %, SUI 84,0 %, XRP 86,3 % ja ZEC 88,3 %.
  * Tulokset koskevat siis vain SOL:ia.

| | Signaaleja | Päiviä | Ero (signaali − satunnainen) | 95 % LV | Holm-p | Lukittu päätös |
|---|---|---|---|---|---|---|
| K | 2 449 | 62 | −0,012 | −0,056 … +0,033 | 0,61 | EI NÄYTTÖÄ AJOITUSEDUSTA |
| J | 1 816 | 62 | −0,064 | −0,111 … −0,019 | 0,009 | TILASTOLLINEN ERO, EI JOHDONMUKAINEN (1 markkina) – ei osoitettu |

* **Long ja short** (eksploratiivinen, BH-korjattu):
  * K long −0,029 (q 0,59) ja K short +0,004 (q 0,90), ei eroa.
  * J long −0,023 (q 0,74) ja **J short −0,112 (q < 0,001)**.
* **Lopputulokset ±1·A, tavoite / stop / aikaraja / epäselvä:**
  * K 1 194 / 1 223 / 4 / 28
  * J 808 / 928 / 1 / 79
  * Satunnaisvertailun tavoiteosuus oli 49 %.
* **Epäselvien herkkyys:**
  * K:n ero pysyy välillä −0,015 … −0,009, eli johtopäätös ei muutu.
  * J:n ero on −0,034, jos kaikki epäselvät olisivat voittoja, ja −0,095, jos kaikki olisivat
    tappioita. Ero on negatiivinen kummassakin tapauksessa.
* **Johtopäätös:** K-signaalien hetki ei eroa satunnaisesta. J-signaalien hetki oli SOL:lla
  satunnaista huonompi. Kumpikaan ei osoita ajoitusetua.

## 6. Vaihe 1: toistojakso (käynnissä, ensisijainen vahvistava testi)

* **Jakso:** 2.10.2026 klo 00:00 UTC (03:00 Suomen aikaa) – 30.10.2026 klo 00:00 UTC (02:00
  Suomen aikaa). Raportin hetkellä kulunut 2 vrk 6 h 15 min, eli päivä 3/28.
* **Säännöt:** samat lukitut säännöt, skripti, siemen ja päätössääntö.
  * Lisäys tehtiin 1.10. ennen jakson alkua: jos alle 3 markkinaa täyttää kattavuusehdon,
    kokonaispäätös jää avoimeksi ja markkinakohtaiset tulokset raportoidaan erikseen.
  * Sääntöjä ei ole muutettu.
* **Tuloksia ei ole katsottu, eikä niitä raportoida ennen jakson loppua.** Tämä on ennakkoon
  lukitun testin ehto.
  * Ajoitustesti 1:n paperikaupat 2.10. jälkeen (luku 4) osuvat samalle ajalle. Ne ovat eri
    mittari, valikoitu otos signaaleista, eikä niiden näkeminen muuta lukittuja sääntöjä.
* **Tiedonkeruun laatu jakson alusta** (seurantapalvelu, 4.10. klo 06:15 UTC):

| Markkina | Minuutteja tallessa / odotettu | Puuttuu | Kauppaminuutteja | Nollaminuutteja tarkistettu | Niistä kauppoja löytyi |
|---|---|---|---|---|---|
| SUI | 3 253 / 3 253 | 0 | 98,99 % | 33 | 0 |
| ZEC | 3 253 / 3 253 | 0 | 94,19 % | 189 | 0 |
| XRP | 3 253 / 3 253 | 0 | 89,98 % | 326 | 0 |
| DOGE | 3 253 / 3 253 | 0 | 88,29 % | 381 | 0 |
| SOL | 3 253 / 3 253 | 0 | 94,99 % (rajan alla 0,01 %) | 163 | 0 |

* **Tiedonkeruu toimii:**
  * Yhtään minuuttia ei puutu, eikä keruussa ole ollut virheitä (3 630 kierrosta 1.10. klo 17:43
    alkaen).
  * Kaikki 1 092 jakson nollaminuuttia tarkistettiin Krakenin kauppahistoriasta, ja jokainen oli
    aidosti kaupaton.
  * Puuttuvat minuutit ovat siis markkinan hiljaisuutta, eivät datavirheitä.
* **Välitilanne kattavuudessa:** tällä hetkellä vain SUI ylittää 95 %:n rajan. Jos tilanne pysyy
  samana jakson loppuun, kokonaispäätös jää lukitun säännön mukaan **avoimeksi**. Tämä on
  datan laatua, ei tulos.

## 7. Datan kattavuus ja luotettavuuteen vaikuttavat seikat (kaikki vaiheet)

1. **Kauppattomat minuutit.**
   * Valituilla altcoineilla on paljon minuutteja ilman kauppoja: historiassa 4–16 % ja
     toistojaksolla 1–12 %.
   * Ne on todennettu aidoiksi kolmella tavalla: uudelleenhaku, 1 min ja 5 min volyymien
     täsmäytys ja reaaliaikainen kauppahistoria.
   * Ne rajaavat markkinat pois ajoitustutkimuksesta.
2. **Valintavinouma livekaupoissa.** Päiväraja ja pysäytys rajasivat avatut kaupat 4–8 %:iin
   signaaleista ja lähes yksinomaan yötunteihin (UTC).
3. **Voittoprosentti on vinossa.** R ja tavoite mitataan toteutuneesta avaushinnasta, joten
   markkinahinnassa tavoite on kauempana kuin stop.
4. **Epäselvät tapaukset.**
   * v1-testissä niitä ei eroteltu, joten määrä puuttuu.
   * Ajoitustesti 1:ssä niitä oli 0.
   * Vaiheen 1 historiassa niitä oli 1,1 % (K) ja 4,4 % (J), ja niille tehtiin herkkyysanalyysi.
5. **Kulut ovat mallinnettuja paperikuluja**, eivät todellisia täyttöjä (ks. 4.4).
6. **Arvioinnin riippumattomuus.** Tunnistuksen sokkoarvioinnit B ja C eivät olleet riippumattomia.
7. **Katsottu data.**
   * Jakso A, arviointidata 29.–30.9. ja ajoitustesti 1:n kaupat ennen 2.10. ovat kehitysdataa.
   * Historiallisen tutkimuksen data 15.7.–15.9. on nyt käytetty.
8. **Korjatut raportointivirheet:**
   * Arkistodokumentissa luki aluksi 0 kauppaa, oikea luku on 1 (−50,85 $).
   * Aiempi karkea kannattavuusrajan arvio (11/16, 87–92 %) korjattiin kaupoittain laskettuun
     (10/16, noin 80 %).
   * Sarjan A yhteissummat laskettiin uudelleen.
9. **Uudelleenkäynnistys T2-testissä** 30.9. 15:27 (3 s). Tila säilyi.

## 8. Johtopäätökset

**Mitä tulokset tukevat:**
* Botti tunnistaa kynttiläkuvioiden muodot sanallisten määritelmien mukaisesti, ja sen laskenta on
  oikein. Arviointi ei kuitenkaan ole riippumaton.
* Nykyisillä säännöillä 1 minuutin kynttilöillä **kaupankäynti ei ole kannattavaa** kulujen
  jälkeen. Tämä toistui kaikissa kolmessa kaupankäyntiaineistossa (jakso A, T2-testi ja
  ajoitustesti 1).
* Syy on rakenteellinen: kulut ovat samaa suuruusluokkaa kuin R tai suuremmat. K-kaupoissa kulut
  olivat mediaanina 1,8 × R, joten edes tavoitteeseen osuminen ei yleensä tuottanut voittoa.
* Signaalien hetki ei ennustanut suuntaa satunnaista paremmin ainoalla riittävästi dataa sisältävällä
  markkinalla (SOL, 62 päivää). J oli siellä satunnaista huonompi.

**Mitä tulokset eivät vielä osoita:**
* Ne eivät osoita, ettei ajoituksessa voisi olla etua muilla markkinoilla tai toistojaksolla.
  Vahvistava toisto on kesken, ja historiassa vain yksi markkina oli mukana.
* Ne eivät osoita, että J-signaali olisi käänteisenä hyvä. Tulos on yhdeltä markkinalta, eikä
  suunnan kääntämistä ole testattu ennakkoon. Sitä ei tehdä tämän tuloksen perusteella.
* Ne eivät kerro, miten pidemmät aikavälit (esim. 15 min tai 1 h kynttilät) toimisivat. Niillä
  kulut ovat suhteessa R:ään pienemmät, mutta niitä ei ole testattu.
* Livekauppojen otos (31 + 42) on liian pieni ja valikoitu ajoituksen arviointiin. Livekaupoille ei
  ole tehty satunnaisvertailua.

**Perusteltu seuraava testi:**
1. **Anna vaiheen 1 toiston valmistua muuttamatta mitään.**
   * Toisto päättyy 30.10. klo 00:00 UTC, ja analyysi ajetaan lukituilla asetuksilla.
   * Paperitilien pysäytys ei haittaa, koska toisto arvioi kaikki signaalit kynttilädatasta.
2. **Jos toisto ei osoita ajoitusetua** (tai kokonaispäätös jää avoimeksi kattavuuden takia),
   1 minuutin kynttiläkuvioilla ei ole perusteita jatkaa kannattavuustestiin.
   * Uusi hypoteesi kannattaa lukita ennakkoon ennen kuin dataa katsotaan. Esimerkiksi samat
     kuviot pidemmällä aikavälillä ja likvideillä markkinoilla, joilla kauppattomia minuutteja on
     vähän.
   * Kynnys kulujen ja R:n suhteelle asetetaan etukäteen.
   * Testi ajetaan ensin satunnaisvertailulla historiadatalla, jota ei ole käytetty.
3. **Vain jos ajoitusetu osoitetaan,** seuraava vaihe on kannattavuustesti (vaihe 2) kulut
   mukaan lukien ja ennakkoon lukittuna, ensin historiassa ja sitten paperilla.
