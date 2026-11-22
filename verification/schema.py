"""
Standardized verification data structures for RikiGaku-AHIRU V12 Suite.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class Verdict(str, Enum):
    PASS = "PASS"
    MARGINAL = "MARGINAL"
    FAIL = "FAIL"
    INFO = "INFO"


@dataclass
class CheckResult:
    check_id: str
    name: str
    metric: str
    measured: Any
    target: str
    unit: str
    verdict: Verdict
    solver: str
    details: str = ""
    remediation: str = ""
    margin_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


@dataclass
class ToolCoverageEntry:
    category: str
    commercial_tools: List[str]
    oss_gpu_executed: List[str]
    execution_mode: str  # "LIVE_A100_GPU", "LIVE_NATIVE_BIN", "LIVE_PYTHON_OSS", "COMMERCIAL_DECK_EXPORTED"
    exported_artifacts: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DomainReport:
    domain_id: int
    code: str
    title_ja: str
    title_en: str
    elapsed_sec: float
    checks: List[CheckResult] = field(default_factory=list)
    tools: List[ToolCoverageEntry] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    plots: List[str] = field(default_factory=list)
    exported_files: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.PASS)

    @property
    def marginal_count(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.MARGINAL)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.FAIL)

    @property
    def overall_verdict(self) -> Verdict:
        if self.fail_count > 0:
            return Verdict.FAIL
        if self.marginal_count > 0:
            return Verdict.MARGINAL
        return Verdict.PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "code": self.code,
            "title_ja": self.title_ja,
            "title_en": self.title_en,
            "overall_verdict": self.overall_verdict.value,
            "pass_count": self.pass_count,
            "marginal_count": self.marginal_count,
            "fail_count": self.fail_count,
            "elapsed_sec": round(self.elapsed_sec, 3),
            "checks": [c.to_dict() for c in self.checks],
            "tools": [t.to_dict() for t in self.tools],
            "metrics": self.metrics,
            "plots": self.plots,
            "exported_files": self.exported_files,
            "notes": self.notes,
        }
