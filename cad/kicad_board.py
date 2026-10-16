"""Read the carrier PCB's geometry straight from the KiCad file.

Board outline, mounting holes and each footprint's courtyard come from
`pcb/cleanairpcb.kicad_pcb`, so the enclosure follows the board if it moves
on. Coordinates are returned relative to the board's lower-left corner,
with +Y pointing *up* (KiCad's Y points down; we flip it here once).
"""

import math
import re
from dataclasses import dataclass
from pathlib import Path

KICAD_PCB = Path(__file__).resolve().parent.parent / "pcb" / "cleanairpcb.kicad_pcb"


def _parse_sexpr(text: str):
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack: list[list] = [[]]
    for tok in tokens:
        if tok == "(":
            stack.append([])
        elif tok == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok.strip('"') if tok.startswith('"') else tok)
    return stack[0][0]


def _children(node: list, name: str) -> list[list]:
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def _child(node: list, name: str) -> list | None:
    found = _children(node, name)
    return found[0] if found else None


@dataclass(frozen=True)
class Footprint:
    reference: str
    name: str
    # Courtyard bounding box in board coordinates (mm, Y up).
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

    @property
    def size(self) -> tuple[float, float]:
        return (self.x_max - self.x_min, self.y_max - self.y_min)


@dataclass(frozen=True)
class Board:
    width: float  # X
    length: float  # Y
    thickness: float
    mounting_holes: list[tuple[float, float]]
    footprints: dict[str, Footprint]


def _courtyard_points(fp: list) -> list[tuple[float, float]]:
    points = []
    for kind in ("fp_line", "fp_rect"):
        for item in _children(fp, kind):
            layer = _child(item, "layer")
            if not layer or layer[1] != "F.CrtYd":
                continue
            for key in ("start", "end"):
                p = _child(item, key)
                points.append((float(p[1]), float(p[2])))
            if kind == "fp_rect":  # add the other two corners
                (x0, y0), (x1, y1) = points[-2], points[-1]
                points += [(x0, y1), (x1, y0)]
    return points


def load_board(path: Path = KICAD_PCB) -> Board:
    root = _parse_sexpr(path.read_text())

    thickness = float(_child(_child(root, "general"), "thickness")[1])

    outline = [
        r
        for r in _children(root, "gr_rect")
        if _child(r, "layer")[1] == "Edge.Cuts"
    ]
    if len(outline) != 1:
        raise ValueError("expected exactly one rectangular Edge.Cuts outline")
    (sx, sy), (ex, ey) = (
        tuple(float(v) for v in _child(outline[0], k)[1:3]) for k in ("start", "end")
    )
    left, right = min(sx, ex), max(sx, ex)
    top, bottom = min(sy, ey), max(sy, ey)

    def to_board(x: float, y: float) -> tuple[float, float]:
        return (x - left, bottom - y)

    holes = []
    footprints = {}
    for fp in _children(root, "footprint"):
        name = fp[1]
        at = _child(fp, "at")
        fx, fy = float(at[1]), float(at[2])
        angle = math.radians(float(at[3])) if len(at) > 3 else 0.0
        if name.startswith("MountingHole:"):
            holes.append(to_board(fx, fy))
            continue
        reference = next(
            (p[2] for p in _children(fp, "property") if p[1] == "Reference"),
            None,
        ) or next(t[2] for t in _children(fp, "fp_text") if t[1] == "reference")
        # KiCad rotates footprints counter-clockwise on screen with Y down.
        pts = []
        for lx, ly in _courtyard_points(fp):
            rx = lx * math.cos(angle) + ly * math.sin(angle)
            ry = -lx * math.sin(angle) + ly * math.cos(angle)
            pts.append(to_board(fx + rx, fy + ry))
        if not pts:
            continue
        xs, ys = zip(*pts)
        footprints[reference] = Footprint(
            reference, name, min(xs), min(ys), max(xs), max(ys)
        )

    return Board(
        width=right - left,
        length=bottom - top,
        thickness=thickness,
        mounting_holes=sorted(holes),
        footprints=footprints,
    )


if __name__ == "__main__":
    b = load_board()
    print(f"board {b.width:.2f} x {b.length:.2f} x {b.thickness}")
    print("holes", [(round(x, 2), round(y, 2)) for x, y in b.mounting_holes])
    for f in b.footprints.values():
        print(
            f"{f.reference:4} {f.name:70} x {f.x_min:6.2f}..{f.x_max:6.2f}"
            f"  y {f.y_min:6.2f}..{f.y_max:6.2f}"
        )
