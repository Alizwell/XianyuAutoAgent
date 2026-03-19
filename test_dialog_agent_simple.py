#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 DialogAgent 测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dialog.dialog_agent import DialogAgent

def test_dialog_agent():
    """测试 DialogAgent 的基本功能"""
    print("=== 测试 DialogAgent ===")

    # 创建 DialogAgent 实例
    chat_id = "test_chat_123"
    user_id = "test_user_456"
    agent = DialogAgent(chat_id, user_id)

    print(f"DialogAgent 已创建，chat_id: {chat_id}, user_id: {user_id}")

    # 测试1: 查询价格
    print("\n=== 测试查询价格 ===")
    response = agent.process_message("我想订北京希尔顿酒店，4月1日入住，住2晚")
    print(f"用户输入: 我想订北京希尔顿酒店，4月1日入住，住2晚")
    print(f"系统回复: {response}")

    # 测试2: 确认预订
    print("\n=== 测试确认预订 ===")
    response = agent.process_message("确认预订")
    print(f"用户输入: 确认预订")
    print(f"系统回复: {response}")

    # 测试3: 付款通知
    print("\n=== 测试付款通知 ===")
    response = agent.process_message("已付款")
    print(f"用户输入: 已付款")
    print(f"系统回复: {response}")

    print("\n=== DialogAgent 测试完成 ===")

if __name__ == "__main__":
    test_dialog_agent()
