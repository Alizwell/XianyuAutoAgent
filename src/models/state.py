"""查询状态模型"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


class QueryStep(Enum):
    """查询步骤枚举"""
    AWAITING_INPUT = "awaiting_input"
    PARSING_IMAGE = "parsing_image"
    AWAITING_HOTEL_NAME = "awaiting_hotel_name"
    AWAITING_CHECKIN_DATE = "awaiting_checkin_date"
    AWAITING_CHECKOUT_DATE = "awaiting_checkout_date"
    AWAITING_ROOM_TYPE = "awaiting_room_type"
    SEARCHING = "searching"
    COMPLETE = "complete"


@dataclass
class QueryState:
    """查询状态数据类"""
    session_id: str
    current_step: QueryStep = QueryStep.AWAITING_INPUT
    hotel_name: Optional[str] = None
    check_in_date: Optional[str] = None  # YYYY-MM-DD
    check_out_date: Optional[str] = None  # YYYY-MM-DD
    room_type: Optional[str] = None
    hotel_id: Optional[str] = None
    image_parse_result: Optional[Dict[str, Any]] = None
    search_results: Optional[List[Dict]] = None
    price_results: Optional[List[Dict]] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'current_step': self.current_step.value,
            'hotel_name': self.hotel_name,
            'check_in_date': self.check_in_date,
            'check_out_date': self.check_out_date,
            'room_type': self.room_type,
            'hotel_id': self.hotel_id,
            'image_parse_result': self.image_parse_result,
            'search_results': self.search_results,
            'price_results': self.price_results,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryState':
        """从字典创建"""
        data = data.copy()
        data['current_step'] = QueryStep(data['current_step'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def update_step(self, step: QueryStep) -> None:
        """更新步骤"""
        self.current_step = step
        self.updated_at = datetime.now()

    def set_hotel_info(self, hotel_name: str, hotel_id: Optional[str] = None) -> None:
        """设置酒店信息"""
        self.hotel_name = hotel_name
        if hotel_id:
            self.hotel_id = hotel_id
        self.updated_at = datetime.now()

    def set_dates(self, check_in: str, check_out: str) -> None:
        """设置日期"""
        self.check_in_date = check_in
        self.check_out_date = check_out
        self.updated_at = datetime.now()

    def is_info_complete(self) -> bool:
        """检查信息是否完整"""
        return all([
            self.hotel_name,
            self.check_in_date,
            self.check_out_date,
            self.room_type
        ])

    def get_missing_fields(self) -> List[str]:
        """获取缺失的字段"""
        missing = []
        if not self.hotel_name:
            missing.append('hotel_name')
        if not self.check_in_date:
            missing.append('check_in_date')
        if not self.check_out_date:
            missing.append('check_out_date')
        if not self.room_type:
            missing.append('room_type')
        return missing
