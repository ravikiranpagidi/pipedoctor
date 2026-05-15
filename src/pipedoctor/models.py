"""Core report models used by PipeDoctor."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


SEVERITY_WEIGHTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
    "info": 0,
    "pass": 0,
}

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
    "pass": 5,
}


@dataclass(frozen=True)
class DiagnoseOptions:
    """User-facing diagnosis options.

    V1 intentionally keeps this small. More knobs can be added without changing
    the one-line ``diagnose(df)`` workflow.
    """

    name: str = "dataframe"
    sample_rows: int = 10000
    key_columns: List[str] = field(default_factory=list)
    critical_columns: List[str] = field(default_factory=list)
    cdc_order_column: Optional[str] = None
    previous: Any = None
    baseline_schema: Optional[Mapping[str, Mapping[str, Any]]] = None
    show: bool = True


@dataclass
class Finding:
    """One actionable diagnostic finding."""

    rule_id: str
    title: str
    severity: str
    message: str
    recommendation: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "recommendation": self.recommendation,
            "evidence": self.evidence,
        }


@dataclass
class DataProfile:
    """Normalized profile returned by an adapter."""

    engine: str
    name: str
    rows: Optional[int]
    columns: List[str]
    schema: Dict[str, Dict[str, Any]]
    nulls: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    duplicates: Dict[str, Any] = field(default_factory=dict)
    cardinality: Dict[str, int] = field(default_factory=dict)
    numeric: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hot_values: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    partitions: Dict[str, Any] = field(default_factory=dict)
    cdc: Dict[str, Any] = field(default_factory=dict)
    plan_text: Optional[str] = None
    sampled: bool = False
    sample_rows: Optional[int] = None

    @property
    def column_count(self) -> int:
        return len(self.columns)


@dataclass
class DiagnosisReport:
    """A complete PipeDoctor report."""

    name: str
    engine: str
    findings: List[Finding]
    metrics: Dict[str, Any]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def score(self) -> int:
        penalty = sum(SEVERITY_WEIGHTS.get(f.severity, 0) for f in self.findings)
        return max(0, 100 - penalty)

    @property
    def risk_counts(self) -> Dict[str, int]:
        counts = {name: 0 for name in SEVERITY_WEIGHTS}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return {k: v for k, v in counts.items() if v}

    def sorted_findings(self) -> List[Finding]:
        return sorted(
            self.findings,
            key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.rule_id),
        )

    def summary(self) -> str:
        counts = ", ".join(f"{k}={v}" for k, v in self.risk_counts.items()) or "none"
        return (
            f"{self.name}: {self.engine}, score={self.score}/100, "
            f"findings={len(self.findings)} ({counts})"
        )

    def print(self) -> None:
        from pipedoctor.reporters.console import print_report

        print_report(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "engine": self.engine,
            "score": self.score,
            "created_at": self.created_at,
            "metrics": self.metrics,
            "findings": [finding.to_dict() for finding in self.sorted_findings()],
        }

    def to_json(self, path: Optional[str] = None, *, indent: int = 2) -> str:
        payload = json.dumps(self.to_dict(), indent=indent, default=str)
        _write_if_path(path, payload)
        return payload

    def to_markdown(self, path: Optional[str] = None) -> str:
        lines = [
            f"# PipeDoctor Report: {self.name}",
            "",
            f"- Engine: `{self.engine}`",
            f"- Health score: `{self.score}/100`",
            f"- Created at: `{self.created_at}`",
            "",
            "## Findings",
            "",
        ]
        if not self.findings:
            lines.append("No findings. The checked data looks healthy.")
        for finding in self.sorted_findings():
            lines.extend(
                [
                    f"### {finding.severity.upper()}: {finding.title}",
                    "",
                    finding.message,
                    "",
                    f"Recommendation: {finding.recommendation}",
                    "",
                ]
            )
            if finding.evidence:
                lines.extend(["Evidence:", ""])
                for key, value in finding.evidence.items():
                    lines.append(f"- `{key}`: `{value}`")
                lines.append("")
        result = "\n".join(lines).rstrip() + "\n"
        _write_if_path(path, result)
        return result

    def to_html(self, path: Optional[str] = None) -> str:
        badges = "".join(
            f"<span class='badge {finding.severity}'>{finding.severity}</span>"
            for finding in self.sorted_findings()
        )
        cards = []
        for finding in self.sorted_findings():
            evidence = "".join(
                f"<li><code>{_escape(str(k))}</code>: {_escape(str(v))}</li>"
                for k, v in finding.evidence.items()
            )
            cards.append(
                "<section class='finding'>"
                f"<div class='severity {finding.severity}'>{finding.severity}</div>"
                f"<h2>{_escape(finding.title)}</h2>"
                f"<p>{_escape(finding.message)}</p>"
                f"<p><strong>Recommendation:</strong> {_escape(finding.recommendation)}</p>"
                f"<ul>{evidence}</ul>"
                "</section>"
            )
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PipeDoctor Report - {_escape(self.name)}</title>
  <style>
    body {{ font-family: Inter, Segoe UI, Arial, sans-serif; margin: 0; color: #17202a; background: #f7f9fb; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 32px 20px; }}
    header {{ background: #0e3b43; color: #fff; padding: 28px; border-radius: 8px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    .score {{ font-size: 48px; font-weight: 800; margin-top: 12px; }}
    .finding {{ background: #fff; border: 1px solid #dfe7ee; border-radius: 8px; padding: 18px; margin: 16px 0; }}
    .severity {{ display: inline-block; text-transform: uppercase; font-weight: 700; font-size: 12px; padding: 4px 8px; border-radius: 999px; }}
    .critical, .high {{ background: #ffe3e3; color: #9b1c1c; }}
    .medium {{ background: #fff4d6; color: #7a4c00; }}
    .low {{ background: #e6f4ff; color: #084b83; }}
    .info, .pass {{ background: #e8f5e9; color: #1b5e20; }}
    code {{ background: #eef3f7; padding: 2px 5px; border-radius: 4px; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>PipeDoctor Report</h1>
    <div>{_escape(self.name)} · {_escape(self.engine)} · {_escape(self.created_at)}</div>
    <div class="score">{self.score}/100</div>
    <div>{badges}</div>
  </header>
  {''.join(cards) if cards else "<p>No findings. The checked data looks healthy.</p>"}
</main>
</body>
</html>
"""
        _write_if_path(path, html)
        return html


def _write_if_path(path: Optional[str], text: str) -> None:
    if path:
        Path(path).write_text(text, encoding="utf-8")


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def findings_to_dicts(findings: Iterable[Finding]) -> List[Dict[str, Any]]:
    return [finding.to_dict() for finding in findings]
