# Kynttiläkuvioiden tunnistuksen tarkistus

Tapauksia 44 (luokat: P 17, N 9, B 12, G 4, K 2)

## Määritelmän mukaan (docs/KUVIOT.md)

| Kuvio | Oikein (TP) | Väärä hälytys (FP) | Löytämättä (FN) | Tapaukset FP / FN |
|---|---|---|---|---|
| Laskeva peittävä | 2 | 0 | 0 | – / – |
| Laskeva marubozu | 1 | 0 | 0 | – / – |
| Nouseva peittävä | 5 | 0 | 0 | – / – |
| Nouseva marubozu | 4 | 0 | 0 | – / – |
| Doji | 3 | 0 | 0 | – / – |
| Sudenkorento-doji | 1 | 0 | 0 | – / – |
| Hautakivi-doji | 1 | 0 | 0 | – / – |
| Vasara | 5 | 0 | 0 | – / – |
| Vasaran muoto (ei trendiä) | 2 | 0 | 0 | – / – |
| Hirttäytyjä | 1 | 0 | 0 | – / – |
| Käänteinen vasara | 1 | 0 | 0 | – / – |
| Käänteisen vasaran muoto (ei trendiä) | 1 | 0 | 0 | – / – |
| Pitkäjalkainen doji | 1 | 0 | 0 | – / – |
| Tähdenlento | 4 | 0 | 0 | – / – |

## Kirjallisuuden mukaan (sis. tunnetut aukot)

| Kuvio | Oikein (TP) | Väärä hälytys (FP) | Löytämättä (FN) | Tapaukset FP / FN |
|---|---|---|---|---|
| Laskeva peittävä | 2 | 0 | 0 | – / – |
| Laskeva marubozu | 1 | 0 | 0 | – / – |
| Nouseva peittävä | 5 | 0 | 1 | – / E6 |
| Nouseva harami (ei toteutettu) | 0 | 0 | 1 | – / G1 |
| Nouseva marubozu | 4 | 0 | 0 | – / – |
| Doji | 2 | 1 | 1 | D8 / D9 |
| Sudenkorento-doji | 1 | 0 | 1 | – / D8 |
| Hautakivi-doji | 1 | 0 | 0 | – / – |
| Vasara | 5 | 0 | 2 | – / H9, H10 |
| Vasaran muoto (ei trendiä) | 1 | 1 | 0 | H9 / – |
| Hirttäytyjä | 1 | 0 | 0 | – / – |
| Käänteinen vasara | 1 | 0 | 0 | – / – |
| Käänteisen vasaran muoto (ei trendiä) | 1 | 0 | 0 | – / – |
| Pitkäjalkainen doji | 1 | 0 | 0 | – / – |
| Tähdenlento | 4 | 0 | 0 | – / – |

## Tapaukset

