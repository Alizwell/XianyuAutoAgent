"""酒店价格查询示例"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.hotel_price_agent import HotelPriceAgent

# 加载环境变量
load_dotenv()


async def example_text_query():
    """文本查询示例"""
    print("=== 文本查询示例 ===")

    agent = HotelPriceAgent()
    session_id = "test-session-001"

    # 逐步提供信息
    result = await agent.process_message(
        session_id=session_id,
        user_message="汉庭南京夫子庙酒店"
    )
    print(f"\n回复: {result['reply']}")

    result = await agent.process_message(
        session_id=session_id,
        user_message="入住日期 2026-03-20"
    )
    print(f"\n回复: {result['reply']}")

    result = await agent.process_message(
        session_id=session_id,
        user_message="离店日期 2026-03-21"
    )
    print(f"\n回复: {result['reply']}")

    result = await agent.process_message(
        session_id=session_id,
        user_message="高级大床房"
    )
    print(f"\n回复: {result['reply']}")

    if result['complete']:
        print(f"\n✅ 查询完成，结果:\n{result['result']}")

    await agent.close()


async def example_full_query():
    """一次性提供完整信息查询示例"""
    print("\n\n=== 完整信息查询示例 ===")

    agent = HotelPriceAgent()
    session_id = "test-session-002"

    # 一次性提供所有信息
    result = await agent.process_message(
        session_id=session_id,
        user_message="我要查询汉庭南京夫子庙酒店 2026-03-20入住 2026-03-21离店 高级大床房"
    )
    print(f"\n回复:\n{result['reply']}")

    if result['complete']:
        print(f"\n✅ 查询完成")

    await agent.close()


if __name__ == "__main__":
    asyncio.run(example_text_query())
    # asyncio.run(example_full_query())
