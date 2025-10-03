import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple
import structlog
from models.valid_file import ValidFile
from models.material_data import MaterialData, QualityRating


class NormalizerService:
    """Service for extracting and normalizing material data from spreadsheet files per constitutional requirements."""

    def __init__(self):
        self.logger = structlog.get_logger("mtf_crawler.normalizer")
        self.unit_mappings = self._load_unit_mappings()
        self.property_mappings = self._load_property_mappings()

    def process_materials(self, files: List[ValidFile]) -> List[MaterialData]:
        """
        Extract and normalize material data from spreadsheet files.

        Args:
            files: List of ValidFile objects to process

        Returns:
            List of MaterialData objects with normalized properties

        Raises:
            NormalizationError: When data extraction/normalization fails
            FileFormatError: When file format is unsupported
        """
        self.logger.info("Processing materials from files", file_count=len(files))

        all_materials = []

        for file in files:
            try:
                materials = self._process_single_file(file)
                all_materials.extend(materials)
                self.logger.info("File processed",
                               filename=file.filename,
                               materials_found=len(materials))

            except Exception as e:
                self.logger.error("Failed to process file",
                                filename=file.filename,
                                error=str(e))
                # Create RAW quality material as fallback
                fallback_material = MaterialData.create_raw(
                    material_name=f"Unknown ({file.filename})",
                    source_file_hash=file.sha256_hash,
                    properties={"error": str(e)}
                )
                all_materials.append(fallback_material)

        self.logger.info("Materials processing completed", total_materials=len(all_materials))
        return all_materials

    def _process_single_file(self, file: ValidFile) -> List[MaterialData]:
        """Process a single spreadsheet file to extract material data."""
        try:
            # Read the file based on its type
            if file.file_type == '.csv':
                df = pd.read_csv(file.file_path)
            elif file.file_type in ['.xlsx', '.xls']:
                # Try to read all sheets and find the one with material data
                excel_file = pd.ExcelFile(file.file_path)
                df = self._find_material_sheet(excel_file)
            else:
                raise FileFormatError(f"Unsupported file type: {file.file_type}")

            # Extract material data from the dataframe
            materials = self._extract_materials_from_df(df, file)
            return materials

        except Exception as e:
            self.logger.error("File processing failed", filename=file.filename, error=str(e))
            raise NormalizationError(f"Failed to process {file.filename}: {str(e)}")

    def _find_material_sheet(self, excel_file: pd.ExcelFile) -> pd.DataFrame:
        """Find the sheet containing material test data."""
        # Common sheet names that contain material data
        material_keywords = ['material', 'test', 'data', 'results', 'properties']

        for sheet_name in excel_file.sheet_names:
            sheet_name_lower = sheet_name.lower()
            if any(keyword in sheet_name_lower for keyword in material_keywords):
                return pd.read_excel(excel_file, sheet_name=sheet_name)

        # If no specific sheet found, use the first one
        return pd.read_excel(excel_file, sheet_name=0)

    def _extract_materials_from_df(self, df: pd.DataFrame, file: ValidFile) -> List[MaterialData]:
        """Extract material data from a pandas DataFrame."""
        materials = []

        # Look for material names in the first column or header
        material_names = self._identify_materials(df)

        if not material_names:
            # Single material file - extract all properties
            material_name = self._extract_material_name_from_file(file.filename)
            material = self._extract_single_material(df, material_name, file)
            materials.append(material)
        else:
            # Multiple materials - process each one
            for material_name in material_names:
                material = self._extract_single_material(df, material_name, file)
                materials.append(material)

        return materials

    def _identify_materials(self, df: pd.DataFrame) -> List[str]:
        """Identify material names in the dataframe."""
        material_names = []

        # Look in first column for material names
        if not df.empty and len(df.columns) > 0:
            first_col = df.iloc[:, 0].dropna().astype(str)

            # Common patterns for material names
            material_patterns = [
                r'(PLA|ABS|PETG|TPU|HIPS)\b.*',
                r'.*filament.*',
                r'.*material.*'
            ]

            for value in first_col:
                for pattern in material_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        material_names.append(value.strip())
                        break

        return list(set(material_names))  # Remove duplicates

    def _extract_material_name_from_file(self, filename: str) -> str:
        """Extract material name from filename."""
        # Remove file extension
        name = filename.rsplit('.', 1)[0]

        # Look for common material types
        material_types = ['PLA', 'ABS', 'PETG', 'TPU', 'HIPS', 'ASA', 'PC', 'PEEK']
        for mat_type in material_types:
            if mat_type.lower() in name.lower():
                return f"{mat_type} Material"

        return name

    def _extract_single_material(self, df: pd.DataFrame, material_name: str, file: ValidFile) -> MaterialData:
        """Extract properties for a single material from the dataframe."""
        properties = {}
        quality = QualityRating.OK

        try:
            # Extract properties from the dataframe
            for col in df.columns:
                col_name = str(col).lower().strip()

                # Skip empty or index columns
                if col_name in ['', 'unnamed', 'index'] or col_name.startswith('unnamed'):
                    continue

                # Get the values for this property
                values = df[col].dropna()
                if len(values) == 0:
                    continue

                # Try to extract numerical values with units
                for value in values[:3]:  # Check first 3 non-null values
                    normalized_prop = self._normalize_property(col_name, value)
                    if normalized_prop:
                        properties.update(normalized_prop)
                        break

            # If we couldn't extract much, mark as WARN quality
            if len(properties) < 3:
                quality = QualityRating.WARN

            return MaterialData.create_normalized(
                material_name=material_name,
                source_file_hash=file.sha256_hash,
                properties=properties,
                quality=quality
            )

        except Exception as e:
            self.logger.warning("Material extraction failed, creating RAW entry",
                              material=material_name, error=str(e))
            return MaterialData.create_raw(
                material_name=material_name,
                source_file_hash=file.sha256_hash,
                properties={"raw_data": df.to_dict()}
            )

    def _normalize_property(self, property_name: str, value: Any) -> Optional[Dict[str, Any]]:
        """Normalize a single property value with unit conversion."""
        try:
            # Convert value to string for processing
            value_str = str(value).strip()

            # Try to extract number and unit
            number_match = re.search(r'([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)', value_str)
            if not number_match:
                return None

            original_value = float(number_match.group(1))

            # Extract unit (everything after the number)
            unit_part = value_str[number_match.end():].strip()
            original_unit = unit_part if unit_part else ""

            # Normalize property name
            normalized_name = self._normalize_property_name(property_name)

            # Convert to SI units if mapping exists
            si_value, si_unit = self._convert_to_si(original_value, original_unit, normalized_name)

            return {
                normalized_name: {
                    "value": si_value,
                    "unit": si_unit,
                    "original_value": original_value,
                    "original_unit": original_unit
                }
            }

        except (ValueError, AttributeError) as e:
            self.logger.debug("Property normalization failed",
                            property=property_name, value=value, error=str(e))
            return None

    def _normalize_property_name(self, name: str) -> str:
        """Normalize property names to standard terms."""
        name_lower = name.lower().strip()

        # Use mapping if available
        if name_lower in self.property_mappings:
            return self.property_mappings[name_lower]

        # Common normalizations
        if any(term in name_lower for term in ['tensile', 'tension']):
            return "tensile_strength"
        elif 'young' in name_lower or 'elastic' in name_lower:
            return "elastic_modulus"
        elif 'elongation' in name_lower or 'strain' in name_lower:
            return "elongation_at_break"
        elif 'impact' in name_lower:
            return "impact_strength"
        elif 'flexural' in name_lower:
            return "flexural_strength"
        elif 'density' in name_lower:
            return "density"
        elif 'temperature' in name_lower and 'glass' in name_lower:
            return "glass_transition_temperature"

        # Clean up the name
        cleaned = re.sub(r'[^a-z0-9_]', '_', name_lower)
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')

        return cleaned

    def _convert_to_si(self, value: float, unit: str, property_name: str) -> Tuple[float, str]:
        """Convert value to SI units if mapping exists."""
        unit_lower = unit.lower().strip()

        # Get SI unit for this property
        si_unit = self._get_si_unit(property_name)

        # Apply conversion if mapping exists
        if unit_lower in self.unit_mappings:
            conversion_factor = self.unit_mappings[unit_lower]
            converted_value = value * conversion_factor
            return converted_value, si_unit

        # No conversion needed/available
        return value, unit

    def _get_si_unit(self, property_name: str) -> str:
        """Get the standard SI unit for a property."""
        si_units = {
            "tensile_strength": "Pa",
            "elastic_modulus": "Pa",
            "flexural_strength": "Pa",
            "impact_strength": "J/m",
            "density": "kg/m³",
            "elongation_at_break": "%",
            "glass_transition_temperature": "K"
        }

        return si_units.get(property_name, "")

    def _load_unit_mappings(self) -> Dict[str, float]:
        """Load unit conversion mappings."""
        return {
            # Pressure/Stress conversions to Pa
            "mpa": 1e6,
            "gpa": 1e9,
            "kpa": 1e3,
            "psi": 6894.76,
            "ksi": 6.89476e6,

            # Temperature conversions to Kelvin
            "°c": lambda c: c + 273.15,
            "celsius": lambda c: c + 273.15,
            "°f": lambda f: (f - 32) * 5/9 + 273.15,

            # Density conversions to kg/m³
            "g/cm³": 1000,
            "g/cm^3": 1000,

            # Length conversions to meters
            "mm": 0.001,
            "cm": 0.01,
            "in": 0.0254,
            "ft": 0.3048
        }

    def _load_property_mappings(self) -> Dict[str, str]:
        """Load property name mappings to standard terms."""
        return {
            "ultimate tensile strength": "tensile_strength",
            "tensile strength": "tensile_strength",
            "yield strength": "yield_strength",
            "elastic modulus": "elastic_modulus",
            "young's modulus": "elastic_modulus",
            "elongation at break": "elongation_at_break",
            "strain at break": "elongation_at_break",
            "flexural modulus": "flexural_modulus",
            "flexural strength": "flexural_strength",
            "impact strength": "impact_strength",
            "charpy impact": "impact_strength",
            "izod impact": "impact_strength",
            "density": "density",
            "specific gravity": "density",
            "glass transition temperature": "glass_transition_temperature",
            "tg": "glass_transition_temperature"
        }


class NormalizationError(Exception):
    """Exception raised when data normalization fails."""
    pass


class FileFormatError(Exception):
    """Exception raised when file format is unsupported."""
    pass
