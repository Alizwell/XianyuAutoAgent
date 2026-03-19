#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格服务简单测试脚本
"""
import os
import sys
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.price_service import PriceService, PriceError


def main():
    """运行价格服务测试"""
    print("Running price service tests...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_price.db")

    try:
        # 测试 PriceError
        print("\n1. Testing PriceError...")
        try:
            raise PriceError("Test error")
        except PriceError:
            print("   ✓ PriceError works")

        # 测试 PriceService 初始化
        print("\n2. Testing PriceService initialization...")
        service = PriceService(db_path)
        print("   ✓ PriceService initialized")

        # 测试缓存键生成
        print("\n3. Testing cache key generation...")
        key = service._get_cache_key("hotel_1", "room_1", "2026-01-01", "2026-01-02")
        expected_key = "hotel_1:room_1:2026-01-01:2026-01-02"
        if key == expected_key:
            print(f"   ✓ Cache key is correct: {key}")
        else:
            print(f"   ✗ Cache key incorrect: got {key}, expected {expected_key}")

        # 测试清空缓存
        print("\n4. Testing clear_cache...")
        service._cache["test"] = "value"
        service.clear_cache()
        if len(service._cache) == 0:
            print("   ✓ Cache cleared successfully")
        else:
            print("   ✗ Cache not cleared")

        # 先创建表
        print("\n5. Creating tables...")
        service.db.execute("""
            CREATE TABLE IF NOT EXISTS price_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hotel_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                check_in_date TEXT NOT NULL,
                check_out_date TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'CNY',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(hotel_id, room_id, check_in_date, check_out_date)
            );
        """)
        print("   ✓ Table created")

        # 测试保存价格
        print("\n6. Testing save_price...")
        price_data = {
            "hotel_id": "hotel_123",
            "room_id": "room_456",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 899.99
        }
        try:
            result = service.save_price(price_data)
            if result and result["price"] == 899.99:
                print("   ✓ save_price works")
            else:
                print("   ✗ save_price returned unexpected result")
        except Exception as e:
            print(f"   ✗ save_price failed: {e}")

        # 测试查询价格（缓存命中）
        print("\n7. Testing query_price (cache hit)...")
        try:
            result = service.query_price("hotel_123", "room_456", "2026-03-20", "2026-03-22")
            if result and result["price"] == 899.99:
                print("   ✓ query_price (cache hit) works")
            else:
                print("   ✗ query_price (cache hit) failed")
        except Exception as e:
            print(f"   ✗ query_price (cache hit) failed: {e}")

        # 测试查询不存在的价格
        print("\n8. Testing query_price (non-existent)...")
        try:
            result = service.query_price("nonexistent", "none", "2026-01-01", "2026-01-02")
            if result is None:
                print("   ✓ query_price returns None for non-existent")
            else:
                print("   ✗ query_price should return None")
        except Exception as e:
            print(f"   ✗ query_price failed: {e}")

        # 测试缺少必填字段
        print("\n9. Testing save_price with missing fields...")
        try:
            service.save_price({
                "hotel_id": "hotel_1",
                "room_id": "room_1"
            })
            print("   ✗ Should have raised PriceError")
        except PriceError:
            print("   ✓ PriceError raised for missing fields")

        print("\n" + "="*50)
        print("All tests completed!")
        print("="*50)
        return 0

    finally:
        # 清理
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
