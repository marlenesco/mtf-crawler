# Research Phase: Technical Decisions

## Web Scraping Library Selection

**Decision**: requests + beautifulsoup4
**Rationale**: 
- Mature, stable libraries with extensive documentation
- Handles custom user-agents required by constitution
- Session management for rate limiting
- Simple, readable code for maintainability

**Alternatives Considered**:
- Scrapy: Too heavyweight for single-site crawling, unnecessary complexity
- httpx: Async capabilities not needed, added complexity without benefit
- urllib: Too low-level, would require significant boilerplate

## Robots.txt and Rate Limiting

**Decision**: robotexclusionrulesparser + tenacity + custom rate limiter
**Rationale**:
- robotexclusionrulesparser: Proper robots.txt compliance per constitution
- tenacity: Built-in exponential backoff and jitter for retry logic
- Custom rate limiter: Fine-grained control over request timing

**Alternatives Considered**:
- scrapy built-in: Rejected due to framework overhead
- time.sleep only: Insufficient for constitutional compliance
- requests-ratelimiter: Less flexible than custom implementation

## Spreadsheet Processing

**Decision**: pandas + openpyxl + xlrd
**Rationale**:
- pandas: Powerful data manipulation and normalization capabilities
- openpyxl: Best support for modern .xlsx files
- xlrd: Required for legacy .xls files
- Combined approach handles all required formats

**Alternatives Considered**:
- Pure openpyxl: Lacks sophisticated data manipulation features
- xlwings: Requires Excel installation, platform dependency
- csv module only: Insufficient for Excel formats

## Data Normalization Strategy

**Decision**: Rule-based normalization with unit conversion mappings
**Rationale**:
- Deterministic and auditable approach
- Maintains original values per constitution requirements
- SI unit conversion follows constitutional data quality principles
- Extensible for new material properties

**Alternatives Considered**:
- ML-based normalization: Too complex, lacks transparency
- Manual normalization: Not scalable for hundreds of posts
- Simple string matching: Insufficient for unit conversions

## Logging Implementation

**Decision**: structlog with JSON formatter
**Rationale**:
- Native Python library with extensive ecosystem
- Structured JSON output compatible with Pino requirements
- Excellent performance and configurability
- Supports constitutional logging requirements

**Alternatives Considered**:
- pino-python: Limited Python ecosystem, fewer features
- Standard logging with JSON formatter: Less structured approach
- Custom logging: Reinventing the wheel, maintenance overhead

## File Storage and Organization

**Decision**: Hierarchical directory structure with SHA-256 deduplication
**Rationale**:
- Clear separation between raw downloads and processed data
- SHA-256 hashing prevents duplicate downloads
- Audit trail maintained per constitutional requirements
- Easy to backup and migrate

**Alternatives Considered**:
- Flat file structure: Poor organization at scale
- Database storage: Unnecessary complexity for file-based approach
- Cloud storage: Adds external dependency and cost
