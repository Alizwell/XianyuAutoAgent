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
