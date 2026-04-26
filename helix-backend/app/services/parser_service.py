from typing import Dict, Any, Optional
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class LabValue:
    value: float
    unit: str
    status: str
    normal_range: str
    raw_text: str


class ParserService:
    """Parse and normalize medical lab values."""

    # Medical reference ranges
    REFERENCE_RANGES = {
        "glucose": {"min": 70, "max": 100, "unit": "mg/dL", "abnormal_high": 126, "abnormal_low": 70},
        "hemoglobin": {"min": 12.0, "max": 17.5, "unit": "g/dL", "abnormal_high": 17.5, "abnormal_low": 7.0},
        "hematocrit": {"min": 36, "max": 46, "unit": "%", "abnormal_high": 46, "abnormal_low": 27},
        "creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dL", "abnormal_high": 1.5, "abnormal_low": 0.4},
        "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L", "abnormal_high": 5.5, "abnormal_low": 2.8},
        "sodium": {"min": 136, "max": 145, "unit": "mEq/L", "abnormal_high": 150, "abnormal_low": 120},
        "wbc": {"min": 4.5, "max": 11.0, "unit": "K/uL", "abnormal_high": 15, "abnormal_low": 2.0},
        "platelets": {"min": 150, "max": 400, "unit": "K/uL", "abnormal_high": 500, "abnormal_low": 50},
        "blood_pressure_systolic": {"min": 90, "max": 120, "unit": "mmHg", "abnormal_high": 140, "abnormal_low": 80},
        "blood_pressure_diastolic": {"min": 60, "max": 80, "unit": "mmHg", "abnormal_high": 90, "abnormal_low": 50},
        "heart_rate": {"min": 60, "max": 100, "unit": "bpm", "abnormal_high": 120, "abnormal_low": 40},
    }

    @staticmethod
    def parse_value(raw_text: str, test_name: str) -> Optional[LabValue]:
        """
        Parse a raw lab value text.
        
        Args:
            raw_text: Raw text from OCR (e.g., "140 mg/dL")
            test_name: Name of the test (e.g., "glucose")
        
        Returns:
            LabValue object or None if parsing fails
        """
        try:
            # Extract number and unit
            match = re.match(r"([\d.]+)\s*(.+)?", raw_text.strip())
            if not match:
                return None

            value_str, unit_str = match.groups()
            value = float(value_str)
            unit = unit_str.strip() if unit_str else ""

            # Get reference range
            ref = ParserService.REFERENCE_RANGES.get(test_name, {})
            if not ref:
                return None

            # Determine status
            if value > ref.get("abnormal_high", ref["max"]):
                status = "high"
            elif value < ref.get("abnormal_low", ref["min"]):
                status = "low"
            else:
                status = "normal"

            normal_range = f"{ref['min']}-{ref['max']} {ref['unit']}"

            return LabValue(
                value=value,
                unit=unit or ref["unit"],
                status=status,
                normal_range=normal_range,
                raw_text=raw_text,
            )

        except Exception as e:
            logger.warning(f"Failed to parse {test_name}: {raw_text} - {e}")
            return None

    @staticmethod
    def normalize_extracted_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize OCR-extracted data into structured format.
        
        Args:
            extracted_data: Raw extracted data from OCR
        
        Returns:
            Normalized and validated data with status indicators
        """
        normalized = {
            "extracted_at": extracted_data.get("extracted_at"),
            "values": {},
            "abnormalities": [],
            "summary": {
                "total_tests": 0,
                "abnormal_count": 0,
                "critical_count": 0,
            }
        }

        for test_name, raw_value in extracted_data.items():
            if test_name in ["extracted_at", "status"]:
                continue

            lab_value = ParserService.parse_value(raw_value, test_name)
            if not lab_value:
                continue

            normalized["values"][test_name] = {
                "value": lab_value.value,
                "unit": lab_value.unit,
                "status": lab_value.status,
                "normal_range": lab_value.normal_range,
                "raw": lab_value.raw_text,
            }

            normalized["summary"]["total_tests"] += 1

            if lab_value.status != "normal":
                normalized["abnormalities"].append({
                    "test": test_name,
                    "value": lab_value.value,
                    "unit": lab_value.unit,
                    "status": lab_value.status,
                    "range": lab_value.normal_range,
                })
                normalized["summary"]["abnormal_count"] += 1

                # Mark critical values
                if lab_value.status == "high" and lab_value.value > ParserService.REFERENCE_RANGES[test_name]["abnormal_high"] * 1.5:
                    normalized["summary"]["critical_count"] += 1

        return normalized

    @staticmethod
    def detect_patterns(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect clinical patterns from normalized data.
        
        Args:
            normalized_data: Normalized lab values
        
        Returns:
            Patterns detected from the data
        """
        patterns = {
            "possible_anemia": False,
            "possible_diabetes": False,
            "possible_kidney_disease": False,
            "hypertension": False,
            "tachycardia": False,
            "leukopenia": False,
            "thrombocytopenia": False,
        }

        values = normalized_data.get("values", {})

        # Anemia pattern
        if values.get("hemoglobin", {}).get("status") == "low":
            patterns["possible_anemia"] = True

        # Diabetes pattern
        if values.get("glucose", {}).get("value", 0) > 126:
            patterns["possible_diabetes"] = True

        # Kidney disease pattern
        if values.get("creatinine", {}).get("status") == "high":
            patterns["possible_kidney_disease"] = True

        # Hypertension pattern
        if (values.get("blood_pressure_systolic", {}).get("status") == "high" or 
            values.get("blood_pressure_diastolic", {}).get("status") == "high"):
            patterns["hypertension"] = True

        # Tachycardia pattern
        if values.get("heart_rate", {}).get("status") == "high":
            patterns["tachycardia"] = True

        # Leukopenia pattern
        if values.get("wbc", {}).get("status") == "low":
            patterns["leukopenia"] = True

        # Thrombocytopenia pattern
        if values.get("platelets", {}).get("status") == "low":
            patterns["thrombocytopenia"] = True

        return {k: v for k, v in patterns.items() if v}

    @staticmethod
    def generate_health_assessment(normalized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a health assessment from normalized data.
        
        Args:
            normalized_data: Normalized lab values
        
        Returns:
            Health assessment with risk indicators
        """
        patterns = ParserService.detect_patterns(normalized_data)
        abnormalities = normalized_data.get("abnormalities", [])

        risk_indicators = []
        for pattern in patterns:
            if pattern == "possible_anemia":
                risk_indicators.append({
                    "type": "hematologic",
                    "indicator": "anemia",
                    "severity": "moderate",
                })
            elif pattern == "possible_diabetes":
                risk_indicators.append({
                    "type": "metabolic",
                    "indicator": "hyperglycemia",
                    "severity": "moderate",
                })
            elif pattern == "possible_kidney_disease":
                risk_indicators.append({
                    "type": "renal",
                    "indicator": "renal_dysfunction",
                    "severity": "high",
                })
            elif pattern == "hypertension":
                risk_indicators.append({
                    "type": "cardiovascular",
                    "indicator": "elevated_bp",
                    "severity": "moderate",
                })

        return {
            "data_quality": {
                "total_values": normalized_data["summary"]["total_tests"],
                "abnormal_values": normalized_data["summary"]["abnormal_count"],
            },
            "abnormalities": abnormalities,
            "patterns": patterns,
            "risk_indicators": risk_indicators,
        }
