# VITA – korjaus, carry-tilanne ja K4H-jatkotestin valmistelu (8.10.2026)

**Tilanne 8.10.2026 noin klo 17:40 UTC (20:40 Suomen aikaa).**
* Kaikki toiminta on paperikauppaa ja tutkimusta, eikä oikeaa rahaa käytetä.
* Lukittu lokakuun toistotesti (2.–30.10.) on koskematon, eikä sen tuloksia ole avattu.

**Yksityiskohtaiset tiedostot:**
* `results/vita/SINI_TRADER_KATKOS_JA_CARRY_2026-10-08.md`: katkos, basis ja carry
* `docs/TUTKIMUS_K4H_SUUNNITELMA.md`: lukittu jatkotestisuunnitelma
* `tutkimus_k4h/tulokset/kehitys_raportti.md`: kehitysanalyysi

---

## Lyhyesti

1. **Sini-trader on taas toiminnassa.** Levy kasvatettiin 1 → 5 GB. Kaikki lokit, tilat ja
   tutkimusdata (990 MB) säilyivät, eikä koodia, sääntöjä tai muuttujia muutettu.
   Katkos kesti noin 64 h (6.10. klo 01:00 – 8.10. klo 17:02 UTC).
2. **XBT:n noin −2 %:n carry-basis oli Sini-traderin oma datavirhe, ei todellinen havainto.**
   * Krakenin perpetual ja spot-indeksi erosivat toisistaan alle 1 bps.
   * Binance, Coinbase ja OKX olivat samalla tasolla.
   * Sini-traderin spot-hinta oli noin 2 % kaikkien yläpuolella.
3. **Funding carry -testi on 16 vuorokauden jälkeen nollan tuntumassa.** Palvelun mukaan
   +1,03 $ (+0,02 %), ja Krakenin datasta laskettu arvio on noin +0,14 $. Aineisto ei riitä
   johtopäätökseen, ja kirjanpidossa on täsmäämättömiä eriä.
4. **K4H-jatkotesti on valmisteltu ja lukittu.** Vahvistusta ei ole ajettu, vaan se odottaa
   hyväksyntääsi. **Kehitysdatalla (jo käytetty, ei näyttöä) strategia oli selvästi tappiollinen:**
   * jo ennen kuluja keskimäärin −0,02…−0,04 % per kauppa
   * kulujen jälkeen noin −0,2 % per kauppa
   * 5 339 kauppaa, netto −11 523 $, kun kauppakoko on 1 000 $.
   * "Suuntavaikutus" on suhteellinen: K-signaali voittaa saman päivän satunnaisen
     samansuuntaisen avauksen, mutta ei tuota absoluuttista hintaliikettä, josta voisi hyötyä.
5. **Aineisto ei tue kannattavuutta** yhdessäkään nyt tutkitussa kynttiläsignaalien muodossa.

---

## 1. Mitä korjasin: Sini-trader

| | |
|---|---|
| **Vika** | Railway Volume (1 000 MB) täyttyi (990 MB). Palvelu kaatui käynnistyksessä, koska `CarryEngine._restore` ei voinut kirjoittaa (`ENOSPC`). Tila oli CRASHED 6.10. klo 01:01 UTC lähtien. |
| **Syy** | Muuttuja `RECORDER_MAX_MB = 1500` sallii tallentimen kasvaa yli levyn koon. Tallennindataa on nyt 317 MB. Loput noin 670 MB on muuta dataa, jonka sisältöä ei tarkistettu (**tarkistamaton**, vaatii koodipääsyn). |
| **Korjaus** | Volume kasvatettiin 5 000 MB:hen (`volumeInstanceResize`). Palvelu käynnistettiin samalla koodilla ded1b59 (`deploymentRedeploy`) klo 17:00:44 UTC. **Mitään ei poistettu eikä muutettu.** |
| **Tila nyt** | Käynnissä. Carry-sessio c1790090826499 on ACTIVE. Tallentimella on 4 pörssiyhteyttä auki, 8 kirjaa ja 0 aukkoa. |
| **Katkos aineistossa** | 6.10. klo 01:00 – 8.10. klo 17:02 UTC (noin 64 h). Aukko koskee carry-moottoria (funding-kertymä, MTM), tallenninta, uutiskeruuta ja muita Sini-traderin toimintoja. Kirjattu poikkeamaksi. |

