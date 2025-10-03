# MyTechFun Crawler Constitution

## Core Principles

### I. Gentle Crawler
The crawler respects `robots.txt`, applies rate-limiting with exponential backoff, and uses an identifiable user-agent: `mytechfun-research-bot/1.0 (contact: ...)`. Rate limiting is particularly enforced during Phase 1 (Discovery) to minimize impact on the source site.

### II. Data Quality
Collected data is normalized to SI units where defined, while also preserving `original_value` and `original_unit`. Data quality is classified as `{OK, WARN, RAW}` based on parsing success rates. The two-phase architecture improves data quality by using structure-specific parsers developed from discovery insights rather than generic assumptions.

### III. Transparency & Provenance
For each saved datum, the following are recorded: post, file, SHA-256 hash, download timestamp, storage_key, sheet/row/column (when available). **NEW**: Discovery report hash is included to trace which parsing strategies were used, providing complete audit trail from discovery through normalization.

### IV. Ethics & Licensing
The crawler respects the CC BY 4.0 license. Every piece of information exposes the attribute: `Data © MyTechFun – Dr. Igor Gaspar, CC BY 4.0` with a link to the source post. Excel files are not republished in full; files are kept only for audit purposes.

### V. Two-Phase Architecture
**UPDATED**: The system operates in two distinct phases:

**Phase 1 (Discovery & Collection)**:
- Services: CrawlerService → ParserService (download only) → StorageService (discovery results)
- Output: Post objects, ValidFile objects, DiscoveryReport with structure analysis
- Storage: `data/discovery/` for reports, `data/raw/` for files

**Phase 2 (Parsing & Normalization)**:
- Services: Load discovery results → NormalizerService (structure-aware) → StorageService (final JSON)
- Output: MaterialData objects with quality ratings, final JSONData with provenance
- Storage: `data/processed/` for normalized JSON files

This separation enables adaptive parsing based on actual file structures found, rather than assumptions.

### VI. Logging & Observability
Structured logging in JSON format via Pino. Operations are idempotent and run-safe; deduplication via SHA-256 hash. Retries are managed with jitter to avoid collisions and overloads. **NEW**: Phase-specific logging enables separate monitoring of discovery and normalization operations.

### VII. Analisi Avanzata dei File Excel

Dopo la raccolta, è obbligatorio analizzare la struttura interna dei file Excel per:
- Individuare le intestazioni reali e le righe chiave
- Identificare le proprietà tecniche (Strength, Modulus, Density, Elongation, ecc.)
- Documentare la posizione delle informazioni chiave (fogli, righe, colonne)
- Sviluppare parser adattivi basati sulle strutture effettivamente trovate

Questa analisi è parte integrante della fase di discovery e condizione necessaria per la normalizzazione affidabile.

## Two-Phase Architectural Benefits

### Problem Addressed
Without knowing the actual structure of MyTechFun.com Excel files, any single-phase normalization strategy would be based on assumptions and likely fail on real data variations.

### Solution Benefits
- **Adaptive Intelligence**: Parsers developed based on actual file structures discovered
- **Higher Success Rates**: Structure-specific parsing vs. generic assumptions
- **Transparent Process**: Clear separation between data collection and data processing
- **Debuggable**: Issues can be isolated to either discovery or normalization phases
- **Iterative Improvement**: Parsing strategies can be refined based on discovery results

## Additional Requirements

- Tech stack: Python 3.11+, open-source libraries, local file storage.
- Security: no sensitive data collected, complete audit trail including discovery report provenance.
- Performance: scraping is rate-limited during Phase 1, Phase 2 is local processing only.
- **NEW**: Discovery reports enable structure analysis without repeated crawling.

## Development Workflow

- Mandatory TDD with phase-specific test suites.
- Code review on every PR.
- Integration tests for contractual changes.
- **NEW**: Discovery phase testing with sample file structures.
- **NEW**: Normalization phase testing with various parsing strategies.

## CLI Interface Requirements

The system MUST support the following command patterns:

```bash
# Phase 1 only: Discovery and collection
python src/cli/crawler.py --phase discovery --url https://www.mytechfun.com/videos/material_test

# Phase 2 only: Normalization using discovery results  
python src/cli/crawler.py --phase normalize --discovery-report data/discovery/report.json

# Both phases: Complete workflow
python src/cli/crawler.py --phase both --url https://www.mytechfun.com/videos/material_test
```

## Quality Thresholds

### Discovery Phase Quality
- **File Structure Recognition**: >60% confidence score for common patterns
- **Column Name Analysis**: Identify property patterns in >70% of files
- **Parsing Recommendations**: Provide strategy recommendations for >80% of file types

### Normalization Phase Quality  
- **OK Rating**: >80% of properties successfully normalized to SI units
- **WARN Rating**: 20-80% normalization success, issues documented
- **RAW Rating**: <20% normalization success, original data preserved

## Governance

This constitution takes precedence over all other practices. Any change requires documentation, approval, and a migration plan. The two-phase architecture is now a constitutional requirement for maintaining data quality and system reliability.

**Version**: 2.0.0 | **Ratified**: 2025-10-03 | **Last Modified**: 2025-10-03  
**Major Change**: Added two-phase architecture as constitutional requirement
