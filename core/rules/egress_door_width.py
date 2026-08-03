"""
Rule 1 — Minimum clear width of designated egress doors.

Reference points for the default threshold (see data/config.yaml for the
full citation and caveats): Hong Kong Buildings Department's Code of
Practice for Fire Safety in Buildings 2011 (exit door width, population-
dependent) and IBC 2021 1010.1.1 (813 mm / 32 in minimum clear width).
Both are commonly-cited *minimums*, not a substitute for a real code check —
the threshold is a config value precisely so it can be corrected per project.
"""
from __future__ import annotations

from typing import Any

from core.rules.base import Rule, RuleResult, Violation
from core.schema import Building


class EgressDoorWidthRule(Rule):
    id = "egress_door_width"
    name = "Minimum Clear Width of Designated Egress Doors"
    description = (
        "Every door flagged as part of the means of egress must have a "
        "clear width at or above the project's configured minimum "
        "(config: min_clear_width_mm)."
    )

    def check(self, building: Building, config: dict[str, Any]) -> RuleResult:
        threshold = float(config.get("min_clear_width_mm", 850))
        exit_doors = [d for d in building.doors if d.is_designated_exit]

        violations: list[Violation] = []
        for door in exit_doors:
            if door.width_mm < threshold:
                violations.append(
                    Violation(
                        rule_id=self.id,
                        severity="fail",
                        element_type="door",
                        element_id=door.id,
                        element_name=door.name,
                        message=(
                            f"'{door.name}' has a clear width of "
                            f"{door.width_mm:.0f} mm, below the configured "
                            f"minimum of {threshold:.0f} mm."
                        ),
                        measured_value=door.width_mm,
                        threshold_value=threshold,
                        unit="mm",
                    )
                )

        return RuleResult(
            rule_id=self.id,
            rule_name=self.name,
            checked_count=len(exit_doors),
            violations=violations,
        )