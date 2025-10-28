#!/usr/bin/env python3
"""
Standalone Government Emissions Data Downloader and Parser

Downloads and parses emissions data from government sources WITHOUT requiring a database.
Outputs parsed data to JSON files for later ingestion.

This is useful for:
- Testing and development
- Offline data collection
- Pre-processing before database ingestion

Usage:
    python scripts/download_government_data.py --sources all
    python scripts/download_government_data.py --sources EPA_SUPPLY_CHAIN_V13
    python scripts/download_government_data.py --list
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

import aiohttp
import pandas as pd

# Government data sources configuration
GOVERNMENT_SOURCES = {
    "EPA_SUPPLY_CHAIN_V13": {
        "name": "EPA Supply Chain GHG Emission Factors v1.3 NAICS",
        "url": "https://pasteur.epa.gov/uploads/10.23719/1531143/SupplyChainGHGEmissionFactors_v1.3.0_NAICS_byGHG_USD2022.csv",
        "format": "csv",
        "description": "1,016 US commodity emission factors by NAICS-6",
    },
    "UK_DEFRA_2025": {
        "name": "UK DEFRA 2025 GHG Conversion Factors",
        "scrape_url": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025",
        "format": "excel",
        "description": "UK government GHG conversion factors (2025)",
        "note": "Requires web scraping to find download link",
    },
    "EPA_EGRID_2024": {
        "name": "EPA eGRID 2024 Emission Factors",
        "url": "https://www.epa.gov/egrid/download-data",
        "format": "excel",
        "description": "US electricity grid emission factors",
        "note": "Requires web scraping to find download link",
    },
}


class GovernmentDataDownloader:
    """Download and parse government emissions data to JSON files."""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("./data/government_emissions")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir = self.output_dir / "downloads"
        self.downloads_dir.mkdir(exist_ok=True)
        self.parsed_dir = self.output_dir / "parsed"
        self.parsed_dir.mkdir(exist_ok=True)
        self.session = None
        self.stats = {
            "downloaded": 0,
            "parsed": 0,
            "failed": 0,
            "total_records": 0,
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),
            headers={"User-Agent": "MOTHRA-Carbon-Data-Crawler/1.0"},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def download_file(self, url: str, filename: str) -> Path | None:
        """Download a file from URL."""
        filepath = self.downloads_dir / filename

        if filepath.exists():
            print(f"✓ File already exists: {filename}")
            return filepath

        print(f"⬇ Downloading: {filename}")
        print(f"  URL: {url}")

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    print(f"✗ Download failed: HTTP {response.status}")
                    return None

                content = await response.read()
                with open(filepath, "wb") as f:
                    f.write(content)

                size_mb = len(content) / (1024 * 1024)
                print(f"✓ Downloaded: {filename} ({size_mb:.2f} MB)")
                self.stats["downloaded"] += 1
                return filepath

        except Exception as e:
            print(f"✗ Download error: {e}")
            self.stats["failed"] += 1
            return None

    async def scrape_download_link(self, page_url: str, patterns: list[str]) -> str | None:
        """Scrape a page for download links matching patterns."""
        print(f"🔍 Scraping: {page_url}")

        try:
            async with self.session.get(page_url) as response:
                if response.status != 200:
                    print(f"✗ Scraping failed: HTTP {response.status}")
                    return None

                html = await response.text()

                import re

                # Find all links
                link_pattern = r'href=["\']([^"\']*)["\']'
                links = re.findall(link_pattern, html, re.IGNORECASE)

                # Filter by patterns
                for link in links:
                    if any(pattern.lower() in link.lower() for pattern in patterns):
                        # Convert relative to absolute URL
                        if link.startswith("/"):
                            from urllib.parse import urljoin

                            link = urljoin(page_url, link)
                        print(f"✓ Found link: {link}")
                        return link

                print("✗ No matching download link found")
                return None

        except Exception as e:
            print(f"✗ Scraping error: {e}")
            return None

    def parse_csv_to_json(self, filepath: Path, source_name: str) -> dict:
        """Parse CSV file to JSON structure."""
        print(f"📊 Parsing CSV: {filepath.name}")

        try:
            df = pd.read_csv(filepath)

            records = []
            for idx, row in df.iterrows():
                record = {
                    "id": f"{source_name}_{idx}",
                    "source": source_name,
                    "data": row.to_dict(),
                    "parsed_at": datetime.utcnow().isoformat(),
                }
                records.append(record)

            result = {
                "source": source_name,
                "file": filepath.name,
                "format": "csv",
                "total_records": len(records),
                "columns": list(df.columns),
                "records": records,
                "metadata": {
                    "parsed_at": datetime.utcnow().isoformat(),
                    "file_size_bytes": filepath.stat().st_size,
                },
            }

            print(f"✓ Parsed {len(records)} records from CSV")
            self.stats["parsed"] += 1
            self.stats["total_records"] += len(records)
            return result

        except Exception as e:
            print(f"✗ Parse error: {e}")
            self.stats["failed"] += 1
            return {}

    def parse_excel_to_json(self, filepath: Path, source_name: str) -> dict:
        """Parse Excel file to JSON structure."""
        print(f"📊 Parsing Excel: {filepath.name}")

        try:
            # Read all sheets
            excel_data = pd.read_excel(filepath, sheet_name=None)

            all_records = []
            sheets_info = {}

            for sheet_name, df in excel_data.items():
                print(f"  Sheet: {sheet_name} ({len(df)} rows)")

                sheet_records = []
                for idx, row in df.iterrows():
                    record = {
                        "id": f"{source_name}_{sheet_name}_{idx}",
                        "source": source_name,
                        "sheet": sheet_name,
                        "data": row.to_dict(),
                        "parsed_at": datetime.utcnow().isoformat(),
                    }
                    sheet_records.append(record)
                    all_records.append(record)

                sheets_info[sheet_name] = {
                    "rows": len(df),
                    "columns": list(df.columns),
                    "records": len(sheet_records),
                }

            result = {
                "source": source_name,
                "file": filepath.name,
                "format": "excel",
                "total_records": len(all_records),
                "sheets": sheets_info,
                "records": all_records,
                "metadata": {
                    "parsed_at": datetime.utcnow().isoformat(),
                    "file_size_bytes": filepath.stat().st_size,
                },
            }

            print(f"✓ Parsed {len(all_records)} total records from {len(excel_data)} sheets")
            self.stats["parsed"] += 1
            self.stats["total_records"] += len(all_records)
            return result

        except Exception as e:
            print(f"✗ Parse error: {e}")
            self.stats["failed"] += 1
            return {}

    def save_json(self, data: dict, source_id: str) -> None:
        """Save parsed data to JSON file."""
        if not data:
            return

        output_file = self.parsed_dir / f"{source_id}.json"
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"💾 Saved: {output_file}")

    async def process_source(self, source_id: str, source_info: dict) -> bool:
        """Process a single data source."""
        print(f"\n{'=' * 80}")
        print(f"Processing: {source_info['name']}")
        print(f"{'=' * 80}")

        # Handle direct download URLs
        if "url" in source_info:
            filename = f"{source_id}_{datetime.now().strftime('%Y%m%d')}.{source_info['format']}"
            filepath = await self.download_file(source_info["url"], filename)

            if not filepath:
                return False

            # Parse based on format
            if source_info["format"] == "csv":
                parsed_data = self.parse_csv_to_json(filepath, source_id)
            elif source_info["format"] == "excel":
                parsed_data = self.parse_excel_to_json(filepath, source_id)
            else:
                print(f"⚠ Unsupported format: {source_info['format']}")
                return False

            # Save parsed data
            if parsed_data:
                self.save_json(parsed_data, source_id)
                return True

        # Handle scraping for download links
        elif "scrape_url" in source_info:
            print(f"⚠ Web scraping required for {source_id}")
            print(f"  Manual download from: {source_info['scrape_url']}")
            return False

        return False

    async def run(self, source_ids: list[str] | None = None) -> None:
        """Run downloader for specified sources."""
        sources_to_process = {}

        if source_ids is None or "all" in source_ids:
            sources_to_process = GOVERNMENT_SOURCES
        else:
            for source_id in source_ids:
                if source_id in GOVERNMENT_SOURCES:
                    sources_to_process[source_id] = GOVERNMENT_SOURCES[source_id]
                else:
                    print(f"⚠ Unknown source: {source_id}")

        print(f"\n📦 Processing {len(sources_to_process)} source(s)")

        for source_id, source_info in sources_to_process.items():
            await self.process_source(source_id, source_info)

        # Print summary
        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")
        print(f"Downloaded:     {self.stats['downloaded']}")
        print(f"Parsed:         {self.stats['parsed']}")
        print(f"Failed:         {self.stats['failed']}")
        print(f"Total Records:  {self.stats['total_records']:,}")
        print(f"\nOutput directory: {self.output_dir.absolute()}")
        print(f"{'=' * 80}\n")


def list_sources():
    """List available data sources."""
    print("\nAvailable Government Emissions Data Sources:\n")
    print(f"{'ID':<25} {'Format':<10} {'Name':<50}")
    print("-" * 85)
    for source_id, info in GOVERNMENT_SOURCES.items():
        print(f"{source_id:<25} {info['format']:<10} {info['name']:<50}")
    print(f"\nTotal: {len(GOVERNMENT_SOURCES)} sources")
    print("\nNotes:")
    for source_id, info in GOVERNMENT_SOURCES.items():
        if "note" in info:
            print(f"  {source_id}: {info['note']}")


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Download and parse government emissions data"
    )
    parser.add_argument(
        "--sources",
        help="Comma-separated list of source IDs, or 'all'",
        default="EPA_SUPPLY_CHAIN_V13",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available sources and exit"
    )
    parser.add_argument(
        "--output", help="Output directory", default="./data/government_emissions"
    )

    args = parser.parse_args()

    if args.list:
        list_sources()
        return

    source_ids = args.sources.split(",") if args.sources != "all" else None

    async with GovernmentDataDownloader(Path(args.output)) as downloader:
        await downloader.run(source_ids)


if __name__ == "__main__":
    asyncio.run(main())
