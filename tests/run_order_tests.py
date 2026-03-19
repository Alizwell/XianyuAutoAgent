#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的测试脚本，不依赖pytest
"""
import os
import sys
import json
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.order_service import (
    OrderService,
    OrderStatus,
    OrderError,
    InvalidStatusTransitionError,
    OrderNotFoundError
)

# 使用临时目录
temp_dir = tempfile.mkdtemp()


def get_test_db_path():
    """获取测试数据库路径"""
    return os.path.join(temp_dir, "test_xianyu.db")


def clean_test_db():
    """清理测试数据库"""
    db_path = get_test_db_path()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            pass


class TestRunner:
    """简单的测试运行器"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def assert_true(self, condition, message=""):
        if not condition:
            raise AssertionError(message or "Expected True")

    def assert_equal(self, a, b, message=""):
        if a != b:
            raise AssertionError(message or f"Expected {a} == {b}")

    def assert_in(self, item, container, message=""):
        if item not in container:
            raise AssertionError(message or f"Expected {item} in {container}")

    def assert_raises(self, exception_type, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            raise AssertionError(f"Expected {exception_type.__name__}")
        except exception_type:
            pass

    def run_test(self, test_name, test_func):
        try:
            test_func()
            print(f"  ✓ {test_name}")
            self.passed += 1
        except AssertionError as e:
            print(f"  ✗ {test_name}: {e}")
            self.failed += 1
            self.errors.append((test_name, str(e)))
        except Exception as e:
            print(f"  ✗ {test_name}: ERROR - {e}")
            self.failed += 1
            self.errors.append((test_name, f"ERROR: {e}"))

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Total: {total}, Passed: {self.passed}, Failed: {self.failed}")
        if self.errors:
            print("\nErrors:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*60}")
        return self.failed == 0


def main():
    """运行所有测试"""
    print("Running order service tests...")

    clean_test_db()

    # 创建测试运行器
    runner = TestRunner()

    # 创建服务实例
    service = OrderService(get_test_db_path())

    # ==================== 测试创建订单 ====================

    def test_create_order_success():
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
        runner.assert_true(order is not None)
        runner.assert_true(order["order_id"].startswith("ORD"))
        runner.assert_equal(order["chat_id"], order_data["chat_id"])
        runner.assert_equal(order["user_id"], order_data["user_id"])
        runner.assert_equal(order["hotel_id"], order_data["hotel_id"])
        runner.assert_equal(order["room_id"], order_data["room_id"])
        runner.assert_equal(order["check_in_date"], order_data["check_in_date"])
        runner.assert_equal(order["check_out_date"], order_data["check_out_date"])
        runner.assert_equal(order["status"], OrderStatus.PENDING)
        runner.assert_equal(order["original_price"], order_data["original_price"])
        runner.assert_equal(order["final_price"], order_data["final_price"])
        runner.assert_equal(json.dumps(order["metadata"]), json.dumps(order_data["metadata"]))
        runner.assert_equal(order["remark"], order_data["remark"])

    def test_create_order_missing_required_fields():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789"
        }

        runner.assert_raises(OrderError, service.create_order, order_data)

    # ==================== 测试订单查询 ====================

    def test_get_order_by_id():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        created_order = service.create_order(order_data)

        order = service.get_order_by_id(created_order["order_id"])
        runner.assert_true(order is not None)
        runner.assert_equal(order["order_id"], created_order["order_id"])
        runner.assert_equal(order["chat_id"], order_data["chat_id"])

    def test_get_order_by_id_not_found():
        order = service.get_order_by_id("invalid_order_id")
        runner.assert_true(order is None)

    def test_get_orders_by_chat():
        chat_id = "test_chat_123"
        user_id = "test_user_456"

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

        service.create_order(order_data1)
        service.create_order(order_data2)

        orders = service.get_orders_by_chat(chat_id)
        runner.assert_equal(len(orders), 2)

        for order in orders:
            runner.assert_equal(order["chat_id"], chat_id)
            runner.assert_equal(order["user_id"], user_id)

    def test_get_orders_by_user():
        chat_id1 = "test_chat_123"
        chat_id2 = "test_chat_456"
        user_id = "test_user_789"

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

        service.create_order(order_data1)
        service.create_order(order_data2)

        orders = service.get_orders_by_user(user_id)
        runner.assert_equal(len(orders), 2)

        chat_ids = [order["chat_id"] for order in orders]
        runner.assert_in(chat_id1, chat_ids)
        runner.assert_in(chat_id2, chat_ids)
        for order in orders:
            runner.assert_equal(order["user_id"], user_id)

    # ==================== 测试状态流转 ====================

    def test_update_status_pending_to_confirmed():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        updated_order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        runner.assert_equal(updated_order["status"], OrderStatus.CONFIRMED)
        runner.assert_true(updated_order["confirmed_at"] is not None)

    def test_update_status_pending_to_expired():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        updated_order = service.update_status(order["order_id"], OrderStatus.EXPIRED)
        runner.assert_equal(updated_order["status"], OrderStatus.EXPIRED)
        runner.assert_true(updated_order["completed_at"] is not None)

    def test_update_status_confirmed_to_paid():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        updated_order = service.update_status(order["order_id"], OrderStatus.PAID)
        runner.assert_equal(updated_order["status"], OrderStatus.PAID)
        runner.assert_true(updated_order["paid_at"] is not None)

    def test_update_status_paid_to_booked():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = service.update_status(order["order_id"], OrderStatus.PAID)
        updated_order = service.update_status(order["order_id"], OrderStatus.BOOKED)
        runner.assert_equal(updated_order["status"], OrderStatus.BOOKED)
        runner.assert_true(updated_order["booked_at"] is not None)

    def test_update_status_booked_to_completed():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = service.update_status(order["order_id"], OrderStatus.PAID)
        order = service.update_status(order["order_id"], OrderStatus.BOOKED)
        updated_order = service.update_status(order["order_id"], OrderStatus.COMPLETED)
        runner.assert_equal(updated_order["status"], OrderStatus.COMPLETED)
        runner.assert_true(updated_order["completed_at"] is not None)

    def test_update_status_paid_to_refunded():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = service.update_status(order["order_id"], OrderStatus.PAID)
        updated_order = service.update_status(order["order_id"], OrderStatus.REFUNDED)
        runner.assert_equal(updated_order["status"], OrderStatus.REFUNDED)

    def test_update_status_refunded_to_completed():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = service.update_status(order["order_id"], OrderStatus.PAID)
        order = service.update_status(order["order_id"], OrderStatus.REFUNDED)
        updated_order = service.update_status(order["order_id"], OrderStatus.COMPLETED)
        runner.assert_equal(updated_order["status"], OrderStatus.COMPLETED)
        runner.assert_true(updated_order["completed_at"] is not None)

    def test_update_status_confirmed_to_cancelled():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        updated_order = service.update_status(order["order_id"], OrderStatus.CANCELLED)
        runner.assert_equal(updated_order["status"], OrderStatus.CANCELLED)

    def test_update_status_cancelled_to_completed():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = service.update_status(order["order_id"], OrderStatus.CANCELLED)
        updated_order = service.update_status(order["order_id"], OrderStatus.COMPLETED)
        runner.assert_equal(updated_order["status"], OrderStatus.COMPLETED)

    # ==================== 测试无效状态流转 ====================

    def test_invalid_status_transition_pending_to_paid():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        runner.assert_raises(InvalidStatusTransitionError, service.update_status, order["order_id"], OrderStatus.PAID)

    def test_invalid_status_transition_confirmed_to_booked():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        runner.assert_raises(InvalidStatusTransitionError, service.update_status, order["order_id"], OrderStatus.BOOKED)

    def test_invalid_status_transition_completed_to_any():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        order = service.update_status(order["order_id"], OrderStatus.CONFIRMED)
        order = service.update_status(order["order_id"], OrderStatus.PAID)
        order = service.update_status(order["order_id"], OrderStatus.BOOKED)
        order = service.update_status(order["order_id"], OrderStatus.COMPLETED)
        runner.assert_raises(InvalidStatusTransitionError, service.update_status, order["order_id"], OrderStatus.CANCELLED)

    # ==================== 测试错误场景 ====================

    def test_update_status_order_not_found():
        runner.assert_raises(OrderNotFoundError, service.update_status, "invalid_order_id", OrderStatus.CONFIRMED)

    def test_update_status_same_status():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }
        order = service.create_order(order_data)
        updated_order = service.update_status(order["order_id"], OrderStatus.PENDING)
        runner.assert_equal(updated_order["status"], OrderStatus.PENDING)
        runner.assert_equal(updated_order["order_id"], order["order_id"])

    # ==================== 边界情况测试 ====================

    def test_create_order_minimal_data():
        order_data = {
            "chat_id": "test_chat_123",
            "user_id": "test_user_456",
            "hotel_id": "hotel_789",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22"
        }

        order = service.create_order(order_data)
        runner.assert_true(order is not None)
        runner.assert_equal(order["room_count"], 1)
        runner.assert_equal(order["currency"], "CNY")
        runner.assert_true(order["original_price"] is None)
        runner.assert_true(order["final_price"] is None)
        runner.assert_true(order["metadata"] is None)
        runner.assert_true(order["remark"] is None)

    def test_create_order_with_metadata():
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

        order = service.create_order(order_data)
        runner.assert_equal(order["metadata"], metadata)

    # ==================== 运行所有测试 ====================

    all_tests = [
        ("test_create_order_success", test_create_order_success),
        ("test_create_order_missing_required_fields", test_create_order_missing_required_fields),
        ("test_get_order_by_id", test_get_order_by_id),
        ("test_get_order_by_id_not_found", test_get_order_by_id_not_found),
        ("test_get_orders_by_chat", test_get_orders_by_chat),
        ("test_get_orders_by_user", test_get_orders_by_user),
        ("test_update_status_pending_to_confirmed", test_update_status_pending_to_confirmed),
        ("test_update_status_pending_to_expired", test_update_status_pending_to_expired),
        ("test_update_status_confirmed_to_paid", test_update_status_confirmed_to_paid),
        ("test_update_status_paid_to_booked", test_update_status_paid_to_booked),
        ("test_update_status_booked_to_completed", test_update_status_booked_to_completed),
        ("test_update_status_paid_to_refunded", test_update_status_paid_to_refunded),
        ("test_update_status_refunded_to_completed", test_update_status_refunded_to_completed),
        ("test_update_status_confirmed_to_cancelled", test_update_status_confirmed_to_cancelled),
        ("test_update_status_cancelled_to_completed", test_update_status_cancelled_to_completed),
        ("test_invalid_status_transition_pending_to_paid", test_invalid_status_transition_pending_to_paid),
        ("test_invalid_status_transition_confirmed_to_booked", test_invalid_status_transition_confirmed_to_booked),
        ("test_invalid_status_transition_completed_to_any", test_invalid_status_transition_completed_to_any),
        ("test_update_status_order_not_found", test_update_status_order_not_found),
        ("test_update_status_same_status", test_update_status_same_status),
        ("test_create_order_minimal_data", test_create_order_minimal_data),
        ("test_create_order_with_metadata", test_create_order_with_metadata),
    ]

    print(f"\nRunning {len(all_tests)} tests...")

    # 每个测试用单独的数据库实例
    for test_name, test_func in all_tests:
        clean_test_db()
        service = OrderService(get_test_db_path())

        # 确保表存在（手动创建测试表）
        create_orders_table_sql = """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                item_id TEXT,
                hotel_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                check_in_date TEXT NOT NULL,
                check_out_date TEXT NOT NULL,
                room_count INTEGER DEFAULT 1,
                original_price REAL,
                final_price REAL,
                currency TEXT DEFAULT 'CNY',
                status TEXT NOT NULL DEFAULT 'PENDING',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                confirmed_at DATETIME,
                paid_at DATETIME,
                booked_at DATETIME,
                completed_at DATETIME,
                metadata TEXT,
                remark TEXT
            );
        """

        try:
            service.db.execute(create_orders_table_sql)
        except Exception as e:
            print(f"  ! Warning: {e}")

        runner.run_test(test_name, test_func)

    # 清理
    clean_test_db()

    # 输出摘要
    success = runner.summary()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
