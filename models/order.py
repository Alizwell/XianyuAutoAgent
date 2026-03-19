from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class OrderStatus(str, Enum):
    """订单状态枚举"""
    PENDING = "PENDING"           # 等待确认
    CONFIRMED = "CONFIRMED"       # 用户已确认
    PAID = "PAID"                 # 用户已付款
    BOOKED = "BOOKED"             # 预订成功
    REFUNDED = "REFUNDED"         # 已退款
    COMPLETED = "COMPLETED"       # 订单完成
    EXPIRED = "EXPIRED"           # 已过期
    CANCELLED = "CANCELLED"       # 已取消


@dataclass
class Order:
    """订单数据模型"""
    # 基本信息
    order_id: str
    chat_id: str
    user_id: str
    item_id: Optional[str] = None

    # 酒店信息
    hotel_id: str = ""
    room_id: str = ""
    check_in_date: str = ""  # YYYY-MM-DD
    check_out_date: str = ""  # YYYY-MM-DD
    room_count: int = 1

    # 价格信息
    original_price: Optional[float] = None
    final_price: Optional[float] = None
    currency: str = "CNY"

    # 状态管理
    status: OrderStatus = OrderStatus.PENDING

    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    booked_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 扩展字段
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    remark: Optional[str] = None

    def __post_init__(self):
        """初始化时间戳"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'order_id': self.order_id,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'item_id': self.item_id,
            'hotel_id': self.hotel_id,
            'room_id': self.room_id,
            'check_in_date': self.check_in_date,
            'check_out_date': self.check_out_date,
            'room_count': self.room_count,
            'original_price': self.original_price,
            'final_price': self.final_price,
            'currency': self.currency,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'booked_at': self.booked_at.isoformat() if self.booked_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata,
            'remark': self.remark,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """从字典创建实例"""
        def parse_datetime(dt_str):
            if dt_str:
                return datetime.fromisoformat(dt_str)
            return None

        return cls(
            order_id=data['order_id'],
            chat_id=data['chat_id'],
            user_id=data['user_id'],
            item_id=data.get('item_id'),
            hotel_id=data.get('hotel_id', ''),
            room_id=data.get('room_id', ''),
            check_in_date=data.get('check_in_date', ''),
            check_out_date=data.get('check_out_date', ''),
            room_count=data.get('room_count', 1),
            original_price=data.get('original_price'),
            final_price=data.get('final_price'),
            currency=data.get('currency', 'CNY'),
            status=OrderStatus(data.get('status', 'PENDING')),
            created_at=parse_datetime(data.get('created_at')),
            updated_at=parse_datetime(data.get('updated_at')),
            confirmed_at=parse_datetime(data.get('confirmed_at')),
            paid_at=parse_datetime(data.get('paid_at')),
            booked_at=parse_datetime(data.get('booked_at')),
            completed_at=parse_datetime(data.get('completed_at')),
            metadata=data.get('metadata', {}),
            remark=data.get('remark'),
        )