**Carry-basis noin −2 %, tarkistus:**

| XBT 6.10. klo 00:07–00:54 UTC | Hinta |
|---|---|
| Kraken perpetual (mark) | 85 786 – 85 953 |
| Krakenin spot-indeksi | 85 789 – 85 948 |
| Binance, Coinbase, OKX | 85 789 – 85 954 |
| **Sini-traderin spot** (laskettu hälytyksestä) | **87 518 – 87 853** |

* Krakenin perpetualin ja indeksin ero koko carry-jaksolla oli tuntitasolla enintään ±3 bps.
* Sini-traderin hälytykset vaihtelivat XBT:llä −50 … −330 bps ja ETH:llä −180 … +222 bps, joten
  ne ovat virheellisiä.
* Virhe ei ollut vanhentunut hinta, koska indeksi ei käynyt sillä tasolla kolmeen päivään.
* Uudelleenkäynnistyksen jälkeen spot-hinta oli taas oikealla tasolla (8,65 bps markista).
* **Juurisyy on koodissa, eikä sitä voitu tarkistaa**, koska Sini-trader-repoon ei ole pääsyä
  tästä istunnosta.
* Virhe vaikuttaa hälytyksiin ja positioiden markkina-arvoon (noin ±20 $ positiota kohden virheen
  aikana).
* Uudelleentasapainotuksia ei tehty, joten toteutuneet erät eivät todennäköisesti muuttuneet
  (**tarkistamaton**).

**Carry-testin jatkuminen:**
* Sessio jatkui automaattisesti uudelleenkäynnistyksessä.
* En pysäyttänyt sitä, koska pysäytys päättäisi lukitun session pysyvästi.
* Basis-virhe on selvitetty datavirheeksi, mutta korjaamatta. Se voi toistua, jolloin testin
  MTM-luvut ovat epäluotettavia.

## 2. Funding carry -testin (vaihe 4) tähänastiset tulokset

* **Jakso:** 22.9.2026 klo 15:27 UTC → käynnissä (16 vrk, josta noin 2,7 vrk katkosta). Lukittu
  kesto on 60–90 vrk.
* **Asetelma:** XBT ja ETH, kumpikin 1 000 $ nimellisarvo, vipu 2, long spot ja short perpetual.
* **Tapahtumat:** 2 avausta, 0 uudelleentasapainotusta tai sulkua ja noin 386 funding-tuntia.

| | Toteutunut (palvelun kirjanpito) | Laskennallinen arvio (Krakenin data) |
|---|---|---|
| Alkupääoma | 4 995,60 $ | – |
| Pääoma nyt | 4 996,63 $ | – |
| Bruttotulos (funding + MTM) | funding −2,35 $ (palvelun etumerkki), MTM −1,52 $ | funding **+4,53 $** (josta katkoksen aikana +1,16 $), MTM −0,18 $ |
| Kulut | palkkiot 4,20 $ | samat 4,20 $ |
| **Nettotulos** | **+1,03 $ (+0,02 %)** | **noin +0,14 $** |
| Suurin pudotus | **puuttuu** (ei pääomahistoriaa rajapinnassa) | noin 0,80 $ (0,016 %) |

* **Riittääkö aineisto? Ei.** Tulos on nolla kirjanpidon epävarmuuden rajoissa.
* Funding-korot olivat matalia: arvion mukaan noin 5 % vuodessa nimellisarvosta ja noin 2 % vuodessa
  5 000 $:n pääomasta ennen kuluja.
