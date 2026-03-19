#!/usr/bin/env python3
"""基本功能测试脚本"""

import sys
sys.path.insert(0, '.')

def test_database():
    """测试数据库连接"""
    print("Testing database connection...")
    from db import db
    print(f"Database path: {db.db_path}")
    print("✓ Database initialized successfully")
    return True

def test_models():
    """测试数据模型"""
    print("\nTesting data models...")
    from models import Order, OrderStatus, User, PriceRecord

    # Test Order creation
    order = Order(
        order_id="TEST001",
        chat_id="chat_123",
        user_id="user_456",
        hotel_id="hotel_789",
        room_id="room_abc",
        check_in_date="2026-04-01",
        check_out_date="2026-04-03",
        original_price=500.0,
        final_price=450.0
    )
    assert order.status == OrderStatus.PENDING
    print("✓ Order model works")

    # Test User creation
    user = User(user_id="user_123", nickname="Test User")
    assert user.risk_level == 0
    print("✓ User model works")

    # Test PriceRecord creation
    price = PriceRecord(
        hotel_id="hotel_001",
        room_id="room_001",
        check_in_date="2026-04-01",
        check_out_date="2026-04-03",
        price=599.0
    )
    assert price.currency == "CNY"
    print("✓ PriceRecord model works")

    return True

def test_order_service():
    """测试订单服务"""
    print("\nTesting order service...")
    from services import OrderService
    from models import OrderStatus

    service = OrderService()

    # Test creating an order
    order = service.create_order(
        order_id="ORDER001",
        chat_id="chat_test",
        user_id="user_test",
        hotel_id="hotel_001",
        room_id="room_001",
        check_in_date="2026-04-10",
        check_out_date="2026-04-12",
        original_price=800.0,
        final_price=750.0
    )
    assert order is not None
    assert order.status == OrderStatus.PENDING
    print("✓ Order creation works")

    # Test retrieving the order
    retrieved = service.get_order_by_id("ORDER001")
    assert retrieved is not None
    assert retrieved.order_id == "ORDER001"
    print("✓ Order retrieval works")

    # Test status update
    result = service.update_status("ORDER001", OrderStatus.CONFIRMED)
    assert result is True
    updated = service.get_order_by_id("ORDER001")
    assert updated.status == OrderStatus.CONFIRMED
    print("✓ Status update works")

    return True

def main():
    """主函数"""
    print("=" * 60)
    print("Hotel Booking System - Basic Functionality Test")
    print("=" * 60)

    try:
        # Run all tests
        test_database()
        test_models()
        test_order_service()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
