# Sokkoarviointi, sarja B: tulokset

**Arvioija: ChatGPT, EI RIIPPUMATON** (oli nähnyt sarjan A tulokset ja T2:n rajan). Tekstimuotoinen numeerinen data, `validointi/chatgpt_B/`), palautettu
30.9.2026. Kyse ei ole ihmisen silmämääräisestä arviosta. Arvioitu 66/66
(`validointi/arviot_B_chatgpt.json`, otos `validointi/arviointi_B.json`).
Data: 29.9.2026 18:43 – 30.9.2026 14:23 UTC, eli jakson A jälkeen ja ennen katsomatta. Samat
5 markkinaa, 1 min kynttilät.
Arvioitava tunnistusmääritelmä T2 (koon alaraja 0,6 ×), vertailuna T1 (0,3 ×). Muoto, edeltävä liike
(10 kynttilää) ja suhteellinen koko (20 kynttilän vertailujakso) arvioitiin erikseen.

## Otosryhmittäin (T2)

Sarakkeet "Oikein / Väärä hälytys / Löytämättä / Oikein hylätty" kuvaavat yhtäpitävyyttä tämän arvioijan kanssa, eivät objektiivista oikeellisuutta.

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
| koko | 9 samaa mieltä (molemmat hylkäsivät) | 9 erimielisyyttä (botti hyväksyi, arvioija hylkäsi) |
| koko kuvio | 9 samaa mieltä (molemmat hylkäsivät) | 9 erimielisyyttä (botti hyväksyi, arvioija hylkäsi) |
| muoto, liike | samat molemmissa (muoto 9 ja liike 6 samaa mieltä) | |

Kaikki 66 tapausta, koon osalta: T2:lla ei ollut erimielisyyksiä yksiselitteisissä arvioissa
(3 epäselvää). T1:llä oli 21 erimielisyyttä, joissa botti hyväksyi ja arvioija hylkäsi.

## Havainnot

* **Muoto:** ei erimielisyyksiä yksiselitteisissä arvioissa. Epäselviä oli 3:
  * B001 (doji) ja B025 (käänteinen vasara) olivat doji-rajalla: runko 13 % ja 14 % vaihteluvälistä,
    botin raja 10 %.
  * B038 (hirttäytyjä) oli epäselvä ylävarjon takia. Ylävarjo oli 11 % vaihteluvälistä, ja
    ChatGPT piti tulkinnanvaraisena, onko sitä "vähän tai ei lainkaan".
* **Koko:** ChatGPT:n raja asettui välille 0,58 (vielä "ei") – 0,76 ("on"). Tapaukset 0,66 ja
  0,73 se arvioi epäselviksi. **Tämä ei ole riippumaton vahvistus T2:n rajalle**, koska ChatGPT oli
  nähnyt 0,6:n rajan ennen arviointia (ks. rajoitukset).
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
* **Arviointi ei ollut riippumaton.** Jesse vahvisti 30.9.2026, että ChatGPT oli ennen sarjan B
  arviointia nähnyt sarjan A arviot, raportit ja T2:n 0,6 ×:n rajan. Sarja B **ei siksi ole
  riippumaton vahvistus** T2:lle eikä muillekaan raja-arvoille. Erityisesti kokoehdon yhtäpitävyys
  voi johtua siitä, että arvioija tunsi rajan. Riippumaton arviointi tehdään sarjalla C uudessa
  keskustelussa ilman aiempaa aineistoa.
* Yksi arvioija ja yksi arviointikerta. Satunnaisotoksessa oli vain 1 muodoltaan oikea kuvio,
  joten löytämättä jääneistä muodoista saadaan edelleen vähän tietoa.
* Jakso on lyhyt (noin 20 tuntia) ja kattaa yhden markkinatilanteen.
