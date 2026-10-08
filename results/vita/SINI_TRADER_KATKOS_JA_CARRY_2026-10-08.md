# Sini-trader (VITA): katkos 6.–8.10.2026, carry-basis-selvitys ja funding-carry-testin tilanne

Kirjattu 8.10.2026 noin klo 17:15 UTC.

**Lähteet:**
* Railwayn deploy-lokit ja Volume-tiedot
* Sini-traderin oma rajapinta (`/carry/status`, `/recorder/status`), luettu vain GET-pyynnöillä
* Krakenin julkiset charts-tiedot (trade, mark, spot-indeksi) ja funding-historia
* Binancen, Coinbasen ja OKX:n julkiset kynttilät

**Sini-traderin lähdekoodi (repo sihteerisini-max/Sini-trader) ei ollut tämän istunnon
käytettävissä.** Koodiin perustuvat päätelmät on siksi merkitty tarkistamattomiksi.

## 1. Katkos

| | Aika (UTC) |
|---|---|
| Viimeinen normaali lokirivi (basis-hälytys) | 6.10.2026 00:54:21 |
| Ensimmäinen kaatuminen (`ENOSPC`, levy täynnä) | 6.10.2026 01:00:15 |
| Railway luovutti uudelleenyritykset; palvelu jäi tilaan CRASHED | 6.10.2026 01:01:09 |
| Volume kasvatettu 1 000 → 5 000 MB (data säilyi, 990 MB) | 8.10.2026 noin 16:58 |
| Uudelleenkäynnistys samalla koodilla (ded1b59, `deploymentRedeploy`) | 8.10.2026 17:00:44, käynnissä 17:02 |
| **Katkoksen kesto** | **noin 64 h** (6.10. 01:00 – 8.10. 17:02) |

**Syy:**
* Volume oli 1 000 MB, ja se täyttyi (990 MB).
* Palvelun muuttuja `RECORDER_MAX_MB = 1500` sallii tallentimen kasvaa yli levyn koon.
* Nyt tallentimen osuus on 317 MB. Loput noin 670 MB on muuta dataa, jonka sisältöä ei tarkistettu
  (**tarkistamaton**).
* Levyn kasvatus 5 000 MB:hen riittää, koska tallentimen raja (1 500 MB) on nyt levyn koon alla.

**Mitä muutettiin:**
* Vain Volumen koko.
* Koodi, muuttujat, kaupankäyntisäännöt, tilat, lokit ja data ovat ennallaan.
* Mitään ei poistettu. Carry-sessio jatkui samana (sessionId c1790090826499, tila ACTIVE).

**Vaikutus aineistoon (noin 64 h:n aukko):**
* **Carry-paperitesti:**
  * Moottori ei ollut käynnissä, joten funding-kertymää ei kirjattu.
  * Tarkistamatonta on, laskeeko moottori aukon fundingin jälkikäteen.
  * Krakenin funding-historiasta laskettu arvio aukon fundingista short-perpille: XBT +0,67 $ ja
    ETH +0,49 $, yhteensä noin **+1,16 $**. Tämä on laskennallinen arvio, ei kirjattu tulos.
* **Tallennin** (kirjat ja ristiinpörssidata 8 markkinalle): aukko 6.10. 01:00 – 8.10. 17:02.
  Tallennin jatkoi uudelleenkäynnistyksen jälkeen, kaikki yhteydet ovat auki eikä aukkoja ole.
* **Uutiskeruu ja muut Sini-traderin toiminnot:** sama aukko.

## 2. Carry-basis noin −2 %: datavirhe, ei todellinen havainto

Sini-trader hälytti 1.–6.10. jatkuvasti:
* XBT:n basis vaihteli −50 … −330 bps
* ETH:n basis vaihteli −180 … +222 bps
* suurin itseisarvo oli XBT 344 bps ja ETH 236 bps (`maxAbsBasisBps`).

**Tarkistus riippumattomasta datasta:**

| Lähde | XBT 6.10. klo 00:07–00:54 UTC |
|---|---|
| Krakenin perpetual, mark | 85 786 – 85 953 |
| Krakenin spot-indeksi | 85 789 – 85 948 |
| Binance BTCUSDT | 85 791 – 85 954 |
| Coinbase BTC-USD | 85 789 – 85 949 |
| OKX BTC-USDT | 85 801 – 85 950 |
| **Sini-traderin spot-hinta** (laskettu hälytyksestä ja markista) | **87 518 – 87 853** |

* Krakenin perpetualin ja spot-indeksin ero oli hälytysten aikaan **−0,4 … +0,7 bps**.
* Koko carry-jaksolla 22.9.–8.10. ero oli tuntitasolla XBT:llä −2,2 … +2,3 bps ja ETH:llä
  −2,6 … +3,1 bps.
* Sini-traderin käyttämä spot-hinta oli noin 2 % kaikkien todellisten markkinoiden yläpuolella.
* Se ei ollut myöskään mikään aiempi hinta: Krakenin indeksi ei käynyt kolmen edeltävän päivän
  aikana tällä tasolla. Kyse ei siis ollut pelkästä vanhentuneesta hinnasta.

**Johtopäätös:** hälytys johtuu Sini-traderin spot-viitehinnan laskenta- tai datavirheestä.
Juurisyy on koodissa, jota ei voitu tarkistaa (**tarkistamaton**).

