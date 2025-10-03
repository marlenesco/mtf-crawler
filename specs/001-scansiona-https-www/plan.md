# Implementation Plan: Two-Phase Material Test Data Extraction from MyTechFun.com

**Branch**: `001-scansiona-https-www` | **Date**: 2025-10-03 | **Updated**: 2025-10-03 | **Spec**: [link](spec.md)
**Input**: Updated feature specification with two-phase approach from `/specs/001-scansiona-https-www/spec.md`

## Execution Flow (/plan command scope)
```
1. Load updated two-phase feature spec from Input path ✓
2. Fill Technical Context for both discovery and normalization phases ✓
3. Fill the Constitution Check section based on constitution document ✓
4. Evaluate Constitution Check section ✓
5. Execute Phase 0 → research.md (updated for two-phase approach) ✓
6. Execute Phase 1 → contracts, data-model.md, quickstart.md (revised for phases) ✓
7. Re-evaluate Constitution Check section ✓
8. Plan Phase 2 → Task generation for discovery and normalization phases ✓
9. STOP - Ready for /tasks command ✓
```

## Summary
**Updated Requirement**: Two-phase approach for crawling MyTechFun.com material test data:
- **Phase 1 (Discovery)**: Crawl posts, download Excel/CSV files, analyze structures, generate discovery report
- **Phase 2 (Normalization)**: Apply structure-specific parsers based on discovery results, normalize to SI units, output structured JSON

**Technical Approach**: Python-based gentle crawler with adaptive parsing. Discovery phase creates intelligence about actual file structures found, enabling robust normalization phase with structure-specific parsers.

## Technical Context

### Phase 1: Discovery & Collection
**Language/Version**: Python 3.11+  
**Primary Dependencies**: requests, beautifulsoup4, pandas, openpyxl, xlrd, tenacity, robotexclusionrulesparser, structlog  
**Storage**: Local file system - raw files in `data/raw/`, discovery reports in `data/discovery/`  
**Output**: Discovery report (JSON) with file structure analysis and parsing recommendations  
**Performance Goals**: Rate-limited scraping, respect robots.txt, exponential backoff  
**Constraints**: <200ms between requests, SHA-256 file integrity verification  

### Phase 2: Parsing & Normalization  
**Input**: Discovery report + downloaded files from Phase 1  
**Processing**: Structure-aware parsing, SI unit normalization, quality assessment  
**Storage**: Normalized JSON files in `data/processed/`  
**Quality Ratings**: OK (fully normalized), WARN (partial), RAW (unparsed)  
**Constraints**: Preserve original values alongside normalized values, full provenance tracking  

**Target Platform**: Linux/macOS  
**Project Type**: single - determines source structure  
**Scale/Scope**: ~100-500 material test posts, adaptive to discovered file structures  

## Two-Phase Architecture Benefits

**Problem Solved**: Eliminates assumptions about Excel file structures by first discovering actual formats used on MyTechFun.com, then developing appropriate parsers.

**Discovery Phase Benefits**:
- Maps real file structures without assumptions
- Identifies column naming patterns actually used
- Documents unit format variations found
- Provides parsing strategy recommendations

**Normalization Phase Benefits**:
- Structure-specific parsers based on discovery
- Higher success rates due to targeted parsing
- Graceful handling of unexpected formats
- Clear quality indicators for parsed data

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [ ] **Gentle Crawler**: Rate limiting, robots.txt compliance, identifiable user-agent ✓
- [ ] **Data Quality**: SI unit normalization, original values preserved, quality classification ✓  
- [ ] **Transparency & Provenance**: SHA-256, timestamps, storage keys, source tracking ✓
- [ ] **Ethics & Licensing**: CC BY 4.0 compliance, attribution, audit-only file retention ✓
- [ ] **Architecture**: Separated services, static JSON DB, file storage ✓
- [ ] **Logging & Observability**: Structured JSON logs, idempotency, deduplication, retry with jitter ✓

**Initial Constitution Check**: PASS

