#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
订单服务测试
"""
import os
import sys
import json
import pytest
from datetime import datetime, timedelta
from services.order_service import (
    OrderService,
    OrderStatus,
    OrderError,
    InvalidStatusTransitionError,
    OrderNotFoundError
)


def get_test_db_path():
    """获取测试数据库路径"""
    return os.path.join(os.path.dirname(__file__), "test_xianyu.db")


def clean_test_db():
    """清理测试数据库"""
    db_path = get_test_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
def order_service():
    """创建订单服务实例（每个测试函数都会清理并重新创建）"""
    clean_test_db()
    service = OrderService(get_test_db_path())
    yield service
    clean_test_db()


class TestOrderService:
    """订单服务测试类"""

    # ==================== 测试订单创建 ====================

    def test_create_order_success(self, order_service: OrderService):
        """测试成功创建订单"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "original_price": 1000.0,
            "final_price": 900.0,
            "metadata": {"source": "test"},
            "remark": "测试订单"
        }

        order = order_service.create_order(order_data)
        assert order is not None
        assert order["order_id"].startswith("ORD")
        assert order["chat_id"] == order_data["chat_id"]
        assert order["user_id"] == order_data["user_id"]
        assert order["hotel_id"] == order_data["hotel_id"]
        assert order["room_id"] == order_data["room_id"]
        assert order["check_in_date"] == order_data["check_in_date"]
        assert order["check_out_date"] == order_data["check_out_date"]
        assert order["status"] == OrderStatus.PENDING
        assert order["original_price"] == order_data["original_price"]
        assert order["final_price"] == order_data["final_price"]
        assert order["metadata"] == order_data["metadata"]
        assert order["remark"] == order_data["remark"]

    def test_create_order_missing_required_fields(self, order_service: OrderService):
        """测试缺少必填字段"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789"
        }

        with pytest.raises(OrderError):
            order_service.create_order(order_data)

    # ==================== 测试订单查询 ====================

    def test_get_order_by_id(self, order_service: OrderService):
        """测试根据ID获取订单"""
        # 创建订单
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        created_order = order_service.create_order(order_data)

        # 查询订单
        order = order_service.get_order_by_id(created_order["order_id"])
        assert order is not None
        assert order["order_id"] == created_order["order_id"]
        assert order["chat_id"] == order_data["chat_id"]

    def test_get_order_by_id_not_found(self, order_service: OrderService):
        """测试查询不存在的订单"""
        order = order_service.get_order_by_id("invalid_order_id")
        assert order is None

    def test_get_orders_by_chat(self, order_service: OrderService):
        """测试根据聊天ID获取订单列表"""
        chat_id = "test_chat_123"
        user_id = "test_user_456"

        # 创建多个订单
        order_data1 = {
            "chat_id": chat_id,
            "user_id": user_id,
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }

        order_data2 = {
            "chat_id": chat_id,
            "user_id": user_id,
            "hotel_id": "hotel_456",
            "room_id": "room_02",
            "check_in_date": "2026-03-25",
            "check_out_date": "2026-03-27"
        }

        order_service.create_order(order_data1)
        order_service.create_order(order_data2)

        # 查询订单列表
        orders = order_service.get_orders_by_chat(chat_id)
        assert len(orders) == 2

        # 验证订单属性
        order_ids = [order["order_id"] for order in orders]
        for order in orders:
            assert order["chat_id"] == chat_id
            assert order["user_id"] == user_id

    def test_get_orders_by_user(self, order_service: OrderService):
        """测试根据用户ID获取订单列表"""
        chat_id1 = "test_chat_123"
        chat_id2 = "test_chat_456"
        user_id = "test_user_789"

        # 创建多个订单
        order_data1 = {
            "chat_id": chat_id1,
            "user_id": user_id,
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }

        order_data2 = {
            "chat_id": chat_id2,
            "user_id": user_id,
            "hotel_id": "hotel_456",
            "room_id": "room_02",
            "check_in_date": "2026-03-25",
            "check_out_date": "2026-03-27"
        }

        order_service.create_order(order_data1)
        order_service.create_order(order_data2)

        # 查询订单列表
        orders = order_service.get_orders_by_user(user_id)
        assert len(orders) == 2

        # 验证订单属性
        chat_ids = [order["chat_id"] for order in orders]
        assert chat_id1 in chat_ids
        assert chat_id2 in chat_ids
        for order in orders:
            assert order["user_id"] == user_id

    # ==================== 测试状态流转 ====================

    def test_update_status_pending_to_confirmed(self, order_service: OrderService):
        """测试从PENDING → CONFIRMED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        assert updated_order["status"] == OrderStatus.CONFIRMED
        assert updated_order["confirmed_at"] is not None

    def test_update_status_pending_to_expired(self, order_service: OrderService):
        """测试从PENDING → EXPIRED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.EXPIRED)
        assert updated_order["status"] == OrderStatus.EXPIRED
        assert updated_order["completed_at"] is not None

    def test_update_status_confirmed_to_paid(self, order_service: OrderService):
        """测试从CONFIRMED → PAID"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.PAID)
        assert updated_order["status"] == OrderStatus.PAID
        assert updated_order["paid_at"] is not None

    def test_update_status_paid_to_booked(self, order_service: OrderService):
        """测试从PAID → BOOKED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = order_service.update_status(order["order_id"], OrderStatus.PAID)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.BOOKED)
        assert updated_order["status"] == OrderStatus.BOOKED
        assert updated_order["booked_at"] is not None

    def test_update_status_booked_to_completed(self, order_service: OrderService):
        """测试从BOOKED → COMPLETED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = order_service.update_status(order["order_id"], OrderStatus.PAID)
        order = order_service.update_status(order["order_id"], OrderStatus.BOOKED)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.COMPLETED)
        assert updated_order["status"] == OrderStatus.COMPLETED
        assert updated_order["completed_at"] is not None

    def test_update_status_paid_to_refunded(self, order_service: OrderService):
        """测试从PAID → REFUNDED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = order_service.update_status(order["order_id"], OrderStatus.PAID)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.REFUNDED)
        assert updated_order["status"] == OrderStatus.REFUNDED

    def test_update_status_refunded_to_completed(self, order_service: OrderService):
        """测试从REFUNDED → COMPLETED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = order_service.update_status(order["order_id"], OrderStatus.PAID)
        order = order_service.update_status(order["order_id"], OrderStatus.REFUNDED)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.COMPLETED)
        assert updated_order["status"] == OrderStatus.COMPLETED
        assert updated_order["completed_at"] is not None

    def test_update_status_confirmed_to_cancelled(self, order_service: OrderService):
        """测试从CONFIRMED → CANCELLED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.CANCELLED)
        assert updated_order["status"] == OrderStatus.CANCELLED

    def test_update_status_cancelled_to_completed(self, order_service: OrderService):
        """测试从CANCELLED → COMPLETED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = order_service.update_status(order["order_id"], OrderStatus.CANCELLED)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.COMPLETED)
        assert updated_order["status"] == OrderStatus.COMPLETED

    # ==================== 测试无效状态流转 ====================

    def test_invalid_status_transition_pending_to_paid(self, order_service: OrderService):
        """测试无效状态流转 PENDING → PAID"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        with pytest.raises(InvalidStatusTransitionError):
            order_service.update_status(order["order_id"], OrderStatus.PAID)

    def test_invalid_status_transition_confirmed_to_booked(self, order_service: OrderService):
        """测试无效状态流转 CONFIRMED → BOOKED"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        with pytest.raises(InvalidStatusTransitionError):
            order_service.update_status(order["order_id"], OrderStatus.BOOKED)

    def test_invalid_status_transition_completed_to_any(self, order_service: OrderService):
        """测试COMPLETED状态不能再流转"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        order = order_service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = order_service.update_status(order["order_id"], OrderStatus.PAID)
        order = order_service.update_status(order["order_id"], OrderStatus.BOOKED)
        order = order_service.update_status(order["order_id"], OrderStatus.COMPLETED)
        with pytest.raises(InvalidStatusTransitionError):
            order_service.update_status(order["order_id"], OrderStatus.CANCELLED)

    # ==================== 测试错误场景 ====================

    def test_update_status_order_not_found(self, order_service: OrderService):
        """测试更新不存在的订单状态"""
        with pytest.raises(OrderNotFoundError):
            order_service.update_status("invalid_order_id", OrderStatus.CONFIRMED)

    def test_update_status_same_status(self, order_service: OrderService):
        """测试更新到相同状态"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = order_service.create_order(order_data)
        updated_order = order_service.update_status(order["order_id"], OrderStatus.PENDING)
        assert updated_order["status"] == OrderStatus.PENDING
        assert updated_order["order_id"] == order["order_id"]

    # ==================== 测试获取所有订单 ====================

    def test_get_all_orders(self, order_service: OrderService):
        """测试获取所有订单"""
        # 创建多个订单
        order_data1 = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }

        order_data2 = {
            "chat_id": "test_chat_456",
            "user_id": "test_user_789",
            "hotel_id": "hotel_456",
            "room_id": "room_02",
            "check_in_date": "2026-03-25",
            "check_out_date": "2026-03-27"
        }

        order1 = order_service.create_order(order_data1)
        order2 = order_service.create_order(order_data2)

        # 更新第二个订单状态
        order_service.update_status(order2["order_id"], OrderStatus.CONFIRMED)

        # 获取所有订单
        all_orders = order_service.get_all_orders()
        assert len(all_orders) == 2

        # 检查所有订单ID都包含在内
        order_ids = [order["order_id"] for order in all_orders]
        assert order1["order_id"] in order_ids
        assert order2["order_id"] in order_ids

        # 验证订单状态
        for order in all_orders:
            if order["order_id"] == order1["order_id"]:
                assert order["status"] == OrderStatus.PENDING
            elif order["order_id"] == order2["order_id"]:
                assert order["status"] == OrderStatus.CONFIRMED

    def test_get_all_orders_filter_status(self, order_service: OrderService):
        """测试按状态过滤获取订单"""
        order_data1 = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }

        order_data2 = {
            "chat_id": "test_chat_456",
            "user_id": "test_user_789",
            "hotel_id": "hotel_456",
            "room_id": "room_02",
            "check_in_date": "2026-03-25",
            "check_out_date": "2026-03-27"
        }

        order1 = order_service.create_order(order_data1)
        order2 = order_service.create_order(order_data2)

        order_service.update_status(order2["order_id"], OrderStatus.CONFIRMED)

        # 获取PENDING状态的订单
        pending_orders = order_service.get_all_orders(OrderStatus.PENDING)
        assert len(pending_orders) == 1
        assert pending_orders[0]["order_id"] == order1["order_id"]

        # 获取CONFIRMED状态的订单
        confirmed_orders = order_service.get_all_orders(OrderStatus.CONFIRMED)
        assert len(confirmed_orders) == 1
        assert confirmed_orders[0]["order_id"] == order2["order_id"]

    def test_get_all_orders_limit(self, order_service: OrderService):
        """测试限制返回数量"""
        for i in range(10):
            order_service.create_order({
                "chat_id": f"test_chat_{i}",
                "user_id": "test_user",
                "hotel_id": "hotel_789",
                "room_id": "room_01",
                "check_in_date": "2026-03-20",
                "check_out_date": "2026-03-22"
            })

        orders = order_service.get_all_orders(limit=5)
        assert len(orders) == 5

    # ==================== 边界情况测试 ====================

    def test_create_order_minimal_data(self, order_service: OrderService):
        """测试使用最少必填字段创建订单"""
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }

        order = order_service.create_order(order_data)
        assert order is not None
        assert order["room_count"] == 1
        assert order["currency"] == "CNY"
        assert order["original_price"] is None
        assert order["final_price"] is None
        assert order["metadata"] is None
        assert order["remark"] is None

    def test_create_order_with_metadata(self, order_service: OrderService):
        """测试包含复杂metadata的订单"""
        metadata = {
            "source": "test",
            "platform": "xianyu",
            "options": {"breakfast": True, "wifi": True}
        }

        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "metadata": metadata
        }

        order = order_service.create_order(order_data)
        assert order["metadata"] == metadata


if __name__ == "__main__":
    # 运行所有测试
    clean_test_db()
    pytest.main([__file__, "-v"])
    clean_test_db()
