# Unified LLM Information Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor hotel information extraction from regex pattern matching to a unified LLM-based extraction service that handles both text and images with ambiguity detection.

**Architecture:** Create a new `LLMExtractionService` in the service layer that unifies text extraction and image extraction using LLMs. The service outputs structured `ExtractedInfo` with ambiguity detection. Update `HotelPriceAgent` to use the new service instead of regex extraction. Keep `ParseImageTool` as a thin wrapper around the service for compatibility with existing tool-based architecture.

**Tech Stack:** Python 3.8+, httpx for async HTTP calls, dataclasses for structured output, LLM API (OpenAI-compatible), pytest for testing.

---

## File Changes Summary

| File | Operation | Purpose |
|------|-----------|---------|
| `requirements.txt` | Check/Modify | Verify httpx dependency is present |
| `src/services/llm_extraction_service.py` | Create | New unified LLM extraction service |
| `src/services/__init__.py` | Modify | Export the new service |
| `src/services/image_recognition_service.py` | Delete | Remove old image-only service |
| `src/agent/hotel_price_agent.py` | Modify | Replace regex extraction with new service |
| `src/tools/parse_image_tool.py` | Modify | Adapt to use new extraction service |
| `tests/unit/test_llm_extraction_service.py` | Create | Unit tests for the new service |
| `tests/integration/test_hotel_agent_llm.py` | Create | Integration tests for agent with LLM extraction |
| `.env.example` | Modify | Add new environment variables |
| `examples/hotel_query_example.py` | Modify | Update example for new architecture |
| `docs/superpowers/specs/2026-03-20-unified-llm-extraction-design.md` | Exists | Design specification ✓ |

---

## Task 0: Verify Dependencies

**Files:**
- Check: `requirements.txt`

- [ ] **Step 1: Check if httpx is already in requirements.txt**

```bash
grep httpx requirements.txt
```

- [ ] **Step 2: Add httpx if missing**

If output is empty, add to requirements.txt:
```
httpx>=0.25.0
```

- [ ] **Step 3: Commit if changes needed**

```bash
git add requirements.txt
git commit -m "chore: add httpx dependency for LLM extraction service"
```

---

## Task 1: Create LLM Extraction Service Data Class and Base Structure

**Files:**
- Create: `src/services/llm_extraction_service.py`
- Create: `tests/unit/test_llm_extraction_service.py`
- Modify: `src/services/__init__.py`

- [ ] **Step 1: Write failing test for basic ExtractedInfo structure**

```python
# tests/unit/test_llm_extraction_service.py
import pytest
from src.services.llm_extraction_service import ExtractedInfo, LLMExtractionService


def test_extracted_info_default_values():
    """Test that ExtractedInfo has correct default values"""
    info = ExtractedInfo()
    assert info.hotel_name is None
    assert info.check_in_date is None
    assert info.check_out_date is None
    assert info.room_type is None
    assert info.price is None
    assert info.confidence == {}
    assert info.ambiguous_fields == []


def test_extracted_info_set_values():
    """Test setting values on ExtractedInfo"""
    info = ExtractedInfo()
    info.hotel_name = "汉庭厦门中山路轮渡酒店"
    info.check_in_date = "2026-03-22"
    info.confidence["hotel_name"] = 0.95
    info.ambiguous_fields.append("check_out_date")

    assert info.hotel_name == "汉庭厦门中山路轮渡酒店"
    assert "check_out_date" in info.ambiguous_fields
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_llm_extraction_service.py -v
```
Expected: FAIL with "No module named 'src.services.llm_extraction_service'"

- [ ] **Step 3: Write minimal implementation of `llm_extraction_service.py` with ExtractedInfo and constructor**

```python
"""Unified LLM Information Extraction Service - extracts hotel info from text or images"""

import os
import json
import asyncio
import logging
from dataclasses import dataclass
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
    confidence: Dict[str, float] = None
    ambiguous_fields: List[str] = None
    raw_response: Optional[str] = None

    def __init__(self):
        self.confidence = {}
        self.ambiguous_fields = []
```

Complete the class with constructor:

```python
class LLMExtractionService:
    """Unified LLM information extraction service - handles both text and images"""

    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        self.api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1").rstrip('/')
        self.vision_model = os.getenv("VISION_MODEL", "gpt-4o")
        self.text_model = os.getenv("TEXT_MODEL", "gpt-3.5-turbo")
        self.timeout = int(os.getenv("EXTRACTION_TIMEOUT", "60"))
        self.max_retries = int(os.getenv("EXTRACTION_MAX_RETRIES", "3"))
        self.confidence_threshold = float(os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.5"))
        self.max_text_length = int(os.getenv("EXTRACTION_MAX_TEXT_LENGTH", "4000"))

        # Validate configuration
        if not self.api_key:
            logger.warning("LLM_API_KEY not set in environment variables")
```

