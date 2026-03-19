from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PriceRecord:
    """价格记录数据模型"""
    hotel_id: str
    room_id: str
    check_in_date: str  # YYYY-MM-DD
    check_out_date: str  # YYYY-MM-DD
    price: float
    currency: str = "CNY"
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'hotel_id': self.hotel_id,
            'room_id': self.room_id,
            'check_in_date': self.check_in_date,
            'check_out_date': self.check_out_date,
            'price': self.price,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PriceRecord':
        """从字典创建实例"""
        def parse_datetime(dt_str):
            if dt_str:
                return datetime.fromisoformat(dt_str)
            return None

        return cls(
            id=data.get('id'),
            hotel_id=data['hotel_id'],
            room_id=data['room_id'],
            check_in_date=data['check_in_date'],
            check_out_date=data['check_out_date'],
            price=data['price'],
            currency=data.get('currency', 'CNY'),
            created_at=parse_datetime(data.get('created_at')),
        )
