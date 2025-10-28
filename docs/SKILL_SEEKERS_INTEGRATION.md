# Skill_Seekers Integration Plan for MOTHRA

## Overview

[Skill_Seekers](https://github.com/yusufkaraaslan/Skill_Seekers/) is an automated tool that transforms documentation websites, GitHub repositories, and PDF files into production-ready Claude AI skills. This document outlines how to leverage Skill_Seekers to enhance MOTHRA's capabilities and create specialized Claude skills for carbon emissions data.

## What is Skill_Seekers?

Skill_Seekers automatically converts various information sources into packaged skill files that can be uploaded to Claude. It features:

- **Documentation Processing**: Automatic detection of LLM-ready files, universal web scraping, smart categorization
- **Multiple Data Sources**: Web documentation, PDFs with OCR, GitHub repositories
- **Performance**: Async mode for 2-3x faster scraping, support for 10K-40K+ page documentation
- **Quality Assurance**: 299 passing tests, MCP (Model Context Protocol) integration
- **Claude Integration**: Direct skill upload capabilities when API credentials are available

## Integration Goals

### 1. Carbon Data Source Documentation Skills

Create specialized Claude skills for each critical carbon data source, enabling Claude to:
- Understand specific API schemas and data structures
- Provide accurate guidance on accessing and querying data sources
- Help developers integrate with carbon data APIs

### 2. MOTHRA Codebase Skill

Generate a comprehensive skill from the MOTHRA repository itself, allowing Claude to:
- Understand the project architecture and agent system
- Provide accurate code assistance for MOTHRA development
- Guide users through database schemas and models
- Help troubleshoot issues based on actual codebase

### 3. Standards & Protocols Skills

Create skills from official documentation of carbon standards:
- GHG Protocol documentation
- ISO 14067 standards
- EN 15804+A2 EPD requirements
- IPCC methodology guides

## Critical Data Sources for Skill Creation

Based on `mothra/data/sources_catalog.yaml`, here are the 11 critical priority sources:

### Government APIs
1. **EPA MOVES** (Motor Vehicle Emission Simulator)
   - URL: https://www.epa.gov/moves
   - Documentation skill for vehicle emissions modeling

2. **EPA Greenhouse Gas Reporting Program**
   - URL: https://www.epa.gov/ghgreporting
   - Comprehensive facility-level GHG data

3. **UK DEFRA Conversion Factors**
   - URL: https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting
   - Annual emission factors for corporate reporting

4. **EIA (US Energy Information Administration) API**
   - URL: https://www.eia.gov/opendata
   - Energy data and carbon intensity information

5. **IPCC Emission Factor Database**
   - URL: https://www.ipcc-nggip.iges.or.jp/EFDB
   - Global emission factors methodology

6. **EU Emissions Trading System (ETS) Data**
   - URL: https://ec.europa.eu/clima/ets
   - European carbon market data

7. **ENTSO-E Transparency Platform**
   - URL: https://transparency.entsoe.eu
   - European electricity generation and carbon intensity

### LCA Databases
8. **Ecoinvent Database**
   - URL: https://ecoinvent.org/the-ecoinvent-database
   - Premium LCA data (requires license)

9. **USDA LCA Commons**
   - URL: https://www.lcacommons.gov
   - US government LCA database

### EPD Registries
10. **EC3 (Embodied Carbon in Construction Calculator)**
    - URL: https://buildingtransparency.org/ec3
    - 90,000+ verified construction material EPDs
    - API documentation: https://buildingtransparency.org/ec3/manage-apps/api-doc/api

## Implementation Plan

### Phase 1: Setup Skill_Seekers

```bash
# Clone Skill_Seekers repository
git clone https://github.com/yusufkaraaslan/Skill_Seekers.git
cd Skill_Seekers

# Install dependencies
pip install -r requirements.txt

# Configure for Claude Code MCP integration (optional)
# Follow MCP setup instructions in Skill_Seekers README
```

### Phase 2: Generate MOTHRA Project Skill

```bash
# Generate skill from MOTHRA GitHub repository
python skill_seeker.py \
  --source github \
  --url https://github.com/nickgogerty/Mothra \
  --name "MOTHRA Carbon Database" \
  --output ./skills/mothra.zip

# This creates a comprehensive skill covering:
# - Project architecture and design patterns
# - Agent system implementation
# - Database schemas and models
# - API integration patterns
# - Quality scoring algorithms
```

### Phase 3: Generate Data Source Documentation Skills

Create individual skills for each critical data source:

```bash
# EC3 API Documentation
python skill_seeker.py \
  --source web \
  --url https://buildingtransparency.org/ec3/manage-apps/api-doc/guide \
  --name "EC3 API Guide" \
  --output ./skills/ec3_api.zip

# EPA GHG Reporting Program
python skill_seeker.py \
  --source web \
  --url https://www.epa.gov/ghgreporting \
  --name "EPA GHG Reporting" \
  --output ./skills/epa_ghg.zip

# UK DEFRA Conversion Factors
python skill_seeker.py \
  --source web \
  --url https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting \
  --name "DEFRA Conversion Factors" \
  --output ./skills/defra_factors.zip

# EIA Open Data API
python skill_seeker.py \
  --source web \
  --url https://www.eia.gov/opendata \
  --name "EIA Open Data API" \
  --output ./skills/eia_api.zip

# IPCC Emission Factor Database
python skill_seeker.py \
  --source web \
  --url https://www.ipcc-nggip.iges.or.jp/EFDB \
  --name "IPCC Emission Factors" \
  --output ./skills/ipcc_efdb.zip
```

### Phase 4: Generate Standards Documentation Skills

```bash
# GHG Protocol Standards
python skill_seeker.py \
  --source web \
  --url https://ghgprotocol.org/standards \
  --name "GHG Protocol Standards" \
  --output ./skills/ghg_protocol.zip

# Download and process ISO standards PDFs (if available)
python skill_seeker.py \
  --source pdf \
  --path ./docs/ISO_14067_2018.pdf \
  --name "ISO 14067 Standard" \
  --output ./skills/iso_14067.zip
```

### Phase 5: Upload Skills to Claude

Once skills are generated, they can be:
1. Uploaded manually through Claude's interface
2. Automatically uploaded via Skill_Seekers with API credentials
3. Accessed through MCP in Claude Code

## Use Cases

### 1. Enhanced Data Source Integration

With data source skills loaded, Claude can:
- Provide exact API endpoint structures
- Generate correct authentication code
- Suggest optimal query patterns
- Troubleshoot API errors with specific documentation context

### 2. MOTHRA Development Assistance

With the MOTHRA codebase skill, Claude can:
- Suggest consistent code patterns matching the project style
- Help implement new agents following existing architecture
- Debug issues with full context of database models and schemas
- Recommend optimal integration points for new features

### 3. Standards Compliance Verification

With standards skills loaded, Claude can:
- Verify data collection methods comply with ISO 14067
- Check if GHG categorization follows the Protocol correctly
- Ensure EPD data includes all required EN 15804+A2 fields
- Validate calculation methodologies against IPCC guidelines

### 4. Automated Documentation Generation

Claude can generate accurate documentation by:
- Cross-referencing multiple data source skills
- Creating integration guides based on actual API documentation
- Writing tutorials that follow official standards
- Producing compliance reports with cited standards

## Integration with MOTHRA Agents

### Discovery Agent Enhancement

Add Skill_Seekers to the discovery workflow:

```python
# mothra/agents/discovery/skill_generator.py
"""Generate Claude skills for discovered data sources."""

import subprocess
from pathlib import Path
from typing import Optional

from mothra.db.models import DataSource


class SkillGenerator:
    """Generate Claude skills from data sources using Skill_Seekers."""

    def __init__(self, skill_seekers_path: Path, output_dir: Path):
        self.skill_seekers_path = skill_seekers_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_skill(self, source: DataSource) -> Optional[Path]:
        """Generate a Claude skill for a data source."""
        if not source.url:
            return None

        skill_name = f"{source.name.replace(' ', '_')}_skill"
        output_path = self.output_dir / f"{skill_name}.zip"

        # Build Skill_Seekers command
        cmd = [
            "python",
            str(self.skill_seekers_path / "skill_seeker.py"),
            "--source", "web",
            "--url", source.url,
            "--name", source.name,
            "--output", str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0 and output_path.exists():
                return output_path
            else:
                print(f"Failed to generate skill for {source.name}: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"Timeout generating skill for {source.name}")
            return None
        except Exception as e:
            print(f"Error generating skill for {source.name}: {e}")
            return None

    async def generate_all_critical_skills(self) -> list[Path]:
        """Generate skills for all critical priority data sources."""
        from sqlalchemy import select
        from mothra.db.session import get_db_context

        skills = []

        async with get_db_context() as session:
            stmt = select(DataSource).where(DataSource.priority == "critical")
            result = await session.execute(stmt)
            sources = result.scalars().all()

            for source in sources:
                print(f"Generating skill for {source.name}...")
                skill_path = await self.generate_skill(source)
                if skill_path:
                    skills.append(skill_path)
                    print(f"  ✓ Generated: {skill_path}")

        return skills
```

### Workflow Integration

Add skill generation to the orchestrator:

```python
# Add to mothra/orchestrator.py

async def generate_data_source_skills(self):
    """Generate Claude skills for all critical data sources."""
    from mothra.agents.discovery.skill_generator import SkillGenerator

    skill_seekers_path = Path("../Skill_Seekers")  # Adjust path as needed
    output_dir = self.settings.data_dir / "skills"

    generator = SkillGenerator(skill_seekers_path, output_dir)
    skills = await generator.generate_all_critical_skills()

    self.logger.info(f"Generated {len(skills)} Claude skills")
    return skills
```

## Benefits

### For Developers

1. **Faster Integration**: Claude provides accurate code examples based on actual documentation
2. **Fewer Errors**: API calls match exact specifications from source documentation
3. **Better Debugging**: Context-aware troubleshooting with knowledge of data structures
4. **Consistent Patterns**: Code suggestions follow project conventions

### For Data Quality

1. **Standards Compliance**: Automated verification against loaded standard documentation
2. **Accurate Transformations**: Data mapping guided by official schemas
3. **Complete Coverage**: Skills ensure all required fields are captured
4. **Validation Rules**: Generate validation code based on standard requirements

### For Maintenance

1. **Living Documentation**: Skills update as documentation changes
2. **Onboarding**: New team members can query Claude about any data source
3. **Knowledge Retention**: Institutional knowledge captured in searchable skills
4. **Cross-referencing**: Find connections between different standards and sources

## Automation Script

Create a comprehensive automation script:

```bash
#!/bin/bash
# scripts/generate_all_skills.sh

set -e

SKILL_SEEKERS_PATH="../Skill_Seekers"
OUTPUT_DIR="./mothra/data/skills"

mkdir -p "$OUTPUT_DIR"

echo "Generating MOTHRA project skill..."
python "$SKILL_SEEKERS_PATH/skill_seeker.py" \
  --source github \
  --url https://github.com/nickgogerty/Mothra \
  --name "MOTHRA Carbon Database" \
  --output "$OUTPUT_DIR/mothra.zip"

echo "Generating critical data source skills..."

# EC3 API
python "$SKILL_SEEKERS_PATH/skill_seeker.py" \
  --source web \
  --url https://buildingtransparency.org/ec3/manage-apps/api-doc/guide \
  --name "EC3 API Guide" \
  --output "$OUTPUT_DIR/ec3_api.zip"

# EPA GHG
python "$SKILL_SEEKERS_PATH/skill_seeker.py" \
  --source web \
  --url https://www.epa.gov/ghgreporting \
  --name "EPA GHG Reporting" \
  --output "$OUTPUT_DIR/epa_ghg.zip"

# Add more sources as needed...

echo "All skills generated successfully!"
echo "Skills location: $OUTPUT_DIR"
```

## Next Steps

1. **Install Skill_Seekers**: Clone and set up the repository
2. **Generate Core Skills**: Start with MOTHRA project and EC3 API
3. **Test with Claude**: Upload skills and verify improved assistance
4. **Automate Generation**: Set up periodic skill updates as documentation changes
5. **Integrate with CI/CD**: Generate skills as part of the build process
6. **Expand Coverage**: Add skills for all 100+ data sources progressively

## Resources

- **Skill_Seekers Repository**: https://github.com/yusufkaraaslan/Skill_Seekers/
- **MCP Documentation**: For Claude Code integration
- **MOTHRA Data Sources**: `mothra/data/sources_catalog.yaml`
- **API Documentation Links**: Listed in each data source entry

## Maintenance

- **Weekly**: Regenerate skills for frequently updated APIs (e.g., EC3, EIA)
- **Monthly**: Full refresh of all critical source skills
- **On Release**: Update MOTHRA project skill when new versions are released
- **As Needed**: Generate new skills when adding data sources to the catalog

---

**Note**: Skill_Seekers provides powerful automation for creating Claude skills. By systematically generating skills for all carbon data sources, MOTHRA can significantly enhance developer productivity and data quality assurance.
