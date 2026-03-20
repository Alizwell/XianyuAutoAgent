"""测试数据模型"""

import pytest
from datetime import datetime
from src.models import QueryState, QueryStep, Hotel, RoomPrice


class TestQueryState:
    """测试查询状态"""

    def test_create_default_state(self):
        """测试创建默认状态"""
        state = QueryState(session_id="test-session-1")
        assert state.session_id == "test-session-1"
        assert state.current_step == QueryStep.AWAITING_INPUT
        assert state.hotel_name is None
        assert state.is_info_complete() is False

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        state = QueryState(
            session_id="test-session-1",
            current_step=QueryStep.AWAITING_ROOM_TYPE,
            hotel_name="汉庭酒店",
            check_in_date="2026-03-20",
            check_out_date="2026-03-21"
        )

        data = state.to_dict()
        new_state = QueryState.from_dict(data)

        assert new_state.session_id == state.session_id
        assert new_state.current_step == state.current_step
        assert new_state.hotel_name == state.hotel_name
        assert new_state.check_in_date == state.check_in_date

    def test_get_missing_fields(self):
        """测试获取缺失字段"""
        state = QueryState(session_id="test")
        state.hotel_name = "汉庭"
        state.check_in_date = "2026-03-20"
        missing = state.get_missing_fields()
        assert 'check_out_date' in missing
        assert 'room_type' in missing
        assert 'hotel_name' not in missing

    def test_is_info_complete(self):
        """测试信息完整判断"""
        state = QueryState(session_id="test")
        state.hotel_name = "汉庭"
        state.check_in_date = "2026-03-20"
        state.check_out_date = "2026-03-21"
        state.room_type = "大床房"
        assert state.is_info_complete() is True


class TestHotel:
    """测试酒店模型"""

    def test_create_from_dict(self):
        """测试从字典创建"""
        data = {
            "hotel_id": "12345",
            "hotel_name": "汉庭南京夫子庙店",
            "brand_name": "汉庭",
            "address": "南京市秦淮区"
        }
        hotel = Hotel.from_dict(data)
        assert hotel.hotel_id == "12345"
        assert hotel.hotel_name == "汉庭南京夫子庙店"

    def test_get_display_text(self):
        """测试展示文本"""
        hotel = Hotel(
            hotel_id="12345",
            hotel_name="汉庭南京夫子庙店",
            brand_name="汉庭",
            address="南京市秦淮区夫子庙",
            price_start=259
        )
        text = hotel.get_display_text()
        assert "汉庭南京夫子庙店" in text
        assert "汉庭" in text
        assert "259" in text


class TestRoomPrice:
    """测试房间价格模型"""

    def test_create_from_dict(self):
        """测试从字典创建"""
        data = {
            "room_type_name": "高级大床房",
            "bed_type": "大床",
            "price": 259,
            "breakfast": "含早",
            "cancel_policy": "入住前可免费取消"
        }
        room = RoomPrice.from_dict(data)
        assert room.room_type_name == "高级大床房"
        assert room.price == 259

    def test_get_display_text(self):
        """测试展示文本"""
        room = RoomPrice(
            room_type_name="高级大床房",
            bed_type="大床",
            price=259,
            original_price=299,
            breakfast="含早",
            cancel_policy="免费取消"
        )
        text = room.get_display_text()
        assert "高级大床房" in text
        assert "259" in text
        assert "299" in text
        assert "含早" in text

    def test_get_short_display(self):
        """测试简短展示"""
        room = RoomPrice(
            room_type_name="高级大床房",
            bed_type="大床",
            price=259
        )
        text = room.get_short_display()
        assert "高级大床房" in text
        assert "259" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
