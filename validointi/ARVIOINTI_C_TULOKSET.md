# Sokkoarviointi, sarja C: tulokset

**Arvioija: ChatGPT, EI TÄYSIN RIIPPUMATON** (ks. rajoitukset). Arvioija sai numeerisen
tekstimuodon (`validointi/chatgpt_C/`) eikä nähnyt kaaviota. Vastaukset palautettiin 30.9.2026, ja
kaikki 66/66 tapausta on arvioitu (`validointi/arviot_C_chatgpt.json`, otos
`validointi/arviointi_C.json`).

Data on jaksolta 29.9.2026 18:43 – 30.9.2026 14:23 UTC, samoilta 5 markkinalta ja 1 minuutin
kynttilöinä. Yksikään kynttilä ei ole sama kuin sarjassa B (`--ohita validointi/arviointi_B.json`).
Arvioitava määritelmä on T2 (koon alaraja 0,6 ×), ja vertailuna on T1 (0,3 ×). Muoto, edeltävä
liike (10 kynttilää) ja suhteellinen koko (20 kynttilän vertailujakso) arvioitiin erikseen.
Paketissa ei ollut botin vastauksia, numeerisia luokittelurajoja eikä otosryhmien nimiä. Ryhmät
yhdistettiin vastauksiin vasta jälkikäteen.

Sarakkeet "Oikein / Väärä hälytys / Löytämättä / Oikein hylätty" kuvaavat yhtäpitävyyttä tämän
arvioijan kanssa, eivät objektiivista oikeellisuutta. Epäselvät arviot ovat omana ryhmänään, eikä
niitä lasketa muihin luokkiin.

## Otosryhmittäin (T2)

| Ryhmä | Osa | Oikein | Väärä hälytys | Löytämättä | Oikein hylätty | Epäselvä (botti kyllä/ei) |
|---|---|---|---|---|---|---|
| Satunnaisotos (33) | muoto | 2 | 0 | 0 | 28 | 0/3 |
| | liike | 6 | 0 | 1 | 7 | 0/4 |
| | koko | 15 | 3 | 0 | 11 | 4/0 |
| | koko kuvio | 1 | 0 | 0 | 30 | 0/2 |
| Botin tunnistamat (24) | muoto | 24 | 0 | 0 | 0 | 0/0 |
| | liike | 6 | 0 | 1 | 3 | 0/2 |
| | koko | 12 | 1 | 0 | 6 | 5/0 |
| | koko kuvio | 8 | 0 | 1 | 9 | 4/2 |

## T1/T2-erimielisyystapaukset (9)

| Osa | T2 | T1 |
|---|---|---|
| koko | 9 samaa mieltä (molemmat hylkäsivät) | 9 erimielisyyttä (botti hyväksyi, arvioija hylkäsi) |
| koko kuvio | 9 samaa mieltä | 9 erimielisyyttä |
| muoto, liike | samat molemmissa (muoto 9/9, liike 4 samaa mieltä ja 2 epäselvää) | |

**Koko, kaikki 66 tapausta:**

| Versio | Oikein | Väärä hälytys | Löytämättä | Oikein hylätty | Epäselvä |
|---|---|---|---|---|---|
| T2 | 27 | 4 | 0 | 26 | 9 |
| T1 | 27 | 21 | 0 | 9 | 9 |

## Havainnot

* **Muoto:** ei erimielisyyksiä yksiselitteisissä arvioissa (57 tapausta). Epäselviä oli 3, ja
  botti hylkäsi kaikki kolme:
  * C020 (doji) ja C044 (sudenkorento-doji) olivat doji-rajalla. Runko oli noin 15 %
    vaihteluvälistä, ja ChatGPT piti "hyvin ohuen" rajaa tulkinnanvaraisena.
  * C041 (hirttäytyjä) oli epäselvä, koska ylävarjo oli rungon mittainen. Rajatapaus koski siis
    ylävarjon vähäisyyttä.
  * Sama kaksi rajatyyppiä esiintyi sarjassa B (B001/B025 ja B038).
