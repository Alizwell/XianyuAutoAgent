"""酒店数据模型"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Hotel:
    """酒店数据类"""
    hotel_id: str
    hotel_name: str
    brand_name: str
    address: str
    rating: Optional[float] = None
    price_start: Optional[float] = None
    distance: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    facilities: Optional[list] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'hotel_id': self.hotel_id,
            'hotel_name': self.hotel_name,
            'brand_name': self.brand_name,
            'address': self.address,
            'rating': self.rating,
            'price_start': self.price_start,
            'distance': self.distance,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'image_url': self.image_url,
            'facilities': self.facilities,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Hotel':
        """从字典创建"""
        return cls(
            hotel_id=data.get('hotel_id', ''),
            hotel_name=data.get('hotel_name', ''),
            brand_name=data.get('brand_name', ''),
            address=data.get('address', ''),
            rating=data.get('rating'),
            price_start=data.get('price_start'),
            distance=data.get('distance'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            image_url=data.get('image_url'),
            facilities=data.get('facilities'),
        )

    @classmethod
    def from_huazhu_response(cls, item: Dict[str, Any]) -> 'Hotel':
        """从华住响应数据创建"""
        return cls(
            hotel_id=str(item.get('hotelId', '')),
            hotel_name=item.get('hotelName', ''),
            brand_name=item.get('brandName', ''),
            address=item.get('address', ''),
            rating=item.get('score'),
            price_start=item.get('price'),
            distance=item.get('distanceDesc'),
            latitude=item.get('latitude'),
            longitude=item.get('longitude'),
            image_url=item.get('imageUrl'),
            facilities=item.get('facilities', []),
        )

    def get_display_text(self) -> str:
        """获取展示文本"""
        text = f"{self.hotel_name}"
        if self.brand_name:
            text += f" ({self.brand_name})"
        if self.price_start:
            text += f" - ¥{int(self.price_start)}起"
        if self.distance:
            text += f"\n📍 {self.address} | {self.distance}"
        return text