- [ ] **Step 4: Update `src/services/__init__.py` to export new service**

Add to `src/services/__init__.py`:
```python
from .llm_extraction_service import LLMExtractionService, ExtractedInfo

__all__ = ["LLMExtractionService", "ExtractedInfo"]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/unit/test_llm_extraction_service.py -v
```
Expected: Both tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/services/llm_extraction_service.py src/services/__init__.py tests/unit/test_llm_extraction_service.py
git commit -m "feat: add ExtractedInfo and LLMExtractionService base structure"
```

---

## Task 2: Implement Text Extraction with LLM

**Files:**
- Modify: `src/services/llm_extraction_service.py`
- Modify: `tests/unit/test_llm_extraction_service.py`

- [ ] **Step 1: Add test for text extraction method**

```python
async def test_extract_from_text_basic():
    """Test basic text extraction"""
    service = LLMExtractionService()
    # This test requires LLM API, skip if no API key
    if not service.api_key:
        pytest.skip("LLM_API_KEY not configured")

    result = await service.extract_from_text("汉庭厦门中山路轮渡酒店 22-23号，高级大床房")
    assert result.hotel_name == "汉庭厦门中山路轮渡酒店"
    assert "check_in_date" in result.ambiguous_fields
    assert "check_out_date" in result.ambiguous_fields
    assert result.room_type == "高级大床房"


async def test_extract_from_text_complete_dates():
    """Test extraction with complete dates"""
    service = LLMExtractionService()
    if not service.api_key:
        pytest.skip("LLM_API_KEY not configured")

    result = await service.extract_from_text("汉庭厦门中山路 2026-03-22 2026-03-23 高级大床房")
    assert result.hotel_name == "汉庭厦门中山路"
    assert result.check_in_date == "2026-03-22"
    assert result.check_out_date == "2026-03-23"
    assert result.room_type == "高级大床房"
    assert result.ambiguous_fields == []
```

Add to imports (already in file, just ensure it's present):
```python
import pytest
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_llm_extraction_service.py::test_extract_from_text_basic -v
```
Expected: FAIL with "AttributeError: 'LLMExtractionService' object has no attribute 'extract_from_text'"

- [ ] **Step 3: Implement `extract_from_text` with prompt building and JSON parsing**

First add the `_build_text_prompt` method:

```python
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
```

Add the `_parse_json_response` method:

```python
    def _parse_json_response(self, content: str) -> ExtractedInfo:
        """Parse LLM JSON response with fault tolerance"""
        result = ExtractedInfo()
        result.raw_response = content

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
```

Add the main `extract_from_text` method with retry:

```python
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

            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Text extraction failed after {self.max_retries} attempts: {str(e)}")
                    return ExtractedInfo()
                # Exponential backoff
                await asyncio.sleep(1 + attempt * 2)

        return ExtractedInfo()
```

Add the unified `extract` method:

```python
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
```

- [ ] **Step 4: Run tests to see if they pass (requires API key)**

```bash
pytest tests/unit/test_llm_extraction_service.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/services/llm_extraction_service.py tests/unit/test_llm_extraction_service.py
git commit -m "feat: implement text extraction with LLM"
```

---

## Task 3: Implement Image Extraction (Multimodal LLM)

**Files:**
- Modify: `src/services/llm_extraction_service.py`
- Modify: `tests/unit/test_llm_extraction_service.py`

- [ ] **Step 1: Add test for image extraction**

```python
async def test_extract_from_image():
    """Test image extraction (multimodal)"""
    service = LLMExtractionService()
    if not service.api_key:
        pytest.skip("LLM_API_KEY not configured")

    # Test with a sample image URL - this would be a real screenshot in actual test
    # For unit test, we mainly test the method signature and error handling
    result = await service.extract_from_image(image_url="https://example.com/hotel-screenshot.jpg")
    # We expect it to fail gracefully with invalid URL
    assert isinstance(result, ExtractedInfo)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_llm_extraction_service.py::test_extract_from_image -v
