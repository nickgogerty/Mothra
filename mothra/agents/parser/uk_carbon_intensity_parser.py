"""
UK Carbon Intensity API Parser.

Parses real-time electricity grid carbon intensity data from the UK National Grid.
API Documentation: https://carbon-intensity.github.io/api-definitions/

Example API response:
{
  "data": [
    {
      "from": "2024-10-25T16:00Z",
      "to": "2024-10-25T16:30Z",
      "intensity": {
        "forecast": 195,
        "actual": 200,
        "index": "moderate"
      }
    }
  ]
}
"""

import json
from datetime import datetime
from typing import Any

from mothra.agents.parser.base_parser import BaseParser
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class UKCarbonIntensityParser(BaseParser):
    """Parser for UK Carbon Intensity API data."""

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse UK Carbon Intensity API response.

        Args:
            data: Raw API response (JSON string, bytes, or dict)

        Returns:
            List of entity dictionaries for carbon intensity readings
        """
        # Parse JSON if needed
        if isinstance(data, (str, bytes)):
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            json_data = json.loads(data)
        else:
            json_data = data

        entities = []

        # Extract intensity data points
        data_points = json_data.get("data", [])

        for point in data_points:
            # Extract time range
            time_from = point.get("from", "")
            time_to = point.get("to", "")

            # Extract intensity data
            intensity = point.get("intensity", {})
            forecast = intensity.get("forecast")
            actual = intensity.get("actual")
            index = intensity.get("index", "unknown")

            # Use actual if available, otherwise forecast
            intensity_value = actual if actual is not None else forecast

            if intensity_value is None:
                continue

            # Create entity for this data point
            entity = self.create_entity_dict(
                name=f"UK Grid Carbon Intensity {time_from}",
                description=f"UK electricity grid carbon intensity from {time_from} to {time_to}. "
                           f"Intensity: {intensity_value} gCO2/kWh ({index} level)",
                entity_type="energy",
                category_hierarchy=["energy", "electricity", "grid", "uk"],
                geographic_scope=["UK"],
                quality_score=0.95,  # High quality - official government data
                custom_tags=["electricity", "grid", "carbon_intensity", "uk", "realtime"],
                # Additional metadata
                time_from=time_from,
                time_to=time_to,
                intensity_forecast=forecast,
                intensity_actual=actual,
                intensity_index=index,
                unit="gCO2/kWh",
                data_type="grid_intensity",
                raw_data=point,
            )

            entities.append(entity)

        logger.info(
            "uk_carbon_intensity_parsed",
            total_entities=len(entities),
            source=self.source.name,
        )

        return entities
