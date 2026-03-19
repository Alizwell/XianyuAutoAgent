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

- [ ] **Step 1: 创建数据库连接管理类**（见原文件第37-95行）

- [ ] **Step 2: 创建数据库Schema**（见原文件第99-194行）

- [ ] **Step 3: 创建 `__init__.py`**（见原文件第197-200行）

- [ ] **Step 4: 提交 Phase 1**

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

- [ ] **Step 1: 创建订单模型**（包含 OrderStatus 枚举和 Order 数据类）

- [ ] **Step 2: 创建用户模型**

- [ ] **Step 3: 创建价格记录模型**

- [ ] **Step 4: 提交**

```bash
git add models/
git commit -m "feat: add data models for order, user and price"
```

---

#### Task 3: 实现订单服务

**Files:**
- Create: `services/__init__.py`
- Create: `services/order_service.py`
- Create: `tests/test_order_service.py`

**步骤：**

- [ ] **Step 1: 编写订单服务测试**

测试内容：
- `test_create_order` - 测试创建订单
- `test_get_order_by_id` - 测试根据ID获取订单
- `test_update_order_status` - 测试更新订单状态
- `test_get_orders_by_chat` - 测试根据聊天ID获取订单列表
- `test_status_transition_validation` - 测试状态流转验证

- [ ] **Step 2: 运行测试确认失败**

```bash
pytest tests/test_order_service.py -v
```

- [ ] **Step 3: 实现订单服务**

核心功能：
- `create_order()` - 创建订单，保存到数据库
- `get_order_by_id()` - 根据ID查询订单
- `update_status()` - 更新订单状态（带状态流转验证）
- `get_orders_by_chat()` - 查询聊天相关的订单列表
- `get_orders_by_user()` - 查询用户的订单列表

状态流转验证：
```python
VALID_TRANSITIONS = {
    OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.EXPIRED],
    OrderStatus.CONFIRMED: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.BOOKED, OrderStatus.CANCELLED, OrderStatus.REFUNDED],
    OrderStatus.BOOKED: [OrderStatus.COMPLETED],
    OrderStatus.REFUNDED: [OrderStatus.COMPLETED],
    OrderStatus.CANCELLED: [OrderStatus.COMPLETED],
    OrderStatus.EXPIRED: [],
    OrderStatus.COMPLETED: [],
}
```

- [ ] **Step 4: 运行测试确认通过**

```bash
pytest tests/test_order_service.py -v
```

- [ ] **Step 5: 提交**

```bash
git add services/ tests/
git commit -m "feat: implement order service with status transitions"
```

---

#### Task 4: 实现价格服务

**Files:**
- Create: `services/price_service.py`
- Create: `tests/test_price_service.py`

**步骤：**

- [ ] **Step 1: 编写价格服务测试**

测试内容：
- `test_query_price_from_cache` - 测试缓存查询
- `test_query_price_from_db` - 测试数据库查询
- `test_save_price` - 测试保存价格
- `test_clear_cache` - 测试清空缓存

- [ ] **Step 2: 实现价格服务**

核心功能：
- `query_price()` - 查询价格（先查缓存，再查数据库）
- `save_price()` - 保存价格记录
- `clear_cache()` - 清空缓存

缓存策略：
```python
# 内存缓存，key格式: hotel_id:room_id:check_in_date:check_out_date
cache_key = f"{hotel_id}:{room_id}:{check_in_date}:{check_out_date}"
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/test_price_service.py -v
```

- [ ] **Step 4: 提交**

```bash
git add services/ tests/
git commit -m "feat: implement price service with caching"
```

---

### Phase 3: 执行层（酒店API封装）

#### Task 5: 创建酒店执行器

**Files:**
- Create: `executor/__init__.py`
- Create: `executor/hotel_api.py`
- Create: `executor/hotel_executor.py`
- Create: `tests/test_hotel_executor.py`

**步骤：**

- [ ] **Step 1: 创建酒店API接口和模型**

定义数据类：
- `HotelSearchRequest` - 酒店搜索请求
- `HotelSearchResult` - 酒店搜索结果
- `BookingRequest` - 预订请求
- `BookingResult` - 预订结果
- `CancelRequest` - 取消请求
- `CancelResult` - 取消结果

定义抽象基类：
```python
class BaseHotelAPI(ABC):
    @abstractmethod
    async def search_hotels(self, request: HotelSearchRequest) -> List[HotelSearchResult]:
        pass

    @abstractmethod
    async def get_room_price(self, hotel_id: str, room_id: str, ...) -> Optional[float]:
        pass

    @abstractmethod
    async def book_room(self, request: BookingRequest) -> BookingResult:
        pass

    @abstractmethod
    async def cancel_booking(self, request: CancelRequest) -> CancelResult:
        pass
```

- [ ] **Step 2: 实现模拟酒店API**

创建 `MockHotelAPI` 类：
- 模拟两家测试酒店（市中心和机场）
- 每种房型有不同基础价格
- 根据日期计算总价
- 模拟预订和取消流程

- [ ] **Step 3: 创建酒店执行器**

创建 `HotelExecutor` 类：
```python
class HotelExecutor:
    def __init__(self, api: BaseHotelAPI):
        self.api = api

    async def search_and_quote(self, ...) -> Optional[Dict]:
        """搜索酒店并返回报价"""
        pass

    async def execute_booking(self, ...) -> BookingResult:
        """执行预订"""
        pass

    async def execute_cancellation(self, ...) -> CancelResult:
        """执行取消"""
        pass
```

- [ ] **Step 4: 提交**

```bash
git add executor/ tests/
git commit -m "feat: add hotel executor with mock API"
```

---

## 总结

本实现计划包含以下主要任务：

1. **Phase 1: 基础设施层**
   - Task 1: 创建数据库模块（SQLite连接管理、Schema定义）

2. **Phase 2: 业务层**
   - Task 2: 创建数据模型（Order、User、PriceRecord）
   - Task 3: 实现订单服务（CRUD操作、状态流转验证）
   - Task 4: 实现价格服务（缓存、数据库查询）

3. **Phase 3: 执行层**
   - Task 5: 创建酒店执行器（API接口、Mock实现、执行器）

每个任务都遵循 TDD 原则：
1. 编写测试（测试失败）
2. 运行测试确认失败
3. 实现代码（测试通过）
4. 运行测试确认通过
5. 提交代码

---

## 下一步

计划已保存到 `docs/superpowers/plans/2026-03-18-hotel-booking-system.md`。

**请确认：**
1. 是否需要调整任何任务的优先级或范围？
2. 是否需要补充任何技术细节？
3. 是否准备好开始执行？

确认后，我将使用 `superpowers:subagent-driven-development` 技能开始执行任务。
