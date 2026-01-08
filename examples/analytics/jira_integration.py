"""
JIRA Integration for Defect Analysis.

This demonstrates the JIRA integration I built
for extracting defect data and generating metrics.
"""

import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth


@dataclass
class JiraConfig:
    """JIRA connection configuration."""
    base_url: str
    username: str
    api_token: str
    project_key: str


class JiraClient:
    """
    JIRA API client for defect data extraction.

    Provides methods to fetch issues, extract defect data,
    and integrate with the metrics calculator.
    """

    def __init__(self, config: JiraConfig):
        self.config = config
        self.auth = HTTPBasicAuth(config.username, config.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        json: dict = None
    ) -> dict:
        """Make authenticated request to JIRA API."""
        url = f"{self.config.base_url}/rest/api/3/{endpoint}"

        response = requests.request(
            method=method,
            url=url,
            auth=self.auth,
            headers=self.headers,
            params=params,
            json=json
        )
        response.raise_for_status()
        return response.json()

    def search_issues(
        self,
        jql: str,
        fields: list[str] = None,
        max_results: int = 100
    ) -> list[dict]:
        """
        Search issues using JQL.

        Args:
            jql: JIRA Query Language string
            fields: List of fields to return
            max_results: Maximum number of results

        Returns:
            List of issue dictionaries
        """
        fields = fields or [
            "summary", "status", "priority", "created",
            "resolutiondate", "labels", "customfield_10001"
        ]

        all_issues = []
        start_at = 0

        while True:
            response = self._make_request(
                "GET",
                "search",
                params={
                    "jql": jql,
                    "fields": ",".join(fields),
                    "startAt": start_at,
                    "maxResults": min(max_results - len(all_issues), 100)
                }
            )

            issues = response.get("issues", [])
            all_issues.extend(issues)

            if len(all_issues) >= response["total"]:
                break
            if len(all_issues) >= max_results:
                break

            start_at += len(issues)

        return all_issues

    def get_defects(
        self,
        sprint: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> list[dict]:
        """
        Fetch defect issues with optional filters.

        Args:
            sprint: Filter by sprint name
            date_from: Created after this date
            date_to: Created before this date

        Returns:
            List of defect issues
        """
        jql_parts = [
            f'project = "{self.config.project_key}"',
            'issuetype = Bug'
        ]

        if sprint:
            jql_parts.append(f'sprint = "{sprint}"')

        if date_from:
            jql_parts.append(
                f'created >= "{date_from.strftime("%Y-%m-%d")}"'
            )

        if date_to:
            jql_parts.append(
                f'created <= "{date_to.strftime("%Y-%m-%d")}"'
            )

        jql = " AND ".join(jql_parts)
        return self.search_issues(jql)

    def get_defects_by_environment(self, environment: str) -> list[dict]:
        """Fetch defects found in specific environment."""
        jql = (
            f'project = "{self.config.project_key}" '
            f'AND issuetype = Bug '
            f'AND labels = "{environment}"'
        )
        return self.search_issues(jql)

    def get_production_defects(self) -> list[dict]:
        """Fetch defects that escaped to production."""
        return self.get_defects_by_environment("production")


class JiraDefectExtractor:
    """
    Extract and transform JIRA data for metrics.

    Converts JIRA issue format to the format expected
    by the DefectMetricsCalculator.
    """

    SEVERITY_MAP = {
        "Highest": "Critical",
        "High": "High",
        "Medium": "Medium",
        "Low": "Low",
        "Lowest": "Low"
    }

    def __init__(self, client: JiraClient):
        self.client = client

    def extract_defects(
        self,
        sprint: str = None,
        date_from: datetime = None,
        date_to: datetime = None
    ) -> list[dict]:
        """
        Extract defects and transform to metrics format.

        Returns:
            List of defect dictionaries ready for metrics calculation
        """
        issues = self.client.get_defects(sprint, date_from, date_to)

        defects = []
        for issue in issues:
            fields = issue["fields"]

            defect = {
                "id": issue["key"],
                "title": fields["summary"],
                "severity": self._map_severity(fields.get("priority", {}).get("name")),
                "found_stage": self._determine_found_stage(fields.get("labels", [])),
                "created_date": self._parse_date(fields["created"]),
                "resolved_date": self._parse_date(fields.get("resolutiondate")),
                "sprint": self._extract_sprint(fields.get("customfield_10001"))
            }
            defects.append(defect)

        return defects

    def _map_severity(self, jira_priority: str) -> str:
        """Map JIRA priority to severity."""
        return self.SEVERITY_MAP.get(jira_priority, "Medium")

    def _determine_found_stage(self, labels: list[str]) -> str:
        """Determine stage where defect was found from labels."""
        stage_labels = {
            "production": "Production",
            "uat": "UAT",
            "qa": "QA Testing",
            "dev": "Development"
        }

        for label in labels:
            lower_label = label.lower()
            if lower_label in stage_labels:
                return stage_labels[lower_label]

        return "QA Testing"  # Default

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse JIRA date string."""
        if not date_str:
            return None
        # JIRA format: 2024-01-15T10:30:00.000+0000
        return datetime.fromisoformat(date_str.replace("+0000", "+00:00"))

    def _extract_sprint(self, sprint_field) -> Optional[str]:
        """Extract sprint name from JIRA sprint field."""
        if not sprint_field:
            return None
        if isinstance(sprint_field, list) and sprint_field:
            # Sprint field is usually a list of sprint strings
            sprint_str = sprint_field[0]
            # Extract name from sprint string
            if "name=" in sprint_str:
                start = sprint_str.find("name=") + 5
                end = sprint_str.find(",", start)
                return sprint_str[start:end]
        return None


# Example usage
if __name__ == "__main__":
    config = JiraConfig(
        base_url=os.getenv("JIRA_BASE_URL"),
        username=os.getenv("JIRA_USERNAME"),
        api_token=os.getenv("JIRA_API_TOKEN"),
        project_key="PROJ"
    )

    client = JiraClient(config)
    extractor = JiraDefectExtractor(client)

    # Extract defects from last sprint
    defects = extractor.extract_defects(sprint="Sprint 10")
    print(f"Found {len(defects)} defects")
