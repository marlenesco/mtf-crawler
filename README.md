# MTF-Crawler: MyTechFun Material Test Data Extractor

> **Project Specification**: The initial definition and specification of this project were created using [GitHub Spec-Kit](https://github.com/github/spec-kit), following structured development practices for clear requirements and implementation guidelines.

An intelligent two-phase crawler to extract and normalize 3D printing material test data from MyTechFun.com.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (Supported: 3.11, 3.12, **3.13** - latest version!)
- Internet connection for crawling

#### ✅ Check Python Version
```bash
python3 --version
# Should show Python 3.11.x, 3.12.x or 3.13.x

python --version   # Usually Python 2.7.x on macOS (ignore this)

brew install python@3.13
brew install python
# Or download from python.org
# https://www.python.org/downloads/
```

#### 🔧 Python 3.13 Setup on macOS (Common Situation)
If you installed Python 3.13 with Homebrew, you may see:
```
Python is installed as /opt/homebrew/bin/python3
Unversioned symlinks python, python-config, pip etc. are installed into
/opt/homebrew/opt/python@3.13/libexec/bin
```

**Correct configuration:**
```bash
python3 --version  # Should show 3.13.x
python3 -m venv venv
source venv/bin/activate
python --version  # Now shows 3.13.x in the virtual environment
# Optionally, always use 'python' for Python 3.13:
echo 'export PATH="/opt/homebrew/opt/python@3.13/libexec/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Installation
```bash
git clone <repository-url>
cd mtf-crawler
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
python --version  # Should be Python 3.11+
pip install -r requirements.txt
```

## 📦 Install dependencies
Install all required dependencies (including Excel analysis packages):
```bash
pip3 install -r requirements.txt
```
Key packages for Excel file analysis:
- pandas
- openpyxl
- xlrd

### ⚡ Quick Run
To start the crawler and analyze downloaded files:
```bash
python3 src/cli/crawler.py --url "https://www.mytechfun.com/videos/material_test" --max-posts 3
python3 simple_analyze.py
```

### ⚙️ Configuration
The project includes ready-to-use configuration files:
- **`.env`** - Default configuration (already present)
- **`.env.example`** - Template with all available options

#### Essential Customization
Before first use, edit the `.env` file:
```bash
# Enter your contact email (required)
MTF_USER_AGENT=mytechfun-research-bot/1.0 (contact: your-email@example.com)
# For testing and development, limit processed posts
MTF_MAX_POSTS=5
# Adjust crawling speed if needed (seconds between requests)
MTF_RATE_LIMIT_DELAY=1.0
```

#### Main Available Configurations
| Variable | Default | Description |
|----------|---------|-------------|
| `MTF_USER_AGENT` | `mytechfun-research-bot/1.0 (contact: user@example.com)` | User agent for web requests |
| `MTF_RATE_LIMIT_DELAY` | `1.0` | Seconds between requests (respectful crawling) |
| `MTF_MAX_POSTS` | `0` | Limit posts to process (0 = unlimited) |
| `MTF_LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `MTF_QUALITY_OK_THRESHOLD` | `80` | % threshold for OK quality |
| `MTF_RESPECT_ROBOTS_TXT` | `true` | Respect robots.txt (constitutional) |

See `.env.example` for all available options.

### Basic Usage
#### Full Approach (Recommended)
```bash
python3 src/cli/crawler.py --phase both --url "https://www.mytechfun.com/videos/material_test"
```
#### Two-Phase Approach (Advanced)
**Phase 1: Discovery & Collection**
```bash
python3 src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test"
```
**Phase 2: Parsing & Normalization**
```bash
python3 src/cli/crawler.py --phase normalize --discovery-report data/discovery/report.json
```

## 📁 System Output
### After Phase 1 (Discovery)
```
data/
├── discovery/
│   ├── report.json          # Full structural analysis
│   ├── posts/               # Cleaned posts
│   └── structures/          # Per-file analysis
├── raw/                     # Downloaded Excel/CSV files
└── logs/                    # Structured logs
```
### After Phase 2 (Normalization)
```
data/
├── processed/               # 🎯 FINAL NORMALIZED DATA
│   ├── {hash1}.json         # Complete data per post
│   ├── {hash2}.json
│   └── ...
├── discovery/              # Discovery results (input for Phase 2)
└── logs/                   # Logs for both phases
```

## 🔧 Advanced Options
### Development and Testing
```bash
python3 src/cli/crawler.py --phase both --url "https://www.mytechfun.com/videos/material_test" --max-posts 5
python3 src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test" --dry-run
python3 src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test" --skip-files
MTF_LOG_LEVEL=DEBUG python3 src/cli/crawler.py --phase both --url "https://www.mytechfun.com/videos/material_test"
```
### Specific Use Case Configurations
#### Fast Test Crawling
```env
MTF_MAX_POSTS=3
MTF_RATE_LIMIT_DELAY=0.5
MTF_LOG_LEVEL=DEBUG
```
#### Production Crawling (Respectful)
```env
MTF_MAX_POSTS=0
MTF_RATE_LIMIT_DELAY=2.0
MTF_LOG_LEVEL=INFO
MTF_VALIDATE_COMPLIANCE=true
```
#### Text Analysis Only (No Download)
```env
MTF_SKIP_FILES=true
MTF_LOG_LEVEL=INFO
```

## 📊 Output Data Structure
### Discovery Report (Phase 1)
```json
{
  "total_posts_crawled": 127,
  "total_files_downloaded": 456,
  "file_structure_patterns": [
    "single_material_vertical",
    "multi_material_table"
  ],
  "parsing_recommendations": {
    "single_material_vertical": "property_value_parser",
    "multi_material_table": "table_row_parser"
  }
}
```
### Final Data (Phase 2)
```json
{
  "post": {
    "url": "https://www.mytechfun.com/videos/material_test/pla-test",
    "title": "Test PLA Filaments",
    "youtube_link": "https://youtube.com/watch?v=...",
    "manufacturer_links": ["https://prusament.com/..."]
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
    "download_timestamp": "2025-10-03T14:30:00Z",
    "discovery_report_hash": "abc123..."
  }
}
```

## ⚡ Main Features
### 🤖 Respectful Crawler
- Automatically respects `robots.txt`
- Intelligent rate limiting (1-2 posts/minute)
- Identifiable user-agent: `mytechfun-research-bot/1.0`

### 🧠 Two-Phase Smart Parsing
1. **Discovery**: Analyzes real structures of Excel/CSV files
2. **Normalization**: Applies specific parsers based on detected patterns

### 📏 SI Normalization
- Temperature: °C/°F → Kelvin (K)
- Pressure: MPa/GPa/psi → Pascal (Pa)
- Length: mm/cm/in → meter (m)
- Density: g/cm³ → kg/m³

### 🔍 Data Quality
- **OK**: >80% properties normalized successfully
- **WARN**: 20-80% normalized, some issues
- **RAW**: <20% normalized, data preserved as found

### 📝 Full Traceability
- SHA-256 hash for each file and post
- Download and processing timestamp
- Link between discovery and normalization
- CC BY 4.0 license preserved

## 🛠️ Troubleshooting
### Installation Errors
**"No module named venv" or Python 2.7 detected**
```bash
brew install python@3.11
python3.11 -m venv venv
python3 -m venv venv
source venv/bin/activate
python --version  # Should show 3.11+
```
**"command not found: python3"**
```bash
brew install python@3.11
# Or download from https://www.python.org/downloads/
brew install pyenv
pyenv install 3.11.5
pyenv global 3.11.5
```
**Dependencies not installing**
```bash
pip install --upgrade pip
xcode-select --install  # On macOS for some dependencies
pip install -r requirements.txt
```
### Common Errors
**"No posts found"**
```bash
curl -I "https://www.mytechfun.com/videos/material_test"
```
**"Discovery report not found"**
```bash
python src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test"
```
**Rate limiting or 429 errors**
```bash
# System handles automatically, just wait
# Or increase delay in .env:
# MTF_RATE_LIMIT_DELAY=2.0
```
**"User agent not configured"**
```bash
# Edit .env with your email:
# MTF_USER_AGENT=mytechfun-research-bot/1.0 (contact: your-email@example.com)
```
**Too verbose logging**
```bash
# Lower level in .env:
# MTF_LOG_LEVEL=WARNING
```
### Expected Performance
- **Phase 1**: 1-2 posts/minute (respects rate limits)
- **Phase 2**: 20-50 files/minute (local processing)
- **Memory**: <500MB per typical batch
- **Storage**: ~1-5MB per post (includes file and JSON)

## 📋 Main Dependencies
Uses the following open-source libraries:
- **requests** + **beautifulsoup4**: Web crawling
- **pandas** + **openpyxl** + **xlrd**: Excel/CSV processing
- **structlog**: Structured JSON logging
- **tenacity**: Exponential backoff retry
See `requirements.txt` for the full list with versions.

## 📖 Next Steps
1. **Run discovery** to understand found structures
2. **Review the report** to see identified patterns
3. **Normalize data** with specific parsers
4. **Analyze results** in `data/processed/`
For detailed documentation, see the folder `specs/001-scansiona-https-www/`.

---

## 🏛️ Constitutional Principles
This project follows strict ethical and technical principles:
- **Respectful crawling**: Configurable rate limiting, robots.txt compliance
- **Transparency**: Structured logging, explicit configuration
- **Full traceability**: SHA-256, timestamps, provenance
- **License preservation**: Automatic CC BY 4.0 attribution
- **Verifiable data quality**: Configurable thresholds, transparent ratings
- **Modular architecture**: Centralized configuration via .env
All configurations comply with the constitutional principles defined in `.specify/memory/constitution.md`.
**Version**: 2.0.0 | **Architecture**: Two-phase | **License**: CC BY 4.0 compliant

## 🏁 Workflow: Crawling, Download, Normalization
### 1. Crawling & Discovery
Extract all posts and downloadable files from MyTechFun:
```bash
python3 src/cli/crawler.py --phase discovery --url "https://www.mytechfun.com/videos/material_test"
```
- Crawls all posts, extracts metadata, and downloads valid .xlsx/.xls/.csv files.
- Generates: `data/discovery/report.json`, `data/discovery/posts.json`, `data/discovery/files.json`.
- Downloaded files are saved in `data/raw/`.
### 2. Normalization & JSON DB Generation
Parse and normalize all downloaded files, generating a JSON for each post:
```bash
python3 src/cli/crawler.py --phase normalize --discovery-report data/discovery/report.json
```
- Loads all posts and files from discovery.
- Extracts and normalizes technical properties from each file.
- Generates one JSON per post in `data/processed/`, even if no files are associated.
- Each JSON contains: post metadata, normalized material properties, provenance.
### 3. Full Pipeline (Both Phases)
Run crawling and normalization in sequence:
```bash
python3 src/cli/crawler.py --phase both --url "https://www.mytechfun.com/videos/material_test"
```
- Executes both steps above automatically.
### 4. Quick Analysis of Downloaded Files
To inspect the structure of downloaded Excel files:
```bash
python3 simple_analyze.py
```
- Prints sheet names, columns, and sample rows for each file in `data/raw/`.
### 5. Advanced Options
- Limit posts: `--max-posts 5`
- Dry run (no download): `--dry-run`
- Skip file download: `--skip-files`
- Debug logging: `MTF_LOG_LEVEL=DEBUG python3 src/cli/crawler.py ...`
### 6. Output Structure
- `data/discovery/`: Discovery reports, posts, files
- `data/raw/`: Downloaded Excel/CSV files
- `data/processed/`: Final normalized JSON per post
### 7. Troubleshooting
- If you see errors about missing modules, install dependencies:
  ```bash
  pip3 install -r requirements.txt
  ```
- For SSL errors on macOS, ensure you have `certifi` installed and Python certificates configured.
- If only one JSON is generated, check logs for errors or missing file associations.

## 📚 Example Commands
- Crawl and download: `python3 src/cli/crawler.py --phase discovery --url "..."`
- Normalize and generate JSON DB: `python3 src/cli/crawler.py --phase normalize --discovery-report data/discovery/report.json`
- Full pipeline: `python3 src/cli/crawler.py --phase both --url "..."`
- Analyze Excel files: `python3 simple_analyze.py`