Uudelleenkäynnistyksen jälkeen spot-hinta oli taas järkevä:
* XBT spot 80 659,8 ja mark 80 729,6 (8,65 bps)
* Krakenin indeksi klo 17:06–17:08 oli 80 647 – 80 779.

Virhe saattaa siis liittyä ajonaikaiseen tilaan, ja se voi toistua.

**Vaikutus carry-testin tuloksiin:**
* Basis vaikuttaa hälytyksiin ja avoimen position markkina-arvoon (MTM).
* Uudelleentasapainotuksia ei tehty (`tradeCount 0`, drift 0,07–0,08 %).
* Toteutuneet erät (palkkiot ja funding) eivät todennäköisesti riipu spot-hinnasta. Tätäkään ei voi
  vahvistaa ilman koodia (**tarkistamaton**).
* Virheen aikana näytetty MTM ja pääoma olivat virheellisiä noin ±2 % × positiokoko, eli noin
  ±20 $ positiota kohden.

## 3. Funding carry -testin (vaihe 4) tähänastiset tulokset

**Testijakso ja asetelma:**
* Sessio alkoi 22.9.2026 klo 15:27 UTC ja on yhä käynnissä.
* Ennakkoon lukittu kesto 60–90 vrk. Aukko 6.–8.10.
* Markkinat PF_XBTUSD ja PF_ETHUSD.
* Kumpaankin 1 000 $:n nimellisarvo, vipu 2, long spot ja short perpetual (delta-neutraali).

**Tapahtumat:**
* 2 avausta 22.9. (XBT ja ETH)
* 0 uudelleentasapainotusta tai suljettua kauppaa (`tradeCount 0`)
* funding-tunteja noin 386 (22.9.–8.10., josta noin 64 h katkoksen aikana)
* basis-hälytyksiä 1 822 rivillä (säilyneet lokit 1.–6.10.), ja ne ovat virheellisiä (ks. luku 2).

**Toteutuneet paperitulokset** (palvelun oma kirjanpito, 8.10. noin klo 17:05 UTC):

| Erä | Arvo |
|---|---|
| Alkupääoma (startEquity) | 4 995,60 $ |
| Pääoma nyt | 4 996,63 $ |
| **Muutos** | **+1,03 $ (+0,02 %)** |
| Palkkiot | 4,20 $ |
| Funding (palvelun etumerkki) | −2,35 $ (XBT −1,59 $, ETH −0,76 $) |
| Toteutumaton MTM | −1,52 $ |
| Suurin pääoman pudotus | **puuttuu**: rajapinta ei anna pääomahistoriaa |

**Laskennallinen arvio Krakenin datasta** (ei toteutunut tulos):

| Erä | Arvio |
|---|---|
| Funding short-perpille koko jaksolta (386 h) | XBT +1,90 $, ETH +2,63 $, yhteensä **+4,53 $** |
| josta katkoksen aikana (64 h) | +1,16 $ |
| MTM nyt (spot-indeksi ja mark) | −0,18 $ |
| Tulos ennen palkkioita | +4,34 $ |
| Palkkioiden (4,20 $) jälkeen | **noin +0,14 $** |
| Suurin pudotus tuntitasolla (MTM + funding) | noin 0,80 $ (0,016 % pääomasta), 7.10. klo 15 UTC |

**Täsmäytys onnistuu vain osin:**
* Palvelun pääoman muutos (+1,03 $) ja arvio (noin +0,14 $) ovat samaa kokoluokkaa, eli molempien
  mukaan tulos on lähellä nollaa.
* **Funding-erän etumerkki ja suuruus eivät täsmää:** palvelu kirjaa −2,35 $, ja Krakenin
  historiasta laskettu arvio on +4,53 $ (ilman katkosta +3,37 $).
* Palvelun käteissaldo (4 998,15 $) ei täsmää yksinkertaiseen laskuun alkupääoma − palkkiot ±
  funding.
* Syitä ei voi selvittää ilman koodia (**tarkistamaton**).

**Riittääkö aineisto johtopäätökseen? Ei.**
* Kyse on 16 vuorokaudesta, joista 2,7 vuorokautta puuttuu. Tulos on noin nolla (+0,02 %) ja
  hyvin pieni suhteessa kirjanpidon epävarmuuksiin.
* Funding-korot olivat jaksolla matalia: noin 0,23 % nimellisarvosta 16 vuorokaudessa, mikä vastaa
  noin 5 %:a vuodessa nimellisarvosta ja noin 2 %:a vuodessa 5 000 $:n pääomasta ennen kuluja.
* Lukittu kesto 60–90 vuorokautta on vielä kesken.

**Puuttuvat tiedot:**
* pääomahistoria ja suurin pudotus palvelun kirjanpidosta
* funding-kirjauksen etumerkkisääntö ja täsmäytys
* kirjaako moottori katkoksen fundingin jälkikäteen
* spot-viitehinnan lähde ja virheen juurisyy
* sisältö, joka täytti levyn (noin 670 MB muuta kuin tallennindataa).

Kaikki edellyttävät pääsyä Sini-traderin repoon.

**Testin jatkuminen:** carry-sessio jatkui automaattisesti uudelleenkäynnistyksen yhteydessä. En
pysäyttänyt sitä, koska pysäytys (`/carry/session/stop`) päättäisi lukitun session pysyvästi.
Katkos ja basis-virhe on kirjattava poikkeamiksi vaiheen 4 loppuraporttiin.
