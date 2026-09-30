# T2-signaalien kaupankäyntitesti: ennakkoon lukittu suunnitelma

Lukittu 30.9.2026, ennen kuin testijakson dataa on olemassa. Tätä asiakirjaa, sääntöjä,
kulumallia, markkinoita, jaksoa ja mittareita **ei muuteta testin aikana eikä tulosten perusteella**.
Lukituksen tunniste on tämän tiedoston sisältävä git-commit. Railway tulostaa käynnistyksessä
ajossa olevan commitin (`Koodiversio (commit): …`).

Kyseessä on vain paperikauppa, eikä testi lähetä oikeita toimeksiantoja.

## 1. Kysymys

Tuottavatko T2-tunnistuksen signaalit lukituilla kaupankäyntisäännöillä nettotuottoa kaikkien
kulujen jälkeen jaksolla, jota ei ole käytetty sääntöjen kehittämiseen eikä raja-arvojen valintaan?

Testi mittaa **kannattavuutta**. Se ei mittaa sitä, tunnistaako botti kuviot oikein (ks. kohta 9).

## 2. Datan saatavuus (tarkistettu 30.9.2026)

| Aineisto | Käyttökelpoinen testiin? | Syy |
|---|---|---|
| Jakso A, 22.9. 18:43 – 29.9. 18:43 | ei | Käytetty v1.1/v2-sääntöjen kehittämiseen ja T2:n valintaan (sarja A). |
| Arviointidata 29.9. 18:43 – 30.9. 14:23 | ei | Kynttilät katsottiin sarjoissa B ja C. Datasta osa on ajalta ennen T2:n määrittelyä, ja päätös pitää T2 ennallaan tehtiin sarjojen B ja C jälkeen. Pituus on vain noin 20 h, jolloin v1.1-T2:lle tulisi arviolta noin 6 kauppaa. |
| Historia ennen jaksoa A | ei päätestiksi | Aiemmin sovittiin, että kannattavuus vahvistetaan vasta lukituksen **jälkeen** alkavalla jaksolla. Markkinat on lisäksi valittu nykyisen vaihdon perusteella (valintavinouma), eikä historiallisia bid/ask-spreadeja ole saatavilla. Voidaan ajaa erikseen raportoitavana lisätarkistuksena vain Jessen päätöksellä, eikä se korvaa tätä testiä. |
| Lukituksen jälkeinen data | ei vielä olemassa | – |

**Johtopäätös:** käyttökelpoista dataa ei ole, joten testi kerätään eteenpäin live-paperikauppana.

## 3. Versiot (`kynttilatulkki/strategy.py`, `RULESETS`)

| Versio | Rooli | Määritelmä |
|---|---|---|
| **v1.1-T2** | **ensisijainen** | v1.1 (lukittu 29.9., `docs/SAANNOT_v2.md`) + tunnistus T2 (koon alaraja 0,6 × keskim. vaihteluväli) |
| v2-T2 | toissijainen | v2 (kulusuodatin R ≥ 4 × kulut) + tunnistus T2 |

* Ainoa ero pohjaversioihin on `tunnistus = "T2"` (testi `tests/test_t2_versiot.py`).
* Versiot v1, v1.1 ja v2 käyttävät edelleen T1:tä, eikä niitä ole muutettu.
* Ensisijaiseksi valittiin v1.1-T2, koska se tuottaa kauppoja noin 10 × enemmän kuin v2-T2. Vain
  sillä voi neljässä viikossa kertyä tulkittava määrä kauppoja. Valinta tehtiin ennen kuin kummankaan
  T2-version tuottoa katsottiin.
* Kahden version rinnakkainen ajo ei vaikuta ensisijaiseen tulkintaan. v2-T2 raportoidaan
  kuvailevasti.

