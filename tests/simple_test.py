#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本
"""
import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.order_service import (
    OrderService,
    OrderStatus,
    OrderError,
    InvalidStatusTransitionError,
    OrderNotFoundError
)


def run_test():
    temp_dir = tempfile.mkdtemp()

    try:
        # 创建订单服务
        db_path = os.path.join(temp_dir, "test_xianyu.db")
        service = OrderService(db_path)

        # 创建订单
        print("1. 测试创建订单...")
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
        order = service.create_order(order_data)
        assert order is not None
        print(f"   ✔️ 成功创建订单: {order['order_id']}")

        # 获取订单
        print("\n2. 测试获取订单...")
        retrieved_order = service.get_order_by_id(order["order_id"])
        assert retrieved_order is not None
        assert retrieved_order["order_id"] == order["order_id"]
        print("   ✔️ 成功获取订单")

        # 更新订单状态
        print("\n3. 测试更新订单状态...")
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        assert order["status"] == OrderStatus.CONFIRMED
        print(f"   ✔️ 成功更新状态为: {OrderStatus.CONFIRMED}")

        order = service.update_status(order["order_id"], OrderStatus.PAID)
        assert order["status"] == OrderStatus.PAID
        print(f"   ✔️ 成功更新状态为: {OrderStatus.PAID}")

        order = service.update_status(order["order_id"], OrderStatus.BOOKED)
        assert order["status"] == OrderStatus.BOOKED
        print(f"   ✔️ 成功更新状态为: {OrderStatus.BOOKED}")

        # 获取订单列表
        print("\n4. 测试获取订单列表...")
        orders_by_chat = service.get_orders_by_chat("test_chat_123")
        assert len(orders_by_chat) == 1
        print("   ✔️ 成功获取聊天ID订单列表")

        orders_by_user = service.get_orders_by_user("test_user_456")
        assert len(orders_by_user) == 1
        print("   ✔️ 成功获取用户ID订单列表")

        # 测试无效状态流转
        print("\n5. 测试无效状态流转...")
        try:
            order = service.update_status(order["order_id"], OrderStatus.PENDING)
            assert False, "应该抛出异常"
        except InvalidStatusTransitionError:
            print("   ✔️ 成功检测到无效状态流转")

        # 测试订单完成
        print("\n6. 测试订单完成...")
        order = service.update_status(order["order_id"], OrderStatus.COMPLETED)
        assert order["status"] == OrderStatus.COMPLETED
        print(f"   ✔️ 成功更新状态为: {OrderStatus.COMPLETED}")

        print("\n🎉 所有测试通过!")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return False

    finally:
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
