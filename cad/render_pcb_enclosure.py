"""Render PNG previews of the PCB enclosure: an exploded 3D view and
cross-sections through the snap fit and a cable slot.

    uv run python render_pcb_enclosure.py [out_dir]
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from build123d import *
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import pcb_enclosure_params as P
from pcb_enclosure import Enclosure

LIGHT = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])


def _mesh(part, tolerance=0.05):
    verts, tris = part.tessellate(tolerance, 0.3)
    v = np.array([(p.X, p.Y, p.Z) for p in verts])
    return v[np.array(tris)]


def _add_shaded(ax, part, rgb, alpha=1.0):
    tris = _mesh(part)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    shade = 0.35 + 0.65 * np.clip(n @ LIGHT, 0, 1)
    colors = np.clip(np.outer(shade, rgb), 0, 1)
    colors = np.hstack([colors, np.full((len(colors), 1), alpha)])
    ax.add_collection3d(Poly3DCollection(tris, facecolors=colors, linewidths=0))


def render_3d(parts, path, elev=28, azim=-55, title=""):
    fig = plt.figure(figsize=(9, 9))
    ax = fig.add_subplot(projection="3d")
    lo = np.full(3, np.inf)
    hi = np.full(3, -np.inf)
    for part, rgb, alpha in parts:
        _add_shaded(ax, part, rgb, alpha)
        bb = part.bounding_box()
        lo = np.minimum(lo, [bb.min.X, bb.min.Y, bb.min.Z])
        hi = np.maximum(hi, [bb.max.X, bb.max.Y, bb.max.Z])
    c = (lo + hi) / 2
    r = (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r)
    ax.set_ylim(c[1] - r, c[1] + r)
    ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    ax.set_title(title)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def _section_polys(part, plane: Plane):
    sec = part & (plane * Box(400, 400, 0.001))
    polys = []
    for face in sec.faces():
        for wire in face.wires():
            pts = [wire.position_at(t) for t in np.linspace(0, 1, 400)]
            local = [plane.to_local_coords(p) for p in pts]
            polys.append(np.array([(p.X, p.Y) for p in local]))
    return polys


def render_section(parts, plane, path, title, xlim=None, ylim=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    for part, rgb, label in parts:
        first = True
        for poly in _section_polys(part, plane):
            ax.fill(*poly.T, color=rgb, alpha=0.7, label=label if first else None)
            ax.plot(*poly.T, color="black", lw=0.5)
            first = False
    ax.set_aspect("equal")
    ax.grid(True, lw=0.3)
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(title)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    enc = Enclosure()
    blue, lid_c = (0.35, 0.55, 0.8), (0.75, 0.85, 0.95)
    green, orange = (0.2, 0.6, 0.3), (0.95, 0.6, 0.2)

    render_3d(
        [
            (enc.base, blue, 1.0),
            (enc.pcb, green, 1.0),
            (enc.components, orange, 1.0),
            (Pos(0, 0, 30) * enc.lid, lid_c, 1.0),
        ],
        out / "pcb_enclosure_exploded.png",
        title=enc.summary(),
    )
    render_3d(
        [(enc.base, blue, 1.0), (enc.lid, lid_c, 1.0)],
        out / "pcb_enclosure_closed.png",
        azim=-30,
        title="closed, cable side (+X)",
    )
    render_3d(
        [(enc.lid_print(), lid_c, 1.0)],
        out / "pcb_enclosure_lid_print.png",
        elev=35,
        title="lid in print orientation",
    )

    parts = [
        (enc.base, blue, "base"),
        (enc.lid, lid_c, "lid"),
        (enc.pcb, green, "pcb"),
        (enc.components, orange, "component envelopes"),
    ]
    # YZ through x=0: snap ridges in the grooves on both short walls
    render_section(
        parts, Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)),
        out / "pcb_enclosure_section_snap.png", "section x=0 (snap walls)",
    )
    yh = enc.outer_y / 2
    render_section(
        parts, Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)),
        out / "pcb_enclosure_section_snap_zoom.png", "snap detail, +Y wall",
        xlim=(yh - 6, yh + 1), ylim=(enc.seam_z - 7, enc.total_height + 1),
    )
    y_slot = enc.slot_positions()["J1"]
    render_section(
        parts, Plane(origin=(0, y_slot, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)),
        out / "pcb_enclosure_section_slot.png", f"section y={y_slot:.1f} (J1 cable slot)",
    )
    x_slot_wall = enc.outer_x / 2 - P.WALL / 2
    render_section(
        parts, Plane(origin=(x_slot_wall, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)),
        out / "pcb_enclosure_section_wall.png", "section through +X wall (cable slots)",
        ylim=(enc.seam_z - 12, enc.total_height + 1),
    )
    hx, hy = enc.mounting_holes[0]
    render_section(
        parts, Plane(origin=(0, hy, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0)),
        out / "pcb_enclosure_section_standoff.png", "section through standoffs",
        ylim=(-1, 14),
    )
    print(f"renders in {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("renders"))
