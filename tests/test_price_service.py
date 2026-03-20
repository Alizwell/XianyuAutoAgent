#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
价格服务测试
"""
import os
import sys
import pytest
from services.price_service import PriceService, PriceError
from db import get_db_instance


import tempfile


@pytest.fixture(scope="function")
def price_service():
    """创建价格服务实例（每个测试函数都会创建新的临时数据库）"""
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    db_path = temp_db.name

    try:
        service = PriceService(db_path)
        yield service
    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass


class TestPriceService:
    """价格服务测试类"""

    # ==================== 测试缓存命中场景 ====================

    def test_cache_hit(self, price_service: PriceService):
        """测试缓存命中场景"""
        # 先保存价格到缓存
        price_data = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 900.0
        }
        price_service.save_price(price_data)

        # 再次查询，应该命中缓存
        price_record = price_service.query_price(
            "hotel_123", "room_01", "2026-03-20", "2026-03-22"
        )
        assert price_record is not None
        assert price_record["price"] == 900.0

    # ==================== 测试缓存未命中场景 ====================

    def test_cache_miss(self, price_service: PriceService):
        """测试缓存未命中，从数据库读取"""
        # 先保存价格到数据库，但不缓存
        price_data = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 900.0
        }
        price_service.save_price(price_data)

        # 清空缓存
        price_service.clear_cache()

        # 查询价格，应该从数据库读取
        price_record = price_service.query_price(
            "hotel_123", "room_01", "2026-03-20", "2026-03-22"
        )
        assert price_record is not None
        assert price_record["price"] == 900.0

    # ==================== 测试保存价格 ====================

    def test_save_price_success(self, price_service: PriceService):
        """测试成功保存价格"""
        price_data = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 900.0,
            "currency": "CNY"
        }

        price_record = price_service.save_price(price_data)
        assert price_record is not None
        assert price_record["hotel_id"] == price_data["hotel_id"]
        assert price_record["room_id"] == price_data["room_id"]
        assert price_record["check_in_date"] == price_data["check_in_date"]
        assert price_record["check_out_date"] == price_data["check_out_date"]
        assert price_record["price"] == price_data["price"]
        assert price_record["currency"] == price_data["currency"]

    def test_save_price_missing_fields(self, price_service: PriceService):
        """测试缺少必填字段"""
        price_data = {
            "hotel_id": "hotel_123",
            "room_id": "room_01"
        }

        with pytest.raises(PriceError):
            price_service.save_price(price_data)

    # ==================== 测试价格查询 ====================

    def test_query_nonexistent_price(self, price_service: PriceService):
        """测试查询不存在的价格"""
        price_record = price_service.query_price(
            "nonexistent_hotel", "nonexistent_room", "2026-03-20", "2026-03-22"
        )
        assert price_record is None

    # ==================== 测试清空缓存 ====================

    def test_clear_cache(self, price_service: PriceService):
        """测试清空缓存"""
        # 保存价格到缓存
        price_data = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 900.0
        }
        price_service.save_price(price_data)

        # 验证缓存中有数据
        assert len(price_service._cache) == 1

        # 清空缓存
        price_service.clear_cache()

        # 验证缓存为空
        assert len(price_service._cache) == 0

    # ==================== 测试更新价格 ====================

    def test_update_price(self, price_service: PriceService):
        """测试更新价格"""
        # 保存初始价格
        price_data1 = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 900.0
        }
        price_service.save_price(price_data1)

        # 验证初始价格
        price_record1 = price_service.query_price(
            "hotel_123", "room_01", "2026-03-20", "2026-03-22"
        )
        assert price_record1["price"] == 900.0

        # 更新价格
        price_data2 = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 950.0
        }
        price_service.save_price(price_data2)

        # 验证价格已更新
        price_record2 = price_service.query_price(
            "hotel_123", "room_01", "2026-03-20", "2026-03-22"
        )
        assert price_record2["price"] == 950.0

    # ==================== 测试不同参数的价格查询 ====================

    def test_query_different_rooms(self, price_service: PriceService):
        """测试查询不同房型的价格"""
        # 保存不同房型的价格
        price_data1 = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 900.0
        }
        price_data2 = {
            "hotel_id": "hotel_123",
            "room_id": "room_02",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 1200.0
        }
        price_service.save_price(price_data1)
        price_service.save_price(price_data2)

        # 查询不同房型的价格
        price1 = price_service.query_price("hotel_123", "room_01", "2026-03-20", "2026-03-22")
        price2 = price_service.query_price("hotel_123", "room_02", "2026-03-20", "2026-03-22")

        assert price1["price"] == 900.0
        assert price2["price"] == 1200.0

    def test_query_different_dates(self, price_service: PriceService):
        """测试查询不同日期的价格"""
        # 保存不同日期的价格
        price_data1 = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-20",
            "check_out_date": "2026-03-22",
            "price": 900.0
        }
        price_data2 = {
            "hotel_id": "hotel_123",
            "room_id": "room_01",
            "check_in_date": "2026-03-25",
            "check_out_date": "2026-03-27",
            "price": 1100.0
        }
        price_service.save_price(price_data1)
        price_service.save_price(price_data2)

        # 查询不同日期的价格
        price1 = price_service.query_price("hotel_123", "room_01", "2026-03-20", "2026-03-22")
        price2 = price_service.query_price("hotel_123", "room_01", "2026-03-25", "2026-03-27")

        assert price1["price"] == 900.0
        assert price2["price"] == 1100.0


if __name__ == "__main__":
    # 运行所有测试
    clean_test_db()
    pytest.main([__file__, "-v"])
    clean_test_db()