```
Expected: FAIL with no attribute `extract_from_image`

- [ ] **Step 3: Implement `extract_from_image` method**

Add `_build_image_prompt`:

```python
    def _build_image_prompt(self) -> str:
        return '''请分析这张酒店预订相关的图片，提取以下信息：

1. 酒店名称 (hotel_name)
2. 入住日期 (check_in_date，格式：YYYY-MM-DD)
3. 离店日期 (check_out_date，格式：YYYY-MM-DD)
4. 房型 (room_type，如：高级大床房、双床房等)
5. 价格 (price，数字，单位元)

请以JSON格式返回结果：
{
  "hotel_name": "酒店名称",
  "check_in_date": "2024-01-01",
  "check_out_date": "2024-01-02",
  "room_type": "房型名称",
  "price": 299,
  "confidence": {
    "hotel_name": 0.95,
    "check_in_date": 0.98,
    "check_out_date": 0.98,
    "room_type": 0.90,
    "price": 0.95
  },
  "ambiguous_fields": []
}

如果某字段无法识别，请设置为null。confidence字段表示每个字段的识别置信度（0-1之间的小数）。如果日期不完整缺少年月，请放入ambiguous_fields。'''
```

Add `extract_from_image`:

```python
    async def extract_from_image(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
    ) -> ExtractedInfo:
        """Extract hotel information from image using multimodal LLM"""
        # Input validation
        if not image_url and not image_base64:
            logger.warning("Neither image_url nor image_base64 provided")
            return ExtractedInfo()

        # Build image content
        if image_url:
            image_content = {
                "type": "image_url",
                "image_url": {"url": image_url}
            }
        else:  # image_base64
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }

        prompt = self._build_image_prompt()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_content
                ]
            }
        ]

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
                            "model": self.vision_model,
                            "messages": messages,
                            "max_tokens": 1000,
                            "temperature": 0.1,
                        },
                    )
                    response.raise_for_status()
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    return self._parse_json_response(content)

            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Image extraction failed after {self.max_retries} attempts: {str(e)}")
                    return ExtractedInfo()
                await asyncio.sleep(1 + attempt * 2)

        return ExtractedInfo()
```

- [ ] **Step 4: Add `close` method for cleanup**

```python
    async def close(self):
        """Cleanup resources - currently no persistent connections"""
        pass
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_llm_extraction_service.py -v
```
Expected: PASS (the URL test will fail gracefully but type check passes)

- [ ] **Step 6: Commit**

```bash
git add src/services/llm_extraction_service.py tests/unit/test_llm_extraction_service.py
git commit -m "feat: implement image extraction with multimodal LLM"
```

---

## Task 4: Update ParseImageTool to Use New Service

**Files:**
- Modify: `src/tools/parse_image_tool.py`

- [ ] **Step 1: Read current file to understand structure**

Read file: `src/tools/parse_image_tool.py`

- [ ] **Step 2: Modify to use LLMExtractionService, preserve `image_type` parameter for backward compatibility**

Replace content:

```python
"""Parse hotel image tool - uses LLM extraction service"""

from typing import Optional, Dict, Any
from src.tools.base_tool import BaseTool, ToolResult
from src.services import LLMExtractionService, ExtractedInfo


class ParseImageTool(BaseTool):
    """解析酒店预订图片工具"""

    name = "parse_hotel_image"
    description = "解析酒店预订界面图片，提取酒店名称、日期、房型信息"

    def __init__(self, extraction_service: Optional[LLMExtractionService] = None):
        self.extraction_service = extraction_service or LLMExtractionService()

    async def execute(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_type: str = "screenshot",
        **kwargs
    ) -> ToolResult:
        try:
            result = await self.extraction_service.extract_from_image(
                image_url=image_url,
                image_base64=image_base64
            )
            # image_type is kept for backward compatibility but not used in new service
            return ToolResult.success_result(data=result.__dict__)
        except Exception as e:
            return ToolResult.error_result(f"图片解析失败: {str(e)}")

    async def close(self):
        await self.extraction_service.close()
```

- [ ] **Step 3: Verify imports are correct**

Check that `src/tools/__init__.py` still exports this tool.

- [ ] **Step 4: Commit**

```bash
git add src/tools/parse_image_tool.py
git commit -m "refactor: adapt ParseImageTool to use new unified LLMExtractionService (keep image_type)"
```

---

## Task 5: Refactor HotelPriceAgent to Use New LLM Extraction Service

**Files:**
- Modify: `src/agent/hotel_price_agent.py`

- [ ] **Step 1: Add dependency injection for LLMExtractionService**

Modify imports:

```python
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from src.models import QueryState, QueryStep
from src.tools import (
    BaseTool,
    ToolResult,
    SearchHotelTool,
    QueryPriceTool,
    ParseImageTool
)
from src.agent.state_manager import StateManager
from src.services import LLMExtractionService, ExtractedInfo
```

Modify `__init__`:

```python
    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        search_hotel_tool: Optional[SearchHotelTool] = None,
        query_price_tool: Optional[QueryPriceTool] = None,
        parse_image_tool: Optional[ParseImageTool] = None,
        extraction_service: Optional[LLMExtractionService] = None,
    ):
        """
        初始化Agent

        Args:
            state_manager: 状态管理器
            search_hotel_tool: 搜索酒店工具
            query_price_tool: 查询价格工具
            parse_image_tool: 解析图片工具
            extraction_service: 统一LLM信息提取服务
        """
        self.state_manager = state_manager or StateManager()
        self.search_hotel_tool = search_hotel_tool or SearchHotelTool()
        self.query_price_tool = query_price_tool or QueryPriceTool()
        self.parse_image_tool = parse_image_tool or ParseImageTool()
        self.extraction_service = extraction_service or LLMExtractionService()
