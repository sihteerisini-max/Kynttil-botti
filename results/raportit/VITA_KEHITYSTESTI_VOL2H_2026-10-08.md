# VITA – kehitystesti VOL2H: tavoite ja stop kahden tunnin hintavaihtelun mukaan (8.10.2026)

**Suunnitelma:** `docs/KEHITYSTESTI_VOL2H_SUUNNITELMA.md`, lukittu ennen laskentaa (commit 146848a,
koodi 15abe6f).
**Täydet tulostaulukot:** `tutkimus/tulokset/vol2h_raportti.md`.

* **Data:** jo käytetty kehitysdata, 1m-kynttilät 15.7.–15.9.2026 (62 vrk), SUI, ZEC, XRP, DOGE ja
  SOL. **Tulos ei ole näyttöä.**
* **Vahvistusaineistoa ei käytetty.**
* Livebotti, paperitilit ja lukittu lokakuun toistotesti ovat ennallaan. Uusia sääntöjä ei
  julkaistu.

## Suora vastaus

**Parantaako malli nettotulosta? Vain siinä mielessä, että se häviää vähemmän.**
* Lukitun kriteerin mukaan molemmat V-mallit "parantavat" tulosta merkitsevästi molemmilla
  tileillä.
* Parannus tulee kuitenkin lähes kokonaan siitä, että **kulusuodatin ohittaa 90–99 % signaaleista**,
  joten tappiollisia kauppoja tulee vähemmän.
* Jokainen malli on edelleen tappiollinen jokaisella tilillä ja kumpaankin suuntaan. Luottamusvälin
  yläraja on kaikissa alle nollan.

**Tukeeko aineisto suurempaa kauppamäärää? Ei.**
* Nettotuotto per kauppa on negatiivinen kaikissa malleissa:
  * NYKYINEN −0,58…−0,61 R
  * V1 −0,32…−0,33 R
  * V2 −0,16…−0,21 R
* Kun odotusarvo on negatiivinen, jokainen lisäkauppa kasvattaa tappiota.
* 100–200 kauppaa päivässä syntyy vain nykyisellä mallilla, ja se on tappiollisin.

## Mitä testattiin

Signaalit ovat ennallaan: K (`aj1-kaanto`) ja J (`aj1-jatko`), kummallekin oma tili. Moottori,
täyttömalli, kulut ja positiorajat ovat samat kuin botissa. Tilikohtaiset tappiorajat on poistettu
kaikista malleista.

| Malli | Stop | Tavoite | Kulusuodatin |
|---|---|---|---|
| NYKYINEN (aj1) | signaalikynttilän ääripää ± 0,1·A | 1 R toteutuneesta avaushinnasta | ei |
| V1 | avaus ∓ 1,0·M | avaus ± min(1,0·M; 0,5·R2) | tavoite ≥ 2 × kulut |
| V2 | avaus ∓ 1,0·M | avaus ± min(0,5·M; 0,5·R2) | tavoite ≥ 2 × kulut |

* **M** = viimeisen 2 tunnin (120 suljettua 1m-kynttilää) 15 minuutin päätösmuutosten mediaani,
  eli tyypillinen liike pitoajan mittaisella ikkunalla.
* **R2** = viimeisen 2 tunnin vaihteluväli.
* Aikaraja on 15 min. Mitoitus on 0,5 %:n riskibudjetti jaettuna stopin etäisyydellä ja kuluilla.
* Jos stop ja tavoite osuvat samaan kynttilään, tapaus kirjataan stopiksi.
* Funding lasketaan Krakenin päivittäisistä keskikoroista. ½ spread on nykyinen mitattu (SUI 0,015 %,
  ZEC 0,027 %, XRP, SOL ja DOGE 0,010–0,012 %).
* **Kokeiltuja versioita oli täsmälleen kolme:** NYKYINEN, V1 ja V2. Muita ei ajettu.

## Tulokset

### Tili K (kääntymissignaalit), noin 214 signaalia päivässä

| Malli | Kauppoja/pv | Osuma | Keskim. voitto | Keskim. tappio | Kulut/kauppa | Netto/kauppa | Netto/kauppa (R, 95 % LV) | Netto, vakiopääoma 62 vrk | Suurin pudotus, vakiopääoma |
|---|---|---|---|---|---|---|---|---|---|
| NYKYINEN | 156,7 | 4,2 % | +0,79 $ | −1,11 $ | 1,04 $ | −1,03 $ | −0,612 (−0,633 … −0,590) | −297 393 $ | 297 393 $ |
| V1 | 19,3 | 40,5 % | +9,30 $ | −18,28 $ | 6,34 $ | −7,11 $ | −0,315 (−0,357 … −0,277) | −18 824 $ | 18 850 $ |
| V2 | 1,9 | 61,7 % | +11,18 $ | −38,33 $ | 8,04 $ | −7,80 $ | −0,163 (−0,302 … −0,056) | −978 $ | 978 $ (9,8 %) |

### Tili J (jatkumissignaalit), noin 163 signaalia päivässä

