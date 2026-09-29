# Paperikaupan sääntösarja v1

Tila: **LUKITTU**, määritelty 29.9.2026 ennen ensimmäistä testiä.
Koodissa: `kynttilatulkki/strategy.py` → `RULESETS["v1"]`.

Sääntöjä ei muuteta tulosten perusteella tähän versioon. Jokainen muutos tehdään
uutena versiona (v2, v3 …), jolle kirjoitetaan oma tiedosto `docs/SAANNOT_vN.md`, ja
se arvioidaan **uudella aineistolla**, jota ei ole käytetty aiempien versioiden
testaukseen eikä muutoksen suunnitteluun (ks. kohta 9).

Vain paperikauppaa. Koodi ei lähetä toimeksiantoja eikä käytä API-avaimia.

---

## 1. Markkina

* **Kraken Derivatives – lineaariset ikuiset futuurit (perpetual)**, symbolit `PF_<KOLIKKO>USD`,
  esim. `PF_XBTUSD`, `PF_ETHUSD`, `PF_SOLUSD`. Mahdollistaa sekä long- että short-kaupan.
* Seurattavat markkinat: oletuksena 5 suurinta PF-perpetualia 24 h USD-vaihdon (`volumeQuote`)
  mukaan testin/ajon alkaessa. Valittu lista tallennetaan tuloksiin.
* Data: Krakenin julkinen charts-rajapinta (1 min kynttilät, `trade`) ja tickers-rajapinta
  (bid/ask, mark-hinta, funding).

## 2. Kulumalli (molempiin suuntiin)

| Kulu | Arvo v1 | Peruste |
|---|---|---|
| Palkkio | **0,050 % nimellisarvosta, avaus JA sulku** | Kraken Derivatives, taker, alin volyymiporras ($0+). Maker 0,020 % – ei käytetä, koska kaikki toimeksiannot oletetaan markkinatoimeksiannoiksi. |
| Spread | Live: todellinen bid/ask hetkellä, jolloin toteutus simuloidaan. Historia: puolikas spread = max(mitattu puolikas spread testin alussa, 0,010 %) | Ostetaan ask-hinnalla, myydään bid-hinnalla |
| Liukuma | 0,020 % tavalliset toteutukset, **0,050 % stop-toteutukset** | Stopit laukeavat nopeassa liikkeessä |
| Funding | Kertyy suhteessa pitoaikaan: nimellisarvo × tuntikorko × pitotunnit. Live: tickerin `fundingRate / markPrice`. Historia: Krakenin historiallinen tuntikorko; jos ei saatavilla, **0,00125 %/h aina omaa positiota vastaan** | Kraken: funding kertyy jatkuvasti, tilitys tunneittain. Positiivinen korko: long maksaa, short saa |

Toteutushinta: long-avaus = viite × (1 + ½spread + liukuma); long-sulku = viite × (1 − ½spread − liukuma);
short peilikuvana.

## 3. Signaali

Vain **VAHVISTETUT** havainnot (kynttilä sulkeutunut). Kaupan suunta tulee havainnon
suunnasta:

* **Long**: vasara, käänteinen vasara, nouseva peittävä kuvio, sudenkorento-doji laskun jälkeen
  (havainnon suunta "nousuun viittaava").
* **Short**: hirttäytyjä, tähdenlento, laskeva peittävä kuvio, hautakivi-doji nousun jälkeen
  (havainnon suunta "laskuun viittaava").
* Ei kauppaa: marubozu, tavallinen ja pitkäjalkainen doji sekä muodot ilman trendiä.

Havainnon on täytettävä **kaikki** ehdot:

1. **Kontekstiehto:** edeltävä 10 minuutin liike on signaalille vastakkainen. Longissa lasku on ≤ −1,5
   keskimääräistä vaihteluväliä, shortissa nousu on ≥ +1,5.
2. **Vähintään kohtalainen selkeys = pisteet ≥ 2**. Pisteet lasketaan näin:
   * +1: kuvion muotoehdot täyttyvät (`docs/KUVIOT.md`)
   * +1: kontekstiehto täyttyy
   * +1: vasarassa alavarjo käy 10 min uudessa pohjassa, tähdenlennossa yläsvarjo
     10 min uudessa huipussa, tai peittävän kuvion runko on ≥ 1,5 × keskimääräinen runko
   * +1: volyymi ≥ 1,5 × keskiarvo; −1: volyymi < 0,7 × keskiarvo
   * Luokat: ≤ 1 heikko, 2 kohtalainen, ≥ 3 selvempi.
3. **Volyymivaatimus:** signaalikynttilän volyymi ≥ **1,2 ×** edeltävien 20 suljetun kynttilän
   keskivolyymi.
