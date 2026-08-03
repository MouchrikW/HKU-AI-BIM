"""
Canonical, source-agnostic data model for a single building/floor.

Both adapters (core/adapters/json_adapter.py and core/adapters/ifc_adapter.py)
produce a `Building` instance from this module, and every Rule only ever
operates on *this* schema — never on raw IFC entities or raw JSON keys.

Why this indirection is worth a whole extra file: it means the rule engine
(the part whose correctness actually matters for a "compliance check") is
completely decoupled from where the data came from. Adding a third source
format later (a CSV export, a Revit schedule dump) means writing one more
adapter, not touching a single rule. See docs/design_notes.md ("Why an
adapter layer") for the fuller reasoning.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Point2D:
    """A plan-view (x, y) position in metres."""
    x: float
    y: float

    def distance_to(self, other: "Point2D") -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass
class Space:
    """An IfcSpace-equivalent: a room, corridor, lobby, or stair."""

    id: str
    name: str
    occupancy_type: str            # "office" | "corridor" | "stair" | "lobby" | "assembly" | ...
    area_m2: float
    centroid: Point2D
    width_m: Optional[float] = None
    depth_m: Optional[float] = None
    is_exit: bool = False          # True for stairs / final-exit discharge spaces
    fire_rating: Optional[str] = None

    def footprint(self) -> tuple[float, float]:
        """Best-effort (width, depth) for rendering. Falls back to a square
        derived from area when explicit dimensions aren't supplied — good
        enough for a schematic diagram, not meant to imply real geometry."""
        if self.width_m and self.depth_m:
            return self.width_m, self.depth_m
        side = math.sqrt(max(self.area_m2, 1.0))
        return side, side


@dataclass
class Door:
    """An IfcDoor-equivalent connecting two spaces (or a space and the
    special 'EXTERIOR' pseudo-space, for a final exit discharge door)."""

    id: str
    name: str
    width_mm: float
    connects: tuple[str, str]      # (space_id_a, space_id_b); either may be "EXTERIOR"
    is_designated_exit: bool = False
    fire_rating: Optional[str] = None


@dataclass
class Building:
    name: str
    spaces: list[Space] = field(default_factory=list)
    doors: list[Door] = field(default_factory=list)
    source_file: Optional[str] = None
    source_format: Optional[str] = None   # "json" | "ifc"

    def space(self, space_id: str) -> Optional[Space]:
        return next((s for s in self.spaces if s.id == space_id), None)