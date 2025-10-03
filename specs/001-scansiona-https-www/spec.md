# Feature Specification: Two-Phase Material Test Data Extraction from MyTechFun.com

**Feature Branch**: `001-scansiona-https-www`  
**Created**: 2025-10-03  
**Updated**: 2025-10-03  
**Status**: Updated - Two-Phase Approach  
**Input**: User description: "Scansiona https://www.mytechfun.com/videos/material_test, individua per ogni post la sezione 'Download files', filtra solo .xlsx/.xls/.csv, ignora .stl/immagini/zip modelli e asset gated. Se nel post ci sono i file di cui sopra salva il testo della pagina eliminando le parti ripetute e non interessanti come l'header, il footer, il menu, il primo tag h1 che ha contenuto MyTechFun.com, il footer è definito dopo l'ultimo tag hr dell post. I dati del post vanno salvati in formato json, c'è sempre un link youtube che riguarda la recensione video del materiale. Scarica i file validi: xlsx/.xls/.csv. Colleziona le informazioni che possono essere interessanti per il materiale. Normalizza e organizza le informazioni per ogni post in file json."

## Two-Phase Execution Flow

### Phase 1: Discovery & Collection
```
1. Crawl https://www.mytechfun.com/videos/material_test
2. For each post:
   a. Extract and clean post text (remove header, footer, menu, promotional content)
   b. Identify "Download files" section
   c. Filter and download only .xlsx/.xls/.csv files (ignore .stl/images/zip/gated assets)
   d. Extract YouTube review link and manufacturer links
   e. Save post metadata and raw downloaded files
   f. Generate file structure analysis report
3. Create discovery report with:
   - File format patterns found
   - Data structure variations
   - Common column names and layouts
   - Material property patterns
   - Recommended parsing strategies
```

### Phase 2: Parsing & Normalization (Based on Discovery Results)
```
1. Load discovery report and adapt parsing strategies
2. For each downloaded file:
   a. Apply appropriate parser based on discovered structure
   b. Extract material properties using identified patterns
   c. Normalize units to SI standard where possible
   d. Assign quality ratings (OK/WARN/RAW) based on parsing success
3. Generate final JSON files with:
   - Post content and metadata
   - Successfully parsed material data
   - Provenance information
   - Quality assessments
```

## Rationale for Two-Phase Approach

**Problem with Single-Phase**: Without knowing the actual structure of MyTechFun.com Excel files, any normalization strategy would be based on assumptions and likely fail on real data.

**Benefits of Two-Phase**:
- **Adaptive**: Parsers developed based on actual file structures found
- **Robust**: Handle variations in file formats discovered during collection
- **Transparent**: Clear visibility into what data structures exist
- **Iterative**: Can improve parsing based on discovery results
- **Debuggable**: Separate collection issues from parsing issues

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
A researcher wants to systematically collect and analyze 3D printing material test data from MyTechFun.com. The system first discovers and collects all available data and files, then applies intelligent parsing based on what was actually found, rather than making assumptions about data structure.

### Phase 1 Acceptance Scenarios
1. **Given** the discovery phase is run on MyTechFun.com material test posts, **When** it completes, **Then** it produces a comprehensive discovery report showing all file structures, column patterns, and data variations found.
2. **Given** Excel/CSV files are downloaded during discovery, **When** they are analyzed, **Then** the system identifies common patterns, material property names, and unit formats actually used.
3. **Given** post content is extracted during discovery, **When** text cleaning is applied, **Then** promotional content, headers, footers are removed while preserving material-relevant information.

### Phase 2 Acceptance Scenarios
1. **Given** discovery results showing specific file structures, **When** Phase 2 parsing is applied, **Then** material data is extracted using structure-specific parsers with high success rates.
2. **Given** normalized material properties from parsing, **When** quality assessment is performed, **Then** each material receives appropriate OK/WARN/RAW ratings based on parsing confidence.
3. **Given** parsed material data, **When** final JSON is generated, **Then** it includes full provenance, original values, normalized values, and quality indicators.

### Edge Cases
- What happens when discovery finds unexpected file structures? → System documents them in discovery report for manual analysis and parser development.
- How does the system handle files that can't be parsed in Phase 2? → They receive RAW quality rating with original data preserved for future analysis.
- What if Phase 1 downloads are corrupted or incomplete? → SHA-256 verification and retry mechanisms ensure data integrity.

## Requirements *(mandatory)*

### Phase 1 Requirements (Discovery & Collection)
- **FR-001**: The system MUST crawl all posts under https://www.mytechfun.com/videos/material_test and extract clean post text.
- **FR-002**: The system MUST identify and download only .xlsx/.xls/.csv files from "Download files" sections.
- **FR-003**: The system MUST ignore .stl, .zip, image files, and gated assets during collection.
- **FR-004**: The system MUST extract YouTube review links and manufacturer links from each post.
- **FR-005**: The system MUST generate a comprehensive discovery report analyzing all downloaded file structures.
- **FR-006**: The system MUST preserve all downloaded files with SHA-256 hashes for integrity verification.
- **FR-007**: The system MUST document file format variations, column patterns, and data structures found.

### Phase 2 Requirements (Parsing & Normalization)
- **FR-008**: The system MUST use discovery results to develop appropriate parsing strategies for each file structure type.
- **FR-009**: The system MUST extract material properties using structure-specific parsers based on discovery findings.
- **FR-010**: The system MUST normalize units to SI standard where conversion patterns are identifiable.
- **FR-011**: The system MUST assign quality ratings (OK/WARN/RAW) based on parsing success and data confidence.
- **FR-012**: The system MUST generate final JSON files with complete provenance, original values, and normalized values.
- **FR-013**: The system MUST handle parsing failures gracefully by preserving raw data with RAW quality rating.

### Key Entities
- **Post**: Represents a single material test post with cleaned text and metadata.
- **ValidFile**: Downloaded spreadsheet file with integrity verification and structure analysis.
- **DiscoveryReport**: Analysis of file structures, patterns, and parsing recommendations.
- **MaterialData**: Extracted and normalized material properties with quality assessment.
- **JSONData**: Final structured output combining post, files, materials, and provenance data.

### CLI Interface
```bash
# Phase 1: Discovery and Collection
python src/cli/crawler.py --phase discovery --url https://www.mytechfun.com/videos/material_test

# Phase 2: Parsing and Normalization (uses discovery results)
python src/cli/crawler.py --phase normalize --discovery-report data/discovery/report.json

# Combined phases (for automated workflows)
python src/cli/crawler.py --phase both --url https://www.mytechfun.com/videos/material_test
```

## Advanced Excel File Analysis Phase

After collecting Excel files via the crawler, it is necessary to analyze their internal structure to identify:
- Where the actual headers are located
- Which rows/columns contain technical properties (e.g., Strength, Modulus, Density, Elongation)
- Whether key information is distributed across multiple sheets or in non-standard positions

### Operational Recommendations
1. Analyze the first 10-20 rows of each sheet to identify headers and technical properties.
2. Search for keywords in columns and cells that may indicate material properties.
3. Extract and normalize technical properties, proposing a standardized data structure.
4. Document the parsing strategies adopted based on the actual structures found.

This phase is essential to develop adaptive parsers and ensure data quality and normalization.
