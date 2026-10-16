# PCB-behuizing (doosje + klikdeksel)

Doosje voor de carrier-PCB (`pcb/cleanairpcb.kicad_pcb`): vier afstandsbusjes
met M3-heat-set-inserts waarop de print vastgeschroefd wordt, een deksel dat
erop klikt, en twee kabeluitsparingen op de naad tussen bak en deksel.
Beide delen in PETG.

- Model: `cad/pcb_enclosure.py`; alle maten: `cad/pcb_enclosure_params.py`
- Printmaat, montagegaten en posities van onderdelen komen **rechtstreeks uit
  het KiCad-bestand** (`cad/kicad_board.py`). Verschuift er iets op de print,
  dan schuift het doosje mee.
- `cd cad && make pcb-enclosure` → STL's in printstand;
  `make test` → controles; `make pcb-enclosure-renders` → plaatjes en doorsneden.

## Maten (afgeleid, stand 2026-10-15)

```
        bovenaanzicht                           zijaanzicht (doorsnede)
   ┌──────────── 64.4 ────────────┐        ┌────────────────────────┐ 31.6  deksel 2.0
   │ ┌──────── 60.4 ───────────┐  │        │╔══════════════════════╗│ 29.6  naad
   │ │ o                     o │  ║ J1     │║ lip 5 mm  ▲ nok      ║│
   │ │  ESP32      [J1]        │  ╨ sleuf  │                         ∪ sleuf 6×6
   │ │  DevKitC    [PS1]       │  │ 79.7   │   onderdelen ≤ 18 mm    │
   │ │             [F1]        │  ║ J3     │ ▬▬▬▬▬▬ PCB ▬▬▬▬▬▬▬▬▬▬▬▬ │ 9.6   bovenkant PCB
   │ │ o           [J3]      o │  ╨ sleuf  │  █              █       │ 8.0   busjes 6 mm
   │ └─────────────────────────┘  │        └────────────────────────┘ 2.0   vloer
   └──────────────────────────────┘ +X
```

| Wat | Maat | Waar het vandaan komt |
|---|---|---|
| Print | 58.42 × 73.66 × 1.6 | KiCad Edge.Cuts |
| Montagegaten | 4× M3, 5.08 mm uit de randen | KiCad MountingHole |
| Speling print ↔ wand | 1.0 rondom | `PCB_SIDE_CLEARANCE` |
| Binnenmaat | 60.4 × 75.7 | print + 2× speling |
| Buitenmaat | 64.4 × 79.7 × 31.6 | + wand 2.0, hoogte zie hieronder |
| Busjes | Ø 8, 6 hoog, gat Ø 4.0 × 6.5 diep | zelfde insert als de filterbehuizing |
| Bovenkant PCB | z = 9.6 | vloer 2 + busje 6 + PCB 1.6 |
| Naad (bovenkant bak) | z = 29.6 | hoogste onderdeel (J1, 18) + 2 speling |

### Aangenomen hoogtes van onderdelen

KiCad kent de hoogtes van onze footprints niet; deze staan in
`COMPONENT_HEIGHTS` en bepalen hoe hoog het doosje wordt. **Controleer ze op
de echte print** — als de ESP32 direct gesoldeerd is in plaats van in
headers, of de JST-stekker lager blijft, kan de bak ~4 mm lager.

| Ref | Onderdeel | Hoogte boven PCB | Aanname |
|---|---|---|---|
| U1 | ESP32-DevKitC V4 | 14 | in female headers (8.5 + 1.6 + module) |
| J1 | JST-XH 4p + stekker + kabelbocht | 18 | de hoogste; bepaalt de bak |
| F1 | Bourns MF-R110 | 15 | staand, radiaal |
| PS1 | Recom R-78B5.0-1.5 | 11 | 10.4 body |
| J3 | Phoenix MPT 2p schroefklem | 8 | liggend |

## Beslissingen en overwegingen

**Print vastzetten: heat-set inserts in busjes.** M3×6 van boven door de print
in een messing insert. Zelfde insert (gat Ø 4.0) als de filterbehuizing, dus
die zijn er al. Busjes van 6 mm laten ruimte voor afgeknipte THT-pootjes.
*Overwogen:* direct in PETG schroeven (gat Ø 2.5): goedkoper, maar draad slijt
bij herhaald openen. *Niet gedaan.*

**Deksel: binnenlip met klik-nokken op de twee korte wanden.** De lip valt
5 mm in de bak (0.2 mm speling), op de korte wanden zit een driehoekige nok
(0.6 mm uit de lip, 1.6 mm hoog, 20 mm lang) die in een V-groef in de
binnenwand klikt. Bij het indrukken overlappen nok en wand 0.4 mm
(`SNAP_INTERFERENCE`): dat bepaalt hoe hard het klikt.
Een vingernagel-uitsparing midden op de −X-wand helpt bij het openen.
*Overwogen:*
- Deksel dat óver de buitenkant valt (rok): netter dicht, maar het doosje
  wordt 2× 2.2 mm breder en de klik zit dan op de buitenwand (stoot je er los).
- Nokken rondom op alle vier wanden: te stug om weer open te krijgen, en de
  +X-wand heeft de kabelsleuven al.

**Printstand en overhang.** Bak: vloer op het bed, geen support. De V-groef
heeft schuine flanken (~31° t.o.v. verticaal), dus geen overhang. Deksel:
omgekeerd (bovenkant op het bed), lip omhoog; de nokflanken zijn ~37° t.o.v.
verticaal → zonder support. 0.5 mm afschuining aan bed-randen tegen
olifantenpoot, 0.6 mm aanloop-afschuining onderaan de lip.

**Kabels: U-sleuven in de bovenrand van de +X-wand.** Beide connectoren
(J1 fan, J3 12 V in) zitten aan de +X-kant van de print, dus alle kabels
gaan aan één kant naar buiten. Elke sleuf staat recht tegenover zijn
connector, 6 breed × 6 diep met ronde bodem; het platte deksel sluit hem van
boven af. De lip heeft daar een uitsparing (sleuf + 1 mm per kant).
- Diepte ≥ breedte, anders steekt een ronde kabel van die breedte omhoog in
  het deksel (eerste versie had 6 × 5 — de test ving dit).
- *Overwogen:* de 12 V-sleuf in de −Y-wand, recht achter de liggende
  schroefklem. Kabel loopt dan rechter, maar de kabels komen aan twee kanten
  naar buiten. *Niet gedaan*; makkelijk om te zetten als het in de kast
  beter uitkomt.
- Geen trekontlasting in het doosje; een tie-wrap om de kabel binnen de wand
  doet hetzelfde.

**Niet gedaan (bewust):**
- Geen USB-opening. Flashen gaat OTA, en USB-flashen vraagt toch al dat de
  buck-5V los is (zie het elektronica-ontwerp) — dan is het deksel er toch af.
  De micro-USB zit ~5 mm van de −Y-binnenwand; past een kabel prima.
- Geen montage-oren of gaten in de bodem om het doosje vast te zetten.
  Dubbelzijdig tape of later een gat boren; desgewenst toe te voegen.
- Geen ventilatie: de buck en ESP32 verstoken samen < 1 W.

## Testprints

Zie [`pcb-enclosure-testprints.md`](pcb-enclosure-testprints.md).

## Printresultaat (2026-10-16)

Geprint in PETG met de standaardparameters hierboven: past en klikt in één
keer, zonder aanpassingen. De waarden in `pcb_enclosure_params.py` zijn dus
de beproefde stand voor deze printer + dit filament.
