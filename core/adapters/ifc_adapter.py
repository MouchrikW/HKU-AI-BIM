"""
Adapter from a real .ifc file to the canonical Building schema, via
ifcopenshell.

Scope, stated plainly (see docs/design_notes.md, "Why the IFC adapter is
best-effort" for the full reasoning):

  FULLY SUPPORTED  — IfcDoor -> Door: name, width (from Pset "Width" /
  "OverallWidth" / "ClearWidth" if present, else the OverallWidth attribute),
  and a designated-exit flag from a name heuristic (/exit|stair/i). This is
  everything Rule 1 (door width) needs.

  BEST-EFFORT      — IfcSpace -> Space: name, area (from a quantity set if
  present), centroid (from ObjectPlacement). Door-to-space *adjacency* is
  NOT derived from IfcRelSpaceBoundary geometry — resolving true space
  boundaries from arbitrary IFC geometry is a substantial computational-
  geometry problem in its own right (arguably a whole separate tool), and
  out of scope for a 1-2 rule sanity-check prototype. Instead, adjacency is
  read from an optional sidecar "<file>.adjacency.json" next to the .ifc
  file (see data/sample_building.ifc.adjacency.json for the format this
  project generates alongside its own sample). Without that sidecar, the IFC
  path still fully supports Rule 1; use the JSON adapter for Rule 2.

This split is a deliberate scope cut, not an oversight — flagged loudly here
and in the README rather than silently producing a Building with wrong or
empty adjacency.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional, Union

from core.schema import Building, Door, Point2D, Space

try:
    import ifcopenshell
    import ifcopenshell.util.element as ifc_element_util
except ImportError as _e:  # pragma: no cover - exercised only when ifcopenshell is absent
    ifcopenshell = None
    _IMPORT_ERROR = _e
else:
    _IMPORT_ERROR = None

_EXIT_NAME_RE = re.compile(r"exit|stair", re.IGNORECASE)


def _require_ifcopenshell() -> None:
    if ifcopenshell is None:
        raise ImportError(
            "ifcopenshell is not installed. Install it with "
            "`pip install ifcopenshell` to use the IFC adapter — the JSON "
            "adapter (core/adapters/json_adapter.py) has no such dependency "
            "and is the recommended default for this prototype."
        ) from _IMPORT_ERROR


def _door_width_mm(ifc_door) -> Optional[float]:
    psets = ifc_element_util.get_psets(ifc_door)
    for pset in psets.values():
        for key in ("Width", "OverallWidth", "ClearWidth"):
            value = pset.get(key)
            if isinstance(value, (int, float)):
                return float(value) * 1000.0  # IFC lengths default to metres
    if getattr(ifc_door, "OverallWidth", None):
        return float(ifc_door.OverallWidth) * 1000.0
    return None


def _space_centroid(ifc_space) -> Point2D:
    try:
        coords = ifc_space.ObjectPlacement.RelativePlacement.Location.Coordinates
        return Point2D(x=float(coords[0]), y=float(coords[1]))
    except Exception:
        return Point2D(x=0.0, y=0.0)


def _space_area_m2(ifc_space) -> float:
    psets = ifc_element_util.get_psets(ifc_space, qtos_only=True)
    for qto in psets.values():
        for key in ("GrossFloorArea", "NetFloorArea", "Area"):
            value = qto.get(key)
            if isinstance(value, (int, float)):
                return float(value)
    return 0.0


def _load_adjacency_sidecar(ifc_path: Path) -> dict[str, tuple[str, str]]:
    sidecar = ifc_path.with_suffix(ifc_path.suffix + ".adjacency.json")
    if not sidecar.exists():
        return {}
    entries = json.loads(sidecar.read_text())
    return {e["door_id"]: tuple(e["connects"]) for e in entries}


def load_ifc_building(path: Union[str, Path]) -> Building:
    _require_ifcopenshell()
    path = Path(path)
    ifc_file = ifcopenshell.open(str(path))

    spaces = []
    for ifc_space in ifc_file.by_type("IfcSpace"):
        name = ifc_space.LongName or ifc_space.Name or ifc_space.GlobalId
        is_exit = bool(_EXIT_NAME_RE.search(name or ""))
        spaces.append(
            Space(
                id=ifc_space.GlobalId,
                name=name,
                occupancy_type="stair" if is_exit else "office",
                area_m2=_space_area_m2(ifc_space),
                centroid=_space_centroid(ifc_space),
                is_exit=is_exit,
            )
        )

    adjacency = _load_adjacency_sidecar(path)
    doors = []
    for ifc_door in ifc_file.by_type("IfcDoor"):
        name = ifc_door.Name or ifc_door.GlobalId
        doors.append(
            Door(
                id=ifc_door.GlobalId,
                name=name,
                width_mm=_door_width_mm(ifc_door) or 0.0,
                connects=adjacency.get(ifc_door.GlobalId, ("UNKNOWN", "UNKNOWN")),
                is_designated_exit=bool(_EXIT_NAME_RE.search(name or "")),
            )
        )

    projects = ifc_file.by_type("IfcProject")
    building_name = (projects[0].Name if projects and projects[0].Name else path.stem)

    return Building(
        name=building_name,
        spaces=spaces,
        doors=doors,
        source_file=str(path),
        source_format="ifc",
    )