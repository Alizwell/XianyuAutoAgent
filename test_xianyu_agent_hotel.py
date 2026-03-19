#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 XianyuAgent 对酒店预订意图的识别和处理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from XianyuAgent import XianyuReplyBot

def test_hotel_intent_recognition():
    """测试酒店意图识别"""
    print("=== 测试 XianyuAgent 酒店意图识别 ===")

    try:
        # 创建 XianyuReplyBot 实例
        bot = XianyuReplyBot()
        print("XianyuReplyBot 已创建")

        # 测试酒店相关的消息
        test_messages = [
            "我想订北京希尔顿酒店，4月1日入住，住2晚",
            "帮我查询北京希尔顿酒店的价格",
            "预订北京希尔顿酒店大床房4月1日至4月3日",
            "有没有北京的酒店推荐",
            "查看我的订单详情"
        ]

        for msg in test_messages:
            print(f"\n---\n用户消息: {msg}")

            # 调用 generate_reply 方法
            item_desc = "北京希尔顿酒店预订"
            context = []
            reply = bot.generate_reply(msg, item_desc, context)

            print(f"系统回复: {reply}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_hotel_intent_recognition()
