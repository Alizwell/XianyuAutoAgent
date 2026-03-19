#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模块测试
"""
import os
import sys
import tempfile
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import Database, get_db_instance


def test_database_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("测试1: 数据库连接")
    print("=" * 50)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)

        # 测试连接
        connected = db.connect()
        print(f"连接状态: {'成功' if connected else '失败'}")

        # 检查表是否创建
        tables = db.get_table_names()
        print(f"创建的表: {tables}")

        expected_tables = {"orders", "price_records", "users"}
        all_tables_exist = expected_tables.issubset(set(tables))
        print(f"所有表存在: {'是' if all_tables_exist else '否'}")

        db.disconnect()

        print(f"测试1: {'通过' if connected and all_tables_exist else '失败'}")
        return connected and all_tables_exist
    finally:
        shutil.rmtree(temp_dir)
        print()


def test_user_operations():
    """测试用户操作"""
    print("=" * 50)
    print("测试2: 用户操作")
    print("=" * 50)

    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)

        # 创建用户
        user_id = "test_user_001"
        nickname = "测试用户"
        db.create_user(user_id, nickname)

        # 查询用户
        user = db.get_user(user_id)
        print(f"用户信息: {user}")
        assert user is not None, "用户创建失败"
        assert user["user_id"] == user_id, "用户ID不匹配"
        assert user["nickname"] == nickname, "昵称不匹配"

        # 更新风险等级
        updated = db.update_user_risk_level(user_id, 1)
        print(f"更新风险等级: {'成功' if updated else '失败'}")
        user = db.get_user(user_id)
        assert user["risk_level"] == 1, "风险等级更新失败"

        # 添加黑名单
        blacklisted = db.add_user_blacklist(user_id)
        print(f"添加黑名单: {'成功' if blacklisted else '失败'}")
        user = db.get_user(user_id)
        assert user["blacklist"] == 1, "黑名单添加失败"

        db.disconnect()
        print("测试2: 通过")
        return True
    except AssertionError as e:
        print(f"测试2: 失败 - {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)
        print()


def test_order_operations():
    """测试订单操作"""
    print("=" * 50)
    print("测试3: 订单操作")
    print("=" * 50)

    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)

        # 创建订单
        order_data = {
            "order_id": "ORD_001",
            "chat_id": "chat_001",
            "user_id": "user_001",
            "hotel_id": "hotel_001",
            "room_id": "room_001",
            "check_in_date": "2026-04-01",
            "check_out_date": "2026-04-03",
            "room_count": 2,
            "original_price": 1000.0,
            "final_price": 900.0,
            "status": "PENDING"
        }

        order_id = db.create_order(order_data)
        print(f"创建订单ID: {order_id}")
        assert order_id > 0, "订单创建失败"

        # 查询订单
        order = db.get_order_by_id("ORD_001")
        print(f"查询订单: {order['order_id']} - {order['status']}")
        assert order is not None, "订单查询失败"
        assert order["order_id"] == "ORD_001", "订单ID不匹配"

        # 更新订单状态
        updated = db.update_order_status("ORD_001", "CONFIRMED")
        print(f"更新订单状态: {'成功' if updated else '失败'}")
        order = db.get_order_by_id("ORD_001")
        assert order["status"] == "CONFIRMED", "订单状态更新失败"
        print(f"更新后状态: {order['status']}")
        print(f"确认时间: {order['confirmed_at']}")

        # 通过chat_id查询订单
        orders = db.get_orders_by_chat_id("chat_001")
        print(f"通过chat_id查询到订单数: {len(orders)}")
        assert len(orders) == 1, "订单查询失败"

        db.disconnect()
        print("测试3: 通过")
        return True
    except AssertionError as e:
        print(f"测试3: 失败 - {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)
        print()


def test_price_record_operations():
    """测试价格记录操作"""
    print("=" * 50)
    print("测试4: 价格记录操作")
    print("=" * 50)

    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)

        # 创建价格记录
        price_data = {
            "hotel_id": "hotel_001",
            "room_id": "room_001",
            "check_in_date": "2026-04-01",
            "check_out_date": "2026-04-03",
            "price": 450.0
        }

        record_id = db.create_price_record(price_data)
        print(f"创建价格记录ID: {record_id}")
        assert record_id >= 0, "价格记录创建失败"

        # 查询价格记录
        record = db.get_price_record(
            "hotel_001", "room_001",
            "2026-04-01", "2026-04-03"
        )
        print(f"价格: {record['price']} {record['currency']}")
        assert record is not None, "价格记录查询失败"
        assert record["price"] == 450.0, "价格不匹配"

        # 测试更新价格（使用INSERT OR REPLACE）
        price_data["price"] = 480.0
        record_id = db.create_price_record(price_data)
        print(f"更新价格后记录ID: {record_id}")

        record = db.get_price_record(
            "hotel_001", "room_001",
            "2026-04-01", "2026-04-03"
        )
        print(f"更新后价格: {record['price']}")
        assert record["price"] == 480.0, "价格更新失败"

        # 查询酒店价格记录
        records = db.get_price_records_by_hotel("hotel_001")
        print(f"酒店价格记录数: {len(records)}")
        assert len(records) == 1, "价格记录查询失败"

        db.disconnect()
        print("测试4: 通过")
        return True
    except AssertionError as e:
        print(f"测试4: 失败 - {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)
        print()


def test_generic_methods():
    """测试通用方法"""
    print("=" * 50)
    print("测试5: 通用方法")
    print("=" * 50)

    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)

        # 测试 find_all
        # 先创建几个用户
        db.insert("users", {"user_id": "u1", "nickname": "用户1"})
        db.insert("users", {"user_id": "u2", "nickname": "用户2"})
        db.insert("users", {"user_id": "u3", "nickname": "用户3"})

        users = db.find_all("users", order_by="user_id ASC")
        print(f"查询所有用户: {[u['user_id'] for u in users]}")
        assert len(users) == 3, "查询失败"

        # 测试带条件的 find_all
        db.update("users", {"risk_level": 1}, {"user_id": "u2"})
        users = db.find_all("users", {"risk_level": 1})
        print(f"查询风险等级为1的用户: {[u['user_id'] for u in users]}")
        assert len(users) == 1, "条件查询失败"
        assert users[0]["user_id"] == "u2", "条件查询结果错误"

        # 测试 limit
        users = db.find_all("users", limit=2)
        print(f"限制返回2条记录: {[u['user_id'] for u in users]}")
        assert len(users) == 2, "limit失败"

        # 测试 delete
        delete_count = db.delete("users", {"user_id": "u1"})
        users = db.find_all("users")
        print(f"删除后剩余用户数: {len(users)}")
        assert len(users) == 2, "删除失败"

        db.disconnect()
        print("测试5: 通过")
        return True
    except AssertionError as e:
        print(f"测试5: 失败 - {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)
        print()


def test_global_instance():
    """测试全局数据库实例"""
    print("=" * 50)
    print("测试6: 全局数据库实例")
    print("=" * 50)

    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, "test_global.db")

        # 获取实例1
        db1 = get_db_instance(db_path)
        db1.create_user("global_user", "全局用户")

        # 获取实例2
        db2 = get_db_instance(db_path)
        user = db2.get_user("global_user")

        print(f"实例1和实例2是同一个: {db1 is db2}")
        assert db1 is db2, "全局实例失败"
        assert user is not None, "全局实例数据访问失败"

        print("测试6: 通过")
        return True
    except AssertionError as e:
        print(f"测试6: 失败 - {e}")
        return False
    finally:
        shutil.rmtree(temp_dir)
        print()


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("数据库模块测试套件")
    print("=" * 50 + "\n")

    results = []
    tests = [
        ("数据库连接", test_database_connection),
        ("用户操作", test_user_operations),
        ("订单操作", test_order_operations),
        ("价格记录操作", test_price_record_operations),
        ("通用方法", test_generic_methods),
        ("全局实例", test_global_instance)
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"测试异常: {e}")
            results.append((name, False))

    print("=" * 50)
    print("测试结果汇总")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "通过" if result else "失败"
        print(f"  - {name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")
    print(f"{'所有测试通过!' if passed == total else '部分测试失败!'}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
