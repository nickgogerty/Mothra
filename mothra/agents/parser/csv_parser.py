"""CSV parser for carbon data."""

from io import StringIO
from typing import Any

import pandas as pd

from mothra.agents.parser.base_parser import BaseParser


class CSVParser(BaseParser):
    """Parser for CSV-formatted carbon data."""

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse CSV data.

        Args:
            data: CSV string or file path

        Returns:
            List of parsed entities
        """
        try:
            if isinstance(data, str):
                # Try as CSV string first
                try:
                    df = pd.read_csv(StringIO(data))
                except Exception:
                    # Try as file path
                    df = pd.read_csv(data)
            else:
                df = pd.DataFrame(data)

            # Convert DataFrame to list of dicts
            records = df.to_dict(orient="records")

            return [self.standardize_entity(record) for record in records]

        except Exception as e:
            self.logger.error("csv_parse_error", error=str(e))
            return []