* **Koko: tämä on uusi havainto sarjaan B verrattuna.** T2:lla oli 4 erimielisyyttä, ja kaikissa
  botti hyväksyi koon ja arvioija ei:
  * tapaukset C023 (0,63 ×), C064 (0,68 ×), C066 (0,65 ×) ja C022 (0,65 ×)
  * ChatGPT kuvasi kaikkia "selvästi pieniksi".
  * Epäselviksi se arvioi koot 0,70–0,77 × (C001, C003, C014, C021, C026, C029, C054).
  * Sarjassa B arvioija piti 0,66:ta ja 0,73:a epäselvinä ja 0,76:ta riittävänä.

  Kahden sarjan perusteella arvioijan raja on epätarkka ja asettuu noin välille 0,6–0,8. T2:n
  0,6 on tämän vyöhykkeen alareunassa. T1:n 0,3 on selvästi arvioijan tulkintaa sallivampi:
  21 erimielisyyttä, sama määrä kuin sarjassa B.
* **Marubozun pituus:** koot 1,20 × (C045) ja 1,27 × (C047) olivat arvioijalle epäselviä. Botin
  raja on 1,2 ×. Sarjassa B raja oli 1,21 × epäselvä ja 1,33 × "on". Näiden kahden sarjan valossa
  botin raja on arvioijan epäselvän vyöhykkeen alareunassa.
* **Edeltävä liike:** kuvio on sama kuin sarjassa B.
  * Arvioija hyväksyi kaksi liikettä, jotka jäivät botin 1,5:n rajan alle: C017 (−0,65) ja
    C049 (−0,63).
  * Epäselviä oli 8.
    * Viisi niistä oli pieniä tai sahaavia liikkeitä (|liike| 0,25–1,20).
    * C038:ssa (−2,06) arvioija näki ensin nousun, joka kääntyi laskuksi.
    * Kaksi oli botin hyväksymiä: C018 (+2,21) ja C063 (+1,70). Niissä arvioija näki ensin laskun
      ja sitten nousun.
  * Botin regressiotrendi ja sanallinen "edeltävä nousu/lasku" eroavat erityisesti suunnan
    vaihtuessa. Näyttöä on edelleen vähän.
* **Laskennan tarkkuus:** perusteluissa mainittiin kokosuhde 12 kertaa. Kaikki 12 osuivat
  0,01:n tarkkuudella botin laskemaan arvoon, joten erimielisyydet koskevat tulkintaa eivätkä
  laskuvirheitä.

**Sääntöihin ei tehdä muutoksia tämän perusteella.** Tunnistusversiot T1 ja T2 sekä lukitut
kaupankäyntiversiot v1.1 ja v2 pysyvät ennallaan.

## Rajoitukset

* **Arviointi ei ollut täysin riippumaton.** Jessen kirjaus 30.9.2026:
  > "Arviointi tehtiin yhdessä keskustelussa kaikille kuudelle osalle. Keskusteluun välittyi
  > aiempien arviointien yhteenveto, joten tämä ei ole täysin riippumaton sokkoarvio.
  > LUE_ENSIN.txt liitettiin ja luettiin. Arviointi perustui osatiedostojen kirjallisiin
  > määritelmiin."

  Tästä seuraa kolme asiaa:
  * Sarja C **ei ole riippumaton vahvistus** T2:lle eikä muillekaan raja-arvoille.
  * Emme tiedä, sisälsikö välittynyt yhteenveto raja-arvoja, kuten T2:n 0,6:n. Sitä ei voi
    sulkea pois.
  * Kaikki kuusi osaa arvioitiin samassa keskustelussa, joten aiempien osien arviot ovat voineet
    vaikuttaa myöhempiin.

  LUE_ENSIN.txt oli tarkoitettu vain käyttäjälle. Se ei sisältänyt tuloksia eikä raja-arvoja, mutta
  se kertoi, että kyseessä on sokkoarviointi ja että aiempia sarjoja on olemassa.
* **Arvioija on kielimalli, ei ihminen.** Se sai hinnat numeroina eikä nähnyt kaaviota.
* Yhtä arvioijaa ja yhtä arviointikertaa käytettiin. Satunnaisotoksessa oli vain 2 muodoltaan
  oikeaa kuviota.
* Jakso on lyhyt (noin 20 tuntia) ja kattaa yhden markkinatilanteen. Jakso on sama kuin sarjassa B,
  mutta tapaukset ovat eri.
