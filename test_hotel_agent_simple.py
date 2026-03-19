#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 HotelAgent（直接使用）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from XianyuAgent import HotelAgent

def test_hotel_agent():
    """测试 HotelAgent"""
    print("=== 测试 HotelAgent ===")

    try:
        # 创建 HotelAgent 实例
        hotel_agent = HotelAgent()
        print("HotelAgent 已创建")

        # 测试完整流程
        messages = [
            "我想订北京希尔顿酒店，4月1日入住，住2晚",
            "确认预订",
            "已付款"
        ]

        item_desc = "北京希尔顿酒店"
        context = []

        for i, msg in enumerate(messages):
            print(f"\n---\n用户({i+1}): {msg}")

            # 调用 HotelAgent 的 generate 方法
            reply = hotel_agent.generate(msg, item_desc, context)

            print(f"系统({i+1}): {reply}")

            # 添加到上下文
            context.append({"role": "user", "content": msg})
            context.append({"role": "assistant", "content": reply})

        print("\n=== HotelAgent 测试完成 ===")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_hotel_agent()
