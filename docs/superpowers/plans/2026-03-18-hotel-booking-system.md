# 咸鱼酒店预订系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于现有闲鱼客服系统，构建分层架构的酒店预订功能，包括订单管理、价格查询和状态流转。

**Architecture:** 采用五层架构（接入层/对话层/业务层/执行层/基础设施层），使用 SQLite 存储，内存缓存，Python 异步实现。

**Tech Stack:** Python 3.8+, SQLite, websockets, loguru, OpenAI API

---

## 前置条件检查

在开始之前，请确认以下项目已完成：

- [ ] 阅读设计文档：`docs/酒店预订系统设计.md`
- [ ] 了解现有代码结构：`main.py`, `XianyuAgent.py`, `XianyuApis.py`
- [ ] 确认 Python 环境 >= 3.8
- [ ] 已安装依赖：`pip install -r requirements.txt`

---

## 任务分解

### Phase 1: 基础设施层（数据库和模型）

#### Task 1: 创建数据库模块

**Files:**
- Create: `db/__init__.py`
- Create: `db/database.py`
- Create: `db/schema.sql`

**步骤：**

- [ ] **Step 1: 创建数据库连接管理类**

```python
# db/database.py
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from loguru import logger

class Database:
    def __init__(self, db_path: str = "data/xianyu.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            with open('db/schema.sql', 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            logger.info("数据库初始化完成")

    def execute(self, sql: str, parameters: tuple = ()) -> int:
        """执行SQL语句，返回影响行数"""
        with self.get_connection() as conn:
            cursor = conn.execute(sql, parameters)
            return cursor.rowcount

    def fetchone(self, sql: str, parameters: tuple = ()) -> dict:
        """查询单条记录"""
        with self.get_connection() as conn:
            cursor = conn.execute(sql, parameters)
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, parameters: tuple = ()) -> list:
        """查询多条记录"""
        with self.get_connection() as conn:
            cursor = conn.execute(sql, parameters)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

# 全局数据库实例
db = Database()
```

- [ ] **Step 2: 创建数据库Schema**

```sql
-- db/schema.sql
-- 订单表
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,
    chat_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    item_id TEXT,

    -- 酒店信息
    hotel_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    check_in_date TEXT NOT NULL,
    check_out_date TEXT NOT NULL,
    room_count INTEGER DEFAULT 1,

    -- 价格信息
    original_price REAL,
    final_price REAL,
    currency TEXT DEFAULT 'CNY',

    -- 状态管理
    status TEXT NOT NULL DEFAULT 'PENDING',

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confirmed_at DATETIME,
    paid_at DATETIME,
    booked_at DATETIME,
    completed_at DATETIME,

    -- 扩展字段
    metadata TEXT,
    remark TEXT
);

CREATE INDEX IF NOT EXISTS idx_orders_chat_id ON orders(chat_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- 价格记录表
CREATE TABLE IF NOT EXISTS price_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_id TEXT NOT NULL,
    room_id TEXT NOT NULL,
    check_in_date TEXT NOT NULL,
    check_out_date TEXT NOT NULL,
    price REAL NOT NULL,
    currency TEXT DEFAULT 'CNY',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(hotel_id, room_id, check_in_date, check_out_date)
);

CREATE INDEX IF NOT EXISTS idx_price_records_lookup ON price_records(
    hotel_id, room_id, check_in_date, check_out_date
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    nickname TEXT,
    blacklist BOOLEAN DEFAULT FALSE,
    risk_level INTEGER DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
```

- [ ] **Step 3: 创建 `__init__.py`**

```python
# db/__init__.py
from .database import Database, db

__all__ = ['Database', 'db']
```

- [ ] **Step 4: 测试数据库连接**

```python
# 测试脚本 test_db.py
from db import db

# 测试插入
result = db.execute(
    "INSERT INTO users (user_id, nickname) VALUES (?, ?)",
    ("test_user", "Test User")
)
print(f"插入影响行数: {result}")

# 测试查询
user = db.fetchone("SELECT * FROM users WHERE user_id = ?", ("test_user",))
print(f"查询结果: {user}")
```

运行: `python test_db.py`
预期: 成功创建数据库文件，插入并查询数据

- [ ] **Step 5: 提交**

```bash
git add db/
git commit -m "feat: add database layer with SQLite schema"
```

---

### Phase 2: 业务层（订单服务和价格服务）

#### Task 2: 创建数据模型

**Files:**
- Create: `models/__init__.py`
- Create: `models/order.py`
- Create: `models/user.py`
- Create: `models/price.py`

**步骤：**

- [ ] **Step 1: 创建订单模型**

```python
# models/order.py
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
        # 转换状态字符串为枚举
        status = OrderStatus(data.get('status', 'PENDING'))

        # 转换时间字符串为datetime
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
            status=status,
            created_at=parse_datetime(data.get('created_at')),
            updated_at=parse_datetime(data.get('updated_at')),
            confirmed_at=parse_datetime(data.get('confirmed_at')),
            paid_at=parse_datetime(data.get('paid_at')),
            booked_at=parse_datetime(data.get('booked_at')),
            completed_at=parse_datetime(data.get('completed_at')),
            metadata=eval(data['metadata']) if data.get('metadata') else {},
            remark=data.get('remark'),
        )
