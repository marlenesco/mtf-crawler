# ParserService Contract - Two-Phase Architecture

## Phase 1: Discovery & Collection Interface
```python
class ParserService:
    def extract_and_download_files(self, post: Post) -> List[ValidFile]:
        """
        Phase 1: Extract and download files from post's "Download files" section
        
        Args:
            post: Post object with cleaned_text and url
            
        Returns:
            List of ValidFile objects for downloaded .xlsx/.xls/.csv files
            
        Raises:
            ParserError: When file extraction fails
            DownloadError: When file download fails
        """
    
    def analyze_file_structure(self, file: ValidFile) -> FileStructureAnalysis:
        """
        Phase 1: Analyze structure of downloaded file for parsing recommendations
        
        Args:
            file: ValidFile object with downloaded content
            
        Returns:
            FileStructureAnalysis with structure type and parsing recommendations
            
        Raises:
            AnalysisError: When file structure analysis fails
        """
    
    def generate_discovery_report(self, files: List[ValidFile], analyses: List[FileStructureAnalysis]) -> DiscoveryReport:
        """
        Phase 1: Generate comprehensive discovery report from all analyzed files
        
        Args:
            files: All ValidFile objects from discovery phase
            analyses: All FileStructureAnalysis objects
            
        Returns:
            DiscoveryReport with aggregated insights and parsing recommendations
        """
```

## Phase 2: Structure-Aware Parsing Interface
```python
    def parse_file_with_strategy(self, file: ValidFile, strategy: str, analysis: FileStructureAnalysis) -> List[MaterialData]:
        """
        Phase 2: Parse file using specific strategy from discovery results
        
        Args:
            file: ValidFile to parse
            strategy: Parsing strategy from discovery report
            analysis: Structure analysis from Phase 1
            
        Returns:
            List of MaterialData objects extracted using targeted parsing
            
        Raises:
            ParsingError: When parsing fails with given strategy
        """
```

## Legacy Interface (Backward Compatibility)
```python
    def extract_files(self, post: Post) -> List[ValidFile]:
        """
        Legacy method: Extract and download files (Phase 1 behavior)
        Maintained for backward compatibility
        """
```

## Constitutional Requirements
- MUST filter only .xlsx/.xls/.csv files during download
- MUST ignore .stl, images, zip, models, and gated assets
- MUST calculate SHA-256 hash for deduplication and integrity verification
- MUST preserve original filename and download metadata
- MUST log all download and analysis operations in structured JSON
- MUST handle parsing failures gracefully (assign RAW quality rating)

## Input Validation
- post must have valid url and cleaned_text
- file must exist and be readable for structure analysis
- strategy must be valid parsing method from discovery recommendations

## Output Guarantees

### Phase 1 Outputs
- **ValidFile objects**: Include SHA-256 hash, original filename, download timestamp
- **FileStructureAnalysis**: Confidence score (0-100), structure type classification
- **DiscoveryReport**: Aggregated patterns, parsing recommendations, quality assessment

### Phase 2 Outputs  
- **MaterialData objects**: Quality rating (OK/WARN/RAW) based on parsing success
- **Original values preserved**: Constitutional requirement for transparency
- **Parsing method documented**: Which strategy was used for audit trail

## Phase-Specific Behavior

### Discovery Phase (Phase 1)
- **File Download**: Identify "Download files" sections, filter by extension
- **Structure Analysis**: Detect layout patterns, column names, unit formats
- **Pattern Recognition**: Group similar structures, recommend parsing strategies
- **Quality Assessment**: Estimate parsability confidence for each file

### Normalization Phase (Phase 2)
- **Strategy Selection**: Use discovery recommendations for parsing approach
- **Targeted Parsing**: Apply structure-specific parsers rather than generic ones
- **Quality Rating**: Assign OK/WARN/RAW based on parsing success rate
- **Fallback Handling**: Preserve raw data when parsing fails

## File Structure Types Supported

### Single Material Vertical
- Properties in first column, values in second column
- One material per file
- Recommended parser: `property_value_parser`

### Multi-Material Table
- Materials as columns, properties as rows (or vice versa)
- Multiple materials per file
- Recommended parser: `table_row_parser`

### Test Results Matrix
- Complex layouts with multiple sheets or sections
- Mixed property types and units
- Recommended parser: `matrix_parser` with custom rules

## Error Handling Strategy

### Phase 1 Errors
- **Download Failures**: Retry with exponential backoff, log and continue
- **Structure Analysis Failures**: Mark as "unknown_structure", preserve file for Phase 2
- **Network Issues**: Constitutional rate limiting, respect robots.txt

### Phase 2 Errors
- **Parsing Failures**: Assign RAW quality rating, preserve original data
- **Unit Conversion Failures**: Assign WARN quality, keep original units
- **Missing Properties**: Log missing data, extract available properties

## Performance Expectations
- **Phase 1 Download**: ~5-10 files per minute (network dependent)
- **Phase 1 Analysis**: ~50-100 files per minute (local processing)
- **Phase 2 Parsing**: ~20-50 files per minute (depends on complexity)
- **Memory Usage**: <500MB for typical 100-file batch

## Testing Contract
```python
def test_extract_and_download_files_returns_valid_files():
    service = ParserService()
    post = create_test_post_with_download_section()
    files = service.extract_and_download_files(post)
    assert isinstance(files, list)
    for file in files:
        assert isinstance(file, ValidFile)
        assert file.sha256_hash is not None
        assert file.file_path exists

def test_analyze_file_structure_returns_analysis():
    service = ParserService()
    file = create_test_valid_file()
    analysis = service.analyze_file_structure(file)
    assert isinstance(analysis, FileStructureAnalysis)
    assert 0 <= analysis.confidence_score <= 100

def test_parse_file_with_strategy_handles_failures():
    service = ParserService()
    # Should assign RAW quality when parsing fails
    # Should preserve original data for audit
```