**Havainto jaksolta A (vain suunnittelua varten, ei näyttöä):** T2 ei muuttanut yhtään kauppaa
T1:een verrattuna. v1.1 ja v1.1-T2 tuottivat samat 49 kauppaa, ja v2 ja v2-T2 samat 5 kauppaa.
T1:n ja T2:n väliin jäävät pienet kynttilät (0,3–0,6 ×) hylkääntyivät jo kulusuodattimessa.
Käytännössä testi mittaa siis lähes varmasti samaa kuin v1.1/v2, eikä se erottele T1:n ja T2:n
vaikutusta kannattavuuteen.

## 4. Säännöt ja kulumalli (ennallaan, `docs/SAANNOT_v2.md`)

> **Kirjoitusvirheen korjaus 30.9.2026 (testin jo käynnissä):** tässä luki alun perin volyymiehdoksi
> "≥ 1,5 ×". Lukitussa koodissa ja `docs/SAANNOT_v1.md`:ssä ehto on **≥ 1,2 ×** (1,5 × on vain
> pisteytyksen lisäpiste). Koodia tai sääntöä ei muutettu – vain tämän kuvauksen virhe korjattiin.

* **Signaali:** vahvistettu kuvio (kynttilä sulkeutunut), pisteet ≥ 2 (kohtalainen), volyymi
  ≥ 1,2 × 20 edeltävän keskiarvo, taustaehto täyttyy, eikä kynttilässä ole ristiriitaisia kuvioita.
* **Avaus:** seuraavan kynttilän avaushinta ± (½ spread + liukuma 0,02 %).
  * Spread tulee Krakenin reaaliaikaisesta tickeristä.
  * Stop on signaalikynttilän ääripää ± 0,1 × keskim. vaihteluväli.
  * Tavoite on 1,5 R, ja aikaraja on 15 kynttilää.
  * Jos stop ja tavoite osuvat samaan kynttilään, stop katsotaan tapahtuneeksi ensin.
  * Hintakuilussa täyttö tehdään kuilun hintaan.
* **Kulut:**
  * taker-palkkio 0,05 % molempiin suuntiin (Kraken Derivatives, $0-porras)
  * ½ spread ja liukuma 0,02 % molempiin suuntiin
  * stop-liukuma 0,05 %
  * toteutunut funding tickerin tuntikorosta.
* **Koko:** riskibudjetti 0,5 % pääomasta.
  * Kulusuodatin: v1.1 R ≥ 2 × kulut, v2 R ≥ 4 × kulut.
  * Nimellisarvo on enintään 3 × pääoma per positio ja 5 × yhteensä, ja positioita on enintään 3.
  * Marginaali on enintään 50 % pääomasta ja vipu enintään 10 ×.
  * Määrä pyöristetään alaspäin Krakenin sallittuun askeleeseen.
* **Tappiorajat:**
  * päivän tappio 2 %
  * 4 peräkkäistä tappiota johtaa 60 minuutin taukoon
  * pudotus 10 % pysäyttää tilin.
* **Pääoma:** 10 000 USD kummallakin paperitilillä.
* **Markkinat (kiinteät):** PF_XBTUSD, PF_ETHUSD, PF_SOLUSD, PF_ZECUSD ja PF_XRPUSD, 1 min
  kynttilät.

> **Poikkeama lukitusta suunnitelmasta 30.9.2026 klo 20.10 (17:10 UTC), Jessen päätös:** seurattavat
> markkinat vaihdettiin: XBT, ETH, SOL, ZEC, XRP → SUI, ZEC, XRP, DOGE, SOL
> (`results/MARKKINAVAIHTO_2026-09-30.md`). Säännöt, kulumalli, tilit ja jakson alku ja loppu pysyivät
> ennallaan. Ennen vaihtoa kauppoja oli 0. Kannattavuus arvioidaan **vaihdon jälkeen avatuista
> kaupoista** (`evaluate --start "2026-09-30 17:10"`). Tämä osa on uudella markkinajoukolla, joten
> kohdan 7 voima-arvio (jakson A markkinat) ei päde siihen sellaisenaan.

## 5. Testijakso

