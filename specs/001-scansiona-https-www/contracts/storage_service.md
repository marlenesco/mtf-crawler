# StorageService Contract - Two-Phase Architecture

## Phase 1: Discovery Storage Interface
```python
class StorageService:
    def save_discovery_results(self, posts: List[Post], files: List[ValidFile], discovery_report: DiscoveryReport) -> bool:
        """
        Phase 1: Save discovery results for Phase 2 processing
        
        Args:
            posts: List of Post objects with cleaned content
            files: List of ValidFile objects downloaded
            discovery_report: Analysis results and parsing recommendations
            
        Returns:
            bool: True if save successful
            
        Raises:
            StorageError: When saving discovery results fails
        """
    
    def load_discovery_results(self, discovery_report_path: str) -> Tuple[List[Post], List[ValidFile], DiscoveryReport]:
        """
        Phase 2: Load discovery results for normalization processing
        
        Args:
            discovery_report_path: Path to discovery report JSON file
            
        Returns:
            Tuple of (posts, files, discovery_report) from Phase 1
            
        Raises:
            StorageError: When loading discovery results fails
        """
```

## Phase 2: Final JSON Storage Interface
```python
    def save_json(self, post: Post, files: List[ValidFile], materials: List[MaterialData], discovery_info: dict) -> JSONData:
        """
        Phase 2: Save final normalized data as structured JSON with full provenance
        
        Args:
            post: Post object with extracted content
            files: List of ValidFile objects downloaded
            materials: List of MaterialData objects with normalized data
            discovery_info: Reference to discovery report used for parsing
            
        Returns:
            JSONData object representing the complete dataset
            
        Raises:
            StorageError: When JSON serialization or file save fails
            ValidationError: When required constitutional fields are missing
        """
    
    def save_json_batch(self, json_data_list: List[JSONData]) -> List[str]:
        """
        Phase 2: Save multiple JSONData objects efficiently
        
        Args:
            json_data_list: List of JSONData objects to save
            
        Returns:
            List of storage_keys for saved files
            
        Raises:
            StorageError: When batch save fails
        """
```

## Legacy Interface (Backward Compatibility)
```python
    def save_json_legacy(self, post: Post, files: List[ValidFile], materials: List[MaterialData]) -> JSONData:
        """
        Legacy method: Save without discovery info
        Maintained for backward compatibility
        """
```

## Constitutional Requirements
- MUST include CC BY 4.0 attribution per constitution
- MUST include complete provenance metadata with discovery report hash
- MUST generate unique storage_key for each dataset
- MUST ensure constitutional compliance in all output
- MUST be idempotent (safe to re-run, handles duplicates via SHA-256)
- MUST preserve audit trail linking Phase 1 discovery to Phase 2 normalization

## Input Validation
- post must have valid url, title, and post_hash
- files must have valid sha256_hash and readable file_path
- materials must have valid quality_rating and source_file_hash
- discovery_info must contain valid discovery_report_hash

## Output Guarantees

### Phase 1 Storage
- **Discovery Report**: Saved as `data/discovery/report.json`
- **Post Data**: Individual posts saved in `data/discovery/posts/`
- **File Analysis**: Structure analyses saved in `data/discovery/structures/`
- **Integrity**: All files verified with SHA-256 hashes

### Phase 2 Storage
- **Final JSON**: Complete datasets in `data/processed/{post_hash}.json`
- **Constitutional Metadata**: CC BY 4.0 attribution, license info
- **Full Provenance**: Links back to discovery report used
- **Quality Assessment**: Summary of parsing success rates

## Storage Structure

### Phase 1 Directory Layout
```
data/
├── discovery/
│   ├── report.json                    # Main DiscoveryReport
│   ├── posts/                         # Individual Post objects
│   │   ├── {post_hash}.json
│   │   └── ...
│   └── structures/                    # FileStructureAnalysis objects
│       ├── {file_hash}.json
│       └── ...
├── raw/                               # Downloaded files
│   ├── {sha256}_{filename}
│   └── ...
└── logs/                              # Discovery phase logs
```

### Phase 2 Directory Layout
```
data/
├── processed/                         # Final JSONData files
│   ├── {post_hash}.json               # Complete normalized datasets
│   └── ...
├── discovery/                         # Discovery results (input)
└── logs/                              # Normalization phase logs
```

## JSON Output Format

### Phase 1 Discovery Report
```json
{
  "generation_timestamp": "2025-10-03T14:30:00Z",
  "total_posts_crawled": 127,
  "total_files_downloaded": 456,
  "file_structure_patterns": [...],
  "column_name_analysis": {...},
  "parsing_recommendations": {...},
  "quality_assessment": {...}
}
```

### Phase 2 Final JSON
```json
{
  "post": {...},
  "files": [...],
  "materials": [...],
  "provenance": {
    "discovery_report_hash": "abc123...",
    "parsing_phase_timestamp": "2025-10-03T15:45:00Z",
    "...": "..."
  },
  "_metadata": {
    "schema_version": "2.0.0",
    "two_phase_architecture": true,
    "constitutional_compliance_verified": true
  },
  "_licensing": {
    "attribution": "Data © MyTechFun – Dr. Igor Gaspar, CC BY 4.0",
    "license": "CC BY 4.0",
    "source_url": "..."
  }
}
```

## Phase-Specific Behavior

### Discovery Phase Storage (Phase 1)
- **Incremental Saving**: Save posts and files as they're processed
- **Structure Analysis**: Save file structure analyses for Phase 2 reference
- **Report Generation**: Aggregate all findings into comprehensive discovery report
- **Deduplication**: Use SHA-256 hashes to avoid duplicate downloads

### Normalization Phase Storage (Phase 2)
- **Discovery Integration**: Reference discovery report used for parsing
- **Quality Documentation**: Include parsing success metrics
- **Constitutional Compliance**: Full metadata and licensing information
- **Audit Trail**: Complete provenance from discovery through normalization

## Performance Expectations
- **Phase 1 Saves**: ~100-200 files per minute (local I/O)
- **Phase 2 Saves**: ~50-100 JSONData objects per minute
- **Memory Usage**: <50MB for typical storage operations
- **Disk Usage**: ~1-5MB per post (including files and JSON)

## Error Handling Strategy
- **Disk Full**: Graceful degradation with clear error messages
- **Permission Errors**: Verify directory write permissions
- **JSON Serialization Errors**: Preserve problematic data with error metadata
- **Corruption Detection**: SHA-256 verification on read operations

## Testing Contract
```python
def test_save_discovery_results_creates_proper_structure():
    service = StorageService()
    posts, files, report = create_test_discovery_data()
    success = service.save_discovery_results(posts, files, report)
    assert success == True
    assert os.path.exists("data/discovery/report.json")

def test_load_discovery_results_maintains_integrity():
    service = StorageService()
    # Should load exactly what was saved in Phase 1
    # Should verify hashes and data integrity

def test_save_json_includes_constitutional_metadata():
    service = StorageService()
    json_data = service.save_json(post, files, materials, discovery_info)
    assert "_licensing" in json_data.to_dict()
    assert "_metadata" in json_data.to_dict()
    assert json_data.provenance.discovery_report_hash is not None
```
