"""All dimensions for the PCB enclosure (box + snap-on lid), in mm.

Board outline, mounting holes and component footprints are NOT here: they
are read from the KiCad file (see kicad_board.py). What lives here is
everything KiCad doesn't know (component heights, clearances, wall sizes)
and the knobs the test slices are meant to tune.

See docs/pcb-enclosure.md for why each value is what it is.
"""

# --- Walls -----------------------------------------------------------------
WALL = 2.0  # side walls, ~4 perimeters at 0.5 mm nozzle (same as the duct)
FLOOR = 2.0  # base floor
LID_PLATE = 2.0  # lid top plate
OUTER_CORNER_RADIUS = 3.0  # outside corners; inside radius follows (= R - WALL)

# --- Board in the box ------------------------------------------------------
PCB_SIDE_CLEARANCE = 1.0  # gap board edge <-> inner wall, each side

# Standoffs (afstandsbusjes) with M3 heat-set inserts, same insert as the
# filter enclosure. Screw: M3x6 from the top through the board.
STANDOFF_HEIGHT = 6.0  # floor top -> PCB bottom; room for cut THT leads
STANDOFF_DIAMETER = 8.0
INSERT_HOLE_DIAMETER = 4.0  # TUNE: snug for the brass insert (test slice 1)
INSERT_HOLE_DEPTH = 6.5  # insert 5 mm + room for melt/screw tip
MIN_FLOOR_UNDER_INSERT = 1.0

# Heights of components ABOVE the PCB top (KiCad has no heights for most of
# our footprints). Envelope = courtyard x this height. Key = reference.
COMPONENT_HEIGHTS = {
    "U1": 14.0,  # ESP32-DevKitC in female headers (8.5 + 1.6 + module ~3.2)
    "PS1": 11.0,  # Recom R-78B5.0-1.5, 10.4 body + stand-off
    "F1": 15.0,  # Bourns MF-R110 radial polyfuse, standing
    "J3": 8.0,  # Phoenix MPT 0,5 2-pole horizontal screw terminal
    "J1": 18.0,  # JST-XH 4p vertical + mated plug (~12) + wire bend
}
# The DevKitC board is longer than its pin-row courtyard: the WROOM antenna
# sticks out at the top (+Y), the micro-USB at the bottom (-Y).
ESP32_EXTEND_TOP = 6.0
ESP32_EXTEND_BOTTOM = 3.5
COMPONENT_TOP_CLEARANCE = 2.0  # tallest envelope <-> lid underside

# --- Snap-fit lid ----------------------------------------------------------
# The lid has an inner lip that drops into the base; on the two short walls
# a ridge on the lip clicks into a V-groove in the base's inner wall.
LID_LIP_HEIGHT = 5.0
LID_LIP_THICKNESS = 1.6
LID_LIP_CLEARANCE = 0.2  # TUNE: lip outer face <-> base inner wall (test slice 2)
LID_LIP_CHAMFER = 0.6  # lead-in on the lip's bottom outer edge
SNAP_LENGTH = 20.0  # length of each ridge along the wall
SNAP_INTERFERENCE = 0.4  # TUNE: how far the ridge overlaps the wall (click force)
SNAP_RIDGE_HEIGHT = 1.6  # ridge base on the lip face (vertical)
SNAP_GROOVE_EXTRA = 0.2  # groove bigger than ridge, so the ridge fully seats
SNAP_FROM_SEAM = 2.5  # ridge centre, measured down from the seam
SNAP_LENGTH_CLEARANCE = 1.0  # groove longer than ridge, each end
MIN_WALL_AT_GROOVE = 1.2

# Fingernail recess under the lid edge, centred on each snap wall, outside.
PRY_NOTCH_WIDTH = 12.0
PRY_NOTCH_DEPTH = 1.0
PRY_NOTCH_HEIGHT = 1.5

# --- Cable exits at the seam -----------------------------------------------
# U-shaped notches in the base's top rim on the +X wall (both connectors sit
# on that side); the lid's flat underside closes them from above. Each one
# lines up with its connector. Key = reference of the connector.
# Depth >= width, else a round cable of that width pokes up into the lid.
CABLE_SLOTS = {
    "J1": {"width": 6.0, "depth": 6.0},  # fan: 4 x 24 AWG, ~5 mm bundle
    "J3": {"width": 6.0, "depth": 6.0},  # 12 V in: 2-core lead, ~5 mm round
}
LIP_SLOT_EXTRA = 1.0  # lip cut-out wider than the slot, each side

# --- Test slices -----------------------------------------------------------
SLICE_BOTTOM_HEIGHT = 9.0  # floor + standoffs + a bit of wall
SLICE_RIM_HEIGHT = 10.0  # top rim of the base: groove + cable slots
