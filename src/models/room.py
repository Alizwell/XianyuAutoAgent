"""房间价格数据模型"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class RoomPrice:
    """房间价格数据类"""
    room_type_name: str
    bed_type: str
    price: float
    currency: str = "CNY"
    original_price: Optional[float] = None
    breakfast: str = ""  # 含早/无早/双早
    cancel_policy: str = ""  # 取消政策
    room_count: int = 0  # 剩余房间数
    area: Optional[str] = None  # 房间面积
    floor: Optional[str] = None  # 楼层
    image_url: Optional[str] = None  # 房间图片
    tags: Optional[List[str]] = None  # 标签（如"网红房型"）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'room_type_name': self.room_type_name,
            'bed_type': self.bed_type,
            'price': self.price,
            'currency': self.currency,
            'original_price': self.original_price,
            'breakfast': self.breakfast,
            'cancel_policy': self.cancel_policy,
            'room_count': self.room_count,
            'area': self.area,
            'floor': self.floor,
            'image_url': self.image_url,
            'tags': self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoomPrice':
        """从字典创建"""
        return cls(
            room_type_name=data.get('room_type_name', ''),
            bed_type=data.get('bed_type', ''),
            price=float(data.get('price', 0)),
            currency=data.get('currency', 'CNY'),
            original_price=float(data['original_price']) if data.get('original_price') else None,
            breakfast=data.get('breakfast', ''),
            cancel_policy=data.get('cancel_policy', ''),
            room_count=int(data.get('room_count', 0)),
            area=data.get('area'),
            floor=data.get('floor'),
            image_url=data.get('image_url'),
            tags=data.get('tags', []),
        )

    @classmethod
    def from_huazhu_response(cls, item: Dict[str, Any]) -> 'RoomPrice':
        """从华住响应数据创建"""
        return cls(
            room_type_name=item.get('roomTypeName', ''),
            bed_type=item.get('bedType', ''),
            price=float(item.get('price', 0)),
            currency=item.get('currency', 'CNY'),
            original_price=float(item['originalPrice']) if item.get('originalPrice') else None,
            breakfast=item.get('breakfast', ''),
            cancel_policy=item.get('cancelPolicy', ''),
            room_count=int(item.get('roomCount', 0)),
            area=item.get('area'),
            floor=item.get('floor'),
            image_url=item.get('imageUrl'),
            tags=item.get('tags', []),
        )

    def get_display_text(self) -> str:
        """获取展示文本"""
        text = f"🏨 {self.room_type_name}"
        if self.bed_type:
            text += f" | {self.bed_type}"
        if self.area:
            text += f" | {self.area}"
        text += f"\n💰 ¥{int(self.price)}"
        if self.original_price and self.original_price > self.price:
            discount = int((1 - self.price / self.original_price) * 100)
            text += f" (原价¥{int(self.original_price)}, 省{discount}%)"
        if self.breakfast:
            text += f" | {self.breakfast}"
        if self.cancel_policy:
            text += f"\n📝 {self.cancel_policy}"
        if self.room_count > 0:
            text += f" | 仅剩{self.room_count}间"
        return text

    def get_short_display(self) -> str:
        """获取简短展示文本"""
        text = f"{self.room_type_name}"
        if self.bed_type:
            text += f"({self.bed_type})"
        text += f" - ¥{int(self.price)}"
        return text
