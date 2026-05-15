"""Human-friendly console rendering."""

from __future__ import annotations

from pipedoctor.models import DiagnosisReport


USE_COLOR = True

ICONS = {
    "critical": "✖",
    "high": "⚠",
    "medium": "⚠",
    "low": "ℹ",
    "info": "ℹ",
    "pass": "✓",
}

COLORS = {
    "critical": "\033[31;1m",
    "high": "\033[31m",
    "medium": "\033[33m",
    "low": "\033[36m",
    "info": "\033[36m",
    "pass": "\033[32m",
    "reset": "\033[0m",
}


def print_report(report: DiagnosisReport) -> None:
    print(f"\nPipeDoctor report for {report.name}")
    print(
        f"Engine: {report.engine} | Health score: {report.score}/100 | "
        f"Findings: {len(report.findings)}"
    )
    if not report.findings:
        print("\n✓ No findings. The checked data looks healthy.")
        return
    for finding in report.sorted_findings():
        icon = ICONS.get(finding.severity, "•")
        severity = finding.severity.upper().ljust(8)
        color = COLORS.get(finding.severity, "") if USE_COLOR else ""
        reset = COLORS["reset"] if color else ""
        print(f"\n{color}{icon} {severity}{reset} {finding.title}")
        print(f"  {finding.message}")
        print(f"  {finding.recommendation}")
        if finding.evidence:
            evidence = ", ".join(
                f"{key}={value}" for key, value in finding.evidence.items()
            )
            print(f"  Evidence: {evidence}")
