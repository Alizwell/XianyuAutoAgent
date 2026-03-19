-- 咸鱼酒店预订系统数据库表结构
-- SQLite数据库

-- ==================== 订单表 (orders) ====================
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT UNIQUE NOT NULL,        -- 订单唯一标识
    chat_id TEXT NOT NULL,                 -- 闲鱼对话ID
    user_id TEXT NOT NULL,                 -- 用户ID
    item_id TEXT,                          -- 闲鱼商品ID

    -- 酒店信息
    hotel_id TEXT NOT NULL,                -- 酒店ID
    room_id TEXT NOT NULL,                 -- 房型ID
    check_in_date TEXT NOT NULL,           -- 入住日期 (YYYY-MM-DD)
    check_out_date TEXT NOT NULL,          -- 离店日期 (YYYY-MM-DD)
    room_count INTEGER DEFAULT 1,         -- 房间数量

    -- 价格信息
    original_price REAL,                   -- 原始价格
    final_price REAL,                      -- 最终价格
    currency TEXT DEFAULT 'CNY',          -- 货币

    -- 状态管理
    status TEXT NOT NULL DEFAULT 'PENDING',
    -- 状态流转: PENDING → CONFIRMED → PAID → BOOKED → COMPLETED
    --                    → REFUNDED → COMPLETED

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confirmed_at DATETIME,                 -- 确认时间
    paid_at DATETIME,                      -- 付款时间
    booked_at DATETIME,                    -- 预订成功时间
    completed_at DATETIME,                 -- 完成时间

    -- 扩展字段
    metadata TEXT,                         -- JSON扩展信息
    remark TEXT                            -- 备注
);

CREATE INDEX IF NOT EXISTS idx_orders_chat_id ON orders(chat_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- ==================== 价格记录表 (price_records) ====================
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

-- ==================== 用户表 (users) ====================
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    nickname TEXT,
    blacklist BOOLEAN DEFAULT FALSE,
    risk_level INTEGER DEFAULT 0,           -- 0=正常, 1=注意, 2=警告
    total_orders INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
