# Tutkimus 15M – yhteenveto ja tulkinta (4.10.2026)

**Lähteet:**
* suunnitelma: `docs/TUTKIMUS15_SUUNNITELMA.md` (lukittu ennen dataa, muutos 1.1 luvussa 13)
* tulokset: `raportti.md` (korjattu ajo 2)
* markkinavalinta: `valinta.md` ja `valinta_v1_0.md`
* datan eheys: `eheys.md`
* virheellinen ajo 1: `raportti_ajo1_virheellinen.md`

Koko tutkimus on paperilaskentaa historiadatalla. Toimeksiantoja ei lähetetty. Livebotti, paperitilit
ja vaiheen 1 toistojakso (2.–30.10.2026) ovat koskemattomia.

## Mitä testattiin

* **Signaalit:** botin lukitut K-kääntymissignaalit (`aj1-kaanto`) ja J-jatkumissignaalit
  (`aj1-jatko`) 15 minuutin kynttilöillä, ilman sääntömuutoksia.
  * Kaikki ikkunat on mitattu kynttilämäärinä.
  * Seuranta-aika on 16 kynttilää eli 4 h.
  * Tavoite ja stop ovat ±1·A markkinahinnasta.
* **Testijakso:** 1.1.2025–1.7.2026 (546 vrk). Jaksoa ei ollut käytetty missään aiemmassa
  kehityksessä tai testissä.
* **Markkinat:** kuusi likvideintä Krakenin perpetualia objektiivisella säännöllä testijaksoa
  edeltävältä ajalta: XBT, ETH, SOL, DOGE, XRP ja PEPE.
* **Signaalien määrä:** 13 156, eli K long 3 947, K short 3 647, J long 2 680 ja J short 2 882.
* **Vertailu:** jokaista signaalia verrattiin 50 satunnaiseen avaushetkeen samalla markkinalla,
  samaan suuntaan ja samana UTC-päivänä.

## Löytyikö ajoitusetua? Ei.

| Ryhmä | D (signaali − satunnainen) | 95 % LV | Holm-p | Lukittu päätös |
|---|---|---|---|---|
| K long | +0,025 | −0,018 … +0,068 | 0,53 | EI NÄYTTÖÄ AJOITUSEDUSTA |
| K short | +0,039 | −0,003 … +0,082 | 0,26 | EI NÄYTTÖÄ AJOITUSEDUSTA |
| J long | −0,043 | −0,091 … +0,006 | 0,26 | EI NÄYTTÖÄ AJOITUSEDUSTA |
| J short | −0,022 | −0,077 … +0,035 | 0,53 | EI NÄYTTÖÄ AJOITUSEDUSTA |

* **K-signaalien ero on pieni ja positiivinen**, mutta mikään ryhmä ei ole tilastollisesti
  merkitsevä.
  * K shortin puoliskot ovat ristiriitaiset: +0,10 ja −0,03.
  * K yhdistettynä (täydentävä mittari) on +0,032, p 0,04 ja BH-q 0,09. Se ei ole näyttöä.
  * Kokoluokka on +0,03, mikä vastaa noin 1,5 prosenttiyksikön parempaa tavoiteosuutta kuin
    satunnaisilla hetkillä.
* **J-signaalit olivat satunnaisia hetkiä heikompia molempiin suuntiin**, mutta eivät
  merkitsevästi. Sama suunta näkyi 1 minuutin tutkimuksessa.
* **Epäselvien tapausten herkkyys** (tavoite ja stop samassa 15m-kynttilässä, 2–4 %) ei muuta
  yhtään päätöstä.

## Ovatko hintaliikkeet riittävän suuria suhteessa kuluihin? Eivät tällä asetelmalla.

* 15 minuutin kynttilöillä ±1·A-liike on selvästi suurempi suhteessa kuluihin kuin 1 minuutin
  kynttilöillä:
  * C/A mediaani 0,37–0,69 markkinasta riippuen
  * 1 minuutin K-kaupoissa C/A oli noin 1,8.
* Kannattavuus vaatisi silti **68–85 %:n tavoiteosuuden**. XBT:llä kulut ovat suurimmat suhteessa
  liikkeeseen: 23 %:ssa signaaleista kannattavuus olisi mahdotonta.
