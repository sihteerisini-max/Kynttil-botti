# Sokkoarviointi, sarja B: tulokset

**Arvioija: ChatGPT** (tekstimuotoinen numeerinen data, `validointi/chatgpt_B/`), palautettu
30.9.2026. Kyse ei ole ihmisen silmämääräisestä arviosta. Arvioitu 66/66
(`validointi/arviot_B_chatgpt.json`, otos `validointi/arviointi_B.json`).
Data: 29.9.2026 18:43 – 30.9.2026 14:23 UTC, eli jakson A jälkeen ja ennen katsomatta. Samat
5 markkinaa, 1 min kynttilät.
Arvioitava tunnistusmääritelmä T2 (koon alaraja 0,6 ×), vertailuna T1 (0,3 ×). Muoto, edeltävä liike
(10 kynttilää) ja suhteellinen koko (20 kynttilän vertailujakso) arvioitiin erikseen.

## Otosryhmittäin (T2)

| Ryhmä | Osa | Oikein | Väärä hälytys | Löytämättä | Oikein hylätty | Epäselvä (botti kyllä/ei) |
|---|---|---|---|---|---|---|
| Satunnaisotos (33) | muoto | 1 | 0 | 0 | 31 | 0/1 |
| | liike | 5 | 0 | 2 | 8 | 1/2 |
| | koko | 17 | 0 | 0 | 15 | 1/0 |
| | koko kuvio | 0 | 0 | 0 | 33 | 0/0 |
| Botin tunnistamat (24) | muoto | 22 | 0 | 0 | 0 | 2/0 |
| | liike | 7 | 0 | 1 | 0 | 0/4 |
| | koko | 14 | 0 | 0 | 8 | 2/0 |
| | koko kuvio | 10 | 0 | 0 | 8 | 1/5 |

## T1/T2-erimielisyystapaukset (9)

| Osa | T2 | T1 |
|---|---|---|
| koko | 9 oikein hylätty | 9 väärää hälytystä |
| koko kuvio | 9 oikein hylätty | 9 väärää hälytystä |
| muoto, liike | samat molemmissa (muoto 9 oikein, liike 6 oikein) | |

Kaikki 66 tapausta, koon osalta: T2 antoi 0 väärää hälytystä ja 0 löytämättä jäänyttä (3 epäselvää).
T1 antoi 21 väärää hälytystä.

## Havainnot

* **Muoto:** ei yhtään väärää hälytystä eikä löytämättä jäänyttä. Epäselviä oli 3, kaikki doji-rajan
  tuntumassa (runko 13–17 % vaihteluvälistä, botin raja 10 %).
* **Koko:** ChatGPT:n oma raja asettui välille 0,58 (vielä "ei") – 0,76 ("on"). Tapaukset 0,66 ja
  0,73 se arvioi epäselviksi. Tulos tukee T2:ta (0,6 ×) ja on T1:n (0,3 ×) vastainen.
* **Marubozun pituus:** ChatGPT piti kynttilää pitkänä vasta koosta 1,33 × alkaen. Koko 1,21 × oli
  sille epäselvä ja koko ≤ 1,04 × "ei". Tämä on linjassa botin 1,2 ×:n rajan kanssa. Sarjan A
  kaksi päinvastaista tapausta eivät toistuneet, joten marubozun rajaa ei muuteta.
* **Edeltävä liike:** tässä on eniten erimielisyyttä.
  * ChatGPT hyväksyi liikkeen kolmessa tapauksessa, jotka jäivät botin 1,5 R:n rajan alle:
    −1,36, −1,20 ja +0,71.
  * Epäselviä oli 7, ja niistä 6 oli pieniä tai sahaavia liikkeitä (|liike| 0,25–0,91).
  * Yhdessä tapauksessa botin regressioliike oli −2,27, mutta ChatGPT näki ensin nousun ja sitten
    laskun.
  * Botin trendiraja voi olla tiukempi kuin tulkinta "edeltävä lasku/nousu". Näyttö on kuitenkin
    vielä pieni: 3 löytämättä jäänyttä ja 7 epäselvää. Muutosta ei tehdä nyt.
* **Laskennan tarkkuus:** ChatGPT mainitsi perusteluissaan kokosuhteen 27 kertaa. Kaikki 27 osuivat
  0,05:n tarkkuudella oikeaan arvoon.

## Rajoitukset

* **Arvioija on kielimalli, ei ihminen.** Se sai hinnat numeroina eikä nähnyt kaaviota. Tulos
  mittaa, vastaako botti ChatGPT:n tulkintaa samoista sanallisista määritelmistä.
* **Riippumattomuus on vielä varmistamatta.** Jos ChatGPT:n keskustelussa oli mukana sarjan A
  arvioita, raportteja tai T2:n raja 0,6, koon tulos ei ole riippumaton. ChatGPT:n oma raja osui
  lähelle 0,6:ta.
* Yksi arvioija ja yksi arviointikerta. Satunnaisotoksessa oli vain 1 muodoltaan oikea kuvio,
  joten löytämättä jääneistä muodoista saadaan edelleen vähän tietoa.
* Jakso on lyhyt (noin 20 tuntia) ja kattaa yhden markkinatilanteen.
