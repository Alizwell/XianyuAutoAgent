"""Unified LLM Information Extraction Service - extracts hotel info from text or images"""

import os
import json
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import httpx
from httpx import HTTPStatusError, NetworkError, TimeoutException

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

    def _build_text_prompt(self, text: str) -> str:
        return f'''请从用户输入中提取酒店预订信息：

用户输入: "{text}"

提取以下字段：
1. 酒店名称 (hotel_name) - 完整提取用户提到的酒店名称
2. 入住日期 (check_in_date) - 请转换为 YYYY-MM-DD 格式
3. 离店日期 (check_out_date) - 请转换为 YYYY-MM-DD 格式
4. 房型 (room_type) - 用户提到的房型，如：高级大床房、双床房等
5. 价格 (price) - 价格数字，单位元

规则：
- 如果某字段无法确定，请设置为 null
- 价格请提取为数字类型（不是字符串）
- 如果日期只有日月缺少年份月份，请设置该字段为 null，加入 ambiguous_fields
- 如果只给出一个日期范围如 "22-23号"，两个日期都缺年月，都加入 ambiguous_fields
- confidence 字段给出每个字段的置信度（0.0-1.0）
- 置信度 < {self.confidence_threshold} 的字段请设为 null

请严格以JSON格式输出：

{{
  "hotel_name": "酒店名称或null",
  "check_in_date": "YYYY-MM-DD或null",
  "check_out_date": "YYYY-MM-DD或null",
  "room_type": "房型名称或null",
  "price": 299 或 null,
  "confidence": {{
    "hotel_name": 0.95,
    "check_in_date": 0.80,
    "check_out_date": 0.80,
    "room_type": 0.90,
    "price": 0.85
  }},
  "ambiguous_fields": ["check_in_date", "check_out_date"]
}}

如果没有歧义，ambiguous_fields 为空数组 []。'''

    def _parse_json_response(self, content: str) -> ExtractedInfo:
        """Parse LLM JSON response with fault tolerance"""
        result = ExtractedInfo()
        result.raw_text = content

        try:
            # Try direct JSON parse
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(content[start:end])
                else:
                    logger.warning("Failed to extract JSON from LLM response")
                    return result
            except Exception as e:
                logger.warning(f"Failed to parse LLM response: {e}")
                return result

        # Map fields
        result.hotel_name = data.get('hotel_name')
        result.check_in_date = data.get('check_in_date')
        result.check_out_date = data.get('check_out_date')
        result.room_type = data.get('room_type')

        price = data.get('price')
        if price is not None:
            try:
                result.price = float(price)
            except (ValueError, TypeError):
                result.price = None

        result.confidence = data.get('confidence', {})
        result.ambiguous_fields = data.get('ambiguous_fields', [])

        # Apply confidence threshold
        for field in ['hotel_name', 'check_in_date', 'check_out_date', 'room_type', 'price']:
            confidence = result.confidence.get(field, 0.0)
            if confidence < self.confidence_threshold:
                setattr(result, field, None)

        return result

    async def extract_from_text(self, text: str) -> ExtractedInfo:
        """Extract hotel information from plain text"""
        # Input validation
        if not text or not text.strip():
            return ExtractedInfo()

        if len(text) > self.max_text_length:
            text = text[:self.max_text_length]
            logger.warning(f"Text truncated to {self.max_text_length} characters")

        prompt = self._build_text_prompt(text)
        messages = [{"role": "user", "content": prompt}]

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.text_model,
                            "messages": messages,
                            "max_tokens": 1000,
                            "temperature": 0.0,
                        },
                    )
                    response.raise_for_status()
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    return self._parse_json_response(content)

            except (HTTPStatusError, NetworkError, TimeoutException) as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Text extraction failed after {self.max_retries} attempts: {str(e)}")
                    return ExtractedInfo()
                # Exponential backoff
                await asyncio.sleep(1 + attempt * 2)
            except Exception as e:
                # Catch-all for any other unexpected exceptions
                if attempt == self.max_retries - 1:
                    logger.error(f"Text extraction failed after {self.max_retries} attempts: {str(e)}")
                    return ExtractedInfo()
                # Exponential backoff
                await asyncio.sleep(1 + attempt * 2)

        return ExtractedInfo()

    async def extract(
        self,
        text: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
    ) -> ExtractedInfo:
        """
        Unified extraction interface - handles text + image combination
        Priority: image > text if both provided
        """
        if image_url or image_base64:
            return await self.extract_from_image(image_url, image_base64)
        elif text:
            return await self.extract_from_text(text)
        else:
            logger.warning("Neither text nor image provided for extraction")
            return ExtractedInfo()

    async def extract_from_image(self, image_url: Optional[str], image_base64: Optional[str]) -> ExtractedInfo:
        """Extract information from image (to be implemented in Task 3)"""
        logger.warning("Image extraction not implemented yet")
        return ExtractedInfo()
