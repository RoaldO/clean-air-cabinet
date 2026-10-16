# PCB-behuizing — testprints (stappenplan)

Doel: de spelingen van het doosje afstellen op jouw printer + PETG voordat je
de hele bak print (~2–3 uur). Achtergrond en maten: [`pcb-enclosure.md`](pcb-enclosure.md).

## Voorbereiden

```bash
cd cad
make pcb-enclosure        # base, lid én de testplakjes, al in printstand
```

Bestanden (in `cad/`, niet in git):

| Bestand | Wat | Printtijd (indicatie) |
|---|---|---|
| `pcb_enclosure_slice_1_bottom.stl` | vloer + 4 busjes + onderste 7 mm wand | ~30 min |
| `pcb_enclosure_slice_2_rim.stl` | bovenste 10 mm van de bak: groeven + sleuven | ~25 min |
| `pcb_enclosure_lid.stl` | het échte deksel (is al dun) | ~35 min |
| `pcb_enclosure_base.stl` | de hele bak — pas als laatste | ~2,5 uur |

**Print alles in hetzelfde PETG en met dezelfde instellingen** als straks de
echte delen: spelingen gelden voor díe printer en dát materiaal. Geen
support nodig. Deksel ligt al omgekeerd (bovenkant op het bed).

Nodig: de print (of een stuk karton/perfboard van 58.4 × 73.7 met gaten),
4 M3-heat-set-inserts + soldeerbout, M3×6-schroefjes, de fan-kabel en de
12 V-kabel.

## Ronde 1 — vloer en busjes (bepaalt of de print erin past)

Print `pcb_enclosure_slice_1_bottom.stl`.

1. Leg de print erin. Valt hij zonder klemmen tussen de wanden, met ~1 mm
   rondom? Vallen de 4 gaten recht boven de busjes?
2. Smelt de 4 inserts erin. Gaan ze recht, en zitten ze vast (niet
   doordraaien bij aandraaien)?
3. Schroef de print vast met M3×6. Raakt een pootje aan de onderkant de vloer?

| Klacht | Parameter (`cad/pcb_enclosure_params.py`) |
|---|---|
| Print klemt / te veel ruimte | `PCB_SIDE_CLEARANCE` (nu 1.0) |
| Gaten vallen niet boven busjes | niet de parameters: check of de KiCad-file de echte print is |
| Insert te los / scheef / barst busje | `INSERT_HOLE_DIAMETER` (nu 4.0), `STANDOFF_DIAMETER` (nu 8) |
| Pootjes raken de vloer | `STANDOFF_HEIGHT` (nu 6) |

Na een wijziging: `make pcb-enclosure-slices` en alleen dit plakje opnieuw.

**Meet meteen ook de echte hoogtes** van de onderdelen (ESP32 met headers,
zekering, JST mét stekker erin + kabelbocht) en vergelijk met
`COMPONENT_HEIGHTS`. Zijn ze lager, zet ze lager: de bak wordt dan lager
(hoogste onderdeel + 2 mm bepaalt de naad).

## Ronde 2 — klikdeksel en kabelsleuven

Print `pcb_enclosure_slice_2_rim.stl` **en** `pcb_enclosure_lid.stl`.

1. Druk het deksel op de ring. Gaat de lip er makkelijk in (zonder nokken
   zou hij vrij moeten vallen)? Klikt het hoorbaar en voelbaar?
2. Zit het deksel vlak op de rand, zonder te wiebelen?
3. Krijg je het met een nagel via de uitsparing op de lange kant (−X) weer los,
   zonder te veel kracht?
4. Leg de fan-kabel en de 12 V-kabel in de sleuven en klik het deksel erop.
   Gaat het dicht zonder dat de kabel klemt? Zit de kabel niet te los?

| Klacht | Parameter |
|---|---|
| Lip gaat er zwaar in / te los, los van de nokken | `LID_LIP_CLEARANCE` (nu 0.2) |
| Klikt niet / te slap | `SNAP_INTERFERENCE` omhoog (nu 0.4, stapjes 0.1) |
| Te stug, krijg hem niet open | `SNAP_INTERFERENCE` omlaag, of `SNAP_LENGTH` korter (nu 20) |
| Deksel staat bol / komt niet vlak | `SNAP_GROOVE_EXTRA` omhoog (nu 0.2) |
| Kabel past niet / klemt | `CABLE_SLOTS[...]["width"]` en `"depth"` (nu 6 × 6; diepte ≥ breedte) |

Let op: de ring is open aan de onderkant en dus slapper dan de echte bak.
Voelt de klik op de ring nét goed, dan is hij op de echte bak iets
stugger. Liever iets aan de slappe kant afstellen.

Na een wijziging: `make pcb-enclosure` en print ring + deksel opnieuw
(beide geraakt bij nok-/lip-parameters; bij alleen sleuven alleen de ring).

## Ronde 3 — het echte werk

Print `pcb_enclosure_base.stl` (en het deksel uit ronde 2 is al goed, of
print het opnieuw na laatste wijzigingen). Monteer: inserts, print, kabels
inpluggen, kabels in de sleuven, deksel erop.

## Bekende aandachtspunten

- Componenthoogtes zijn aangenomen (zie de tabel in `pcb-enclosure.md`).
  `make test` controleert dat niets tegen deksel of lip komt — maar alleen
  met díe aangenomen hoogtes.
- De V-groef is maar 0.6 mm diep; olifantenpoot of een te dikke eerste laag
  doet er niets aan (zit bovenin), maar overextrusie wel: dan klikt hij
  stugger dan berekend.
- Na elke parameterwijziging: `make test` — die vangt botsingen en te dunne
  wanden voordat je print.
