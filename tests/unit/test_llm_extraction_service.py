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
