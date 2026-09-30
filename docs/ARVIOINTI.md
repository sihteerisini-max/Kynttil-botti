# Kuviotunnistuksen sokkoarviointi

Tarkoitus: selvittää, kuvaako botti näkemänsä kynttilät oikein. Ennustuskykyä ja kannattavuutta
ei arvioida tässä. Kaupankäyntisäännöt ovat ennallaan.

## Menettely

1. **Otos** (`python -m validointi.arviointi_otos --tag A`): 11 kuviota × (3 botin muodoltaan
   tunnistamaa + 3 satunnaista 1 min kynttilää), järjestys sekoitettu. Näytetään vain arvioitavaa
   kynttilää edeltävät 30 kynttilää ja kynttilä itse, ei myöhempää hintakehitystä. Kauppattomat
   (täytetyt) minuutit jätetään pois. Otos tallennetaan tiedostoon `validointi/arviointi_<sarja>.json`.
2. **Arviointi**: kaksi erillistä kysymystä. Muotoehdot: on kuvio / ei ole / epäselvä.
   Taustaehdot (edeltävä liike ja suhteellinen koko): täyttyvät / eivät täyty / epäselvä. Sivulla
   näytetään kirjallisuuden sanallinen määritelmä (docs/LAHTEET.md). Botin vastaus ja numeeriset
   raja-arvot ovat piilossa, kunnes tulokset avataan.
3. **Tulokset** (`python -m validointi.arviointi_tulokset …`) kuvioittain ja erikseen muodolle,
   taustalle ja koko kuviolle: oikein tunnistettu, väärä hälytys, löytämättä, oikein hylätty.
   **Epäselvät arviot omana ryhmänään**, eikä niitä lasketa mihinkään muuhun luokkaan.
4. **Määritelmämuutokset** perustellaan arvioilla, ei esiintymistiheydellä. Muutoksen jälkeen
   tunnistus arvioidaan **uudella, aiemmin luokittelemattomalla sarjalla** jakson A jälkeiseltä
   datalta, esimerkiksi `--data-glob 'data/PF_*_<uusi jakso>.csv' --tag B`. Sarjan A arvioita ei
   käytetä muutetun määritelmän hyvyyden todisteena.

## Sarjat

| Sarja | Data | Tapauksia | Tila |
|---|---|---|---|
| A | jakso A (22.–29.9.2026), 5 Kraken-perpetualia | 66 | arvioitu 30.9.2026 – tulokset `validointi/ARVIOINTI_A_TULOKSET.md`; johti muutokseen T2 |
| B | 29.9.2026 18:43 UTC jälkeen, samat 5 markkinaa | 66 | odottaa dataa; arvioitava T2, vertailu T1; liike ja koko erikseen |
