"""
Defect Metrics Calculator.

This demonstrates the defect analytics tool I built
for tracking quality metrics and defect escape rates.
"""

import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class DefectSeverity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DefectStage(Enum):
    """Stage where defect was found."""
    DEVELOPMENT = "Development"
    CODE_REVIEW = "Code Review"
    QA_TESTING = "QA Testing"
    UAT = "UAT"
    PRODUCTION = "Production"


@dataclass
class Defect:
    """Defect data model."""
    id: str
    title: str
    severity: DefectSeverity
    found_stage: DefectStage
    introduced_stage: DefectStage
    created_date: datetime
    resolved_date: Optional[datetime] = None
    sprint: Optional[str] = None


class DefectMetricsCalculator:
    """
    Calculate defect metrics for quality analysis.

    Provides metrics like:
    - Defect Escape Rate
    - Defect Density
    - Mean Time to Resolution
    - Severity Distribution
    """

    def __init__(self, defects: list[Defect]):
        self.defects = defects
        self.df = self._to_dataframe()

    def _to_dataframe(self) -> pd.DataFrame:
        """Convert defects to DataFrame for analysis."""
        data = []
        for d in self.defects:
            data.append({
                "id": d.id,
                "title": d.title,
                "severity": d.severity.value,
                "found_stage": d.found_stage.value,
                "introduced_stage": d.introduced_stage.value,
                "created_date": d.created_date,
                "resolved_date": d.resolved_date,
                "sprint": d.sprint,
                "is_escaped": d.found_stage == DefectStage.PRODUCTION
            })
        return pd.DataFrame(data)

    def defect_escape_rate(self) -> float:
        """
        Calculate Defect Escape Rate (DER).

        DER = (Defects found in Production / Total Defects) * 100
        """
        total = len(self.df)
        if total == 0:
            return 0.0

        escaped = len(self.df[self.df["is_escaped"]])
        return (escaped / total) * 100

    def mean_time_to_resolution(self) -> float:
        """
        Calculate Mean Time to Resolution (MTTR) in days.
        """
        resolved = self.df[self.df["resolved_date"].notna()].copy()
        if len(resolved) == 0:
            return 0.0

        resolved["resolution_time"] = (
            resolved["resolved_date"] - resolved["created_date"]
        ).dt.days

        return resolved["resolution_time"].mean()

    def severity_distribution(self) -> dict:
        """Get distribution of defects by severity."""
        return self.df["severity"].value_counts().to_dict()

    def stage_distribution(self) -> dict:
        """Get distribution of defects by found stage."""
        return self.df["found_stage"].value_counts().to_dict()

    def defects_by_sprint(self) -> dict:
        """Get defect count by sprint."""
        return self.df.groupby("sprint").size().to_dict()

    def escape_rate_by_sprint(self) -> dict:
        """Calculate escape rate for each sprint."""
        result = {}
        for sprint in self.df["sprint"].unique():
            sprint_df = self.df[self.df["sprint"] == sprint]
            total = len(sprint_df)
            escaped = len(sprint_df[sprint_df["is_escaped"]])
            result[sprint] = (escaped / total * 100) if total > 0 else 0
        return result

    def generate_report(self) -> dict:
        """Generate comprehensive metrics report."""
        return {
            "total_defects": len(self.df),
            "defect_escape_rate": round(self.defect_escape_rate(), 2),
            "mean_time_to_resolution_days": round(
                self.mean_time_to_resolution(), 2
            ),
            "severity_distribution": self.severity_distribution(),
            "stage_distribution": self.stage_distribution(),
            "defects_by_sprint": self.defects_by_sprint(),
            "escape_rate_by_sprint": self.escape_rate_by_sprint()
        }

    def plot_severity_distribution(self, save_path: str = None):
        """Create pie chart of severity distribution."""
        fig, ax = plt.subplots(figsize=(8, 6))

        severity_counts = self.df["severity"].value_counts()
        colors = ["#ff4444", "#ff8800", "#ffcc00", "#44aa44"]

        ax.pie(
            severity_counts.values,
            labels=severity_counts.index,
            autopct="%1.1f%%",
            colors=colors[:len(severity_counts)]
        )
        ax.set_title("Defect Severity Distribution")

        if save_path:
            plt.savefig(save_path)
        plt.close()

    def plot_escape_rate_trend(self, save_path: str = None):
        """Create line chart of escape rate trend by sprint."""
        fig, ax = plt.subplots(figsize=(10, 6))

        escape_rates = self.escape_rate_by_sprint()
        sprints = list(escape_rates.keys())
        rates = list(escape_rates.values())

        ax.plot(sprints, rates, marker="o", linewidth=2)
        ax.axhline(y=5, color="r", linestyle="--", label="Target (5%)")

        ax.set_xlabel("Sprint")
        ax.set_ylabel("Escape Rate (%)")
        ax.set_title("Defect Escape Rate Trend")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.xticks(rotation=45)
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
        plt.close()


# Example usage
if __name__ == "__main__":
    # Sample defects for demonstration
    sample_defects = [
        Defect(
            id="DEF-001",
            title="Login fails with special characters",
            severity=DefectSeverity.HIGH,
            found_stage=DefectStage.QA_TESTING,
            introduced_stage=DefectStage.DEVELOPMENT,
            created_date=datetime(2024, 1, 15),
            resolved_date=datetime(2024, 1, 17),
            sprint="Sprint 1"
        ),
        Defect(
            id="DEF-002",
            title="Data not saved on form submit",
            severity=DefectSeverity.CRITICAL,
            found_stage=DefectStage.PRODUCTION,
            introduced_stage=DefectStage.DEVELOPMENT,
            created_date=datetime(2024, 1, 20),
            resolved_date=datetime(2024, 1, 21),
            sprint="Sprint 1"
        ),
    ]

    calculator = DefectMetricsCalculator(sample_defects)
    report = calculator.generate_report()
    print(report)
