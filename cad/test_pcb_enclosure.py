"""Guards for the PCB enclosure: fit, collisions, wall thickness, slots."""

import pytest
from build123d import *

import pcb_enclosure_params as P
from pcb_enclosure import Enclosure

TOL = 1e-3


@pytest.fixture(scope="module")
def enc() -> Enclosure:
    return Enclosure()


def _volume(part) -> float:
    return part.volume if part is not None and part.solids() else 0.0


def test_board_matches_kicad(enc):
    assert enc.board.width == pytest.approx(58.42)
    assert enc.board.length == pytest.approx(73.66)
    assert len(enc.mounting_holes) == 4


def test_every_component_has_a_height(enc):
    assert set(enc.board.footprints) <= set(P.COMPONENT_HEIGHTS)


def test_pcb_fits_cavity_with_clearance(enc):
    bb = enc.pcb.bounding_box()
    assert enc.cavity_x / 2 - bb.max.X == pytest.approx(P.PCB_SIDE_CLEARANCE)
    assert enc.cavity_y / 2 - bb.max.Y == pytest.approx(P.PCB_SIDE_CLEARANCE)


def test_pcb_rests_on_standoffs_without_overlap(enc):
    assert _volume(enc.base & enc.pcb) < TOL
    # ...and actually touches them: lower the board 0.1 mm -> it collides
    assert _volume(enc.base & (Pos(0, 0, -0.1) * enc.pcb)) > 0


def test_components_clear_base_and_lid(enc):
    assert _volume(enc.components & enc.base) < TOL
    assert _volume(enc.components & enc.lid) < TOL
    top = max(e.z_max for e in enc.envelopes)
    assert enc.seam_z - top >= P.COMPONENT_TOP_CLEARANCE - TOL


def test_lid_only_touches_base_at_the_snap_ridges(enc):
    lid_without_ridges = enc.lid - enc.snap_ridges()
    assert _volume(lid_without_ridges & enc.base) < TOL


def test_ridges_interfere_while_pushing_on(enc):
    """Half-way down (ridge above the groove) the ridge overlaps the wall:
    that overlap is what makes it click."""
    lift = P.SNAP_RIDGE_HEIGHT + 2 * P.SNAP_GROOVE_EXTRA
    overlap = _volume((Pos(0, 0, lift) * enc.snap_ridges()) & enc.base)
    assert overlap > 0


def test_ridges_seat_in_grooves(enc):
    """Fully closed, the ridges sit inside the grooves: no overlap left."""
    assert _volume(enc.snap_ridges() & enc.base) < TOL


def test_wall_behind_groove_is_thick_enough(enc):
    groove_depth = P.SNAP_INTERFERENCE + P.SNAP_GROOVE_EXTRA
    assert P.WALL - groove_depth >= P.MIN_WALL_AT_GROOVE


def test_insert_hole_leaves_floor(enc):
    floor_left = enc.pcb_bottom_z - P.INSERT_HOLE_DEPTH
    assert floor_left >= P.MIN_FLOOR_UNDER_INSERT
    assert P.STANDOFF_DIAMETER - P.INSERT_HOLE_DIAMETER >= 2 * 1.5


@pytest.mark.parametrize("ref", list(P.CABLE_SLOTS))
def test_cable_slot_is_open_with_lid_on(enc, ref):
    """A cable of slot width fits through the closed seam: nothing of the
    base or lid in its way."""
    y = enc.slot_positions()[ref]
    s = P.CABLE_SLOTS[ref]
    r = s["width"] / 2 - 0.05
    cable = Pos(enc.outer_x / 2 - P.WALL / 2, y, enc.seam_z - s["depth"] + r + 0.05) * (
        Rot(0, 90, 0) * Cylinder(r, P.WALL * 3)
    )
    assert _volume(cable & enc.base) < TOL
    assert _volume(cable & enc.lid) < TOL


def test_slots_away_from_corners(enc):
    for ref, y in enc.slot_positions().items():
        half = P.CABLE_SLOTS[ref]["width"] / 2 + P.LIP_SLOT_EXTRA
        assert abs(y) + half <= enc.cavity_y / 2 - P.OUTER_CORNER_RADIUS


def test_lid_print_orientation_on_bed(enc):
    bb = enc.lid_print().bounding_box()
    assert bb.min.Z == pytest.approx(0)
    assert bb.max.Z == pytest.approx(P.LID_PLATE + P.LID_LIP_HEIGHT)


def test_parts_are_single_solids(enc):
    assert len(enc.base.solids()) == 1
    assert len(enc.lid.solids()) == 1
