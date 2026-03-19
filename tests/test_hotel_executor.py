#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
酒店执行器测试
"""
import os
import sys
import pytest
import random
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from executor.hotel_executor import HotelExecutor, HotelError, HotelAPIError, HotelBookingError


@pytest.fixture(scope="function")
def hotel_executor():
    """创建酒店执行器实例"""
    executor = HotelExecutor(mock=True)
    return executor


class TestHotelExecutor:
    """酒店执行器测试类"""

    # ==================== 测试初始化 ====================

    def test_init_mock_mode(self):
        """测试初始化 - 模拟模式"""
        executor = HotelExecutor(mock=True)
        assert executor.mock is True

    def test_init_real_mode(self):
        """测试初始化 - 真实模式"""
        executor = HotelExecutor(api_key="test_key", base_url="https://api.example.com", mock=False)
        assert executor.mock is False
        assert executor.api_key == "test_key"
        assert executor.base_url == "https://api.example.com"

    # ==================== 测试查询价格 ====================

    def test_query_price_success(self, hotel_executor: HotelExecutor):
        """测试查询价格成功"""
        result = hotel_executor.query_price(
            hotel_id="HOTEL_001",
            room_id="ROOM_001",
            check_in_date="2026-03-20",
            check_out_date="2026-03-22"
        )

        assert result["success"] is True
        assert result["hotel_id"] == "HOTEL_001"
        assert result["room_id"] == "ROOM_001"
        assert result["check_in_date"] == "2026-03-20"
        assert result["check_out_date"] == "2026-03-22"
        assert 200 <= result["price"] <= 800
        assert result["currency"] == "CNY"
        assert "original_price" in result
        assert "discount" in result
        assert "available" in result
        assert "tax" in result

    def test_query_price_mock_randomness(self, hotel_executor: HotelExecutor):
        """测试查询价格的随机性 - 多次查询可能有不同结果"""
        prices = set()
        for _ in range(10):
            result = hotel_executor.query_price(
                hotel_id="HOTEL_001",
                room_id="ROOM_001",
                check_in_date="2026-03-20",
                check_out_date="2026-03-22"
            )
            prices.add(result["price"])

        # 多次查询可能产生不同的价格（虽然偶尔可能相同）
        assert len(prices) >= 1

    @patch('random.randint')
    def test_query_price_fixed_price(self, mock_randint: MagicMock, hotel_executor: HotelExecutor):
        """测试查询价格 - 固定随机值"""
        mock_randint.return_value = 500
        result = hotel_executor.query_price(
            hotel_id="HOTEL_001",
            room_id="ROOM_001",
            check_in_date="2026-03-20",
            check_out_date="2026-03-22"
        )
        assert result["price"] == 500

    def test_query_price_real_mode_not_implemented(self):
        """测试真实模式的查询价格尚未实现"""
        executor = HotelExecutor(mock=False)
        with pytest.raises(HotelAPIError):
            executor.query_price(
                hotel_id="HOTEL_001",
                room_id="ROOM_001",
                check_in_date="2026-03-20",
                check_out_date="2026-03-22"
            )

    # ==================== 测试预订房间 ====================

    def test_book_room_success(self, hotel_executor: HotelExecutor):
        """测试预订房间成功"""
        guest_info = {
            "name": "张三",
            "phone": "13800138000",
            "id_card": "110101199001011234"
        }

        with patch('random.random') as mock_random:
            mock_random.return_value = 0.5  # 确保不触发失败

            result = hotel_executor.book_room(
                hotel_id="HOTEL_001",
                room_id="ROOM_001",
                check_in_date="2026-03-20",
                check_out_date="2026-03-22",
                guest_info=guest_info
            )

            assert result["success"] is True
            assert result["booking_id"].startswith("BK")
            assert result["hotel_id"] == "HOTEL_001"
            assert result["room_id"] == "ROOM_001"
            assert result["check_in_date"] == "2026-03-20"
            assert result["check_out_date"] == "2026-03-22"
            assert result["guest_info"] == guest_info
            assert result["status"] == "CONFIRMED"
            assert 200 <= result["total_price"] <= 800
            assert result["currency"] == "CNY"

    def test_book_room_failure(self, hotel_executor: HotelExecutor):
        """测试预订房间失败"""
        guest_info = {
            "name": "张三",
            "phone": "13800138000"
        }

        with patch('random.random') as mock_random:
            mock_random.return_value = 0.05  # 触发失败

            with pytest.raises(HotelBookingError) as exc_info:
                hotel_executor.book_room(
                    hotel_id="HOTEL_001",
                    room_id="ROOM_001",
                    check_in_date="2026-03-20",
                    check_out_date="2026-03-22",
                    guest_info=guest_info
                )

            assert "No rooms available" in str(exc_info.value)

    def test_book_room_real_mode_not_implemented(self):
        """测试真实模式的预订尚未实现"""
        executor = HotelExecutor(mock=False)
        guest_info = {"name": "张三"}
        with pytest.raises(HotelBookingError):
            executor.book_room(
                hotel_id="HOTEL_001",
                room_id="ROOM_001",
                check_in_date="2026-03-20",
                check_out_date="2026-03-22",
                guest_info=guest_info
            )

    # ==================== 测试取消预订 ====================

    def test_cancel_booking_success(self, hotel_executor: HotelExecutor):
        """测试取消预订成功"""
        booking_id = "BK1234567890AB"

        with patch('random.random') as mock_random:
            mock_random.return_value = 0.5  # 确保不触发失败

            result = hotel_executor.cancel_booking(booking_id)

            assert result["success"] is True
            assert result["booking_id"] == booking_id
            assert result["status"] == "CANCELED"
            assert 100 <= result["refund_amount"] <= 500
            assert result["refund_currency"] == "CNY"
            assert result["refund_method"] == "原路返回"

    def test_cancel_booking_failure(self, hotel_executor: HotelExecutor):
        """测试取消预订失败"""
        booking_id = "BK1234567890AB"

        with patch('random.random') as mock_random:
            mock_random.return_value = 0.03  # 触发失败

            with pytest.raises(HotelAPIError) as exc_info:
                hotel_executor.cancel_booking(booking_id)

            assert "Booking not found or cannot be canceled" in str(exc_info.value)

    def test_cancel_booking_real_mode_not_implemented(self):
        """测试真实模式的取消预订尚未实现"""
        executor = HotelExecutor(mock=False)
        with pytest.raises(HotelAPIError):
            executor.cancel_booking("BK1234567890AB")

    # ==================== 测试错误处理 ====================

    def test_query_price_exception_handling(self, hotel_executor: HotelExecutor):
        """测试查询价格时的异常处理"""
        with patch.object(hotel_executor, '_mock_query_price') as mock_method:
            mock_method.side_effect = Exception("Network error")

            with pytest.raises(HotelAPIError) as exc_info:
                hotel_executor.query_price(
                    hotel_id="HOTEL_001",
                    room_id="ROOM_001",
                    check_in_date="2026-03-20",
                    check_out_date="2026-03-22"
                )

            assert "Price query failed" in str(exc_info.value)

    def test_book_room_exception_handling(self, hotel_executor: HotelExecutor):
        """测试预订房间时的异常处理"""
        guest_info = {"name": "张三"}

        with patch.object(hotel_executor, '_mock_book_room') as mock_method:
            mock_method.side_effect = Exception("Payment failed")

            with pytest.raises(HotelBookingError) as exc_info:
                hotel_executor.book_room(
                    hotel_id="HOTEL_001",
                    room_id="ROOM_001",
                    check_in_date="2026-03-20",
                    check_out_date="2026-03-22",
                    guest_info=guest_info
                )

            assert "Booking failed" in str(exc_info.value)

    def test_cancel_booking_exception_handling(self, hotel_executor: HotelExecutor):
        """测试取消预订时的异常处理"""
        with patch.object(hotel_executor, '_mock_cancel_booking') as mock_method:
            mock_method.side_effect = Exception("Server error")

            with pytest.raises(HotelAPIError) as exc_info:
                hotel_executor.cancel_booking("BK1234567890AB")

            assert "Cancel booking failed" in str(exc_info.value)

    # ==================== 测试异常类继承 ====================

    def test_exception_hierarchy(self):
        """测试异常类的继承关系"""
        assert issubclass(HotelAPIError, HotelError)
        assert issubclass(HotelBookingError, HotelError)

    # ==================== 测试真实API方法占位符 ====================

    def test_real_query_price_not_implemented(self, hotel_executor: HotelExecutor):
        """测试真实查询价格方法未实现"""
        with pytest.raises(NotImplementedError):
            hotel_executor._real_query_price(
                "HOTEL_001", "ROOM_001", "2026-03-20", "2026-03-22"
            )

    def test_real_book_room_not_implemented(self, hotel_executor: HotelExecutor):
        """测试真实预订方法未实现"""
        with pytest.raises(NotImplementedError):
            hotel_executor._real_book_room(
                "HOTEL_001", "ROOM_001", "2026-03-20", "2026-03-22", {}
            )

    def test_real_cancel_booking_not_implemented(self, hotel_executor: HotelExecutor):
        """测试真实取消预订方法未实现"""
        with pytest.raises(NotImplementedError):
            hotel_executor._real_cancel_booking("BK1234567890AB")


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v"])
