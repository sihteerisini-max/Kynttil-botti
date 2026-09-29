# Tunnistusehdot

Merkinnät: R = vaihteluväli (ylin − alin), B = runko |päätös − avaus|,
U = yläsvarjo, L = alavarjo. "Keskim." = 20 edeltävän suljetun kynttilän
keskiarvo. Raja-arvot ovat `patterns.Params`-luokassa.

## Konteksti (vain edeltävistä suljetuista kynttilöistä)

* **Edeltävä liike**: 10 edeltävän päätöshinnan regressiosuoran kokonaisliike
  jaettuna keskim. R:llä. ≥ +1,5 → nousu, ≤ −1,5 → lasku, muuten sivuttain.
* **Koko**: R / keskim. R → pieni < 0,5 ≤ tavallinen < 1,5 ≤ suuri < 2,5 ≤ poikkeuksellisen suuri.
* **Volyymi**: volyymi / keskim. volyymi. ≥ 1,5 tukee havaintoa, < 0,7 heikentää.
* Kynttilää ei muototulkita, jos R < 0,3 × keskim. R tai historiaa < 20 kynttilää.

## Kynttilät

| Kuvio | Ehdot | Merkitys kontekstin mukaan |
|---|---|---|
| Doji | B ≤ 0,10 R | Epäröinti. Trendin jälkeen voi kertoa hiipumisesta; sivuttain vähämerkityksinen |
| Sudenkorento-doji | doji + U ≤ 0,10 R, L ≥ 0,60 R | Laskun jälkeen nousuun viittaava |
| Hautakivi-doji | doji + L ≤ 0,10 R, U ≥ 0,60 R | Nousun jälkeen laskuun viittaava |
| Pitkäjalkainen doji | doji + U, L ≥ 0,30 R ja R ≥ keskim. R | Voimakas epäröinti |
| Vasara | B > 0,10 R, L ≥ 2B, L ≥ 0,60 R, U ≤ 0,15 R, **edeltävä lasku** | Nousuun viittaava |
| Hirttäytyjä | sama muoto, **edeltävä nousu** | Laskuun viittaava |
| Käänteinen vasara | B > 0,10 R, U ≥ 2B, U ≥ 0,60 R, L ≤ 0,15 R, **edeltävä lasku** | Nousuun viittaava |
| Tähdenlento | sama muoto, **edeltävä nousu** | Laskuun viittaava |
| Nouseva peittävä | ed. laskeva (B > 0,1 R), nyt nouseva, avaus ≤ ed. päätös, päätös > ed. avaus, B > ed. B | Laskun jälkeen nousuun viittaava |
| Laskeva peittävä | peilikuva | Nousun jälkeen laskuun viittaava |
| Marubozu | B ≥ 0,90 R ja R ≥ 1,2 × keskim. R | Yksisuuntainen voima (jatkuvuus) |

Sivuttaisliikkeessä vasaran ja käänteisen vasaran muodot raportoidaan
"muotoisina (ei trendiä)" ja merkitään epäröinniksi.

**Signaalin selkeys** (heikko / kohtalainen / selvempi) = pisteet:
muoto +1, konteksti sopii +1, uusi 10 min pohja/huippu tai iso runko +1,
volyymi suuri +1 / pieni −1. Selkeys kuvaa, kuinka hyvin kuvio täyttää
oppikirjan ehdot – ei todennäköisyyttä hinnan suunnalle.

---

# Vaihe 2: kaaviokuviot (tausta: CAIA, 18.11.2025)

Lähde: <https://caia.org/blog/2025/11/18/crypto-chart-patterns-beginners-guide-market-signals/>

Käännekuviot:
* **Pää ja hartiat** (laskeva) / **käänteinen pää ja hartiat** (nouseva): kolme
  huippua/pohjaa, keskimmäinen äärimmäisin, niskalinja. Murtuman volyymin
  tulisi kasvaa selvästi (artikkeli: 25–30 %).
* **Tuplahuippu / tuplapohja**: kaksi testiä samasta vastus-/tukitasosta,
  välissä maltillinen pohja/huippu. Altis valemurtumille.
* **Kolmoishuippu / kolmoispohja**: kolme testiä; volyymi usein hiipuu testi testiltä.

Jatkumis-/murtumakuviot:
* **Nouseva kiila** (tyypillisesti laskeva murtuma) ja **laskeva kiila**
  (tyypillisesti nouseva murtuma): kapeneva kanava.
* **Liput**: jyrkän liikkeen (lipputanko) jälkeinen vastasuuntainen kanava;
  paluu yleensä 25–38 % tangosta, yli 50 % = kuvio epäonnistui.

Artikkelin yleiset huomiot: volyymi vahvistaa murtuman, useamman aikatason
tarkastelu vahvistaa signaalia, kuviot on tehty lähinnä 4 h / päivätasolle.
Artikkelin onnistumisprosentit eivät ole suoraan siirrettävissä 1 min
kynttilöihin – ne pitää mitata itse omalla datalla.

Toteutusidea vaiheeseen 2: tunnista paikalliset huiput/pohjat (swing points)
vain vahvistetuista kynttilöistä ja viiveellä (huippu vahvistuu vasta, kun
sen jälkeen on k kynttilää), jotta tulevaisuustietoa ei vuoda.