* **Puuttuvat tiedot:**
  * pääomahistoria ja suurin pudotus
  * funding-kirjauksen etumerkki ja täsmäytys (palvelu −2,35 $, arvio +4,53 $)
  * käteissaldon täsmäytys
  * kirjataanko katkoksen funding jälkikäteen
  * spot-virheen juurisyy.

  Kaikki vaativat Sini-trader-repon koodin.

## 3. K4H-jatkotesti: 15 minuutin K-signaalit ja kiinteä 4 tunnin pito

**Lukittu ennen laskelmia** (`docs/TUTKIMUS_K4H_SUUNNITELMA.md`, commit a587ffe, koodi d0c207a):

| | Sääntö |
|---|---|
| Signaali | Botin `aj1-kaanto` (K) 15m-kynttilöillä ennallaan, long ja short. |
| Avaus | Signaalikynttilän jälkeisen kynttilän avaushinta. |
| Sulku | Täsmälleen 16 kynttilää (4 h) myöhemmin avaushintaan. Ei stoppia eikä tavoitetta. |
| Päällekkäiset signaalit | Enintään 1 positio per markkina. Avoimen position aikana tulevat signaalit ohitetaan ja kirjataan. Positiota ei käännetä eikä pidennetä. Eri markkinoilla positioita voi olla samaan aikaan. |
| Kulut | Taker 0,05 % kummassakin päässä, ½ mitattu spread + 0,02 % liukuma kummassakin päässä. Funding Krakenin tuntikoroista, tai 0,01 % per kauppa, kun historiaa ei ole. |
| Markkinat | XBT, ETH, SOL, DOGE, XRP ja PEPE. |
| H1 | D16 = signaalin 4 h muutos − 50 satunnaisen hetken keskiarvo (sama markkina, suunta ja päivä) > 0. Ehdot: Holm-p < 0,05, molemmat puoliskot ja ≥ 4/6 markkinaa. |
| H2 | Nettotuotto per kauppa > 0 kaikkien kulujen jälkeen. Ehdot: 95 %:n luottamusvälin alaraja > 0, Holm-p < 0,05, molemmat puoliskot ja ≥ 4/6 markkinaa. |
| Päätös | Vain H1 ja H2 yhdessä johtavat jatkoon eteenpäin kerättävään paperitestiin. Tämä ei ole lupa oikeaan kaupankäyntiin. |
| Vahvistusdata | **1.1.–1.10.2024**, jota ei ole käytetty missään aiemmassa analyysissä. Ajetaan vain hyväksynnälläsi: palvelu estää ajon, kunnes `VAHVISTUS_SALLITTU=1`. |

**Kehitysanalyysi** (1.1.2025–1.7.2026, jo käytetty Tutkimus 15M:ssä, **ei näyttöä**):

| | K long | K short |
|---|---|---|
| Signaaleja / toteutettuja kauppoja | 3 947 / 2 756 | 3 647 / 2 583 |
| D16 satunnaisiin verrattuna | +0,30 A (Holm-p 0,013) | +0,29 A (Holm-p 0,013) |
| **Brutto per kauppa ennen kuluja** | **−0,043 %** | **−0,018 %** |
| Kulut per kauppa (spread ja liukuma + palkkiot + funding) | 0,18 % | 0,19 % |
| **Netto per kauppa** | **−0,228 %** (LV −0,36 … −0,09) | **−0,203 %** (LV −0,30 … −0,10) |
| Markkinoita, joilla netto > 0 | 0/6 | 0/6 |
| Lukitun säännön kuvaus | suuntavaikutus näkyy, mutta ei kata kuluja | sama |

* **Salkku** (1 000 $ per kauppa): 5 339 kauppaa, brutto −1 644 $, kulut 9 879 $ ja **netto
  −11 523 $**. Suurin pudotus oli 11 748 $, eli enemmän kuin 6 000 $:n vertailupääoma.
