"""
Renders a schematic 2D egress-connectivity diagram for a Building +
ComplianceReport: rooms as rectangles (from Space.footprint()), doors as
connecting lines, coloured by violation status.

Honest framing: this is a connectivity/adjacency diagram, not a true CAD
floor plan — the schema doesn't carry wall polygons, only room footprints
and door connections. That's a deliberate scope cut (see docs/design_notes.md)
appropriate for a sanity-check prototype; it should read as "which rooms and
doors have a problem", not as an architectural drawing.
"""
from __future__ import annotations

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from core.engine import ComplianceReport
from core.rules.travel_distance import EXTERIOR
from core.schema import Building

PASS_COLOR = "#2F6F5E"
FAIL_COLOR = "#C43E3E"
CRITICAL_COLOR = "#7A1F1F"
EXIT_COLOR = "#1B2A4A"
DOOR_OK_COLOR = "#9AA5B1"
TEXT_ON_DARK = "#F5F6F3"


def _violated_space_status(report: ComplianceReport) -> dict[str, str]:
    status: dict[str, str] = {}
    for result in report.rule_results:
        for v in result.violations:
            if v.element_type == "space":
                status[v.element_id] = v.severity
    return status


def _violated_door_ids(report: ComplianceReport) -> set[str]:
    return {
        v.element_id
        for result in report.rule_results
        for v in result.violations
        if v.element_type == "door"
    }


def render_floor_diagram(building: Building, report: ComplianceReport, ax=None):
    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#F5F6F3")
    ax.set_facecolor("#F5F6F3")

    space_status = _violated_space_status(report)
    bad_doors = _violated_door_ids(report)
    positions = {s.id: (s.centroid.x, s.centroid.y) for s in building.spaces}

    if building.spaces:
        building_cx = sum(p[0] for p in positions.values()) / len(positions)
        building_cy = sum(p[1] for p in positions.values()) / len(positions)
    else:
        building_cx = building_cy = 0.0

    # --- rooms ---
    for space in building.spaces:
        w, d = space.footprint()
        x, y = space.centroid.x, space.centroid.y
        if space.is_exit:
            color = EXIT_COLOR
        else:
            severity = space_status.get(space.id)
            color = (
                CRITICAL_COLOR if severity == "critical"
                else FAIL_COLOR if severity == "fail"
                else PASS_COLOR
            )
        rect = patches.FancyBboxPatch(
            (x - w / 2, y - d / 2), w, d,
            boxstyle="round,pad=0,rounding_size=0.15",
            linewidth=1.2, edgecolor="white", facecolor=color,
            alpha=0.92, zorder=2,
        )
        ax.add_patch(rect)
        ax.text(x, y, space.name, ha="center", va="center", fontsize=7.5,
                 color=TEXT_ON_DARK, zorder=3, wrap=True, fontweight="medium")

    # --- doors ---
    for door in building.doors:
        a, b = door.connects
        color = FAIL_COLOR if door.id in bad_doors else DOOR_OK_COLOR
        lw = 3.0 if door.id in bad_doors else 1.4
        style = "--" if door.id in bad_doors else "-"

        if EXTERIOR in (a, b):
            inside_id = b if a == EXTERIOR else a
            if inside_id not in positions:
                continue
            ix, iy = positions[inside_id]
            dx, dy = ix - building_cx, iy - building_cy
            norm = (dx ** 2 + dy ** 2) ** 0.5 or 1.0
            ex, ey = ix + dx / norm * 2.5, iy + dy / norm * 2.5
            ax.plot([ix, ex], [iy, ey], color=color, linewidth=lw,
                     linestyle=style, zorder=1)
            ax.plot(ex, ey, marker="^", color=color, markersize=7, zorder=1)
            continue

        if a not in positions or b not in positions:
            continue
        (x1, y1), (x2, y2) = positions[a], positions[b]
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw,
                 linestyle=style, zorder=1)

    ax.set_aspect("equal")
    ax.axis("off")
    status_text = "PASS" if report.passed else f"{report.total_violations} issue(s)"
    ax.set_title(f"{building.name} — egress connectivity ({status_text})",
                 fontsize=11, color="#1E1E24", fontweight="bold", pad=14)

    legend_handles = [
        patches.Patch(color=PASS_COLOR, label="Space — OK"),
        patches.Patch(color=FAIL_COLOR, label="Violation"),
        patches.Patch(color=CRITICAL_COLOR, label="Unreachable"),
        patches.Patch(color=EXIT_COLOR, label="Exit / stair"),
    ]
    ax.legend(handles=legend_handles, loc="upper center",
              bbox_to_anchor=(0.5, -0.02), ncol=4, frameon=False, fontsize=8)

    if own_fig:
        fig.tight_layout()
        return fig
    return ax