* **Alku:** paperitilien todellinen aloitushetki lämmittelyn jälkeen. Railway-lokissa rivi on
  `TESTIJAKSO [v1.1-T2]: <alku> – <loppu>`. Kirjataan tiedostoon `results/TESTIJAKSOT.md`.
* **Loppu:** alku + 28 vuorokautta, kiinteästi. Jaksoa ei pidennetä eikä lyhennetä tulosten
  perusteella.
* **Mukaan otetaan kaupat,** jotka on **avattu** jakson aikana (`evaluate --start/--end`). Lopussa
  auki olevat kaupat sulkeutuvat normaalisti viimeistään 15 minuutissa.
* **Katkokset (Railway, Kraken-rajapinta):** katkon aikana ei avata kauppoja, mutta avoimet
  positiot ajetaan loppuun. Katkojen yhteiskesto raportoidaan, eikä jaksoa pidennetä.
* **Tilin pysähtyminen** 10 %:n pudotusrajaan on osa sääntöjä. Tiliä ei nollata jakson aikana.
  Jos tili pysähtyy, jakson loppuosa raportoidaan kauppattomana.

## 6. Mittarit ja tulkinta (`python -m kynttilatulkki.evaluate`, ennallaan)

Kustakin versiosta raportoidaan:

1. kauppojen määrä ja kauppapäivät
2. nettotulos kaikkien kulujen jälkeen (USD ja % alkupääomasta) sekä tulos ennen kuluja ja kulut
   eriteltyinä
3. keskimääräinen nettotuotto per kauppa: USD, % alkupääomasta ja × riskibudjetti
   (**ensisijainen mittari**)
4. suurin pääoman pudotus (toteutuneista kaupoista)
5. epävarmuus:
   * 95 %:n luottamusväli päivälohkobootstrapilla (3 päivän lohkot) ja kauppajonon
     lohkobootstrapilla
   * tulkinnassa käytetään varovaisempaa väliä
   * lisäksi viiveen 1 autokorrelaatio, jakson puoliskot ja suurimman päivän osuus
6. sulkemissyyt ja tulos kuvioittain (kuvaileva).

Tulkintasäännöt (ennallaan, kiinteät):

* **n < 30 tai kauppapäiviä < 10** → KESKENERÄINEN NÄYTTÖ. Aineisto ei riitä johtopäätökseen.
* **Varovaisen välin yläraja < 0** → NÄYTTÖ TAPPIOLLISUUDESTA.
* **Alaraja > 0, molemmat puoliskot positiivisia ja yksikään päivä ei tuota yli 50 %
  nettovoitosta** → ALUSTAVA NÄYTTÖ VOITOLLISUUDESTA. Tämä ei ole hyväksyntä, vaan vaatii toiston
  uudella jaksolla.
* **Muuten** → EI NÄYTTÖÄ SUUNTAAN TAI TOISEEN.

n ≥ 30 on vain tulkinnan alaraja, ei riittävä näyttö.

**Toissijainen herkkyystarkistus (ei muuta virallista tulosta):** laskelma siitä, paljonko tulos
muuttuisi, jos avaus olisi tehty avaushetkellä nähtävissä olleeseen Krakenin noteeraukseen (ask tai
bid + liukuma) eikä avauskynttilän avaushintaan. Data tulee lokiriveiltä `AVAUS_JSON`.

## 7. Voima-arvio (jakson A kauppatiheydestä, suunnittelua varten)

| Versio | Kauppoja / vrk (A) | Odotettu n / 28 vrk | Pienin havaittava keskiarvo |
|---|---|---|---|
| v1.1-T2 | ≈ 7 | ≈ 200, jos tili ei pysähdy | ≈ 0,15–0,2 × riskibudjetti per kauppa (≈ 0,08–0,1 % pääomasta) |
| v2-T2 | ≈ 0,7 | ≈ 20 | jää lähes varmasti tilaan KESKENERÄINEN (n < 30) |

* Pienempää todellista etua testi ei todennäköisesti erota nollasta.
* **Pysähtymisriski:** jaksolla A v1.1 menetti noin 8 % viikossa. Jos sama toistuu, v1.1-T2
  pysähtyy 10 %:n pudotusrajaan ennen jakson loppua, ja kauppoja kertyy arvioitua vähemmän.

