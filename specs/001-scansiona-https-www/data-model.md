# Data Model Design - Two-Phase Architecture

## Core Entities

### Post
**Purpose**: Represents a single material test post from MyTechFun.com
**Attributes**:
- `url`: Source URL of the post
- `title`: Post title extracted from HTML
- `cleaned_text`: Post content with header/footer/menu removed
- `youtube_link`: YouTube review video URL
- `manufacturer_links`: List of filament manufacturer URLs found in post
- `download_timestamp`: ISO timestamp of when post was crawled
- `post_hash`: SHA-256 hash of cleaned content for deduplication

### ValidFile
**Purpose**: Represents a downloaded spreadsheet file from a post
**Attributes**:
- `filename`: Original filename from the website
- `file_type`: Extension (.xlsx, .xls, or .csv)
- `sha256_hash`: File content hash for deduplication and integrity
- `file_path`: Local storage path relative to data/raw/
- `download_timestamp`: ISO timestamp of download
- `source_post_url`: URL of the post containing this file
- `file_size`: File size in bytes for validation
- `url`: Original download URL

### DiscoveryReport (NEW - Phase 1 Output)
**Purpose**: Analysis results from Phase 1 discovery process
**Attributes**:
- `generation_timestamp`: When the discovery report was created
- `total_posts_crawled`: Number of posts processed
- `total_files_downloaded`: Number of valid files collected
- `file_structure_patterns`: List of identified file structure types
- `column_name_analysis`: Common column names and variations found
- `unit_format_patterns`: Units and formats discovered in the data
- `material_name_patterns`: How materials are identified in files
- `parsing_recommendations`: Suggested parsing strategies per structure type
- `quality_assessment`: Overall data quality indicators from discovery

### FileStructureAnalysis (NEW - Phase 1 Component)
**Purpose**: Detailed analysis of individual file structures
**Attributes**:
- `file_hash`: SHA-256 of the analyzed file
- `structure_type`: Identified structure pattern (e.g., "single_material_vertical", "multi_material_table")
- `sheet_names`: List of Excel sheet names
- `header_rows`: Detected header row positions
- `data_start_row`: Where actual data begins
- `column_mappings`: Detected property-to-column mappings
- `unit_patterns`: Units found in this specific file
- `material_identifiers`: How materials are named/identified
- `confidence_score`: Parsing confidence (0-100)

### MaterialData
**Purpose**: Normalized information about a 3D printing material (Phase 2 Output)
**Attributes**:
- `material_name`: Standardized material name
- `brand`: Manufacturer/brand name if available
- `properties`: Dictionary of material properties with values
- `original_values`: Original values as found in source files
- `normalized_values`: SI-normalized values with units
- `quality_rating`: OK/WARN/RAW based on parsing success
- `source_file_hash`: SHA-256 of source file
- `parsing_method`: Which parser was used for this material
- `confidence_score`: Parsing confidence for this specific material

### JSONData
**Purpose**: Final structured output combining all data (Phase 2 Output)
**Attributes**:
- `post`: Post object with cleaned content
- `files`: List of ValidFile objects downloaded
- `materials`: List of MaterialData objects extracted
- `provenance`: Provenance metadata
- `discovery_info`: Reference to discovery report used for parsing
- `parsing_summary`: Summary of parsing results and quality

### Provenance
**Purpose**: Audit trail and traceability per constitutional requirements
**Attributes**:
- `source_url`: Original post URL
- `download_timestamp`: When data was collected
- `storage_key`: Unique identifier for this dataset
- `sha256_hash`: Hash of the complete dataset
- `file_count`: Number of files processed
- `material_count`: Number of materials extracted
- `discovery_report_hash`: Hash of discovery report used
- `parsing_phase_timestamp`: When Phase 2 normalization occurred

## Phase-Specific Data Flow

### Phase 1: Discovery & Collection
```
Input: URL (https://www.mytechfun.com/videos/material_test)
↓
Process: Crawl → Clean → Download → Analyze
↓
Output: 
- Post objects (cleaned text, links)
- ValidFile objects (downloaded files)
- DiscoveryReport (structure analysis)
- FileStructureAnalysis objects (per file)
```

### Phase 2: Parsing & Normalization
```
Input: 
- DiscoveryReport (parsing strategies)
- ValidFile objects (raw files)
- Post objects (metadata)
↓
Process: Parse → Normalize → Assess Quality
↓
Output:
- MaterialData objects (normalized properties)
- JSONData objects (complete dataset)
- Updated Provenance (full audit trail)
```

## Storage Structure

### Phase 1 Storage
```
data/
├── raw/                     # Downloaded files (ValidFile.file_path)
│   ├── {sha256}_{filename}  # Actual files with hash prefix
│   └── ...
├── discovery/               # Discovery results
│   ├── report.json          # Main DiscoveryReport
│   ├── structures/          # Individual FileStructureAnalysis
│   └── posts/               # Post objects from Phase 1
└── logs/                    # Structured logs
```

### Phase 2 Storage  
```
data/
├── processed/               # Final JSON outputs
│   ├── {post_hash}.json     # Complete JSONData per post
│   └── ...
├── discovery/               # Discovery results (input for Phase 2)
└── logs/                    # Parsing logs
```

## Entity Relationships

### Discovery Phase (1)
- **Post** 1:N **ValidFile** (one post can have multiple downloadable files)
- **ValidFile** 1:1 **FileStructureAnalysis** (each file gets analyzed)
- **DiscoveryReport** 1:N **FileStructureAnalysis** (aggregates all analyses)

### Normalization Phase (2)
- **FileStructureAnalysis** 1:N **MaterialData** (one file structure can yield multiple materials)
- **Post** + **ValidFile[]** + **MaterialData[]** → **JSONData** (final combination)
- **JSONData** 1:1 **Provenance** (complete audit trail)

## Data Quality Indicators

### Discovery Phase Quality
- **File Integrity**: SHA-256 verification
- **Structure Confidence**: 0-100 score for structure recognition
- **Content Assessment**: Estimated parsability

### Normalization Phase Quality  
- **OK**: >80% properties successfully normalized to SI units
- **WARN**: 20-80% properties normalized, some issues detected
- **RAW**: <20% normalization success, preserved as raw data

## Constitutional Compliance Mapping

- **Gentle Crawler**: Rate limiting enforced in Post creation
- **Data Quality**: Original + normalized values in MaterialData
- **Transparency**: Complete Provenance chain for audit
- **Ethics**: CC BY 4.0 attribution in JSONData metadata
- **Architecture**: Separated models enable service isolation
- **Observability**: Structured logging at each entity transition