| Id | Luokka | Kuvaus | Määritelmä | Kirjallisuus | Tunnistettu | OK |
|---|---|---|---|---|---|---|
| D1 | P | Doji sivuttaisliikkeessä: runko 5 %, varjot 45/50 %, koko 0,8 × keskim. | doji | doji | doji | ✓ |
| D2 | P | Pitkäjalkainen doji: runko 4 %, varjot 48/48 %, koko 1,5 × keskim. | long_legged_doji | long_legged_doji | long_legged_doji | ✓ |
| D3 | P | Sudenkorento-doji laskun jälkeen: runko 5 %, yläsvarjo 2 %, alavarjo 93 % | dragonfly_doji | dragonfly_doji | dragonfly_doji | ✓ |
| D4 | P | Hautakivi-doji nousun jälkeen: runko 5 %, yläsvarjo 93 %, alavarjo 2 % | gravestone_doji | gravestone_doji | gravestone_doji | ✓ |
| D5 | N | Hyrrä (spinning top): runko 15 % – liian suuri dojiksi, varjot 40/45 % | – | – | – | ✓ |
| D6a | B | Runko 9,9 % (juuri doji-rajan alla), varjot 45/45,1 %, koko 0,8 × | doji | doji | doji | ✓ |
| D6b | B | Runko 10,1 % (juuri doji-rajan yli), varjot 45/44,9 %, koko 0,8 × | – | – | – | ✓ |
| D7 | N | Pikkuruinen kynttilä: koko 0,2 × keskim. (alle 0,3 × tulkintarajan), runko 2 % | – | – | – | ✓ |
| D8 | B | Sudenkorennon näköinen, mutta yläsvarjo 12 % (> 10 %) -> tavallinen doji | doji | dragonfly_doji | doji | ✓ |
| D9 | G | Doji, mutta historiaa vain 15 kynttilää (lämmittely kesken) | – | doji | – | ✓ |
| H1 | P | Vasara laskun jälkeen: nouseva, runko 20 %, yläsvarjo 5 %, alavarjo 75 %, koko 1,2 × | hammer | hammer | hammer | ✓ |
| H2 | P | Vasara laskun jälkeen, laskeva runko: runko 20 %, yläsvarjo 5 %, alavarjo 75 % | hammer | hammer | hammer | ✓ |
| H3 | P | Hirttäytyjä nousun jälkeen: sama muoto kuin H1 | hanging_man | hanging_man | hanging_man | ✓ |
| H4 | P | Vasaran muoto sivuttaisliikkeessä (ei trendiä) | hammer_shape | hammer_shape | hammer_shape | ✓ |
| H5 | N | Liian lyhyt alavarjo: runko 30 %, yläsvarjo 15 %, alavarjo 55 % (< 60 %) | – | – | – | ✓ |
| H6 | N | Liian pitkä yläsvarjo: runko 15 %, yläsvarjo 25 % (> 15 %), alavarjo 60 % | – | – | – | ✓ |
| H7a | B | Yläsvarjo 14,9 % (juuri rajan alla), runko 20 %, alavarjo 65,1 % | hammer | hammer | hammer | ✓ |
| H7b | B | Yläsvarjo 15,1 % (juuri rajan yli), runko 20 %, alavarjo 64,9 % | – | – | – | ✓ |
| H8a | B | Alavarjo 2,03 × runko (juuri rajan yli): runko 30 %, yläsvarjo 9 %, alavarjo 61 % | hammer | hammer | hammer | ✓ |
| H8b | B | Alavarjo 1,94 × runko (juuri rajan alla): runko 31 %, yläsvarjo 9 %, alavarjo 60 % | – | – | – | ✓ |
| H9 | G | Vasara loivan laskun jälkeen (liike ≈ −1,2 R < 1,5 R:n trendiraja) | bullish_engulfing, hammer_shape | bullish_engulfing, hammer | bullish_engulfing, hammer_shape | ✓ |
| H10 | G | Pieni vasara: täydellinen muoto, mutta koko 0,25 × keskim. (< 0,3 ×) | – | hammer | – | ✓ |
| I1 | P | Tähdenlento nousun jälkeen: laskeva, runko 20 %, yläsvarjo 75 %, alavarjo 5 % | shooting_star | shooting_star | shooting_star | ✓ |
| I2 | P | Käänteinen vasara laskun jälkeen: nouseva, runko 20 %, yläsvarjo 75 %, alavarjo 5 % | inverted_hammer | inverted_hammer | inverted_hammer | ✓ |
| I3 | N | Liian lyhyt yläsvarjo nousun jälkeen: runko 30 %, yläsvarjo 55 %, alavarjo 15 % | – | – | – | ✓ |
| I4a | B | Tähdenlento, alavarjo 14,9 % (juuri rajan alla) | shooting_star | shooting_star | shooting_star | ✓ |
| I4b | B | Tähdenlennon näköinen, alavarjo 15,1 % (juuri rajan yli) | – | – | – | ✓ |
| I5 | P | Käänteisen vasaran muoto sivuttaisliikkeessä | inverted_shape | inverted_shape | inverted_shape | ✓ |
| E1 | P | Nouseva peittävä laskun jälkeen: runko 0,7 peittää edellisen 0,5 rungon | bullish_engulfing | bullish_engulfing | bullish_engulfing | ✓ |
| E2 | P | Laskeva peittävä nousun jälkeen: runko 0,7 peittää edellisen 0,5 rungon | bearish_engulfing | bearish_engulfing | bearish_engulfing | ✓ |
| E3 | N | Runko ei yllä edellisen avaukseen (100,45 < 100,5) | – | – | – | ✓ |
| E4 | N | Edellinen kynttilä on doji (runko 5 %), ei peitettävää runkoa | – | – | – | ✓ |
| E5 | N | Sama suunta kuin edellisellä (molemmat nousevia) | – | – | – | ✓ |
| E6 | B | Päätös täsmälleen edellisen avauksen tasolla (100,5 = 100,5) | – | bullish_engulfing | – | ✓ |
| E7 | P | Iso nouseva peittävä, joka on myös marubozu (runko 94 %, koko 1,38 ×) | bullish_engulfing, bullish_marubozu | bullish_engulfing, bullish_marubozu | bullish_engulfing, bullish_marubozu | ✓ |
| E8 | P | Nouseva peittävä ilman edeltävää laskua (tunnistetaan, konteksti heikko) | bullish_engulfing | bullish_engulfing | bullish_engulfing | ✓ |
| M1 | P | Nouseva marubozu: runko 95 %, koko 1,5 × (edellinen nouseva -> ei peittävää) | bullish_marubozu | bullish_marubozu | bullish_marubozu | ✓ |
| M2 | P | Laskeva marubozu, joka peittää edellisen nousevan rungon | bearish_engulfing, bearish_marubozu | bearish_engulfing, bearish_marubozu | bearish_engulfing, bearish_marubozu | ✓ |
| M3 | N | Runko 85 % (< 90 %) – vahva kynttilä muttei marubozu | – | – | – | ✓ |
| M4a | B | Runko 95 %, koko 1,19 × (juuri alle 1,2 ×) | – | – | – | ✓ |
| M4b | B | Runko 95 %, koko 1,21 × (juuri yli 1,2 ×) | bullish_marubozu | bullish_marubozu | bullish_marubozu | ✓ |
| G1 | G | Nouseva harami laskun jälkeen: pieni nouseva runko edellisen laskevan rungon sisällä | – | bullish_harami | – | ✓ |
| K1 | K | Vasaraksi muodostuva kynttilä, joka 30 s kohdalla on vasara mutta sulkeutuu marubozuna | bullish_engulfing, bullish_marubozu | bullish_engulfing, bullish_marubozu | bullish_engulfing, bullish_marubozu | ✓ |
| K2 | K | Tähdenlento, joka näkyy keskeneräisenä ja vahvistuu sellaisenaan | shooting_star | shooting_star | shooting_star | ✓ |

