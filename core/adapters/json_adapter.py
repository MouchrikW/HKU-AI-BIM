"""
Adapter for the simplified JSON building format (see data/*.json for
examples, and docs/design_notes.md for the schema rationale).

This is the fully-tested, zero-extra-dependency path: no compiled library,
so it's also what the Streamlit app falls back to for arbitrary user uploads
when the (optional) IFC path isn't available or doesn't carry adjacency data.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from core.schema import Building, Door, Point2D, Space


def load_json_building(path: Union[str, Path]) -> Building:
    path = Path(path)
    data = json.loads(path.read_text())
    return building_from_dict(data, source_file=str(path))


def building_from_dict(data: dict, source_file: Optional[str] = None) -> Building:
    spaces = [
        Space(
            id=s["id"],
            name=s["name"],
            occupancy_type=s.get("occupancy_type", "office"),
            area_m2=s.get("area_m2", 0.0),
            centroid=Point2D(**s["centroid"]),
            width_m=s.get("width_m"),
            depth_m=s.get("depth_m"),
            is_exit=s.get("is_exit", False),
            fire_rating=s.get("fire_rating"),
        )
        for s in data.get("spaces", [])
    ]
    doors = [
        Door(
            id=d["id"],
            name=d["name"],
            width_mm=d["width_mm"],
            connects=tuple(d["connects"]),
            is_designated_exit=d.get("is_designated_exit", False),
            fire_rating=d.get("fire_rating"),
        )
        for d in data.get("doors", [])
    ]
    return Building(
        name=data.get("name", "Unnamed Building"),
        spaces=spaces,
        doors=doors,
        source_file=source_file,
        source_format="json",
    )