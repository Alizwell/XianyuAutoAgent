# 酒店价格查询Agent实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现一个酒店价格查询Agent，支持用户通过文本或图片查询华住酒店价格，自动识别图片中的酒店信息并返回价格。

**Architecture:** 采用分层架构设计，包含Agent层（HotelPriceAgent负责对话状态管理）、Tool层（三个Tool分别处理酒店搜索、价格查询、图片识别）、适配器层（HuaZhuAdapter封装华住API调用）。状态使用Redis持久化，支持30分钟会话保持。

**Tech Stack:** Python 3.8+, 现有Flask/FastAPI框架, Redis, httpx/aiohttp, Pillow(图片处理), 多模态LLM API(Claude/GPT-4V)

---

## 文件结构

```
src/
├── agent/
│   ├── __init__.py
│   ├── hotel_price_agent.py      # HotelPriceAgent主类
│   └── state_manager.py          # 状态管理器
├── tools/
│   ├── __init__.py
│   ├── base_tool.py              # Tool基类
│   ├── search_hotel_tool.py      # 搜索酒店Tool
│   ├── query_price_tool.py       # 查询价格Tool
│   └── parse_image_tool.py       # 图片识别Tool
├── adapters/
│   ├── __init__.py
│   ├── base_adapter.py           # 适配器基类
│   └── huazhu_adapter.py         # 华住适配器
├── services/
│   ├── __init__.py
│   └── image_recognition_service.py  # 图片识别服务
├── models/
│   ├── __init__.py
│   ├── state.py                  # 状态模型
│   ├── hotel.py                  # 酒店数据模型
│   └── room.py                   # 房间数据模型
└── utils/
    ├── __init__.py
    ├── date_parser.py            # 日期解析工具
    └── validators.py             # 验证工具

tests/
├── unit/
│   ├── test_hotel_price_agent.py
│   ├── test_search_hotel_tool.py
│   ├── test_query_price_tool.py
│   ├── test_parse_image_tool.py
│   └── test_huazhu_adapter.py
├── integration/
│   └── test_price_query_flow.py
└── fixtures/
    ├── hotel_search_response.json
    ├── room_info_response.json
    └── hotel_booking_image.jpg
```

---

## Task 1: 基础模型定义

**Files:**
- Create: `src/models/__init__.py`
- Create: `src/models/state.py`
- Create: `src/models/hotel.py`
- Create: `src/models/room.py`
- Test: `tests/unit/test_models.py`

- [ ] **Step 1: 创建状态模型**

```python
# src/models/state.py
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

class QueryStep(Enum):
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
    session_id: str
    current_step: QueryStep = QueryStep.AWAITING_INPUT
    hotel_name: Optional[str] = None
    check_in_date: Optional[str] = None  # YYYY-MM-DD
    check_out_date: Optional[str] = None  # YYYY-MM-DD
    room_type: Optional[str] = None
    hotel_id: Optional[str] = None
    image_parse_result: Optional[Dict[str, Any]] = None
    search_results: Optional[list] = None
    price_results: Optional[list] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueryState':
        data = data.copy()
        data['current_step'] = QueryStep(data['current_step'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
```

- [ ] **Step 2: 创建酒店和房间模型**

```python
# src/models/hotel.py
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Hotel:
    hotel_id: str
    hotel_name: str
    brand_name: str
    address: str
    rating: Optional[float] = None
    price_start: Optional[float] = None
    distance: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    def to_dict(self) -> dict:
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
        }

# src/models/room.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class RoomPrice:
    room_type_name: str
    bed_type: str
    price: float
    currency: str = "CNY"
    original_price: Optional[float] = None
    breakfast: str = ""  # 含早/无早
    cancel_policy: str = ""  # 取消政策
    room_count: int = 0
    area: Optional[str] = None
    floor: Optional[str] = None

    def to_dict(self) -> dict:
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
        }
```

- [ ] **Step 3: 运行测试验证模型**

```bash
# 创建测试文件 tests/unit/test_models.py
# 然后运行测试
python -m pytest tests/unit/test_models.py -v
```

---

## Task 2: 华住适配器实现

**Files:**
- Create: `src/adapters/__init__.py`
- Create: `src/adapters/base_adapter.py`
- Create: `src/adapters/huazhu_adapter.py`
- Test: `tests/unit/test_huazhu_adapter.py`
- Test Fixtures: `tests/fixtures/hotel_search_response.json`, `tests/fixtures/room_info_response.json`

- [ ] **Step 1: 创建基类**

```python
# src/adapters/base_adapter.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class HotelAdapter(ABC):
    """酒店适配器基类"""

    @abstractmethod
    async def search_hotel(self, keyword: str, check_in_date: str,
                          check_out_date: str, **kwargs) -> List[Dict[str, Any]]:
        """搜索酒店"""
        pass

    @abstractmethod
    async def query_room_info(self, hotel_id: str, check_in_date: str,
                             check_out_date: str, **kwargs) -> Dict[str, Any]:
        """查询房间信息"""
        pass
```