## Luokittelijan korjaukset

* **H9**: Alkuperäinen käsin kirjattu vastaus oli {hammer_shape}. Ajon jälkeen botti tunnisti myös nousevan peittävän. Tarkistettu määritelmää vasten: loivan laskun viimeisen kynttilän runko on 0,13 (13 % vaihteluvälistä > 10 %), vasaran nouseva runko 0,24 > 0,13, avaus = edellinen päätös ja päätös > edellinen avaus -> peittävä kuvio täyttyy. Virhe oli luokittelijan, ei botin.

## Jakso A: tunnistusten määrät (1 min, 5 markkinaa)

Tulkittavia kynttilöitä (historiaa ≥ 20, volyymi > 0): 49652

| Kuvio | Vahvistettuja | Osuus kynttilöistä |
|---|---|---|
| Laskeva peittävä | 5099 | 10.3% |
| Nouseva peittävä | 5045 | 10.2% |
| Nouseva marubozu | 2111 | 4.3% |
| Laskeva marubozu | 2037 | 4.1% |
| Doji | 1626 | 3.3% |
| Käänteisen vasaran muoto (ei trendiä) | 1127 | 2.3% |
| Vasaran muoto (ei trendiä) | 1094 | 2.2% |
| Vasara | 652 | 1.3% |
| Hautakivi-doji | 640 | 1.3% |
| Hirttäytyjä | 631 | 1.3% |
| Sudenkorento-doji | 631 | 1.3% |
| Tähdenlento | 615 | 1.2% |
| Käänteinen vasara | 591 | 1.2% |
| Pitkäjalkainen doji | 311 | 0.6% |
