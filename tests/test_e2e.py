#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试
模拟完整对话流程
"""

import os
import sys
import unittest
from loguru import logger
from dialog.dialog_agent import DialogAgent
from services.order_service import OrderService
from services.price_service import PriceService
from executor.hotel_executor import HotelExecutor

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEndToEnd(unittest.TestCase):
    """端到端测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        logger.info("=== 开始端到端测试 ===")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        logger.info("=== 端到端测试完成 ===")

    def setUp(self):
        """每个测试方法初始化"""
        # 确保数据库目录存在
        os.makedirs("data", exist_ok=True)

        # 删除默认的数据库以确保测试隔离
        default_db = "data/xianyu.db"
        if os.path.exists(default_db):
            try:
                os.remove(default_db)
                logger.debug(f"删除默认数据库: {default_db}")
            except Exception as e:
                logger.warning(f"无法删除默认数据库: {e}")

        # 初始化测试数据
        self.chat_id = "e2e_test_chat"
        self.user_id = "e2e_test_user"

        # 创建各个服务和Agent
        self.order_service = OrderService()
        self.price_service = PriceService()
        self.hotel_executor = HotelExecutor(mock=True)

        # 创建 DialogAgent
        self.dialog_agent = DialogAgent(
            self.chat_id,
            self.user_id,
            self.order_service,
            self.price_service,
            self.hotel_executor
        )

    def tearDown(self):
        """每个测试方法清理"""
        try:
            os.unlink(self.db_path)
            logger.debug(f"删除临时数据库: {self.db_path}")
        except Exception as e:
            logger.warning(f"删除临时数据库失败: {e}")

    def test_complete_booking_flow(self):
        """测试完整的预订流程"""
        logger.info("测试完整的预订流程...")

        # 1. 用户发起预订请求
        logger.info("--- 用户：我想订北京希尔顿酒店，4月1日入住，住2晚 ---")
        user_msg1 = "我想订北京希尔顿酒店，4月1日入住，住2晚"
        reply1 = self.dialog_agent.process_message(user_msg1)
        logger.info(f"--- 系统：{reply1} ---")

        # 验证回复包含价格信息
        self.assertIn("查询到价格", reply1)
        self.assertIn("是否确认预订", reply1)

        # 2. 用户确认预订
        logger.info("--- 用户：确认预订 ---")
        user_msg2 = "确认预订"
        reply2 = self.dialog_agent.process_message(user_msg2)
        logger.info(f"--- 系统：{reply2} ---")

        # 验证回复包含订单号
        self.assertIn("订单已创建", reply2)
        self.assertIn("订单号", reply2)
        self.assertIn("请在付款后告知我", reply2)

        # 提取订单号
        import re
        order_id_match = re.search(r'订单号[：:]\s*(ORD[0-9A-Z]{20})', reply2)
        self.assertIsNotNone(order_id_match, "订单号应该存在于回复中")
        if order_id_match:
            order_id = order_id_match.group(1)
            logger.debug(f"提取到订单号: {order_id}")

        # 3. 用户通知已付款
        logger.info("--- 用户：已付款 ---")
        user_msg3 = "已付款"
        reply3 = self.dialog_agent.process_message(user_msg3)
        logger.info(f"--- 系统：{reply3} ---")

        # 验证回复包含预订成功信息
        self.assertIn("预订成功", reply3)
        self.assertIn("预订号", reply3)

        logger.success("完整预订流程测试通过")

    def test_price_query_only(self):
        """测试仅查询价格不预订的流程"""
        logger.info("测试仅查询价格的流程...")

        # 用户查询价格
        user_msg = "查询上海希尔顿酒店大床房3月20日入住，3月22日离店的价格"
        reply = self.dialog_agent.process_message(user_msg)

        # 验证回复
        self.assertIn("查询到价格", reply)
        self.assertIn("是否确认预订", reply)

        logger.success("仅查询价格的流程测试通过")

    def test_cancellation_flow(self):
        """测试取消预订的流程"""
        logger.info("测试取消预订的流程...")

        # 1. 先开始一个预订流程
        user_msg1 = "订广州希尔顿酒店5月1日入住，5月3日离店"
        reply1 = self.dialog_agent.process_message(user_msg1)

        # 2. 用户取消
        user_msg2 = "取消"
        reply2 = self.dialog_agent.process_message(user_msg2)

        # 验证取消成功
        self.assertIn("已取消当前操作", reply2)
        self.assertIn("有什么可以帮您的", reply2)

        logger.success("取消预订流程测试通过")


if __name__ == '__main__':
    unittest.main()