## Project Structure

### Documentation (this feature)
```
specs/001-scansiona-https-www/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
src/
├── models/              # Data models (Post, MaterialData, Provenance)
├── services/            # Core services (crawler, parser, normalizer)
├── cli/                 # Command line interface
└── lib/                 # Utilities (logging, file handling, validation)

data/
├── raw/                 # Downloaded files
├── processed/           # Normalized JSON outputs
└── logs/                # Structured logs

config/
└── settings/            # Configuration files
```

**Structure Decision**: Single project structure selected as this is a standalone crawler without web/mobile components. Core functionality organized into models, services, CLI, and utilities with separate data and configuration directories.

## Phase 0: Outline & Research

**Research Tasks Completed**:

### 1. Web Scraping Library Selection
- **Decision**: requests + beautifulsoup4
- **Rationale**: Mature, well-documented, handles custom user-agents and session management
- **Alternatives considered**: scrapy (too heavyweight), httpx (unnecessary async complexity)

### 2. Robots.txt and Rate Limiting
- **Decision**: robotexclusionrulesparser + tenacity + custom rate limiter
- **Rationale**: Ensures ethical crawling per constitution requirements
- **Alternatives considered**: scrapy built-in (rejected due to framework overhead)

### 3. Spreadsheet Processing
- **Decision**: pandas + openpyxl + xlrd
- **Rationale**: pandas for data manipulation, openpyxl for .xlsx, xlrd for legacy .xls
- **Alternatives considered**: pure openpyxl (lacks data manipulation), xlwings (requires Excel installation)

### 4. Data Normalization Strategy
- **Decision**: Rule-based normalization with unit conversion mappings
- **Rationale**: Deterministic, auditable, follows constitution data quality requirements
- **Alternatives considered**: ML-based (too complex), manual (not scalable)

### 5. Logging Implementation
- **Decision**: structlog with JSON formatter
- **Rationale**: Python-native, structured JSON output, compatible with Pino requirements
- **Alternatives considered**: pino-python (limited ecosystem), raw logging (lacks structure)

**Output**: research.md with all technical decisions resolved

## Phase 1: Design & Contracts

### Data Model Design
**Entities Extracted from Spec**:
- Post: URL, title, cleaned_text, youtube_link, manufacturer_links, download_timestamp
- ValidFile: filename, file_type, sha256_hash, file_path, download_timestamp
- MaterialData: material_name, properties, original_values, normalized_values, quality_rating
- Provenance: source_url, extraction_timestamp, storage_key, sheet_position

### API Contracts
**Internal Service Contracts** (no external API):
- CrawlerService.crawl_posts() → List[Post]
- ParserService.extract_files() → List[ValidFile]  
- NormalizerService.process_materials() → List[MaterialData]
- StorageService.save_json() → JSONData

### Contract Tests
Generated failing tests for each service contract to enforce TDD approach.

### Quickstart Validation
Integration test scenario covering full crawler execution from URL input to JSON output.

### Agent Context Update
Updated .github/copilot-instructions.md with current tech stack and constitutional requirements.

**Post-Design Constitution Check**: PASS - All requirements maintained through design phase

**Output**: data-model.md, contracts/, quickstart.md, .github/copilot-instructions.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each service contract → implementation task
- Each entity → model creation task [P]
- Configuration setup → environment task [P]
- Integration test → validation task

**Ordering Strategy**:
- Setup tasks first (environment, config, logging)
- Models before services (dependency order)
- Core services before CLI integration
- Validation tasks last
- Mark [P] for parallel execution where no dependencies exist

**Estimated Output**: 15-20 numbered, ordered tasks in tasks.md

## Phase 3+: Future Implementation

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run quickstart.md, verify JSON output structure, test on sample posts)

## Complexity Tracking
*No constitutional violations identified - all requirements can be satisfied with standard approaches*

## Progress Tracking

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (N/A)

---
*Based on Constitution v1.0.1 - See `.specify/memory/constitution.md`*
