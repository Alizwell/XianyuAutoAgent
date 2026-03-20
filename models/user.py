from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class User:
    """用户数据模型"""
    user_id: str
    nickname: Optional[str] = None
    blacklist: bool = False
    risk_level: int = 0  # 0=正常, 1=注意, 2=警告
    total_orders: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """初始化时间戳"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'nickname': self.nickname,
            'blacklist': self.blacklist,
            'risk_level': self.risk_level,
            'total_orders': self.total_orders,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建实例"""
        def parse_datetime(dt_str):
            if dt_str:
                return datetime.fromisoformat(dt_str)
            return None

        return cls(
            user_id=data['user_id'],
            nickname=data.get('nickname'),
            blacklist=data.get('blacklist', False),
            risk_level=data.get('risk_level', 0),
            total_orders=data.get('total_orders', 0),
            created_at=parse_datetime(data.get('created_at')),
            updated_at=parse_datetime(data.get('updated_at')),
        )
