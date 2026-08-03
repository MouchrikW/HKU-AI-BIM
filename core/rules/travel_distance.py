"""
Rule 2 — Maximum travel distance from any occupied space to the nearest exit.

Design choice: distance is computed over a *graph* (spaces as nodes, doors as
weighted edges — weight = straight-line centroid-to-centroid distance), and
we take the shortest path to the nearest exit node via Dijkstra, rather than
a naive straight-line distance from each room to the nearest exit point.

Naive Euclidean distance ignores walls entirely and will happily tell you a
space "passes" because an exit is 8 m away as the crow flies, even if there's
no door-path between them. Routing over the model's actual door connectivity
is a small step up in fidelity that costs almost nothing extra to compute,
and — as a free side effect — it also catches spaces with *no* path to any
exit at all (a missing door / modelling error), which we surface as its own
"critical" finding below. That fell out of the graph approach for free; it
would have needed a special case with the naive approach. See
docs/design_notes.md, "Why a graph instead of a full navigable path", for
where this simplification does and doesn't hold up against a real navmesh /
path-of-travel analysis.
"""
from __future__ import annotations

from typing import Any

import networkx as nx

from core.rules.base import Rule, RuleResult, Violation
from core.schema import Building

EXTERIOR = "EXTERIOR"


def build_egress_graph(building: Building) -> nx.Graph:
    """Undirected graph of the building's egress connectivity.

    Nodes: every Space, plus the virtual EXTERIOR node.
    Edges: one per Door. A door to EXTERIOR gets a small fixed weight (there's
    no interior centroid on that side to measure to); an interior-to-interior
    door is weighted by the straight-line distance between the two spaces'
    centroids.
    """
    graph = nx.Graph()
    graph.add_node(EXTERIOR)
    for space in building.spaces:
        graph.add_node(space.id)

    for door in building.doors:
        a, b = door.connects
        if a == EXTERIOR or b == EXTERIOR:
            weight = 1.0
        else:
            space_a, space_b = building.space(a), building.space(b)
            if space_a is None or space_b is None:
                continue
            weight = max(space_a.centroid.distance_to(space_b.centroid), 0.5)
        graph.add_edge(a, b, weight=weight, door_id=door.id)
    return graph


class TravelDistanceRule(Rule):
    id = "travel_distance"
    name = "Maximum Travel Distance to Nearest Exit"
    description = (
        "Every occupied space must have a graph-connected path to an exit "
        "(a stair/final-exit space, or the exterior) no longer than the "
        "project's configured maximum (config: max_travel_distance_m)."
    )

    def check(self, building: Building, config: dict[str, Any]) -> RuleResult:
        threshold = float(config.get("max_travel_distance_m", 45))
        graph = build_egress_graph(building)

        exit_nodes = {s.id for s in building.spaces if s.is_exit} | {EXTERIOR}
        occupied = [s for s in building.spaces if not s.is_exit]

        violations: list[Violation] = []
        for space in occupied:
            if space.id not in graph:
                continue

            best_distance = None
            for exit_id in exit_nodes:
                if exit_id not in graph:
                    continue
                try:
                    distance = nx.shortest_path_length(
                        graph, space.id, exit_id, weight="weight"
                    )
                except nx.NetworkXNoPath:
                    continue
                if best_distance is None or distance < best_distance:
                    best_distance = distance

            if best_distance is None:
                violations.append(
                    Violation(
                        rule_id=self.id,
                        severity="critical",
                        element_type="space",
                        element_id=space.id,
                        element_name=space.name,
                        message=(
                            f"'{space.name}' has no connected path to any "
                            f"exit or the exterior in this model — check for "
                            f"a missing door."
                        ),
                        measured_value=float("inf"),
                        threshold_value=threshold,
                        unit="m",
                    )
                )
            elif best_distance > threshold:
                violations.append(
                    Violation(
                        rule_id=self.id,
                        severity="fail",
                        element_type="space",
                        element_id=space.id,
                        element_name=space.name,
                        message=(
                            f"'{space.name}' is {best_distance:.1f} m from "
                            f"the nearest exit, exceeding the configured "
                            f"maximum of {threshold:.0f} m."
                        ),
                        measured_value=round(best_distance, 1),
                        threshold_value=threshold,
                        unit="m",
                    )
                )

        return RuleResult(
            rule_id=self.id,
            rule_name=self.name,
            checked_count=len(occupied),
            violations=violations,
        )