import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.services.llm_service import call_llm
from app.services.parser_service import ParserService
from app.models.schemas import HelixResponse

logger = logging.getLogger(__name__)


class ReportService:
    """Generate structured health reports with safety rules."""

    HELIX_PROMPT_TEMPLATE = """
You are HELIX, a medical AI assistant. Your role is to analyze medical lab results and generate structured insights.

CRITICAL SAFETY RULES:
1. NEVER output a diagnosis like "you have diabetes" or "you have kidney disease"
2. ALWAYS use careful language like "indication of possible risk", "values suggest consideration of"
3. If data is insufficient, return: {{"error": "insufficient_data", "reason": "description"}}
4. Only assess abnormal values found in the data
5. Do NOT guess or infer diagnoses beyond the data

PATIENT DATA:
{patient_data}

TASK:
Analyze the above lab values and generate a JSON response with:
- summary: Brief overview of findings (2-3 sentences, NO diagnosis)
- abnormalities: List of unusual values found
- risk_assessment: Possible risk factors based on values (use "indication of", "suggests consideration of")
- recommendations: Practical recommendations for patient discussion with doctor
- confidence: 0.0-1.0 based on data completeness

OUTPUT MUST BE VALID JSON only, no markdown or extra text.
"""

    @staticmethod
    def generate_report(
        user_id: str,
        parsed_data: Dict[str, Any],
        report_id: str,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete health report from parsed data.
        
        Args:
            user_id: User identifier
            parsed_data: Normalized lab values
            report_id: Report identifier
            file_metadata: Original file metadata
        
        Returns:
            Complete report with analysis
        """
        try:
            # Generate assessment from parsed data
            assessment = ParserService.generate_health_assessment(parsed_data)

            # Build prompt
            data_summary = ReportService._format_data_for_prompt(parsed_data)
            prompt = ReportService.HELIX_PROMPT_TEMPLATE.format(
                patient_data=data_summary
            )

            # Call LLM for report generation
            logger.info(f"Generating report for user {user_id}")
            llm_response = call_llm(
                prompt=prompt,
                model="auto",
                use_ollama=True
            )

            # Parse LLM response
            report_content = ReportService._parse_llm_response(llm_response)

            # Build final report
            report = {
                "id": report_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "file_metadata": file_metadata or {},
                "parsed_data": parsed_data,
                "assessment": assessment,
                "report": report_content,
                "metadata": {
                    "version": "1.0",
                    "status": "completed",
                    "total_values": assessment["data_quality"]["total_values"],
                    "abnormal_values": assessment["data_quality"]["abnormal_values"],
                }
            }

            logger.info(f"Report generated successfully for user {user_id}")
            return {
                "status": "success",
                "report": report
            }

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                "status": "error",
                "error": str(e),
                "report": None
            }

    @staticmethod
    def _format_data_for_prompt(parsed_data: Dict[str, Any]) -> str:
        """Format parsed data into readable text for LLM."""
        lines = []
        values = parsed_data.get("values", {})

        for test_name, test_data in values.items():
            value = test_data.get("value")
            unit = test_data.get("unit")
            status = test_data.get("status")
            normal_range = test_data.get("normal_range")

            lines.append(
                f"- {test_name.replace('_', ' ').title()}: {value} {unit} "
                f"(Status: {status}, Normal range: {normal_range})"
            )

        return "\n".join(lines) if lines else "No lab values available"

    @staticmethod
    def _parse_llm_response(response: str) -> Dict[str, Any]:
        """
        Parse LLM response to ensure valid structure.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Validated report content
        """
        try:
            # Extract JSON from response
            import json
            import re

            # Try to find JSON object in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(response)

            # Validate required fields
            required_fields = ["summary", "abnormalities", "risk_assessment", "recommendations", "confidence"]
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = [] if field in ["abnormalities", "risk_assessment", "recommendations"] else (0.0 if field == "confidence" else "")

            return parsed

        except Exception as e:
            logger.warning(f"Failed to parse LLM response, using fallback: {e}")
            return {
                "summary": "Unable to generate report. Please try again.",
                "abnormalities": [],
                "risk_assessment": [],
                "recommendations": ["Consult with a healthcare provider for complete assessment"],
                "confidence": 0.0,
                "error": str(e)
            }

    @staticmethod
    def format_for_display(report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format report for frontend display.
        
        Args:
            report: Complete report
        
        Returns:
            Formatted report for display
        """
        return {
            "id": report.get("id"),
            "created_at": report.get("created_at"),
            "summary": report.get("report", {}).get("summary"),
            "abnormalities": report.get("report", {}).get("abnormalities", []),
            "risk_assessment": report.get("report", {}).get("risk_assessment", []),
            "recommendations": report.get("report", {}).get("recommendations", []),
            "confidence": report.get("report", {}).get("confidence", 0.0),
            "data_summary": {
                "total_values": report.get("metadata", {}).get("total_values"),
                "abnormal_values": report.get("metadata", {}).get("abnormal_values"),
            }
        }

    @staticmethod
    def validate_report_safety(report: Dict[str, Any]) -> bool:
        """
        Validate report for safety compliance.
        
        Args:
            report: Report to validate
        
        Returns:
            True if safe, False otherwise
        """
        dangerous_keywords = [
            "diagnosed with", "you have", "patient has", "diagnosis",
            "definitely", "certainly", "confirmed", "proven"
        ]

        report_text = json.dumps(report).lower()

        for keyword in dangerous_keywords:
            if keyword in report_text:
                logger.warning(f"Safety violation detected: {keyword}")
                return False

        return True