- [ ] **Step 2: 实现华住适配器**

```python
# src/adapters/huazhu_adapter.py
import httpx
import json
from typing import List, Dict, Any, Optional
from .base_adapter import HotelAdapter

class HuaZhuAdapter(HotelAdapter):
    """华住酒店适配器"""

    BASE_URL = "https://hweb-hotel.huazhu.com"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def search_hotel(self, keyword: str, check_in_date: str,
                          check_out_date: str, city_name: str = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索酒店
        对应接口：GET /hotels/search/search
        """
        url = f"{self.BASE_URL}/hotels/search/search"

        params = {
            "keyword": keyword,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "source": "1",
            "cityType": "cities",
            "limit": limit
        }

        if city_name:
            params["cityName"] = city_name

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # 解析华住响应格式
            hotels = self._parse_search_response(data)
            return hotels

        except httpx.HTTPError as e:
            raise HuaZhuAPIError(f"Search hotel failed: {str(e)}")

    async def query_room_info(self, hotel_id: str, check_in_date: str,
                             check_out_date: str, room_type: str = None) -> Dict[str, Any]:
        """
        查询房间信息
        对应接口：POST /v2/hotels/hotelDetail/getRoomInfo
        """
        url = f"{self.BASE_URL}/v2/hotels/hotelDetail/getRoomInfo"

        payload = {
            "hotelId": hotel_id,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "rcpType": "1",
            "roomCount": "1"
        }

        try:
            response = await self.client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()

            # 解析华住响应格式
            room_info = self._parse_room_info_response(data)

            # 如果指定了房型，进行过滤
            if room_type:
                room_info['room_list'] = [
                    r for r in room_info['room_list']
                    if room_type.lower() in r['room_type_name'].lower()
                ]

            return room_info

        except httpx.HTTPError as e:
            raise HuaZhuAPIError(f"Query room info failed: {str(e)}")

    def _parse_search_response(self, data: Dict) -> List[Dict]:
        """解析搜索响应"""
        hotels = []
        # 根据华住实际响应格式解析
        # 这里需要根据实际响应结构调整
        hotel_list = data.get('data', {}).get('list', [])
        for item in hotel_list:
            hotels.append({
                'hotel_id': str(item.get('hotelId', '')),
                'hotel_name': item.get('hotelName', ''),
                'brand_name': item.get('brandName', ''),
                'address': item.get('address', ''),
                'rating': item.get('rating', None),
                'price_start': item.get('price', None),
                'distance': item.get('distanceDesc', '')
            })
        return hotels

    def _parse_room_info_response(self, data: Dict) -> Dict:
        """解析房间信息响应"""
        # 根据华住实际响应格式解析
        result = {
            'hotel_id': '',
            'hotel_name': '',
            'check_in_date': '',
            'check_out_date': '',
            'room_list': []
        }

        # 解析逻辑根据实际响应结构调整
        # ...

        return result

class HuaZhuAPIError(Exception):
    """华住API错误"""
    pass
```

- [ ] **Step 3: 创建测试固件**

```json
// tests/fixtures/hotel_search_response.json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "hotelId": "9026308",
        "hotelName": "汉庭南京夫子庙酒店",
        "brandName": "汉庭",
        "address": "南京市秦淮区夫子庙景区",
        "rating": 4.8,
        "price": 259,
        "distanceDesc": "距市中心2.5公里"
      }
    ],
    "total": 1
  }
}
```

```json
// tests/fixtures/room_info_response.json
{
  "code": 200,
  "message": "success",
  "data": {
    "hotelId": "9026308",
    "hotelName": "汉庭南京夫子庙酒店",
    "roomList": [
      {
        "roomTypeName": "高级大床房",
        "bedType": "大床",
        "price": 259,
        "originalPrice": 299,
        "currency": "CNY",
        "breakfast": "含早",
        "cancelPolicy": "入住前可免费取消",
        "roomCount": 5,
        "area": "25-30"
      }
    ]
  }
}
```

---

由于计划内容较长，我已将其保存到文件。以下是剩余部分的任务概览：

**Task 3: 图片识别服务**
- 创建 ImageRecognitionService 类
- 实现调用多模态LLM识别酒店信息
- 解析识别结果，提取关键字段

**Task 4: Agent状态管理**
- 创建 StateManager 类
- 实现Redis存储和TTL管理
- 状态序列化和反序列化

**Task 5: HotelPriceAgent主类**
- 创建 HotelPriceAgent 类
- 实现消息处理流程
- 集成三个Tool的调用逻辑

**Task 6: Tool实现**
- 实现 SearchHotelTool
- 实现 QueryPriceTool
- 实现 ParseImageTool

**Task 7: 系统集成**
- 与现有对话Agent集成
- 注册到Agent路由系统
- 配置和启动脚本

**Task 8: 测试**
- 单元测试
- 集成测试
- 端到端测试

完整的实现计划文档已保存到 `docs/superpowers/plans/2026-03-20-hotel-price-agent.md`，包含了每个任务的详细步骤、代码和测试用例。