## 8. Tulevan tiedon esto

* Live-ajossa signaali muodostetaan vain suljetuista kynttilöistä, ja avaus tehdään seuraavalla
  kynttilällä. `detect()` hylkää historian, jossa on myöhempiä kynttilöitä.
* Testit (`tests/test_live_vs_historia.py`, myös T2-versioille): live-silmukka tuottaa samat kaupat
  kuin historiatesti samalla datalla. Katkaistu ja muokattu tuleva data ei muuta aiempia
  signaaleja.
* **Jälkitarkistus jakson jälkeen:** testijakson kynttilät ladataan (`kynttilatulkki.lataa`) ja
  ajetaan historiatestinä samoilla versioilla.
  * Signaalien (markkina, suunta, signaaliaika) on vastattava live-ajoa.
  * Poikkeamat raportoidaan ja selvitetään.
  * Virallinen tulos on live-paperitilien tulos.

## 9. Tunnistus ja kannattavuus erikseen

* **Tunnistuksen toimivuus** tarkoittaa sitä, vastaako botti kuvioiden kirjallisia määritelmiä.
  * Sitä arvioidaan vain sokkoarvioinneilla (`docs/ARVIOINTI.md`, sarjat A–C).
  * Sarjat B ja C eivät olleet riippumattomia.
  * Testijakson päätyttyä voidaan tehdä uusi sokkosarja jakson kynttilöistä erillisenä raporttina.
* **Kannattavuus** tarkoittaa sitä, tuottavatko signaalit nettotuottoa. Sitä arvioidaan vain tällä
  testillä.
* Hyvä tunnistus ei todista kannattavuutta, eikä tappiollinen testi todista tunnistusta vääräksi.
  Raportissa nämä ovat eri osioina.

## 10. Kielletyt muutokset ja virhetilanteet

* **Testin aikana ei muuteta** sääntöjä, raja-arvoja, kulumallia, markkinoita, jaksoa eikä
  mittareita, eikä tilejä nollata (`RESET_STATE` pysyy tyhjänä).
* **Jos löytyy tulokseen vaikuttava ohjelmavirhe:**
  1. testi pysäytetään
  2. virhe kirjataan
  3. korjaus tehdään uutena versiona
  4. uusi 28 vuorokauden jakso alkaa alusta
  5. virheellisen ajon tulokset raportoidaan erikseen virheellisinä.
* **Pelkkä infrastruktuurimuutos** (esim. Railwayn uudelleenkäynnistys) ei muuta sääntöjä. Tila
  jatkuu Volumesta.

## 11. Käynnistys Railwayssä

Ympäristömuuttujat:

```
MODE=paper
RULES=v1.1-T2,v2-T2
SYMBOLS=PF_XBTUSD,PF_ETHUSD,PF_SOLUSD,PF_ZECUSD,PF_XRPUSD
STATE_DIR=/data/state
LOG_DIR=/data/logs
TEST_DAYS=28
LOG_TOKEN=<oma pitkä satunnainen merkkijono>
```

* Poista `BACKTEST_DAYS` ja `RESET_STATE`.
* Volume liitetään polkuun `/data`, jotta tila ja lokit säilyvät uudelleenkäynnistysten yli.
* Lokit saa selaimella osoitteesta
  `https://<railway-domain>/kaupat_v1.1-T2.jsonl?token=<LOG_TOKEN>`. Domain luodaan kohdasta
  Settings → Networking → Generate Domain. Tiedostot ovat tärkeitä, koska Railwayn omien lokien
  säilytysaika on rajallinen.

Arviointi jakson jälkeen:

```
python -m kynttilatulkki.evaluate --trades kaupat_v1.1-T2.jsonl kaupat_v2-T2.jsonl \
    --events tapahtumat_v1.1-T2.jsonl tapahtumat_v2-T2.jsonl --start <alku> --end <loppu>
```
