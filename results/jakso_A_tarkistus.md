# Jakso A – rajattu tarkistus (29.9.2026)

Data: sama 1 min Kraken-data kuin v1-testissä (`data/`, 5 × 10 080 kynttilää). Kaupat
toistettiin täsmälleen samoina (42 kpl). Pieni pääomaero (~1 USD) johtuu siitä, ettei
historiallista funding-dataa ollut tarkistusympäristössä.

## 1. Riskilaskenta ja −1,38 R

* Positiokoko = 0,5 % pääomasta / (R + arvioidut kulut per yksikkö). Kulut sisältyvät.
* Stop-kaupat (22): keskim. nettotappio 47,12 USD vs. riskibudjetti 47,64 USD → **98,9 % budjetista**.
* "R" raportissa = qty × |avaushinta − stop| (hintaetäisyys ilman kuluja), keskim. 34,40 USD.
  Kulut olivat keskim. 0,38 × tämä etäisyys → stop-tappio ≈ −1,38 R. Kyse on R:n
  määritelmästä, ei riskilaskennan virheestä.
* Pieni epäjohdonmukaisuus: arvio laskee avauksen spread+liukuman kahdesti (se on jo R:ssä)
  ja olettaa sulkuun 0,02 % liukuman, vaikka stopissa käytetään 0,05 %. Vaikutukset
  kumoavat toisensa (varattu 0,391 R, toteutunut 0,376 R).

## 2. Volyymi

* Yksikkö: Krakenin charts-API:n volyymi kohde-etuuden yksiköinä (esim. XRP-kpl). Suhde on
  saman markkinan sisällä yksikötön – laskenta oikein.
* Nollavolyymit ovat vain täytettyjä kauppattomia minuutteja (0,6–3 %); datassa ei ole muita
  nollia. 42 signaalista 4:n vertailuikkunassa oli 1 nolla / 20 → vaikutus keskiarvoon ≤ 5 %.
* 616,9× (XRP 27.9. 04:37) on todellinen piikki: 3,06 milj. XRP, viikon suurin minuutti,
  vertailukeskiarvo 4 956. Myös 216,8× ja 90,5× ovat todellisia piikkejä ilman nollia.
* Volyymijakauma on hyvin vino: 22 % kaikista kynttilöistä ylittää 1,2 × keskiarvon, ja
  kaikki 42 signaalia ylittäisivät 1,2 × mediaanin.

## 3. Hinnan kulku kaupan aikana

Rajoite: 1 min OHLC ei kerro järjestystä kynttilän sisällä. Konservatiivinen laskenta jättää
stop-kynttilän pois; tulos oli sama kummallakin tavalla. "Nettovoitolla" = sulku kynttilän
parhaaseen hintaan markkinatoimeksiantona olisi tuottanut voittoa kaikkien kulujen jälkeen
(yläraja – parasta hintaa ei käytännössä saa).

* Nettovoitolla jossain vaiheessa: **25/42** (stopilla päättyneistä 9/22, aikarajalla 15/19).
* Paras suotuisa liike osuutena 1,5 R -tavoitteesta: mediaani **22 %** (≈ 0,33 R), ka 28 %.
  ≥ 50 %: 8/42 (mediaaniaika 4 min), ≥ 75 %: 3/42 (5 min), ≥ 100 %: 1/42 (15 min).
* Paras kohta saavutettiin mediaanina **2. minuutilla**.
* Mediaaniliike suotuisaan suuntaan (≈ 0,33 R) on pienempi kuin kaupan kulut (≈ 0,38 R).

## Kehitysvertailu (jakso A, tappiorajat pois) – vain suuntaa antava

| Muutos (yksi kerrallaan) | Kauppoja | Netto USD | Ennen kuluja USD | ka R |
|---|---|---|---|---|
| v1 | 85 | −1 632 | −464 | −0,58 |
| tavoite 1,0 R | 87 | −1 664 | −472 | −0,58 |
| tavoite 0,75 R | 87 | −1 615 | −418 | −0,56 |
| stop-puskuri 0,5 ATR | 156 | −2 195 | −110 | −0,44 |
| kulusuodatin 4× | 8 | −144 | −83 | −0,42 |
| pitoaika 5 min | 88 | −1 492 | −322 | −0,51 |
| volyymiehto pois | 149 | −2 292 | −303 | −0,49 |

Mikään yksittäinen muutos ei ollut jaksolla A kannattava.