```

- [ ] **Step 2: Remove `_extract_info_from_text` regex method, replace with LLM call in `process_message`**

Modify `process_message` method:

```python
    async def process_message(
        self,
        session_id: str,
        user_message: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理用户消息

        Args:
            session_id: 会话ID
            user_message: 用户消息
            image_url: 图片URL（如果用户发送了图片）
            image_base64: 图片base64

        Returns:
            处理结果，包含回复内容和是否完成
        """
        # 获取或创建状态
        state = self.state_manager.get_state(session_id)
        if not state:
            state = self.state_manager.create_state(session_id)

        # Use unified LLM extraction for both text and image
        extracted = await self.extraction_service.extract(
            text=user_message,
            image_url=image_url,
            image_base64=image_base64
        )

        # Fill extracted info into state - only fill if not already set and confidence good
        if extracted.hotel_name and not state.hotel_name:
            state.hotel_name = extracted.hotel_name
        if extracted.check_in_date and not state.check_in_date:
            normalized = self._normalize_date(extracted.check_in_date)
            state.check_in_date = normalized
        if extracted.check_out_date and not state.check_out_date:
            normalized = self._normalize_date(extracted.check_out_date)
            state.check_out_date = normalized
        if extracted.room_type and not state.room_type:
            state.room_type = extracted.room_type
        if extracted.price:
            # Store price if extracted for reference
            pass

        # LLM already identified ambiguous fields - ambiguous fields are already null
        # so _advance_to_missing_step will handle asking user to confirm
        self._advance_to_missing_step(state)

        # 根据当前步骤处理
        result = await self._process_by_step(state)

        # 保存状态
        self.state_manager.save_state(state)

        return {
            'reply': result['reply'],
            'complete': state.current_step == QueryStep.COMPLETE,
            'state': state.to_dict(),
            'result': result.get('result'),
            'ambiguous_fields': extracted.ambiguous_fields,
        }
```

- [ ] **Step 3: Remove the old `_parse_image` method that uses ParseImageTool directly**
- Remove the old `_extract_info_from_text` method entirely
- Keep `_normalize_date`, `_calculate_nights` since they are still useful

- [ ] **Step 4: Update `close` method to close extraction_service**

Update existing `close` method:

```python
    async def close(self):
        """关闭所有工具和服务"""
        await self.search_hotel_tool.close()
        await self.query_price_tool.close()
        await self.parse_image_tool.close()
        await self.extraction_service.close()
```

- [ ] **Step 5: Verify `_advance_to_missing_step` works with new approach**

Existing method already checks for missing fields (null/empty) and advances to the appropriate step. Since LLM sets ambiguous fields to null, this existing logic works correctly. No changes needed.

- [ ] **Step 6: Test the changes by running existing tests**

```bash
pytest tests/unit/test_models.py -v
```

- [ ] **Step 7: Commit**

```bash
git add src/agent/hotel_price_agent.py
git commit -m "refactor: replace regex extraction with unified LLM extraction service in HotelPriceAgent"
```

---

## Task 6: Remove Old Image Recognition Service

**Files:**
- Delete: `src/services/image_recognition_service.py`
- Modify: `src/services/__init__.py`

- [ ] **Step 1: Remove old image recognition service file**

```bash
git rm src/services/image_recognition_service.py
```

- [ ] **Step 2: Remove from `src/services/__init__.py` exports**

Remove line that imports `ImageRecognitionService`.

- [ ] **Step 3: Commit**

```bash
git add src/services/__init__.py
git commit -m "refactor: remove old ImageRecognitionService (merged into LLMExtractionService)"
```

---

## Task 7: Update Configuration and Documentation

**Files:**
- Modify: `.env.example`
- Create: `tests/integration/test_hotel_agent_llm.py`

- [ ] **Step 1: Add new environment variables to `.env.example`**

Add to `.env.example`:

```
# 统一LLM提取服务配置
LLM_API_KEY=your_api_key
LLM_API_BASE=https://api.openai.com/v1
VISION_MODEL=gpt-4o
TEXT_MODEL=gpt-3.5-turbo
EXTRACTION_TIMEOUT=60
EXTRACTION_MAX_RETRIES=3
EXTRACTION_CONFIDENCE_THRESHOLD=0.5
EXTRACTION_MAX_TEXT_LENGTH=4000
```

- [ ] **Step 2: Create simple integration test**

Create `tests/integration/test_hotel_agent_llm.py`:

```python
"""Integration test for HotelPriceAgent with LLM extraction"""

import pytest
from src.agent.hotel_price_agent import HotelPriceAgent
from src.services import LLMExtractionService


@pytest.mark.asyncio
async def test_agent_process_message_with_llm_extraction():
    """Test agent processes message with LLM extraction"""
    service = LLMExtractionService()
    if not service.api_key:
        pytest.skip("LLM_API_KEY not configured")

    agent = HotelPriceAgent(extraction_service=service)
    result = await agent.process_message(
        session_id="test-001",
        user_message="汉庭厦门中山路轮渡酒店 22-23号，高级大床房"
    )

    assert result['state']['hotel_name'] == "汉庭厦门中山路轮渡酒店"
    assert result['state']['room_type'] == "高级大床房"
    # Dates should be missing (ambiguous), expect question
    assert not result['complete']
    assert "日期" in result['reply'] or "22" in result['reply']


@pytest.mark.asyncio
async def test_agent_process_complete_info():
    """Test agent with complete information"""
    service = LLMExtractionService()
    if not service.api_key:
        pytest.skip("LLM_API_KEY not configured")

    agent = HotelPriceAgent(extraction_service=service)
    result = await agent.process_message(
        session_id="test-002",
        user_message="汉庭厦门中山路 2026-03-22 2026-03-23 高级大床房"
    )

    assert result['state']['hotel_name'] == "汉庭厦门中山路"
    assert result['state']['check_in_date'] == "2026-03-22"
    assert result['state']['check_out_date'] == "2026-03-23"
    assert result['state']['room_type'] == "高级大床房"
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/integration/test_hotel_agent_llm.py -v
```

- [ ] **Step 4: Commit**

```bash
git add .env.example tests/integration/test_hotel_agent_llm.py
git commit -m "docs: add env vars example and integration test"
```

---

## Task 8: Update Example

**Files:**
- Modify: `examples/hotel_query_example.py`

- [ ] **Step 1: Read current example file**

Read: `examples/hotel_query_example.py`

- [ ] **Step 2: Update imports and usage to reflect new architecture**

Update imports to include `LLMExtractionService` and verify the example still works with new structure. If example manually creates `ImageRecognitionService`, update to use `LLMExtractionService` instead.

- [ ] **Step 3: Commit**

```bash
git add examples/hotel_query_example.py
git commit -m "docs: update example for new LLM extraction architecture"
```

---

## Task 9: Run Full Test Suite and Fix Issues

**Files:**
- Multiple (fix any issues found)

- [ ] **Step 1: Run all hotel-related tests**

```bash
pytest tests -k hotel -v
```

- [ ] **Step 2: Fix any failing tests**

- [ ] **Step 3: Run full test suite**

```bash
pytest
```

- [ ] **Step 4: Commit any fixes**

```bash
git add .
git commit -m "fix: fix failing tests after refactoring"
```

---

## Done Check List

- [ ] All dependencies verified/added
- [ ] All tests pass
- [ ] Unified extraction service works for both text and images
- [ ] Ambiguity detection works (asks user for missing info like month)
- [ ] Old image service removed
- [ ] ParseImageTool adapted to new service with backward compatibility
- [ ] Environment variables documented (including EXTRACTION_MAX_TEXT_LENGTH)
- [ ] Agent close() method cleans up extraction_service
- [ ] Tests added
- [ ] Example updated

## Testing Strategy

1. **Unit tests**: Test `ExtractedInfo` structure, JSON parsing, error handling
2. **Integration tests**: End-to-end agent processing with LLM extraction (skipped when no API key)
3. **Manual testing**: Try various user inputs to verify ambiguity detection works

## Notes for Implementer

- `superpowers:test-driven-development` skill recommended
- Follow TDD: write test first → see fail → implement → verify pass
- The API key is read from environment, tests skip if not configured
- Keep the existing `_normalize_date` method - it handles edge cases LLM might miss
- LLM temperature set to 0.0 for text extraction (deterministic), 0.1 for images
- Backward compatibility: `image_type` parameter preserved in ParseImageTool
