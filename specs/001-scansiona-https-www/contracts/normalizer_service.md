# NormalizerService Contract - Phase 2 Focus

## Phase 2: Structure-Aware Normalization Interface
```python
class NormalizerService:
    def process_materials_with_discovery(self, files: List[ValidFile], discovery_report: DiscoveryReport) -> List[MaterialData]:
        """
        Phase 2: Extract and normalize material data using discovery insights
        
        Args:
            files: List of ValidFile objects to process
            discovery_report: Discovery results with parsing strategies
            
        Returns:
            List of MaterialData objects with normalized properties and quality ratings
            
        Raises:
            NormalizationError: When data extraction/normalization fails
            FileFormatError: When file format is unsupported
        """
    
    def normalize_single_material(self, file: ValidFile, analysis: FileStructureAnalysis, strategy: str) -> List[MaterialData]:
        """
        Phase 2: Process single file using specific parsing strategy
        
        Args:
            file: ValidFile to process
            analysis: Structure analysis from Phase 1
            strategy: Parsing strategy from discovery recommendations
            
        Returns:
            List of MaterialData objects extracted from this file
            
        Raises:
            ParsingError: When parsing fails with given strategy
        """
    
    def assess_normalization_quality(self, material: MaterialData) -> QualityRating:
        """
        Assess quality of normalized material data
        
        Args:
            material: MaterialData object to assess
            
        Returns:
            QualityRating (OK/WARN/RAW) based on normalization success
        """
```

## Legacy Interface (Backward Compatibility)
```python
    def process_materials(self, files: List[ValidFile]) -> List[MaterialData]:
        """
        Legacy method: Process materials without discovery insights
        Uses generic parsing strategies - maintained for backward compatibility
        """
```

## Constitutional Requirements
- MUST normalize units to SI where possible (Phase 2 focus)
- MUST preserve original values and units for transparency
- MUST classify data quality (OK, WARN, RAW) based on parsing success
- MUST handle multiple materials per file using discovery insights
- MUST maintain provenance (sheet/row/column positions)
- MUST use structure-specific parsing strategies from discovery report
- MUST assign RAW quality rating when parsing fails completely

## Input Validation
- files must be valid spreadsheet formats (.xlsx/.xls/.csv)
- files must exist on disk and be readable
- discovery_report must contain valid parsing recommendations
- analysis must have confidence_score between 0-100

## Output Guarantees
- **MaterialData objects**: Include both original and normalized values
- **Quality Ratings**: OK (>80% normalized), WARN (20-80%), RAW (<20%)
- **Parsing Method**: Document which strategy was used for audit trail
- **Provenance**: Full source file hash and parsing timestamp
- **SI Units**: Temperature in Kelvin, pressure in Pascal, etc.

## Phase-Specific Behavior

### Phase 2 Primary Mode (Discovery-Driven)
- **Strategy Selection**: Use discovery report recommendations
- **Structure-Aware**: Apply parsing based on identified file structure type
- **Quality Assessment**: Rate based on actual parsing success
- **Targeted Extraction**: Focus on properties identified during discovery
- **Fallback Handling**: Gracefully handle unexpected formats

### Legacy Mode (Generic Parsing)
- **Best-Effort**: Apply generic parsing strategies
- **Lower Success Rate**: Expected due to lack of structure insights
- **More RAW Ratings**: Expected for complex/unusual file structures

## Parsing Strategies by Structure Type

### Single Material Vertical (`property_value_parser`)
- Look for property names in first column
- Extract values from second column
- Handle units embedded in value cells
- Expected success rate: 80-90%

### Multi-Material Table (`table_row_parser`)
- Materials as column headers or row labels
- Properties as the opposing dimension
- Cross-reference to extract material-property pairs
- Expected success rate: 70-80%

### Test Results Matrix (`matrix_parser`)
- Complex multi-sheet or multi-section layouts
- Custom rules based on discovered patterns
- May require sheet-specific parsing logic
- Expected success rate: 50-70%

### Unknown Structure (`generic_parser`)
- Fallback when discovery couldn't classify structure
- Best-effort property extraction
- Higher chance of RAW quality rating
- Expected success rate: 30-50%

## Unit Normalization Rules
- **Temperature**: °C/°F → Kelvin (K)
- **Pressure/Strength**: MPa/GPa/psi → Pascal (Pa)
- **Length**: mm/cm/in → meter (m)
- **Density**: g/cm³ → kg/m³
- **Percentage**: % → decimal (preserve % unit for clarity)

## Error Handling Strategy
- **Parsing Failures**: Assign RAW quality, preserve original data
- **Unit Conversion Failures**: Assign WARN quality, keep original units
- **Missing Properties**: Log gaps, extract available properties
- **File Corruption**: Skip file with error logging
- **Memory Issues**: Process files in batches

## Performance Expectations
- **Discovery-Driven**: 20-50 materials per minute
- **Legacy Mode**: 10-30 materials per minute  
- **Memory Usage**: <200MB for typical 50-file batch
- **Success Rate**: 70-85% with discovery, 40-60% without

## Testing Contract
```python
def test_process_materials_with_discovery_uses_strategies():
    service = NormalizerService()
    files = create_test_files()
    discovery_report = create_test_discovery_report()
    materials = service.process_materials_with_discovery(files, discovery_report)
    assert isinstance(materials, list)
    for material in materials:
        assert isinstance(material, MaterialData)
        assert material.quality_rating in [QualityRating.OK, QualityRating.WARN, QualityRating.RAW]

def test_assess_normalization_quality_rates_correctly():
    service = NormalizerService()
    # High normalization success should get OK rating
    # Partial success should get WARN rating  
    # Failed parsing should get RAW rating

def test_preserves_original_values():
    # Must maintain original values alongside normalized ones
    # Constitutional transparency requirement
```