* **Tärkein havainto: suuntavaikutus on suhteellinen.**
  * K-signaalit syntyvät kääntymiskuvioina trendin jälkeen. Saman päivän satunnaiset
    samansuuntaiset avaukset menettävät tällöin keskimäärin enemmän kuin signaali.
  * Signaali on siksi "satunnaista parempi", mutta sen oma 4 tunnin hintaliike on ennen kuluja
    lähellä nollaa tai negatiivinen.
  * Tällaisesta edusta ei voi hyötyä yksittäisellä suuntakaupalla.
* Kannattavuus vaatisi noin +0,19 %:n bruttotuoton per kauppa. Kehitysdatalla se oli noin −0,03 %.

## 4. Mitä voidaan päätellä ja mitä ei vielä tiedetä

**Voidaan päätellä:**
* Sini-traderin katkoksen syy oli levyn kokoasetus. Data säilyi.
* XBT:n −2 %:n basis oli datavirhe, ei markkinailmiö.
* Funding carry on ollut 16 vuorokauden aikana noin nollatulos.
* K-kääntymissignaali 15 minuutin kynttilöillä ja kiinteällä 4 tunnin pidolla **ei ollut
  kannattava kehitysdatalla**. Se oli tappiollinen jo ennen kuluja ja selvästi tappiollinen kulujen
  jälkeen kaikilla kuudella markkinalla.
* Tämä on johdonmukaista aiempien tulosten kanssa: 1 minuutin livetestit, 1 minuutin historia ja
  Tutkimus 15M.

**Ei vielä tiedetä:**
* Säilyykö suhteellinen D16-vaikutus uudella datalla (vahvistusta ei ole ajettu).
* Funding carryn todellinen tuotto ja riski pidemmällä jaksolla ja eri korkoympäristöissä.
* Sini-traderin kirjanpidon täsmäytys (funding-etumerkki, käteinen) ja spot-virheen juurisyy.
* Lokakuun toistotestin tulos (avataan 30.10. jälkeen).

## 5. Perusteltu seuraava kehitysaskel

1. **K4H-vahvistusta ei kannata ajaa.**
   * Vaikka suhteellinen vaikutus säilyisi 2024 datalla, kannattavuusehto (H2) vaatisi bruttotuoton
     nousun noin −0,03 %:sta yli +0,19 %:iin per kauppa. Kehitysdata ei anna sille mitään tukea.
   * Käyttämätön vuoden 2024 data on arvokas. Sen voi säästää hypoteesille, jolla on realistinen
     mahdollisuus kattaa kulut.
   * Jos haluat silti tieteellisen vastauksen suhteellisen vaikutuksen pysyvyydestä, vahvistus
     ajetaan sellaisenaan hyväksynnälläsi. Se kestää noin 20 minuuttia.
2. **Kynttiläsignaaleista lyhyellä aikavälillä kannattaa luopua kaupankäyntistrategian pohjana.**
   * Neljä toisistaan riippumatonta aineistoa näyttää saman: suuntaetua ei ole riittävästi kuluihin
     nähden.
3. **Ensisijainen jatkosuunta on eri tuottolähde, jossa kulut ovat pieni osa tuotosta:**
   * a) **Funding carryn jatko korjattuna:** spot-viitteen korjaus, täsmäytys ja pääomahistoria.
     Tämä vaatii, että annat tälle istunnolle pääsyn Sini-trader-repoon.
   * b) **Aikasarjamomentum päivä- tai 4h-kynttilöillä**, ennakkoon lukittuna. Kulukynnys
     tarkistetaan ensin ilman signaaleja (tilanneraportin kokeilu 1).
4. **Ylläpito:** Sini-traderin levyä ja tallentimen rajaa (`RECORDER_MAX_MB`) kannattaa valvoa.
   Raja (1 500 MB) on nyt levyn alla, mutta muuta dataa kertyy edelleen.

Uusia strategiamuutoksia ei ole julkaistu. Livebotti, paperitilit ja toistotesti ovat ennallaan.
