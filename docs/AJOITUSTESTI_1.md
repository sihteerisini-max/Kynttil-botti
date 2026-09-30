# AJOITUSTESTI 1: kääntyminen ja jatkuminen (paperikauppa)

Lukittu 30.9.2026 ennen käynnistystä, Jessen pyynnöstä. **Vain paperikauppaa**: oikeita
toimeksiantoja ei lähetetä. Testi arvioi **ajoitusta**, eli osuuko hinta ensin tavoitteeseen vai
stoppiin. Pelkkä voittoprosentti ei todista kaupankäyntietua. Kulut lasketaan ja näytetään,
mutta ne eivät estä avauksia.

**Alkuhetki:** paperitilien todellinen aloitushetki. Railway-loki `TESTIJAKSO [aj1-kaanto]`, ja
tapahtuma `testi_alkoi` tallentuu tiedostoon `tapahtumat_<versio>.jsonl`. Hetki kirjataan tiedostoon
`results/TESTIJAKSOT.md`.
**Käynnistyi 30.9.2026 klo 20.39 Suomen aikaa (17:39 UTC)** koodilla b4a92ff. Päättyy 28.10.2026 17:39 UTC, joten pituus on 28 vuorokautta.

## Tilit (erilliset paperitilit, kumpikin 10 000 USD)

| Versio | Merkki | Signaalit |
|---|---|---|
| `aj1-kaanto` | K | T2-kääntymiskuviot (ennallaan) |
| `aj1-jatko` | J | jatkumissignaali (uusi, alla) |

Signaalityypit ovat eri tileillä. Niiden tulokset, pääoma, positiopaikat ja tappiorajat eivät
siksi vaikuta toisiinsa, eikä niitä yhdistetä.

## Yhteiset säännöt (molemmat tilit)

Pohja on `v1.1-T2`, ja siihen tehtiin vain seuraavat muutokset:

* **Kulusuodatin pois** avausten esteenä (`min_r_to_cost = 0`). Kulut arvioidaan ja kirjataan
  edelleen: palkkiot, spread ja liukuma molempiin suuntiin sekä funding. Avauksessa näytetään myös
  kulujen arvio suhteessa R:ään.
* **Tavoite 1 R ja stop 1 R.**
  * R = |toteutunut avaushinta − stop|.
  * Stop on signaalikynttilän ääripää ± 0,1 × keskimääräinen vaihteluväli (ennallaan).
  * Tavoite = avaushinta ± 1,0 × R.
  * **Aikaraja** on 15 kynttilää (15 min).

Ennallaan pysyvät:

* **Avaus:** vain suljetuista kynttilöistä. Avaus tehdään signaalikynttilän jälkeisen kynttilän
  avaushintaan, joka on ensimmäinen hinta signaalin valmistumisen jälkeen. Siihen lisätään ½ spread
  ja liukuma 0,02 %. Signaalin valmistumista edeltäviä hintoja ei käytetä.
* **Sulku:**
  * Stop ja tavoite tarkistetaan kynttilän sulkeutuessa.
  * Jos molemmat osuvat samaan kynttilään, järjestystä ei voi tietää. Tapaus merkitään
    **epäselväksi**, ja kirjanpidossa se käsitellään stoppina (varovainen oletus).
  * Hintakuilussa täyttö tehdään avaushintaan.
* **Koko ja riski:**
  * riskibudjetti 0,5 % pääomasta
  * enintään 3 × pääoma per positio ja 5 × pääoma yhteensä
  * enintään 3 positiota
  * marginaali enintään 50 %, vipu enintään 10 ×
  * määrä pyöristetään alaspäin.
* **Tappiorajat:**
  * päivän tappio 2 %
  * 4 peräkkäistä tappiota johtaa 60 minuutin taukoon
  * pudotus 10 % pysäyttää tilin.
* **Markkinat:** PF_SUIUSD, PF_ZECUSD, PF_XRPUSD, PF_DOGEUSD ja PF_SOLUSD (1 min kynttilät).
* **Toistuvat avaukset estetty:**
  * Samalla markkinalla voi olla vain yksi avoin positio.
  * Sama signaalikynttilä voi avata enintään yhden kaupan, myös uudelleenkäynnistyksen jälkeen.
  * Ohitukset kirjataan syineen.

## Kääntymissignaali (K) – ennallaan

T2-tunnistus. Hyväksyttäviä kuvioita ovat vasara, käänteinen vasara, nouseva peittävä kuvio,
tähdenlento, hirttäytyjä ja laskeva peittävä kuvio.

Lisäksi vaaditaan:
* kuvion vaatima edeltävä trendi (10 min regressioliike vähintään 1,5 keskimääräistä vaihteluväliä
  vastakkaiseen suuntaan)
* pisteet ≥ 2
* volyymi ≥ 1,2 × 20 edeltävän keskiarvo.