| Malli | Kauppoja/pv | Osuma | Keskim. voitto | Keskim. tappio | Kulut/kauppa | Netto/kauppa | Netto/kauppa (R, 95 % LV) | Netto, vakiopääoma 62 vrk | Suurin pudotus, vakiopääoma |
|---|---|---|---|---|---|---|---|---|---|
| NYKYINEN | 130,3 | 7,2 % | +1,04 $ | −1,41 $ | 1,20 $ | −1,24 $ | −0,575 (−0,599 … −0,549) | −232 378 $ | 232 378 $ |
| V1 | 12,2 | 41,3 % | +10,89 $ | −23,75 $ | 7,76 $ | −9,44 $ | −0,329 (−0,384 … −0,275) | −12 401 $ | 12 425 $ |
| V2 | 1,4 | 59,8 % | +10,88 $ | −41,03 $ | 7,98 $ | −10,00 $ | −0,208 (−0,297 … −0,012) | −905 $ | 972 $ (9,7 %) |

Taulukoiden selitykset:
* **Vakiopääoma:** jokainen kauppa mitoitetaan 10 000 $:n pääomasta (riskiyksiköt × 50 $), jolloin
  korkoa korolle ei vääristä vertailua.
* **Kompoundoiva tili:** NYKYINEN-malli menettää koko 10 000 $:n pääoman sekä K- että J-tilillä
  ilman tappiorajoja, ja V1 menettää noin 70–85 % pääomasta.
* **Long ja short erikseen** ovat täydessä raportissa. Kaikki ovat negatiivisia. Paras on V2 K short
  (−0,11 R, 60 kauppaa, ei luotettava).
* **"Netto/kauppa $"** pienenee nykyisellä mallilla, koska pääoma hupenee. Vertailukelpoinen luku on
  R-sarake.

### Kuinka paljon kelvollisia tilaisuuksia nykyiset signaalit tuottavat?

| | K | J | Yhteensä |
|---|---|---|---|
| Signaaleja päivässä | 214 | 163 | **noin 377** |
| Avattu, NYKYINEN (ei kulusuodatinta; positiorajat rajoittavat) | 157 | 130 | 287 |
| Kulusuodattimen (tavoite ≥ 2 × kulut) läpäisseitä ja avattuja, V1 | 19 | 12 | **noin 31** |
| Sama, V2 | 1,9 | 1,4 | **noin 3** |

* Kun tavoite mitoitetaan kahden tunnin tyypilliseen 15 minuutin liikkeeseen, **vain 8–10 %
  signaaleista** (V1) täyttää ehdon, että tavoite on vähintään kaksinkertainen kuluihin nähden.
  Puolet pienemmällä tavoitteella (V2) ehdon täyttää vain noin 1 %.
* Tavoite on mediaanina 0,43 % hinnasta, kun edestakaiset kulut ovat 0,17 %. Kulut ovat siis noin
  40 % tavoitteesta.
* **Kelvollisia tilaisuuksia on siis noin 3–31 päivässä, ei 100–200.** Yksikään taso ei ole ollut
  kannattava.

## Miksi pienemmät tavoitteet eivät auta

* **V2:n osumaprosentti nousi 60 %:iin,** mutta tappio stopissa on noin 3,5 kertaa voiton
  suuruinen. Stop on kaksi kertaa tavoitteen etäisyys, ja kulut tulevat molemmissa päissä.
* **Kannattavuus vaatisi:**
  * V1: noin 70 %:n osumatarkkuuden (toteutunut 40–41 %)
  * V2: noin 80 %:n osumatarkkuuden (toteutunut 60–62 %).
* **Signaalien suunta ei ole satunnaista parempi** (aiemmat tutkimukset). Siksi mikään
  tavoite- ja stop-geometria ei voi tehdä niistä kannattavia. Geometria muuttaa vain tappion
  jakautumista: harvemmat, isommat tappiot tai useammat, pienemmät.
* Pienempi tavoite tarkoittaa, että kulut ovat suurempi osa liikkeestä. Suuntaedutta tämä vain
  heikentää tilannetta.

## Rajoitukset

* Data on kehitysdataa, ja tulokset ovat kehitysanalyysiä.
* Spreadit mitattiin nyt, koska historiallisia ei ole.
* Tavoitteen täyttö on mallinnettu taker-toimeksiantona kosketuksesta. Limit-toimeksianto voisi
  säästää spreadin ja palkkion eron, mutta silloin täyttyminen on epävarmaa.
* 1m-kynttilöillä saman kynttilän osumat käsitellään varovaisesti stoppina. Niitä oli V-malleissa
  vain 0–1 %.
* Tilikohtaiset tappiorajat poistettiin. Botissa ne olisivat pysäyttäneet tilit aiemmin.

## Johtopäätös ja suositus

1. **V1:tä ja V2:ta ei kannata viedä vahvistukseen eikä paperitestiin.** Kehitysdatalla ne ovat
   tappiollisia per kauppa luottamusvälien perusteella. Vahvistusdata kannattaa säästää.
2. **Suurempi kauppamäärä ei ole perusteltu** nykyisillä signaaleilla millään tutkitulla
   tavoite- ja stop-mallilla.
3. Tulos vahvistaa aiemman havainnon: **ongelma on signaalien puuttuva suuntaetu suhteessa
   kuluihin, ei sulkusääntö.** Jatkokehityksen kannattaa painottua eri tuottolähteeseen:
   * korjattu funding carry
   * pidemmän aikavälin momentum, kulukynnys tarkistettuna ensin.
