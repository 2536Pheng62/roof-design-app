from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


def _aligned_latex(expression: str, substitution: Optional[str], result: Optional[str]) -> str:
    lines = [expression]
    if substitution:
        lines.append(substitution)
    if result:
        lines.append(result)
    inner = r" \\ ".join(lines)
    return rf"\begin{{aligned}} {inner} \end{{aligned}}"


@dataclass
class CalculationStep:
    title: str
    expression: str
    substitution: Optional[str]
    result: Optional[str]
    status: Optional[str] = None
    note: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "latex": _aligned_latex(self.expression, self.substitution, self.result),
            "status": self.status,
            "note": self.note,
            "metadata": self.metadata,
        }


class CalculationLogMixin:
    def __init__(self) -> None:
        self.steps: List[Dict[str, Any]] = []

    def add_step(
        self,
        title: str,
        expression: str,
        substitution: Optional[str],
        result: Optional[str],
        *,
        status: Optional[str] = None,
        note: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        step = CalculationStep(
            title=title,
            expression=expression,
            substitution=substitution,
            result=result,
            status=status,
            note=note,
            metadata=metadata or {},
        )
        self.steps.append(step.to_dict())

    def reset_steps(self) -> None:
        self.steps = []
