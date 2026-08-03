"""
Shared contract every rule implements, plus the result types they return.

Adding rule #3 later means: implement `Rule`, drop the file in core/rules/,
register it in core/engine.py's DEFAULT_RULES list. Nothing else changes.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from core.schema import Building


@dataclass
class Violation:
    rule_id: str
    severity: str              # "fail" | "critical"
    element_type: str          # "door" | "space"
    element_id: str
    element_name: str
    message: str
    measured_value: float
    threshold_value: float
    unit: str

    def to_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    checked_count: int
    violations: list[Violation] = field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return self.checked_count - len(self.violations)

    @property
    def passed(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "checked_count": self.checked_count,
            "passed_count": self.passed_count,
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
        }


class Rule(ABC):
    id: str
    name: str
    description: str

    @abstractmethod
    def check(self, building: Building, config: dict[str, Any]) -> RuleResult:
        """Run this rule against `building` using thresholds in `config`."""
        raise NotImplementedError