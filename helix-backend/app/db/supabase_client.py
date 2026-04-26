import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import json

try:
    from supabase import create_client, Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# In-memory mock database for DEMO mode
_mock_reports_db: Dict[str, Dict[str, Any]] = {}
_mock_chat_db: List[Dict[str, Any]] = []


class SupabaseClient:
    """Supabase client for database and storage operations. Supports DEMO mode."""

    _instance: Optional["SupabaseClient"] = None

    def __init__(self):
        """Initialize Supabase client."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase credentials not configured. Using in-memory mock storage.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("✓ Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                self.client = None

    @classmethod
    def get_instance(cls) -> "SupabaseClient":
        """Get or create singleton instance."""
        if cls._instance is None:
            cls._instance = SupabaseClient()
        return cls._instance

    def is_available(self) -> bool:
        """Check if Supabase is available."""
        return self.client is not None

    def create_report(
        self,
        user_id: str,
        file_name: str,
        file_url: str,
        parsed_data: Dict[str, Any]
    ) -> Optional[str]:
        report_id = str(uuid.uuid4())

        if not self.is_available():
            _mock_reports_db[report_id] = {
                "id": report_id,
                "user_id": user_id,
                "file_name": file_name,
                "file_url": file_url,
                "parsed_data": parsed_data,
                "created_at": datetime.utcnow().isoformat(),
                "status": "processing"
            }
            logger.info(f"[MOCK DB] Created report {report_id}")
            return report_id

        try:
            self.client.table("reports").insert({
                "id": report_id,
                "user_id": user_id,
                "file_name": file_name,
                "file_url": file_url,
                "parsed_data": parsed_data,
                "created_at": datetime.utcnow().isoformat(),
                "status": "processing"
            }).execute()
            logger.info(f"Created report {report_id} for user {user_id}")
            return report_id
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return None

    def update_report_status(
        self,
        report_id: str,
        status: str,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not self.is_available():
            if report_id in _mock_reports_db:
                _mock_reports_db[report_id]["status"] = status
                if analysis_result:
                    _mock_reports_db[report_id]["analysis_result"] = analysis_result
                    _mock_reports_db[report_id]["report"] = analysis_result  # Alias for front-end formatting
                return True
            return False

        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            if analysis_result:
                update_data["analysis_result"] = analysis_result
            self.client.table("reports").update(update_data).eq("id", report_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to update report status: {e}")
            return False

    def get_report(self, report_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_available():
            report = _mock_reports_db.get(report_id)
            if report and report.get("user_id") == user_id:
                return report
            return None

        try:
            response = self.client.table("reports").select("*").eq("id", report_id).eq("user_id", user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return None

    def get_user_reports(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.is_available():
            return [r for r in _mock_reports_db.values() if r.get("user_id") == user_id][:limit]

        try:
            response = self.client.table("reports").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get user reports: {e}")
            return []

    def upload_file(self, user_id: str, file_content: bytes, file_name: str) -> Optional[str]:
        if not self.is_available():
            logger.info("[MOCK DB] File uploaded to memory")
            return f"mock_url_{file_name}"

        try:
            timestamp = datetime.utcnow().timestamp()
            storage_path = f"{user_id}/{timestamp}_{file_name}"
            self.client.storage.from_("reports").upload(storage_path, file_content)
            return self.client.storage.from_("reports").get_public_url(storage_path)
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            return None

    def create_chat_message(
        self, report_id: str, user_id: str, message: str, response: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        message_id = str(uuid.uuid4())
        
        if not self.is_available():
            _mock_chat_db.insert(0, {
                "id": message_id,
                "report_id": report_id,
                "user_id": user_id,
                "message": message,
                "response": response,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            })
            return message_id

        try:
            self.client.table("chat_messages").insert({
                "id": message_id,
                "report_id": report_id,
                "user_id": user_id,
                "message": message,
                "response": response,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            return message_id
        except Exception as e:
            logger.error(f"Failed to create chat message: {e}")
            return None

    def get_chat_history(self, report_id: str, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if not self.is_available():
            return [m for m in _mock_chat_db if m.get("report_id") == report_id and m.get("user_id") == user_id][:limit]

        try:
            response = self.client.table("chat_messages").select("*").eq(
                "report_id", report_id
            ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []


def get_supabase() -> SupabaseClient:
    return SupabaseClient.get_instance()
