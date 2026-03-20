"""Unified LLM Information Extraction Service - extracts hotel info from text or images"""

import os
import json
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ExtractedInfo:
    """LLM extraction result container"""
    hotel_name: Optional[str] = None
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    room_type: Optional[str] = None
    price: Optional[float] = None
    confidence: Dict[str, float] = field(default_factory=dict)
    ambiguous_fields: List[str] = field(default_factory=list)
    raw_text: Optional[str] = None


class LLMExtractionService:
    """Unified LLM information extraction service - handles both text and images"""

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1").rstrip('/')
        self.vision_model = os.getenv("VISION_MODEL", "gpt-4o")
        self.text_model = os.getenv("TEXT_MODEL", "gpt-3.5-turbo")

        # Validate and set numeric configuration values
        try:
            self.timeout = int(os.getenv("EXTRACTION_TIMEOUT", "60"))
        except ValueError:
            self.timeout = 60

        try:
            self.max_retries = int(os.getenv("EXTRACTION_MAX_RETRIES", "3"))
        except ValueError:
            self.max_retries = 3

        try:
            self.confidence_threshold = float(os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.5"))
        except ValueError:
            self.confidence_threshold = 0.5

        try:
            self.max_text_length = int(os.getenv("EXTRACTION_MAX_TEXT_LENGTH", "4000"))
        except ValueError:
            self.max_text_length = 4000

        # Validate configuration
        if not self.api_key:
            logger.warning("LLM_API_KEY not set in environment variables")
