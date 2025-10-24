"""
Data Quality Scorer: Multi-dimensional quality assessment.

Evaluates carbon data across five dimensions:
- Completeness: Are required fields present?
- Accuracy: Does the data pass sanity checks?
- Consistency: Is the data internally consistent?
- Timeliness: Is the data current?
- Provenance: Is the source credible?
"""

from datetime import datetime, timedelta
from typing import Any

from mothra.config import settings
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class DataQualityScorer:
    """Multi-dimensional quality assessment for carbon data."""

    def __init__(self) -> None:
        self.required_fields = ["value", "unit", "scope", "source_id"]
        self.optional_fields = ["uncertainty_min", "uncertainty_max", "methodology", "temporal_validity"]
        self.weights = {
            "completeness": 0.25,
            "accuracy": 0.30,
            "consistency": 0.20,
            "timeliness": 0.15,
            "provenance": 0.10,
        }

    def calculate_quality_score(self, data_entry: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate overall quality score across all dimensions.

        Args:
            data_entry: Data entry to score

        Returns:
            Dictionary with scores and confidence level
        """
        scores = {
            "completeness": self.assess_completeness(data_entry),
            "accuracy": self.assess_accuracy(data_entry),
            "consistency": self.assess_consistency(data_entry),
            "timeliness": self.assess_timeliness(data_entry),
            "provenance": self.assess_provenance(data_entry),
        }

        weighted_score = sum(scores[dim] * self.weights[dim] for dim in scores)

        confidence_level = self.get_confidence_level(weighted_score)

        logger.debug(
            "quality_score_calculated",
            overall=weighted_score,
            confidence=confidence_level,
            dimensions=scores,
        )

        return {
            "overall_score": weighted_score,
            "dimensions": scores,
            "confidence_level": confidence_level,
            "passes_threshold": weighted_score >= settings.min_quality_score,
        }

    def assess_completeness(self, data: dict[str, Any]) -> float:
        """
        Assess data completeness.

        Args:
            data: Data entry

        Returns:
            Completeness score (0.0 to 1.0)
        """
        required_complete = sum(
            1 for field in self.required_fields if data.get(field) is not None
        ) / len(self.required_fields)

        optional_complete = sum(
            1 for field in self.optional_fields if data.get(field) is not None
        ) / len(self.optional_fields)

        # Weighted: required fields 70%, optional fields 30%
        return required_complete * 0.7 + optional_complete * 0.3

    def assess_accuracy(self, data: dict[str, Any]) -> float:
        """
        Assess data accuracy through sanity checks.

        Args:
            data: Data entry

        Returns:
            Accuracy score (0.0 to 1.0)
        """
        checks_passed = 0
        total_checks = 0

        # Check 1: Value is positive
        if "value" in data:
            total_checks += 1
            try:
                if float(data["value"]) >= 0:
                    checks_passed += 1
            except (ValueError, TypeError):
                pass

        # Check 2: Unit is recognized
        if "unit" in data:
            total_checks += 1
            valid_units = ["kgCO2e", "tCO2e", "gCO2e", "kgCO2", "tCO2"]
            if any(unit in str(data["unit"]) for unit in valid_units):
                checks_passed += 1

        # Check 3: Scope is valid (1, 2, or 3)
        if "scope" in data:
            total_checks += 1
            try:
                if int(data["scope"]) in [1, 2, 3]:
                    checks_passed += 1
            except (ValueError, TypeError):
                pass

        # Check 4: Uncertainty range is logical
        if "uncertainty_min" in data and "uncertainty_max" in data:
            total_checks += 1
            try:
                if float(data["uncertainty_min"]) <= float(data["uncertainty_max"]):
                    checks_passed += 1
            except (ValueError, TypeError):
                pass

        if total_checks == 0:
            return 0.5  # Neutral score if no checks could be performed

        return checks_passed / total_checks

    def assess_consistency(self, data: dict[str, Any]) -> float:
        """
        Assess internal consistency.

        Args:
            data: Data entry

        Returns:
            Consistency score (0.0 to 1.0)
        """
        score = 1.0

        # Check consistency between value and uncertainty range
        if all(k in data for k in ["value", "uncertainty_min", "uncertainty_max"]):
            try:
                value = float(data["value"])
                min_val = float(data["uncertainty_min"])
                max_val = float(data["uncertainty_max"])

                # Value should be within uncertainty range
                if not (min_val <= value <= max_val):
                    score -= 0.3
            except (ValueError, TypeError):
                score -= 0.2

        # Check consistency between entity type and scope
        entity_type = data.get("entity_type", "")
        scope = data.get("scope")

        # Example: Energy entities typically have scope 2
        if entity_type == "energy" and scope and int(scope) != 2:
            score -= 0.1

        return max(0.0, score)

    def assess_timeliness(self, data: dict[str, Any]) -> float:
        """
        Assess data timeliness.

        Args:
            data: Data entry

        Returns:
            Timeliness score (0.0 to 1.0)
        """
        # Check if temporal validity is provided
        if "temporal_validity" not in data and "year" not in data:
            return 0.5  # Neutral score if no temporal info

        try:
            # Get data year
            year = None
            if "year" in data:
                year = int(data["year"])
            elif "temporal_validity" in data:
                # Extract year from temporal validity
                validity = data["temporal_validity"]
                if isinstance(validity, dict) and "start" in validity:
                    year = int(validity["start"][:4])

            if year is None:
                return 0.5

            current_year = datetime.now().year
            age_years = current_year - year

            # Score decreases with age
            if age_years <= 1:
                return 1.0
            elif age_years <= 3:
                return 0.8
            elif age_years <= 5:
                return 0.6
            elif age_years <= 10:
                return 0.4
            else:
                return 0.2

        except (ValueError, TypeError, KeyError):
            return 0.5

    def assess_provenance(self, data: dict[str, Any]) -> float:
        """
        Assess data provenance/credibility.

        Args:
            data: Data entry

        Returns:
            Provenance score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Check if source is known
        source = data.get("source", "").lower()

        # High credibility sources
        high_credibility = [
            "epa",
            "defra",
            "ipcc",
            "ecoinvent",
            "iso",
            "ghg protocol",
            "government",
        ]
        if any(src in source for src in high_credibility):
            score += 0.3

        # Check if methodology is documented
        if "methodology" in data or "calculation_method" in data:
            score += 0.1

        # Check if source URL is provided
        if "source_url" in data:
            score += 0.1

        return min(1.0, score)

    def get_confidence_level(self, score: float) -> str:
        """
        Convert score to confidence level.

        Args:
            score: Quality score (0.0 to 1.0)

        Returns:
            Confidence level string
        """
        if score >= 0.9:
            return "very_high"
        elif score >= 0.8:
            return "high"
        elif score >= 0.7:
            return "medium"
        elif score >= 0.5:
            return "low"
        else:
            return "very_low"
