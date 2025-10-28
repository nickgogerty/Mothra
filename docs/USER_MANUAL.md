# 🌍 MOTHRA Emissions Factor Lookup Tool - User Manual

Welcome to MOTHRA (Mapping Operational Transparency for High-Resolution Assessments)! This friendly guide will help you find emissions factors quickly and easily using our semantic search technology.

## 📚 Table of Contents

- [What is MOTHRA?](#what-is-mothra)
- [Quick Start Guide](#quick-start-guide)
- [Available Data Sources](#available-data-sources)
- [How to Search](#how-to-search)
- [Understanding Results](#understanding-results)
- [Advanced Features](#advanced-features)
- [Example Searches](#example-searches)
- [Tips & Tricks](#tips--tricks)
- [Troubleshooting](#troubleshooting)

---

## 🎯 What is MOTHRA?

MOTHRA is an intelligent carbon emissions database that uses **semantic search** to help you find emissions factors. Unlike traditional keyword searches, MOTHRA understands the *meaning* of your queries, so you can search naturally - just like asking a colleague!

### Key Features:
- 🔍 **Natural Language Search** - Search using everyday language
- 🎯 **Smart Matching** - Finds relevant data even without exact keywords
- 📊 **Standardized Units** - Returns emissions in CO2e per reference unit
- 🌐 **Multiple Data Sources** - Integrates government and industry data
- ⚡ **Fast Results** - Instant semantic similarity matching

---

## 🚀 Quick Start Guide

### 1. Basic Search

The simplest way to search is with the `search_emissions_factors.py` script:

```bash
python scripts/search_emissions_factors.py "what you're looking for"
```

**Example:**
```bash
python scripts/search_emissions_factors.py "coal power plant"
```

### 2. View Your Results

Results show:
- ✅ Similarity score (0-1, higher is better)
- 📊 **Emission Factor** (value + units)
- 📍 Location, fuel type, sector
- 📅 Time period

### 3. Refine Your Search

Add options to get better results:
```bash
# Get more results
python scripts/search_emissions_factors.py "steel" -n 20

# Show detailed information
python scripts/search_emissions_factors.py "california energy" -d

# Filter by minimum similarity
python scripts/search_emissions_factors.py "natural gas" -s 0.5
```

---

## 📊 Available Data Sources

MOTHRA currently integrates the following data sources:

### 1. 🏛️ **EIA (Energy Information Administration) - SEDS**

**Source:** U.S. Energy Information Administration State Energy Data System
**Coverage:** United States, state-level data
**Years:** 1960-2023 (varies by series)
**Update Frequency:** Annual

**Data Points Include:**
- ✅ **CO2 Emissions by Fuel Type**
  - Coal emissions (all sectors + sector-specific)
  - Natural gas emissions (all sectors + sector-specific)
  - Petroleum emissions (all sectors + sector-specific)
  - Total fossil fuel emissions

- ✅ **CO2 Emissions by Sector**
  - Electric Power Sector
  - Industrial Sector
  - Commercial Sector
  - Residential Sector
  - Transportation Sector
  - Total (All Sectors)

- ✅ **Carbon Intensity Metrics**
  - CO2 per GDP (Metric tons CO2 per million dollars)
  - CO2 per Energy (Metric tons CO2 per billion Btu)
  - Per Capita CO2 emissions (Metric tons per person)

**Units Available:**
- Metric tons CO2 per billion Btu
- Metric tons CO2 per million chained (2017) dollars
- Metric tons CO2 per capita
- Million metric tons CO2 (total emissions)

**Geographic Coverage:**
- All 50 U.S. States
- District of Columbia
- U.S. National totals

**Example Data Points:**
```
California Coal Emissions (Industrial Sector): 2.8 million metric tons CO2 (2023)
Texas Total CO2 Intensity: 319.5 metric tons CO2/million $ GDP (2023)
Vermont Per Capita Emissions: 8.3 metric tons CO2/person (2023)
```

### 2. 🏭 **EIA Facility-Level Data**

**Source:** EIA Electricity Facility Fuel Data
**Coverage:** 15,000+ U.S. power plants
**Years:** 2001-2024
**Update Frequency:** Monthly/Annual

**Data Points Include:**
- ✅ Fuel consumption by facility
- ✅ Electricity generation by facility
- ✅ Fuel types (Coal, Natural Gas, Petroleum, Nuclear, Renewables)
- ✅ Plant location (state, county)
- ✅ Prime mover type (turbine, generator type)

**Units Available:**
- MMBtu (fuel consumption)
- MWh (electricity generation)
- Calculated: MMBtu/MWh (heat rate/efficiency)

### 3. 🌍 **EC3 (Embodied Carbon in Construction) Database**

**Source:** Building Transparency / EC3
**Coverage:** Global construction materials and products
**Update Frequency:** Continuous (crowdsourced + verified EPDs)

**Data Points Include:**
- ✅ Building materials (steel, concrete, timber, glass, etc.)
- ✅ Environmental Product Declarations (EPDs)
- ✅ Embodied carbon (manufacturing + transport)
- ✅ Product-specific impacts

**Units Available:**
- kg CO2e per unit (kg, m³, m², etc.)
- Varies by material and product type

### 4. 📚 **EPA & Other Government Datasets**

**Coverage:** Various environmental datasets
**Data Points Include:**
- Process emissions
- Transportation emissions
- Waste management
- Industrial activities

---

## 🔍 How to Search

### Natural Language Queries

MOTHRA understands natural language, so search like you're talking to a person:

**Good Examples:**
- ✅ "coal power plant emissions in Texas"
- ✅ "natural gas heating residential"
- ✅ "steel production carbon footprint"
- ✅ "California electricity generation"
- ✅ "transportation fuel emissions"

**Also Works:**
- ✅ Single words: "coal", "steel", "concrete"
- ✅ Technical terms: "blast furnace", "CCGT", "embodied carbon"
- ✅ Locations: "California", "Pacific Northwest", "USA"
- ✅ Sectors: "industrial", "residential", "transport"

### Search Syntax

```bash
python scripts/search_emissions_factors.py "YOUR QUERY" [OPTIONS]
```

**Options:**
- `-n NUMBER` or `--limit NUMBER` - Number of results (default: 10)
- `-s SCORE` or `--min-similarity SCORE` - Minimum similarity 0-1 (default: 0.0)
- `-d` or `--details` - Show detailed information
- `-h` or `--help` - Show help message

**Examples:**
```bash
# Basic search
python scripts/search_emissions_factors.py "coal"

# Get 5 results with details
python scripts/search_emissions_factors.py "natural gas" -n 5 -d

# Only show highly relevant results (similarity > 0.5)
python scripts/search_emissions_factors.py "steel" -s 0.5
```

---

## 📈 Understanding Results

### Result Format

Each result shows:

```
1. [0.746] Texas - All Fuels CO2 Emissions (All Sectors, 2023)
   Type: emission

   📊 EMISSION FACTOR:
      Value: 319.50 Metric tons CO2 per million chained (2017) dollars
      Period: 2023
      Fuel: All Fuels
      Sector: All Sectors
      Location: Texas
```

### What Each Field Means:

1. **[0.746]** - Similarity Score
   - Range: 0.0 to 1.0
   - **0.7+** = Excellent match
   - **0.5-0.7** = Good match
   - **0.3-0.5** = Moderate match
   - **<0.3** = Weak match (may not be relevant)

2. **Entity Name** - Descriptive title of the data point

3. **Type** - Entity classification:
   - `emission` - CO2 emission data
   - `process` - Industrial/energy process
   - `material` - Construction material or product
   - `energy` - Energy generation/consumption

4. **📊 EMISSION FACTOR** - The actual emissions data:
   - **Value** - Numeric emission factor
   - **Unit** - CO2e per reference unit
   - **Period** - Year or time period
   - **Fuel** - Fuel type (if applicable)
   - **Sector** - Economic sector
   - **Location** - Geographic region

### Common Units Explained:

| Unit | Meaning | Use Case |
|------|---------|----------|
| Metric tons CO2 per billion Btu | CO2 per energy consumed | Energy efficiency, fuel comparison |
| Metric tons CO2 per million $ GDP | CO2 per economic output | Carbon intensity of economy |
| Metric tons CO2 per capita | CO2 per person | Population-based comparisons |
| Million metric tons CO2 | Total emissions | Absolute emission quantities |
| kg CO2e per kg | Embodied carbon per mass | Material comparisons |
| kg CO2e per m³ | Embodied carbon per volume | Bulk materials (concrete, etc.) |
| MMBtu per MWh | Heat rate/efficiency | Power plant efficiency |

---

## 🎨 Advanced Features

### 1. Filtering by Entity Type

Use the general search tool to filter by type:

```bash
python scripts/search_entities.py "renewable energy" --type emission -n 10
```

**Entity Types:**
- `emission` - Emission factors and CO2 data
- `process` - Industrial processes, energy generation
- `material` - Construction materials, products
- `energy` - Energy systems
- `transport` - Transportation modes

### 2. Detailed Information

Add `-d` flag to see:
- Full descriptions
- Category hierarchies
- Custom tags
- Additional metadata

```bash
python scripts/search_emissions_factors.py "coal" -d
```

### 3. Adjusting Relevance Threshold

Filter out weak matches:

```bash
# Only show results with >50% similarity
python scripts/search_emissions_factors.py "steel production" -s 0.5

# Only show excellent matches (>70% similarity)
python scripts/search_emissions_factors.py "natural gas" -s 0.7
```

### 4. Large Result Sets

Get more results for comprehensive analysis:

```bash
# Get top 50 results
python scripts/search_emissions_factors.py "electricity generation" -n 50
```

---

## 💡 Example Searches

### By Fuel Type

```bash
# Coal emissions
python scripts/search_emissions_factors.py "coal emissions"

# Natural gas emissions
python scripts/search_emissions_factors.py "natural gas co2"

# Petroleum products
python scripts/search_emissions_factors.py "petroleum emissions"

# All fossil fuels
python scripts/search_emissions_factors.py "fossil fuel carbon"
```

### By Sector

```bash
# Industrial sector
python scripts/search_emissions_factors.py "industrial emissions"

# Residential buildings
python scripts/search_emissions_factors.py "residential heating emissions"

# Commercial sector
python scripts/search_emissions_factors.py "commercial building energy"

# Transportation
python scripts/search_emissions_factors.py "transportation fuel emissions"

# Electric power
python scripts/search_emissions_factors.py "electricity generation carbon"
```

### By Location

```bash
# State-level data
python scripts/search_emissions_factors.py "california emissions"
python scripts/search_emissions_factors.py "texas energy carbon"

# Regional queries
python scripts/search_emissions_factors.py "pacific northwest electricity"

# National data
python scripts/search_emissions_factors.py "usa total emissions"
```

### By Process/Material

```bash
# Steel production
python scripts/search_emissions_factors.py "steel manufacturing"

# Concrete
python scripts/search_emissions_factors.py "concrete carbon footprint"

# Aluminum
python scripts/search_emissions_factors.py "aluminum production emissions"

# Glass manufacturing
python scripts/search_emissions_factors.py "glass embodied carbon"
```

### Combination Queries

```bash
# Specific combinations
python scripts/search_emissions_factors.py "california coal power plant"
python scripts/search_emissions_factors.py "texas industrial natural gas"
python scripts/search_emissions_factors.py "residential heating oil emissions"
python scripts/search_emissions_factors.py "commercial sector electricity northeast"
```

---

## 🎯 Tips & Tricks

### Getting Better Results

1. **Start Broad, Then Narrow**
   ```bash
   # Start: "emissions"
   # Narrow: "coal emissions"
   # Specific: "industrial coal emissions california"
   ```

2. **Use Synonyms**
   - MOTHRA understands related terms
   - "power plant" = "electricity generation" = "power station"
   - "carbon" = "CO2" = "emissions" = "greenhouse gas"

3. **Include Context**
   - Better: "steel production emissions"
   - Good: "steel carbon"
   - Works: "steel"

4. **Check Similarity Scores**
   - Scores < 0.3 may not be relevant
   - Adjust with `-s` flag to filter

5. **Use Details Mode for Learning**
   ```bash
   python scripts/search_emissions_factors.py "query" -d
   ```
   This shows full descriptions and helps you understand the data.

### Common Patterns

**Finding State Data:**
```bash
python scripts/search_emissions_factors.py "[state name] [fuel/sector]"
# Example: "california natural gas"
```

**Comparing Fuels:**
```bash
# Search each fuel separately
python scripts/search_emissions_factors.py "coal emissions"
python scripts/search_emissions_factors.py "natural gas emissions"
# Compare the emission factors
```

**Finding Sector-Specific Data:**
```bash
python scripts/search_emissions_factors.py "[sector] [fuel] emissions"
# Example: "industrial coal emissions"
```

---

## 🔧 Troubleshooting

### "No emission factors found!"

**Possible Causes:**
1. Searched entities don't have emission factor metadata
2. Only steel/material database entities were found (no EIA data)
3. Query too specific

**Solutions:**
- ✅ Try broader terms: "emissions" instead of "carbon footprint of steel"
- ✅ Include location: "california emissions" instead of just "emissions"
- ✅ Use fuel or sector keywords: "coal", "natural gas", "industrial"
- ✅ Lower similarity threshold: add `-s 0.0`

### Results Don't Match My Query

**Possible Causes:**
1. Semantic search found related but different concepts
2. Limited data in database for your specific query

**Solutions:**
- ✅ Check similarity scores - ignore results < 0.3
- ✅ Be more specific in your query
- ✅ Use `-s 0.5` to filter weak matches
- ✅ Try alternative phrasings

### Duplicate Results

**Cause:** Multiple emission factors for the same location/fuel (different metrics)

**Solution:** This is expected! Different units measure different things:
- CO2 per Btu = energy efficiency
- CO2 per dollar = economic intensity
- Total CO2 = absolute emissions

### Slow Search

**Cause:** First search loads the embedding model (~2 seconds)

**Solution:** Subsequent searches are fast! Model stays in memory.

---

## 📞 Need Help?

### Common Questions

**Q: What's the difference between the search scripts?**
- `search_entities.py` - Searches ALL entities, shows general info
- `search_emissions_factors.py` - Filters for entities with emission factors, shows CO2e data

**Q: Can I search for multiple queries at once?**
- Currently no, but you can script it:
  ```bash
  for fuel in coal gas oil; do
    python scripts/search_emissions_factors.py "$fuel emissions" -n 3
  done
  ```

**Q: How often is data updated?**
- EIA SEDS: Annual (usually September/October)
- EIA Facility: Monthly/Annual
- EC3: Continuous
- Database updates: Run ingestion scripts as needed

**Q: Can I export results?**
- Currently results display in terminal
- Pipe to file: `python scripts/search_emissions_factors.py "query" > results.txt`

### Getting More Data

To add more data to the database:

```bash
# Ingest all EIA data (takes time!)
python scripts/ingest_eia_data.py --all

# Embed new entities
python scripts/embed_entities.py
```

### Support

- 📖 Check the documentation in `/docs`
- 🐛 Report issues on GitHub
- 💬 Community forums (if available)

---

## 🎓 Understanding Semantic Search

### How It Works

MOTHRA uses **vector embeddings** to understand meaning:

1. Your query is converted to a 384-dimensional vector
2. All database entities have pre-computed vectors
3. Cosine similarity finds the closest matches
4. Results are ranked by similarity score

### Why It's Better Than Keywords

**Keyword Search:**
- ❌ Exact matches only
- ❌ Misses synonyms
- ❌ Can't understand context

**Semantic Search (MOTHRA):**
- ✅ Understands meaning
- ✅ Finds related concepts
- ✅ Works with natural language
- ✅ Handles typos and variations

**Example:**
- Query: "electricity from gas"
- Finds: "Natural gas power generation", "CCGT electricity", "Gas turbine emissions"
- Keyword search would miss most of these!

---

## 🌟 Best Practices

### For Accurate Results

1. ✅ **Be Specific** - "California industrial coal emissions" > "emissions"
2. ✅ **Check Scores** - Trust results with similarity > 0.5
3. ✅ **Verify Units** - Make sure the unit matches your needs
4. ✅ **Check Time Period** - Ensure data is from the right year
5. ✅ **Cross-Reference** - Compare multiple results when possible

### For Efficient Searches

1. ⚡ **Start Simple** - Begin with basic terms, refine as needed
2. ⚡ **Use Filters** - `-s` and `-n` flags save time
3. ⚡ **Batch Queries** - Search related terms together
4. ⚡ **Save Common Queries** - Create shell aliases for frequent searches

### For Data Quality

1. 📊 **Understand Sources** - Know where data comes from (EIA, EC3, etc.)
2. 📊 **Check Metadata** - Use `-d` flag to see full details
3. 📊 **Note Limitations** - State-level data may not reflect local variations
4. 📊 **Use Multiple Sources** - Cross-validate when possible

---

## 📝 Quick Reference Card

### Essential Commands

```bash
# Basic search
python scripts/search_emissions_factors.py "QUERY"

# With options
python scripts/search_emissions_factors.py "QUERY" -n 10 -d -s 0.5

# Alternative search (all entities)
python scripts/search_entities.py "QUERY" --type emission
```

### Option Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-n NUMBER` | Number of results | `-n 20` |
| `-s SCORE` | Min similarity (0-1) | `-s 0.5` |
| `-d` | Show details | `-d` |
| `--type` | Filter by type | `--type emission` |
| `-h` | Show help | `-h` |

### Similarity Score Guide

| Score | Match Quality | Action |
|-------|---------------|--------|
| 0.7-1.0 | Excellent | Use with confidence |
| 0.5-0.7 | Good | Verify relevance |
| 0.3-0.5 | Moderate | Check carefully |
| 0.0-0.3 | Weak | Probably not relevant |

---

## 🚀 What's Next?

### Upcoming Features

- 🔄 More data sources (IPCC, GREET, etc.)
- 📊 Export to CSV/JSON
- 🌐 Web interface
- 📱 API access
- 🔗 Data linking and relationships
- 📈 Trend analysis
- 🗺️ Geographic visualization

### Contributing

Help us expand MOTHRA:
- 📥 Suggest new data sources
- 🐛 Report bugs
- 💡 Request features
- 📖 Improve documentation

---

## 📚 Additional Resources

### External Documentation

- **EIA SEDS:** https://www.eia.gov/state/seds/
- **EIA API:** https://www.eia.gov/opendata/
- **EC3 Database:** https://www.buildingtransparency.org/
- **EPA Emissions:** https://www.epa.gov/ghgemissions

### MOTHRA Documentation

- Technical Architecture: `/docs/ARCHITECTURE.md`
- Database Schema: `/docs/DATABASE_SCHEMA.md`
- API Reference: `/docs/API.md`
- Developer Guide: `/docs/DEVELOPER.md`

---

## ✨ Happy Searching!

MOTHRA makes finding emissions factors easy and intuitive. Start with simple queries and explore the power of semantic search!

**Remember:**
- 🎯 Search naturally
- 📊 Check similarity scores
- 🔍 Use details mode to learn
- 💡 Iterate and refine

**Questions? Start here:**
```bash
python scripts/search_emissions_factors.py "coal emissions" -n 5 -d
```

---

*Last Updated: October 2025*
*Version: 1.0*
*MOTHRA - Mapping Operational Transparency for High-Resolution Assessments*
