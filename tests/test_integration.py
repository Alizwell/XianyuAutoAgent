#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统集成测试
测试数据库 -> 模型 -> 服务 -> 执行器的完整链路
"""

import os
import sys
import tempfile
import unittest
from loguru import logger
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_db_instance
from services.order_service import OrderService, OrderStatus
from services.price_service import PriceService
from executor.hotel_executor import HotelExecutor
from dialog.dialog_agent import DialogAgent


class TestIntegration(unittest.TestCase):
    """系统集成测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        logger.info("=== 开始系统集成测试 ===")
        # 创建临时数据库文件
        cls.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.temp_db.close()
        cls.db_path = cls.temp_db.name
        logger.debug(f"使用临时数据库: {cls.db_path}")

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        try:
            os.unlink(cls.db_path)
            logger.debug(f"删除临时数据库: {cls.db_path}")
        except Exception as e:
            logger.warning(f"删除临时数据库失败: {e}")
        logger.info("=== 系统集成测试完成 ===")

    def setUp(self):
        """每个测试方法初始化"""
        # 初始化各个服务
        self.order_service = OrderService(self.db_path)
        self.price_service = PriceService()
        self.hotel_executor = HotelExecutor(mock=True)

        # 测试数据
        self.test_chat_id = "test_chat_123"
        self.test_user_id = "test_user_456"
        self.test_hotel_id = "hotel_789"
        self.test_room_id = "room_010"

        # 日期设置（明天入住，住2晚）
        check_in = datetime.now() + timedelta(days=1)
        check_out = check_in + timedelta(days=2)
        self.test_check_in = check_in.strftime("%Y-%m-%d")
        self.test_check_out = check_out.strftime("%Y-%m-%d")

    def test_database_service_integration(self):
        """测试数据库与服务层集成"""
        logger.info("测试数据库与服务层集成...")

        # 1. 价格服务测试
        price_data = {
            "hotel_id": self.test_hotel_id,
            "room_id": self.test_room_id,
            "check_in_date": self.test_check_in,
            "check_out_date": self.test_check_out,
            "price": 500
        }
        saved_price = self.price_service.save_price(price_data)
        self.assertIsNotNone(saved_price)
        self.assertEqual(saved_price["hotel_id"], self.test_hotel_id)
        self.assertEqual(saved_price["room_id"], self.test_room_id)
        self.assertEqual(saved_price["price"], 500)

        # 查询价格
        queried_price = self.price_service.query_price(
            self.test_hotel_id, self.test_room_id,
            self.test_check_in, self.test_check_out
        )
        self.assertIsNotNone(queried_price)
        self.assertEqual(queried_price["price"], 500)

        # 2. 订单服务测试
        order_data = {
            "chat_id": self.test_chat_id,
            "user_id": self.test_user_id,
            "hotel_id": self.test_hotel_id,
            "room_id": self.test_room_id,
            "check_in_date": self.test_check_in,
            "check_out_date": self.test_check_out
        }
        created_order = self.order_service.create_order(order_data)
        self.assertIsNotNone(created_order)
        self.assertEqual(created_order["chat_id"], self.test_chat_id)
        self.assertEqual(created_order["user_id"], self.test_user_id)
        self.assertEqual(created_order["status"], OrderStatus.PENDING)

        logger.success("数据库与服务层集成测试通过")

    def test_service_executor_integration(self):
        """测试服务层与执行器集成"""
        logger.info("测试服务层与执行器集成...")

        # 测试价格查询
        price_result = self.hotel_executor.query_price(
            self.test_hotel_id, self.test_room_id,
            self.test_check_in, self.test_check_out
        )
        self.assertTrue(price_result["success"])
        self.assertGreater(price_result["price"], 0)

        # 测试预订
        guest_info = {
            "name": "张三",
            "phone": "13800138000",
            "email": "zhangsan@example.com"
        }
        booking_result = self.hotel_executor.book_room(
            self.test_hotel_id, self.test_room_id,
            self.test_check_in, self.test_check_out,
            guest_info
        )
        self.assertTrue(booking_result["success"])
        self.assertIsNotNone(booking_result["booking_id"])

        logger.success("服务层与执行器集成测试通过")

    def test_order_status_flow(self):
        """测试订单状态流转"""
        logger.info("测试订单状态流转...")

        # 创建订单（初始状态PENDING）
        order_data = {
            "chat_id": self.test_chat_id,
            "user_id": self.test_user_id,
            "hotel_id": self.test_hotel_id,
            "room_id": self.test_room_id,
            "check_in_date": self.test_check_in,
            "check_out_date": self.test_check_out
        }
        order = self.order_service.create_order(order_data)
        self.assertEqual(order["status"], OrderStatus.PENDING)

        # 测试状态流转: PENDING → CONFIRMED
        confirmed_order = self.order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        self.assertEqual(confirmed_order["status"], OrderStatus.CONFIRMED)

        # 测试状态流转: CONFIRMED → PAID
        paid_order = self.order_service.update_status(order["order_id"], OrderStatus.PAID)
        self.assertEqual(paid_order["status"], OrderStatus.PAID)

        # 测试状态流转: PAID → BOOKED
        booked_order = self.order_service.update_status(order["order_id"], OrderStatus.BOOKED)
        self.assertEqual(booked_order["status"], OrderStatus.BOOKED)

        # 测试状态流转: BOOKED → COMPLETED
        completed_order = self.order_service.update_status(order["order_id"], OrderStatus.COMPLETED)
        self.assertEqual(completed_order["status"], OrderStatus.COMPLETED)

        logger.success("订单状态流转测试通过")

    def test_dialog_agent_integration(self):
        """测试对话Agent与服务层集成"""
        logger.info("测试对话Agent与服务层集成...")

        # 初始化DialogAgent
        dialog_agent = DialogAgent(self.test_chat_id, self.test_user_id)

        # 模拟价格查询
        price_msg = f"查询{self.test_hotel_id}酒店{self.test_room_id}房型，{self.test_check_in}入住，{self.test_check_out}离店的价格"
        reply = dialog_agent.process_message(price_msg)
        self.assertIsNotNone(reply)
        logger.debug(f"DialogAgent回复: {reply}")

        # 模拟确认预订
        confirm_msg = "确认预订"
        reply = dialog_agent.process_message(confirm_msg)
        self.assertIsNotNone(reply)
        logger.debug(f"DialogAgent回复: {reply}")

        logger.success("对话Agent与服务层集成测试通过")


if __name__ == '__main__':
    unittest.main()
