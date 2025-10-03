# Quickstart Guide: Two-Phase Material Test Data Crawler

## Prerequisites
- Python 3.11+
- Virtual environment (recommended)
- Internet connection for crawling

## Installation
```bash
# Clone repository and navigate to project directory
cd mtf-crawler

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Two-Phase Quick Start

### Phase 1: Discovery & Collection
```bash
# Run discovery phase to collect data and analyze file structures
python src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test"

# Check discovery results
ls data/raw/             # Downloaded Excel/CSV files
cat data/discovery/report.json  # Structure analysis report
ls data/discovery/posts/ # Cleaned post data
```

### Phase 2: Parsing & Normalization
```bash
# Run normalization phase using discovery results
python src/cli/crawler.py --phase normalize --discovery-report data/discovery/report.json

# Check final output
ls data/processed/       # Final JSON files with normalized data
tail -f data/logs/crawler.log  # Monitor structured logs
```

### Combined Workflow (Both Phases)
```bash
# For automated workflows - runs both phases sequentially
python src/cli/crawler.py --phase both --url "https://www.mytechfun.com/videos/material_test"
```

## Understanding the Two-Phase Output

### Phase 1 Discovery Output
After running the discovery phase, you'll find:

**Discovery Report** (`data/discovery/report.json`):
```json
{
  "generation_timestamp": "2025-10-03T14:30:00Z",
  "total_posts_crawled": 45,
  "total_files_downloaded": 127,
  "file_structure_patterns": [
    "single_material_vertical",
    "multi_material_table", 
    "test_results_matrix"
  ],
  "column_name_analysis": {
    "tensile_strength": ["Tensile Strength", "UTS", "Ultimate Tensile"],
    "elastic_modulus": ["E-Modulus", "Young's Modulus", "Elasticity"]
  },
  "parsing_recommendations": {
    "single_material_vertical": "property_value_parser",
    "multi_material_table": "table_row_parser"
  }
}
```

**Downloaded Files** (`data/raw/`):
- Files named with SHA-256 prefix for deduplication
- Preserved in original format for Phase 2 processing

### Phase 2 Normalization Output
After running the normalization phase, you'll find:

**Final JSON Files** (`data/processed/{post_hash}.json`):
```json
{
  "post": {
    "url": "https://www.mytechfun.com/videos/material_test/pla-comparison",
    "title": "PLA Filament Test Results",
    "cleaned_text": "...",
    "youtube_link": "https://youtube.com/watch?v=..."
  },
  "materials": [
    {
      "material_name": "PLA Standard",
      "properties": {
        "tensile_strength": {
          "value": 45000000,
          "unit": "Pa",
          "original_value": 45,
          "original_unit": "MPa"
        }
      },
      "quality_rating": "OK"
    }
  ],
  "provenance": {
    "source_url": "...",
    "discovery_report_hash": "abc123...",
    "parsing_phase_timestamp": "2025-10-03T15:45:00Z"
  }
}
```

## Development and Testing

### Limited Testing (Recommended for Development)
```bash
# Test with limited posts for development
python src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test" --max-posts 5

# Dry run (no file downloads)
python src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test" --dry-run

# Skip file downloads, only extract post content
python src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test" --skip-files
```

### View Discovery Analysis
```bash
# Pretty-print discovery report
python -c "import json; print(json.dumps(json.load(open('data/discovery/report.json')), indent=2))"

# View file structure analysis
ls data/discovery/structures/
cat data/discovery/structures/{file_hash}.json
```

### Monitor Progress
```bash
# Real-time log monitoring
tail -f data/logs/crawler.log | grep -E "(INFO|ERROR)"

# View specific phase logs
grep "discovery" data/logs/crawler.log
grep "normalize" data/logs/crawler.log
```

## Troubleshooting

### Common Phase 1 Issues
- **No files found**: Check if posts contain "Download files" sections
- **Download failures**: Verify network connectivity and robots.txt compliance
- **Low structure confidence**: Review discovery report for file format variations

### Common Phase 2 Issues
- **Low normalization success**: Check discovery report recommendations
- **RAW quality ratings**: Expected for unusual file structures, preserved for manual analysis
- **Missing properties**: Normal for files with non-standard layouts

### Recovery Workflows
```bash
# Re-run only failed normalizations
python src/cli/crawler.py --phase normalize --discovery-report data/discovery/report.json --retry-failed

# Regenerate discovery report from existing files
python src/cli/crawler.py --phase analyze-existing --input-dir data/raw/
```

## Constitutional Compliance Verification
```bash
# Verify constitutional compliance of output
python src/lib/validation.py --check-compliance data/processed/

# View compliance report
cat data/compliance-report.json
```

## Expected Performance
- **Phase 1**: ~1-2 posts per minute (respects rate limits)
- **Phase 2**: ~10-50 files per minute (local processing)
- **Total Time**: 50-100 posts typically complete in 30-60 minutes

## Next Steps
1. Review discovery report to understand file structures found
2. Examine normalized JSON outputs for data quality
3. Use parsed material data for your research/analysis needs
4. Consider contributing parsing improvements for new file structures discovered