Määritelmät: `docs/KUVIOT.md` ja `docs/LAHTEET.md`.

## Jatkumissignaali (J) – uusi, `kynttilatulkki/jatkuminen.py`

Kaikki ehdot lasketaan suljetusta signaalikynttilästä ja sitä **edeltävästä** suljetusta
historiasta. **Short**, kun kaikki ehdot täyttyvät. **Long** on peilikuva.

| # | Ehto (short) | Raja | Peruste |
|---|---|---|---|
| 1 | Trendi: 10 edeltävän kynttilän regressioliike / keskimääräinen vaihteluväli | ≤ −1,5 | sama trendimääritelmä kuin kääntymissignaaleissa |
| 2 | Kynttilän suunta | laskeva | liike jatkuu samaan suuntaan |
| 3 | Runko / vaihteluväli | ≥ 0,50 | voimakas kynttilä, ei doji eikä pelkkä väri |
| 4 | Vaihteluväli / 20 edeltävän keskiarvo | ≥ 1,0 | vähintään tavallisen kokoinen liike |
| 5 | (Päätös − alin) / vaihteluväli | ≤ 0,25 | päättyy lähelle alinta, eikä liikettä hylätty |
| 6 | Päätös vs. 10 edeltävän kynttilän alin | alle | murtaa edeltävän 10 min pohjan, joten liike jatkuu |
| 7 | Volyymi / 20 edeltävän keskiarvo | ≥ 1,2 | sama volyymiraja kuin kääntymissignaaleissa |

* Rajat valittiin etukäteen pyöreinä arvoina, ja trendi- ja volyymirajat ovat samat kuin
  kääntymissignaaleissa.
* Rajoja **ei sovitettu** mihinkään yksittäiseen liikkeeseen. Esimerkiksi DOGEn 30.9. klo 20.20
  lasku ei olisi täyttänyt ehtoja, koska sen volyymi oli 0,12 ×.
* Ehtojen täyttyminen ja puuttuvat ehdot näkyvät seurantasivulla jokaiselle kynttilälle.
* Testit: `tests/test_jatkuminen.py` (ehdot, pelkkä väri ei riitä, volyymi, murto, keskeneräinen
  kynttilä) ja `tests/test_live_vs_historia.py` (live = historiatesti myös näille versioille).

## Muut muutokset koodissa

* **Live-ajon käsittelyjärjestys** on nyt sama kuin historiatestissä: kullakin minuutilla ensin
  kaikkien markkinoiden avaukset ja sitten sulkeutumiset. Aiemmin yhden markkinan saman minuutin
  sulku saattoi vaikuttaa toisen markkinan avaukseen (vapautuva positiopaikka tai pääoma), mikä on
  pieni tulevan tiedon vuoto.
* Kauppariveille lisättiin kentät `signaalityyppi`, `lopputulos` (tavoite, stop, aikaraja tai
  epäselvä), `hintaliike_pnl` (tulos ennen kaikkia kuluja) ja `cost_to_r`.

## Mitä raportoidaan (erikseen K ja J, long ja short)

* kauppojen määrä
* tavoitteen, stopin, aikarajan ja epäselvien osuudet
* tulos ennen kuluja (hintaliike) ja nettotulos kulujen jälkeen
* suurin pudotus
* ohitettujen signaalien syyt.

**Vertailukohta ajoitukselle:** koska tavoite ja stop mitataan toteutuneesta avaushinnasta, jossa
avauskulu on mukana, tavoite on markkinahinnasta hieman kauempana kuin stop. Satunnaisella
avauksella tavoitteen osuus olisi siksi hieman alle 50 %.

## Arvioitu seuraus tappiorajoista (kehitysjakso A, vain suunnittelutieto)

* Jaksolla A kulut olivat ilman kulusuodatinta keskimäärin noin 1,1–1,6 R per kauppa.
* Molemmat tilit olisivat pysähtyneet 10 %:n pudotusrajaan noin 3 vuorokaudessa:
  * K noin 25 kauppaa
  * J noin 36 kauppaa.
* Päivän tappioraja esti suurimman osan signaaleista.
* Rajat pidettiin Jessen pyynnöstä ennallaan. Jos tili pysähtyy, sitä ei nollata kesken testin.
  Mahdollinen muutos tehdään uutena versiona ja uutena vaiheena.

## Arkistoidut vaiheet (ei yhdistetä)

* **T2-kannattavuustesti** (`v1.1-T2` ja `v2-T2`, `docs/TESTI_T2.md`): 30.9. 15:21 UTC – tämän
  vaiheen alku. Markkinavaihto oli 17:10 UTC. Tila- ja lokitiedostot säilyvät Volumessa
  (`paper_v1.1-T2.pkl`, `kaupat_v1.1-T2.jsonl` ja niin edelleen), ja seurantasivun arkisto-osio
  näyttää ne.
