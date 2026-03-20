import pytest
import asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
