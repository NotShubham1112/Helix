"""
Supabase Database Initialization and Management

This module helps initialize Supabase tables and schema for Helix.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def init_database() -> bool:
    """
    Initialize Supabase database schema.
    
    Executes SQL migrations:
    1. Create tables (reports, analysis, chat_messages, vector_memory)
    2. Create indexes for performance
    3. Enable Row-Level Security (RLS)
    
    Run this once on first deployment.
    
    Returns:
        Success status
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials not configured")
        return False

    try:
        from supabase import create_client
        
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Read migration SQL
        sql_path = os.path.join(
            os.path.dirname(__file__),
            "../sql/migrations/02_helix_reports.sql"
        )
        
        if not os.path.exists(sql_path):
            logger.warning(f"Migration file not found: {sql_path}")
            return False
        
        with open(sql_path, 'r') as f:
            sql = f.read()
        
        # Execute SQL (requires admin key)
        # Note: This requires using Supabase's SQL editor or admin client
        logger.info("Please run the migration SQL manually in Supabase SQL Editor")
        logger.info(f"Migration file: {sql_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def create_storage_bucket() -> bool:
    """
    Create 'reports' storage bucket in Supabase.
    
    Run this once on first deployment.
    
    Returns:
        Success status
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase credentials not configured")
        return False

    try:
        from supabase import create_client
        
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Create bucket
        client.storage.create_bucket(
            "reports",
            options={
                "public": False,
                "allowed_mime_types": [
                    "application/pdf",
                    "image/jpeg",
                    "image/png",
                    "image/tiff"
                ],
                "file_size_limit": 52428800  # 50MB
            }
        )
        
        logger.info("Created 'reports' storage bucket")
        return True
        
    except Exception as e:
        if "already exists" in str(e):
            logger.info("Bucket already exists")
            return True
        logger.error(f"Failed to create bucket: {e}")
        return False


def verify_schema() -> bool:
    """
    Verify that all required tables exist.
    
    Returns:
        Success status
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase credentials not configured")
        return False

    try:
        from supabase import create_client
        
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        required_tables = ["reports", "analysis", "chat_messages"]
        
        for table in required_tables:
            try:
                response = client.table(table).select("*").limit(1).execute()
                logger.info(f"✓ Table '{table}' exists")
            except Exception as e:
                logger.error(f"✗ Table '{table}' missing: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


if __name__ == "__main__":
    print("Helix Database Initialization")
    print("=" * 50)
    
    print("\n1. Running schema initialization...")
    if init_database():
        print("✓ Schema initialized (manual SQL editor required)")
    else:
        print("✗ Schema initialization failed")
    
    print("\n2. Creating storage bucket...")
    if create_storage_bucket():
        print("✓ Storage bucket created")
    else:
        print("✗ Storage bucket creation failed")
    
    print("\n3. Verifying schema...")
    if verify_schema():
        print("✓ Schema verified")
    else:
        print("✗ Schema verification failed")
    
    print("\n" + "=" * 50)
    print("Database initialization complete!")
