"""
Runs the registered rules against a Building and assembles a ComplianceReport.

This is intentionally the only place that knows the full list of active
rules — app.py, run_checks.py, and the tests all go through `run_checks()`
rather than importing individual rule classes, so the "what rules are active"
decision lives in exactly one place.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from core.rules.base import Rule, RuleResult
from core.rules.egress_door_width import EgressDoorWidthRule
from core.rules.travel_distance import TravelDistanceRule
from core.schema import Building

DEFAULT_RULES: list[Rule] = [EgressDoorWidthRule(), TravelDistanceRule()]


@dataclass
class ComplianceReport:
    building_name: str
    source_file: Optional[str]
    rule_results: list[RuleResult] = field(default_factory=list)

    @property
    def total_violations(self) -> int:
        return sum(len(r.violations) for r in self.rule_results)

    @property
    def passed(self) -> bool:
        return self.total_violations == 0

    def to_dict(self) -> dict:
        return {
            "building_name": self.building_name,
            "source_file": self.source_file,
            "passed": self.passed,
            "total_violations": self.total_violations,
            "rule_results": [r.to_dict() for r in self.rule_results],
        }


def run_checks(
    building: Building,
    config: dict[str, Any],
    rules: Optional[list[Rule]] = None,
) -> ComplianceReport:
    active_rules = rules if rules is not None else DEFAULT_RULES
    results = [rule.check(building, config) for rule in active_rules]
    return ComplianceReport(
        building_name=building.name,
        source_file=building.source_file,
        rule_results=results,
    )