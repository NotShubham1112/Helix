import logging
import io
from typing import Optional

logger = logging.getLogger(__name__)

class OcrEngine:
    """
    Modular OCR Engine for Helix MVP.
    Designed to be production-upgradable with different backends (PaddleOCR, EasyOCR, Tesseract).
    """

    def __init__(self, preferred_engine: str = "easyocr"):
        self.preferred_engine = preferred_engine
        self._engine_instance = None
        self._initialized = False

    def _initialize_engine(self):
        """Lazy initialization of OCR engine to save memory/VRAM if not used."""
        if self._initialized:
            return True
            
        try:
            if self.preferred_engine == "easyocr":
                import easyocr
                # Using English as default. gpu=False by default to avoid VRAM conflicts with LLM
                self._engine_instance = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR initialized successfully (CPU mode).")
            elif self.preferred_engine == "paddleocr":
                from paddleocr import PaddleOCR
                # use_gpu=True if user has RTX 3050, but we default to CPU for initial safety
                self._engine_instance = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
                logger.info("PaddleOCR initialized successfully.")
            else:
                logger.warning(f"Engine {self.preferred_engine} not specifically handled. Falling back to simple mock.")
                self._engine_instance = None
            
            self._initialized = True
            return True
        except ImportError as e:
            logger.error(f"Failed to import {self.preferred_engine}: {e}. Check local installation.")
            self._initialized = False
            return False
        except Exception as e:
            logger.error(f"Error initializing OCR engine: {e}")
            self._initialized = False
            return False

    def perform_ocr(self, image_bytes: bytes) -> str:
        """
        Runs OCR on provided image bytes. 
        MOCK MODE: Returns a deterministic string for MVP functionality without heavy dependencies.
        """
        logger.info("OCR Engine running in LIGHTWEIGHT MOCK MODE.")
        # This string is carefully formatted to match the regex in app/services/mvp_hba1c.py
        return "PATIENT: JOHN DOE | TEST: HEMOGLOBIN A1C | RESULT: 6.2 % | DATE: 2026-04-19"

# Singleton instance
ocr_engine = OcrEngine(preferred_engine="easyocr")
