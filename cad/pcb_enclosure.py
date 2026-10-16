"""Enclosure for the carrier PCB: a box with four heat-set-insert standoffs
the board screws onto, and a lid that snaps onto it. Cables leave through
U-notches in the base's top rim, closed from above by the lid.

Model coordinates: board centred on X/Y = 0, base floor bottom at Z = 0.
Every size comes from pcb_enclosure_params.py or the KiCad board file.

    uv run python pcb_enclosure.py           # export print files
    uv run python pcb_enclosure.py --slices  # export test slices only
    uv run python pcb_enclosure.py --show    # assembly in the OCP viewer
"""

import sys
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from build123d import *

import pcb_enclosure_params as P
from kicad_board import Board, load_board

OUT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Envelope:
    """Space a component occupies above the PCB (courtyard x height)."""

    reference: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    z_min: float
    z_max: float

    def solid(self) -> Part:
        return Pos(
            (self.x_min + self.x_max) / 2,
            (self.y_min + self.y_max) / 2,
            (self.z_min + self.z_max) / 2,
        ) * Box(
            self.x_max - self.x_min, self.y_max - self.y_min, self.z_max - self.z_min
        )


class Enclosure:
    def __init__(self, board: Board | None = None):
        self.board = board or load_board()

    # --- derived sizes ----------------------------------------------------
    @property
    def cavity_x(self) -> float:
        return self.board.width + 2 * P.PCB_SIDE_CLEARANCE

    @property
    def cavity_y(self) -> float:
        return self.board.length + 2 * P.PCB_SIDE_CLEARANCE

    @property
    def outer_x(self) -> float:
        return self.cavity_x + 2 * P.WALL

    @property
    def outer_y(self) -> float:
        return self.cavity_y + 2 * P.WALL

    @property
    def pcb_bottom_z(self) -> float:
        return P.FLOOR + P.STANDOFF_HEIGHT

    @property
    def pcb_top_z(self) -> float:
        return self.pcb_bottom_z + self.board.thickness

    def _board_xy(self, x: float, y: float) -> tuple[float, float]:
        """KiCad board coords (lower-left origin) -> model coords."""
        return (x - self.board.width / 2, y - self.board.length / 2)

    @cached_property
    def mounting_holes(self) -> list[tuple[float, float]]:
        return [self._board_xy(x, y) for x, y in self.board.mounting_holes]

    @cached_property
    def envelopes(self) -> list[Envelope]:
        result = []
        for ref, fp in self.board.footprints.items():
            x0, y0 = self._board_xy(fp.x_min, fp.y_min)
            x1, y1 = self._board_xy(fp.x_max, fp.y_max)
            if ref == "U1":
                y0 -= P.ESP32_EXTEND_BOTTOM
                y1 += P.ESP32_EXTEND_TOP
            result.append(
                Envelope(
                    ref, x0, y0, x1, y1,
                    self.pcb_top_z, self.pcb_top_z + P.COMPONENT_HEIGHTS[ref],
                )
            )
        return result

    @property
    def seam_z(self) -> float:
        """Top of the base walls = underside of the lid plate."""
        return max(e.z_max for e in self.envelopes) + P.COMPONENT_TOP_CLEARANCE

    @property
    def total_height(self) -> float:
        return self.seam_z + P.LID_PLATE

    @property
    def snap_z(self) -> float:
        return self.seam_z - P.SNAP_FROM_SEAM

    # --- 2D profiles -------------------------------------------------------
    def outer_profile(self) -> Sketch:
        return RectangleRounded(self.outer_x, self.outer_y, P.OUTER_CORNER_RADIUS)

    def cavity_profile(self) -> Sketch:
        return offset(self.outer_profile(), -P.WALL)

    def lip_outer_profile(self) -> Sketch:
        return offset(self.cavity_profile(), -P.LID_LIP_CLEARANCE)

    def lip_inner_profile(self) -> Sketch:
        return offset(self.lip_outer_profile(), -P.LID_LIP_THICKNESS)

    # --- cable slots -------------------------------------------------------
    def slot_positions(self) -> dict[str, float]:
        """Y position of each cable slot, lined up with its connector."""
        envs = {e.reference: e for e in self.envelopes}
        return {
            ref: (envs[ref].y_min + envs[ref].y_max) / 2 for ref in P.CABLE_SLOTS
        }

    def _slot_cutter(self, y: float, width: float, depth: float) -> Part:
        x_in = self.cavity_x / 2 - 0.5
        length = P.WALL + 1.0
        r = width / 2
        bottom = self.seam_z - depth
        box_h = depth - r + 1.0  # up past the seam
        upper = Pos(x_in + length / 2, y, bottom + r + box_h / 2) * Box(
            length, width, box_h
        )
        round_bottom = Pos(x_in + length / 2, y, bottom + r) * (
            Rot(0, 90, 0) * Cylinder(r, length)
        )
        return upper + round_bottom

    # --- snap ridge / groove ----------------------------------------------
    def _triangle_prism(
        self, y_face: float, sign: int, protrusion: float, height: float,
        length: float, embed: float,
    ) -> Part:
        """Triangular bar along X, its flat side at y_face, apex `protrusion`
        further in direction `sign` (+1 = +Y). `embed` extends the flat side
        backwards so booleans fuse/cut cleanly."""
        z = self.snap_z
        pts = [
            (y_face - sign * embed, z - height / 2),
            (y_face, z - height / 2),
            (y_face + sign * protrusion, z),
            (y_face, z + height / 2),
            (y_face - sign * embed, z + height / 2),
        ]
        profile = Plane.YZ * Polygon(*pts, align=None)
        return extrude(profile, length / 2, both=True)

    def snap_ridges(self) -> Part:
        face_y = self.cavity_y / 2 - P.LID_LIP_CLEARANCE
        protrusion = P.LID_LIP_CLEARANCE + P.SNAP_INTERFERENCE
        return sum(
            (
                self._triangle_prism(
                    s * face_y, s, protrusion, P.SNAP_RIDGE_HEIGHT,
                    P.SNAP_LENGTH, embed=0.3,
                )
                for s in (-1, 1)
            ),
            start=Part(),
        )

    def snap_grooves(self) -> Part:
        wall_y = self.cavity_y / 2
        depth = P.SNAP_INTERFERENCE + P.SNAP_GROOVE_EXTRA
        height = P.SNAP_RIDGE_HEIGHT + 2 * P.SNAP_GROOVE_EXTRA
        length = P.SNAP_LENGTH + 2 * P.SNAP_LENGTH_CLEARANCE
        return sum(
            (
                self._triangle_prism(s * wall_y, s, depth, height, length, embed=0.3)
                for s in (-1, 1)
            ),
            start=Part(),
        )

    # --- parts -------------------------------------------------------------
    @cached_property
    def base(self) -> Part:
        body = extrude(self.outer_profile(), self.seam_z)
        body = chamfer(body.edges().group_by(Axis.Z)[0], 0.5)  # elephant foot
        body -= Pos(0, 0, P.FLOOR) * extrude(self.cavity_profile(), self.seam_z)

        for x, y in self.mounting_holes:
            body += Pos(x, y, P.FLOOR) * Cylinder(
                P.STANDOFF_DIAMETER / 2, P.STANDOFF_HEIGHT,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
            body -= Pos(x, y, self.pcb_bottom_z) * Cylinder(
                P.INSERT_HOLE_DIAMETER / 2, P.INSERT_HOLE_DEPTH,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )

        body -= self.snap_grooves()

        for ref, y in self.slot_positions().items():
            s = P.CABLE_SLOTS[ref]
            body -= self._slot_cutter(y, s["width"], s["depth"])

        # fingernail recess under the lid edge, middle of the -X wall
        body -= Pos(
            -self.outer_x / 2, 0, self.seam_z - P.PRY_NOTCH_HEIGHT / 2
        ) * Box(2 * P.PRY_NOTCH_DEPTH, P.PRY_NOTCH_WIDTH, P.PRY_NOTCH_HEIGHT)
        return body

    @cached_property
    def lid(self) -> Part:
        """Lid in assembly position (plate on top of the base walls)."""
        plate = Pos(0, 0, self.seam_z) * extrude(self.outer_profile(), P.LID_PLATE)
        plate = chamfer(plate.edges().group_by(Axis.Z)[-1], 0.5)

        lip_bottom = self.seam_z - P.LID_LIP_HEIGHT
        lip = Pos(0, 0, lip_bottom) * extrude(
            self.lip_outer_profile(), P.LID_LIP_HEIGHT
        )
        lip = chamfer(lip.edges().group_by(Axis.Z)[0], P.LID_LIP_CHAMFER)
        lip -= Pos(0, 0, lip_bottom - 1) * extrude(
            self.lip_inner_profile(), P.LID_LIP_HEIGHT + 2
        )
        lip += self.snap_ridges()

        # lip cut-outs where the cables come through
        lip_x = self.cavity_x / 2 - P.LID_LIP_CLEARANCE - P.LID_LIP_THICKNESS / 2
        for ref, y in self.slot_positions().items():
            w = P.CABLE_SLOTS[ref]["width"] + 2 * P.LIP_SLOT_EXTRA
            lip -= Pos(lip_x, y, lip_bottom + P.LID_LIP_HEIGHT / 2) * Box(
                P.LID_LIP_THICKNESS + 2, w, P.LID_LIP_HEIGHT + 0.01
            )
        return plate + lip

    @cached_property
    def pcb(self) -> Part:
        plate = Pos(0, 0, self.pcb_bottom_z) * Box(
            self.board.width, self.board.length, self.board.thickness,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        for x, y in self.mounting_holes:
            plate -= Pos(x, y, self.pcb_bottom_z) * Cylinder(
                1.6, 10, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
        return plate

    @cached_property
    def components(self) -> Part:
        return sum((e.solid() for e in self.envelopes), start=Part())

    # --- print orientation & slices ---------------------------------------
    def base_print(self) -> Part:
        return self.base  # floor on the bed

    def lid_print(self) -> Part:
        """Upside down: plate on the bed, lip pointing up."""
        flipped = Rot(180, 0, 0) * self.lid
        return Pos(0, 0, -flipped.bounding_box().min.Z) * flipped

    def slice_bottom(self) -> Part:
        """Floor + standoffs: board fit, hole positions, insert holes."""
        keep = Box(
            self.outer_x + 2, self.outer_y + 2, P.SLICE_BOTTOM_HEIGHT,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        return self.base & keep

    def slice_rim(self) -> Part:
        """Top rim of the base: snap grooves, cable slots, lid fit."""
        z0 = self.seam_z - P.SLICE_RIM_HEIGHT
        keep = Pos(0, 0, z0) * Box(
            self.outer_x + 2, self.outer_y + 2, P.SLICE_RIM_HEIGHT + 1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        return Pos(0, 0, -z0) * (self.base & keep)

    def summary(self) -> str:
        return (
            f"outside {self.outer_x:.1f} x {self.outer_y:.1f} x "
            f"{self.total_height:.1f} mm (base {self.seam_z:.1f} + lid "
            f"{P.LID_PLATE:.1f}); cavity {self.cavity_x:.1f} x "
            f"{self.cavity_y:.1f}; PCB top at z={self.pcb_top_z:.1f}"
        )


def export(enc: Enclosure, slices_only: bool = False) -> None:
    files = {
        "pcb_enclosure_slice_1_bottom": enc.slice_bottom(),
        "pcb_enclosure_slice_2_rim": enc.slice_rim(),
    }
    if not slices_only:
        files["pcb_enclosure_base"] = enc.base_print()
        files["pcb_enclosure_lid"] = enc.lid_print()
    for name, part in files.items():
        export_stl(part, OUT_DIR / f"{name}.stl")
        print(f"wrote {name}.stl")


if __name__ == "__main__":
    enc = Enclosure()
    print(enc.summary())
    if "--show" in sys.argv:
        from ocp_vscode import show

        show(
            enc.base,
            enc.pcb,
            enc.components,
            Pos(0, 0, 25) * enc.lid,
            names=["base", "pcb", "components", "lid"],
            colors=["steelblue", "green", "orange", "lightblue"],
            alphas=[1, 1, 0.6, 0.8],
        )
    else:
        export(enc, slices_only="--slices" in sys.argv)