* **Toteutunut tavoiteosuus oli 45–51 %**, ja satunnaisilla hetkillä 46–50 %.
* Kannattavuusrajaan on siis noin 25–31 prosenttiyksikön ero. Jos K:n pieni ero olisikin todellinen,
  se kattaisi siitä vain murto-osan.
* Vaihetta 2 (kannattavuus kulujen jälkeen) ei suunnitelman mukaan ajettu, koska ajoitusetua ei
  osoitettu.

## Eksploratiivisia havaintoja (hypoteeseja, ei näyttöä eikä peruste muuttaa sääntöjä)

* **K-signaalien jälkeen hinta liikkuu enemmän molempiin suuntiin** kuin satunnaisten hetkien
  jälkeen (MFE +0,43–0,49 A, MAE +0,22–0,28 A, q < 0,02).
  * Signaali näyttää merkitsevän volatiliteetin kasvua, ei suuntaa.
  * Suunnattu 4 tunnin tuotto oli K:lla positiivinen molempiin suuntiin (+0,29…+0,32 A, q 0,01–0,02).
    Se ei kuitenkaan näkynyt tavoite/stop-mittarissa merkitsevästi.
* **J longin jälkeen 4 tunnin tuotto oli selvästi negatiivinen** (−0,48 A, q 0,002), eli nousun
  "jatkuminen" kääntyi keskimäärin laskuksi.
* Näitä ei käytetä päätöksiin, koska täydentäviä mittareita on monta. Ne voi testata vain uutena,
  ennakkoon lukittuna hypoteesina uudella datalla.

## Poikkeamat suunnitelmasta (läpinäkyvyys)

1. **Muutos 1.1 ennen testidataa.**
   * Lukittu 1 minuutin kattavuusehto (≥ 99 % kauppaminuutteja) hylkäsi kaikki markkinat, myös
     XBT:n (98,6 %).
   * Ehto mitattiin uudelleen 15m-kynttilöistä samalla 99 %:n rajalla.
   * Muutos kirjattiin ennen kuin testijakson dataa oli ladattu.
2. **Koodikorjaus ajon 1 jälkeen.**
   * A laskettiin juoksevalla summalla. Siihen jäi liukulukujäännös kahden signaalin
     vertailuhetkiin, jotka osuivat PEPEn pitkälle kaupattomalle jaksolle 1.11.2025. Tämä vääristi
     täydentäviä mittareita.
   * Korjaus on suunnitelman mukainen (A = 0 -hetket jätetään pois). Sääntöjä ei muutettu.
   * Ensisijaiset päätökset olivat molemmissa ajoissa samat. Ajo 1 on säilytetty sellaisenaan.

## Rajoitukset

* Spreadit mitattiin nyt (lokakuu 2026), koska historiallisia bid/ask-hintoja ei ole.
* Ehdokaslista on Krakenin nykyinen, joten myöhemmin poistetut markkinat puuttuvat.
* Kyseessä on yksi 18 kuukauden jakso ja yksi seuranta-aika.
* Funding-historiaa saatiin noin puolelle tunneista. Sillä ei ole merkitystä, koska vaihetta 2 ei
  ajettu.
* Signaalikohtainen CSV (13 156 riviä) ja raakadata ovat Tutkimus15-palvelun Volumessa
  (`/data/t15`).

## Mitä tulokset oikeuttavat tekemään seuraavaksi

* **K- ja J-signaaleista 15 minuutin kynttilöillä ei ole perustetta tehdä paperitestiä
  kannattavuudesta.** Ajoitusetua ei osoitettu, ja kulut vaatisivat tavoiteosuuden, joka on
  kaukana mitatusta.
* Vaiheen 1 toistojakso (1 min, 2.–30.10.2026) jatkuu lukittuna. Sen tulos raportoidaan erikseen.
* Jos tutkimusta jatketaan, perusteltu suunta on **uusi, ennakkoon lukittu hypoteesi** uudella
  datalla. Käyttämätöntä historiaa on esimerkiksi 1.1.–30.9.2024 tai 1.7.2026 jälkeinen aika
  toiston jälkeen. Vaihtoehtoja:
  * a) K-signaalien volatiliteettihavainto suuntaneutraalina hypoteesina
  * b) pidempi aikaväli (esim. 1 h), jolla C/A on pienempi.

  Kummassakin kannattavuusrajan tavoiteosuus lasketaan etukäteen ja asetetaan ehdoksi ennen kuin
  kannattavuutta edes arvioidaan.
