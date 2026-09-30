# Sokkoarviointi, sarja A: tulokset

Arvioija: Jesse, 30.9.2026. Arvioitu 66/66 tapausta (`validointi/arviot_A.json`, otos
`validointi/arviointi_A.json`). Data: jakso A (22.–29.9.2026), 1 min kynttilät, 5 Kraken-perpetualia.
Tunnistusmääritelmä T1 (käytössä myös lukituissa kaupankäyntiversioissa).
Sarjassa A taustaehdot kysyttiin yhtenä kysymyksenä (edeltävä liike ja suhteellinen koko yhdessä).

## Muotoehdot

| | Oikein tunnistettu | Väärä hälytys | Löytämättä | Oikein hylätty | Epäselvä (botti kyllä/ei) |
|---|---|---|---|---|---|
| Yhteensä | 34 | 1 | 0 | 30 | 2 / 1 |

* Ainoa väärä hälytys: A015 (vasara). Alavarjo on 2,17 × runko, joten raja 2 × täyttyy niukasti,
  ja runko on 32 % vaihteluvälistä.
* Satunnaisista 33 kynttilästä arvioit kuvioksi vain 2, ja botti löysi molemmat. Löytämättä
  jääneiden arvioimiseen aineisto on siis heikko: satunnaisissa minuuteissa oikeita kuvioita on
  vähän.

## Taustaehdot

| | Oikein tunnistettu | Väärä hälytys | Löytämättä | Oikein hylätty | Epäselvä (botti kyllä/ei) |
|---|---|---|---|---|---|
| Yhteensä | 21 | 9 | 4 | 21 | 5 / 6 |

* **Väärät hälytykset (9):** sudenkorento 2, hautakivi 3, vasara 2, hirttäytyjä 2. Kaikissa
  kynttilän koko oli 0,32–0,56 × edeltävien keskiarvo. Vasaroissa ja hirttäytyjissä
  edeltävä liike täytti botin trendirajan selvästi (−1,9 … −2,9 ja +2,0 … +2,5), joten
  erimielisyys johtuu todennäköisesti koosta.
* Yhdenkynttilän kuvioissa arvioit taustaehdon täyttyneeksi vain, kun koko oli vähintään 0,63 ×
  keskiarvo. Kaikki 17 tapausta, joiden koko oli alle 0,57 ×, arvioit täyttymättömiksi.
  Botin raja on 0,30 ×.
* **Löytämättä (4):**
  * Marubozu 2 kpl (A007 koko 0,62 ×, A042 0,84 ×): pidit kynttilää pitkänä, botin raja on 1,2 ×.
  * Peittävä kuvio 2 kpl:
    * A019 laskeva peittävä, edeltävä liike −2,1, eli botin mukaan lasku, kun vaaditaan nousu.
    * A023 nouseva peittävä, edeltävä liike −0,7, eli botin mukaan alle trendirajan.
* **Epäselvät** osuivat pääosin lähelle botin trendirajaa (±1,5), esimerkiksi −1,26, −1,33,
  +0,94 ja +1,89.

## Koko kuvio (muoto ja tausta)

| | Oikein tunnistettu | Väärä hälytys | Löytämättä | Oikein hylätty | Epäselvä (botti kyllä/ei) |
|---|---|---|---|---|---|
| Yhteensä | 9 | 7 | 2 | 40 | 5 / 3 |

## Johtopäätös ja määritelmämuutos T2

* Muotoehdot vastaavat arvioitasi hyvin: 1 väärä hälytys 35:stä.
* Selvin ja johdonmukaisin erimielisyys on suhteellisen koon alaraja. Siitä tehdään yksi muutos:
  **T2: kynttilää ei tulkita, jos sen vaihteluväli on alle 0,6 × edeltävien 20 keskiarvo**
  (T1: 0,3 ×). Muita ehtoja ei muuteta.
* Peittävän kuvion määritelmää ei muuteta. Marubozun pituusrajaa (1,2 ×) ei muuteta, koska
  kaksi tapausta ei riitä perusteeksi. Sen sijaan se tarkistetaan sarjassa B.
* Sarjassa A (sama aineisto, josta muutos johdettiin) T2 poistaisi kaikki 9 taustaehtojen väärää
  hälytystä ilman uusia löytämättä jääneitä. **Tämä ei ole näyttö**, koska muutos on sovitettu
  tähän aineistoon.
* T2 koskee vain tunnistuksen arviointia. Lukitut kaupankäyntiversiot v1, v1.1 ja v2 käyttävät
  edelleen T1:tä.

## Rajoitukset

* Yksi arvioija ja 66 tapausta. Kuviota kohden on vain 6 tapausta.
* Sarjassa A liike ja koko kysyttiin yhdessä, joten syy on päätelty arvoista eikä kysytty
  erikseen. Sarjassa B ne kysytään erikseen.
* Jakso A on katsottua kehitysdataa.

## Seuraava vaihe: sarja B

Uusi, aiemmin luokittelematon otos jakson A jälkeiseltä datalta (alkaen 29.9.2026 18:43 UTC),
samat 5 markkinaa. Arvioitava määritelmä on T2 ja vertailuna T1. Liike ja koko kysytään
erikseen. Otokseen valitaan kuviota kohden yksi tapaus, jossa T1 ja T2 ovat taustasta eri mieltä,
jotta muutoksen vaikutus tulee testatuksi.
