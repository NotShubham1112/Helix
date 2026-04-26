from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from app.db.supabase_client import get_supabase
from app.services.report_service import ReportService
from app.dependencies.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{report_id}")
async def get_report_details(
    report_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get detailed report information.
    
    Args:
        report_id: Report identifier
        user_id: Authenticated user ID
    
    Returns:
        Detailed report with analysis
    """
    try:
        supabase = get_supabase()
        report = supabase.get_report(report_id, user_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Format for display
        formatted = ReportService.format_for_display(report)

        return {
            "status": "success",
            "report": formatted
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get report details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/raw")
async def get_raw_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get raw unformatted report data.
    
    Args:
        report_id: Report identifier
        user_id: Authenticated user ID
    
    Returns:
        Raw report JSON
    """
    try:
        supabase = get_supabase()
        report = supabase.get_report(report_id, user_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return {
            "status": "success",
            "data": report
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get raw report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/export")
async def export_report(
    report_id: str,
    format: str = "json",
    user_id: str = Depends(get_current_user_id)
):
    """
    Export report in different formats.
    
    Args:
        report_id: Report identifier
        format: Export format (json, pdf, csv)
        user_id: Authenticated user ID
    
    Returns:
        Exported report
    """
    try:
        supabase = get_supabase()
        report = supabase.get_report(report_id, user_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if format == "json":
            return {
                "status": "success",
                "format": "json",
                "data": report
            }
        elif format == "csv":
            # Convert to CSV format
            csv_data = _convert_to_csv(report)
            return {
                "status": "success",
                "format": "csv",
                "data": csv_data
            }
        else:
            raise HTTPException(status_code=400, detail=f"Format {format} not supported")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a report (with confirmation).
    
    Args:
        report_id: Report identifier
        user_id: Authenticated user ID
    
    Returns:
        Deletion status
    """
    try:
        supabase = get_supabase()
        report = supabase.get_report(report_id, user_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        # Delete from database
        if supabase.is_available():
            supabase.client.table("reports").delete().eq("id", report_id).execute()

        logger.info(f"Deleted report {report_id} for user {user_id}")

        return {
            "status": "success",
            "message": "Report deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _convert_to_csv(report: dict) -> str:
    """Convert report to CSV format."""
    lines = []

    # Header
    lines.append("Lab Test,Value,Unit,Status,Normal Range")

    # Values
    for test, data in report.get("parsed_data", {}).get("values", {}).items():
        line = f"{test},{data.get('value')},{data.get('unit')},{data.get('status')},{data.get('normal_range')}"
        lines.append(line)

    return "\n".join(lines)