4. Jos samasta kynttilästä syntyy sekä long- että short-signaali, **ei kauppaa**. Jos saman suunnan
   signaaleja on useita, perusteeksi kirjataan kaikki.
5. Samassa markkinassa ei saa olla avointa positiota. Positiota ei käännetä eikä kasvateta.

## 4. Avaus

* Signaali vahvistuu kynttilän sulkeutuessa. Avaus tapahtuu **seuraavan kynttilän avaushinnalla**,
  joka on ensimmäinen vahvistuksen jälkeen saatava hinta. Hintaan lisätään spread ja liukuma
  (kohta 2).
* Jos avaushinta on jo stopin väärällä puolella, kauppa perutaan.

## 5. Stop, tavoite ja pitoaika

* **Stop loss**: long = signaalikynttilän alin − 0,10 × keskimääräinen vaihteluväli (ATR20);
  short = signaalikynttilän ylin + 0,10 × ATR20.
* **Riski R** = |toteutunut avaushinta − stop|.
* **Kulusuodatin**: kauppaa ei avata, jos R < **2 ×** arvioitu kokonaiskulu per yksikkö
  (2 × palkkio + 2 × (½spread + liukuma), avaushinnasta laskettuna).
* **Voittotavoite**: avaushinta ± **1,5 R**.
* **Maksimipitoaika**: **15 kynttilää**. Jos stop tai tavoite ei ole lauennut, positio suljetaan
  16. kynttilän avaushinnalla.
* **Tarkistus kynttilän sisällä**: jos saman kynttilän ylin ja alin osuvat sekä stopiin että
  tavoitteeseen, oletetaan **stop ensin** (varovainen oletus).
* **Hintakuilu**: jos kynttilä avautuu stopin tai tavoitteen yli, toteutus tapahtuu avaushinnalla.
* Stop ja tavoite toteutetaan markkinatoimeksiantona (taker-palkkio, spread ja liukuma).

## 6. Positiokoko

* Paperipääoma aluksi **10 000 USD**.
* Riski per kauppa **0,5 %** nykyisestä toteutuneesta pääomasta.
* Määrä = riski USD / (R + arvioitu kokonaiskulu per yksikkö).
* Katot: yhden position nimellisarvo ≤ **3 × pääoma**, kaikkien avointen positioiden yhteensä
  ≤ **5 × pääoma** (Krakenin maksimivipu on 10×). Jos katto rajoittaa, kokoa pienennetään eikä
  riskiä kasvateta.
* Avoimia positioita enintään **3** yhtä aikaa, yksi per markkina.

## 7. Tappiorajat

* **Päivän tappioraja**: kun UTC-päivän toteutunut nettotulos ≤ **−2 %** päivän aloituspääomasta,
  uusia kauppoja ei avata ennen seuraavaa UTC-päivää.
* **Tappioputki**: **4** peräkkäistä tappiollista kauppaa → **60 minuutin** tauko uusille kaupoille.
* **Maksimipudotus**: pääoma ≤ **90 %** (−10 %) huippupääomasta → kaupankäynti pysähtyy kokonaan.
  Jatkaminen vaatii käsin tehdyn nollauksen.
* Tappiorajat eivät sulje avoimia positioita. Ne suljetaan normaalisti stopilla, tavoitteella
  tai aikarajalla.

## 8. Kirjaus

Jokaisesta kaupasta tulostetaan ja tallennetaan: sääntöversio, markkina, suunta, avausaika ja
-hinta, **avausperuste** (kuviot, pisteet, konteksti, volyymi), stop, tavoite, koko,
sulkemisaika ja -hinta, **sulkemissyy** (stop / tavoite / aikaraja / ajon loppu), bruttotulos,
palkkiot, funding, **nettotulos** ja tulos R-kertoimina. Spreadin ja liukuman vaikutus sisältyy
toteutushintoihin, ja se raportoidaan myös erikseen arviona.

Historiatesti ja live-paperikauppa käyttävät **samaa moottoria** (`paper.py`) ja samoja sääntöjä.
Ainoa ero on spreadin ja fundingin lähde (kohta 2).

## 9. Arviointikäytäntö

1. v1 lukitaan ennen ensimmäistä testiä.
2. Ensimmäinen historiatesti ajetaan jaksolla A. Jakson rajat ja markkinat kirjataan tiedostoon
   `results/`.
3. Jos v1:tä halutaan muuttaa, muutos kirjataan versioksi v2 perusteluineen ennen testiä.
4. v2 (ja vertailun vuoksi v1) arvioidaan **jaksolla B**, joka on kokonaan jakson A jälkeen ja jota
   ei ole katsottu. Jaksoa A ei käytetä v2:n hyvyyden todisteena.
5. Live-paperikauppa on oma, aidosti tuleva testijaksonsa.
