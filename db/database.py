#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接管理模块
使用SQLite数据库
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class Database:
    """数据库连接管理类"""

    def __init__(self, db_path="data/xianyu.db"):
        """
        初始化数据库连接
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._conn = None
        self._cursor = None
        self._ensure_data_dir()
        self._ensure_tables()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.db_path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

    def _ensure_tables(self):
        """确保所有表存在"""
        try:
            self.connect()
            # 读取并执行schema.sql
            schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                self._cursor.executescript(schema_sql)
                self._conn.commit()
            else:
                print("Warning: schema.sql not found at %s" % schema_path)
        except Exception as e:
            print("Error ensuring tables: %s" % e)
            if self._conn:
                self._conn.rollback()
        finally:
            self.disconnect()

    def connect(self):
        """
        连接到数据库
        Returns:
            是否成功连接
        """
        try:
            self._conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            self._conn.row_factory = sqlite3.Row
            self._cursor = self._conn.cursor()
            return True
        except Exception as e:
            print("Error connecting to database: %s" % e)
            self._conn = None
            self._cursor = None
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self._conn:
            try:
                self._conn.close()
            except Exception as e:
                print("Error disconnecting from database: %s" % e)
            finally:
                self._conn = None
                self._cursor = None

    def execute(self, sql, params=None):
        """
        执行SQL语句
        Args:
            sql: SQL语句
            params: 参数列表
        Returns:
            查询结果（如果是SELECT语句），否则返回None
        """
        try:
            if not self._conn or not self._cursor:
                if not self.connect():
                    return None

            if params:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)

            if sql.strip().upper().startswith("SELECT"):
                results = self._cursor.fetchall()
                return [dict(row) for row in results]
            else:
                self._conn.commit()
                return None
        except Exception as e:
            print("Error executing SQL: %s" % e)
            print("SQL: %s" % sql)
            print("Params: %s" % params)
            if self._conn:
                self._conn.rollback()
            return None

    def executemany(self, sql, params):
        """
        批量执行SQL语句
        Args:
            sql: SQL语句
            params: 参数列表的列表
        Returns:
            是否成功执行
        """
        try:
            if not self._conn or not self._cursor:
                if not self.connect():
                    return False

            self._cursor.executemany(sql, params)
            self._conn.commit()
            return True
        except Exception as e:
            print("Error executing SQL many: %s" % e)
            if self._conn:
                self._conn.rollback()
            return False

    def get_last_insert_id(self):
        """获取最后插入的ID"""
        try:
            result = self.execute("SELECT last_insert_rowid() as id")
            if result:
                return result[0]["id"]
            return -1
        except Exception as e:
            print("Error getting last insert id: %s" % e)
            return -1

    def get_table_names(self):
        """获取所有表名"""
        try:
            result = self.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            if result:
                return [row["name"] for row in result]
            return []
        except Exception as e:
            print("Error getting table names: %s" % e)
            return []

    def table_exists(self, table_name):
        """
        检查表是否存在
        Args:
            table_name: 表名
        Returns:
            是否存在
        """
        return table_name in self.get_table_names()

    # ==================== 通用查询方法 ====================

    def find_one(self, table, conditions=None, fields=["*"]):
        """
        查询单条记录
        Args:
            table: 表名
            conditions: 查询条件
            fields: 返回字段
        Returns:
            单条记录或None
        """
        field_str = ", ".join(fields)
        sql = "SELECT {field_str} FROM {table}".format(field_str=field_str, table=table)
        params = []

        if conditions:
            where_clause = " AND ".join(["{k} = ?".format(k=k) for k in conditions.keys()])
            sql += " WHERE {where_clause}".format(where_clause=where_clause)
            params = list(conditions.values())

        sql += " LIMIT 1"
        results = self.execute(sql, params)
        return results[0] if results else None

    def find_all(self, table, conditions=None, fields=["*"], order_by=None, limit=None):
        """
        查询多条记录
        Args:
            table: 表名
            conditions: 查询条件
            fields: 返回字段
            order_by: 排序字段
            limit: 限制条数
        Returns:
            记录列表
        """
        field_str = ", ".join(fields)
        sql = "SELECT {field_str} FROM {table}".format(field_str=field_str, table=table)
        params = []

        if conditions:
            where_clause = " AND ".join(["{k} = ?".format(k=k) for k in conditions.keys()])
            sql += " WHERE {where_clause}".format(where_clause=where_clause)
            params = list(conditions.values())

        if order_by:
            sql += " ORDER BY {order_by}".format(order_by=order_by)

        if limit:
            sql += " LIMIT {limit}".format(limit=limit)

        results = self.execute(sql, params)
        return results if results else []

    def insert(self, table, data):
        """
        插入单条记录
        Args:
            table: 表名
            data: 数据字典
        Returns:
            插入的ID
        """
        fields = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data.values()])
        sql = "INSERT INTO {table} ({fields}) VALUES ({placeholders})".format(
            table=table, fields=fields, placeholders=placeholders
        )
        params = list(data.values())

        try:
            result = self.execute(sql, params)
            # For INSERT statements, we don't get a result, but we should still return the last insert id
            if sql.strip().upper().startswith("INSERT"):
                return self.get_last_insert_id()
            if result is None:
                return -1
            return self.get_last_insert_id()
        except Exception as e:
            print(f"Insert error: {e}")
            return -1

    def update(self, table, data, conditions):
        """
        更新记录
        Args:
            table: 表名
            data: 更新的数据
            conditions: 更新条件
        Returns:
            影响的行数
        """
        set_clause = ", ".join(["{k} = ?".format(k=k) for k in data.keys()])
        where_clause = " AND ".join(["{k} = ?".format(k=k) for k in conditions.keys()])
        sql = "UPDATE {table} SET {set_clause} WHERE {where_clause}".format(
            table=table, set_clause=set_clause, where_clause=where_clause
        )

        params = list(data.values()) + list(conditions.values())

        # 先查询有多少符合条件的记录
        count_sql = "SELECT COUNT(*) FROM {table} WHERE {where_clause}".format(
            table=table, where_clause=where_clause
        )
        count_params = list(conditions.values())
        count_result = self.execute(count_sql, count_params)
        if count_result:
            affected = count_result[0]['COUNT(*)']
            self.execute(sql, params)
            return affected
        return 0

    def delete(self, table, conditions):
        """
        删除记录
        Args:
            table: 表名
            conditions: 删除条件
        Returns:
            影响的行数
        """
        where_clause = " AND ".join(["{k} = ?".format(k=k) for k in conditions.keys()])
        sql = "DELETE FROM {table} WHERE {where_clause}".format(table=table, where_clause=where_clause)
        params = list(conditions.values())

        original_count = self._cursor.rowcount
        self.execute(sql, params)
        return self._cursor.rowcount - original_count

    # ==================== 订单相关方法 ====================

    def create_order(self, order_data):
        """
        创建订单
        Args:
            order_data: 订单数据
        Returns:
            订单ID或None
        """
        required_fields = [
            "order_id", "chat_id", "user_id", "hotel_id",
            "room_id", "check_in_date", "check_out_date"
        ]
        for field in required_fields:
            if field not in order_data:
                print("Missing required field: %s" % field)
                return None

        data = {
            "order_id": order_data["order_id"],
            "chat_id": order_data["chat_id"],
            "user_id": order_data["user_id"],
            "item_id": order_data.get("item_id"),
            "hotel_id": order_data["hotel_id"],
            "room_id": order_data["room_id"],
            "check_in_date": order_data["check_in_date"],
            "check_out_date": order_data["check_out_date"],
            "room_count": order_data.get("room_count", 1),
            "original_price": order_data.get("original_price"),
            "final_price": order_data.get("final_price"),
            "currency": order_data.get("currency", "CNY"),
            "status": order_data.get("status", "PENDING"),
            "metadata": json.dumps(order_data.get("metadata")) if order_data.get("metadata") else None,
            "remark": order_data.get("remark")
        }

        return self.insert("orders", data)

    def update_order_status(self, order_id, status):
        """
        更新订单状态
        Args:
            order_id: 订单ID
            status: 新状态
        Returns:
            是否成功
        """
        data = {"status": status, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        status_fields = {
            "CONFIRMED": "confirmed_at",
            "PAID": "paid_at",
            "BOOKED": "booked_at",
            "REFUNDED": "refunded_at",
            "COMPLETED": "completed_at",
            "EXPIRED": "completed_at",
            "CANCELLED": "completed_at"
        }

        if status in status_fields:
            data[status_fields[status]] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result = self.update("orders", data, {"order_id": order_id})
        return result > 0

    def get_order_by_id(self, order_id):
        """
        根据订单ID获取订单
        Args:
            order_id: 订单ID
        Returns:
            订单信息或None
        """
        return self.find_one("orders", {"order_id": order_id})

    def get_orders_by_chat_id(self, chat_id):
        """
        根据对话ID获取订单
        Args:
            chat_id: 对话ID
        Returns:
            订单列表
        """
        return self.find_all("orders", {"chat_id": chat_id}, order_by="created_at DESC")

    # ==================== 用户相关方法 ====================

    def create_user(self, user_id, nickname=None):
        """
        创建用户
        Args:
            user_id: 用户ID
            nickname: 昵称
        Returns:
            用户ID
        """
        user = self.find_one("users", {"user_id": user_id})
        if user:
            return user["id"]

        data = {
            "user_id": user_id,
            "nickname": nickname
        }
        return self.insert("users", data)

    def get_user(self, user_id):
        """
        获取用户信息
        Args:
            user_id: 用户ID
        Returns:
            用户信息或None
        """
        return self.find_one("users", {"user_id": user_id})

    def update_user_risk_level(self, user_id, risk_level):
        """
        更新用户风险等级
        Args:
            user_id: 用户ID
            risk_level: 风险等级
        Returns:
            是否成功
        """
        result = self.update("users", {"risk_level": risk_level}, {"user_id": user_id})
        return result > 0

    def add_user_blacklist(self, user_id):
        """
        将用户加入黑名单
        Args:
            user_id: 用户ID
        Returns:
            是否成功
        """
        result = self.update("users", {"blacklist": True}, {"user_id": user_id})
        return result > 0

    # ==================== 价格记录相关方法 ====================

    def create_price_record(self, price_data):
        """
        创建价格记录
        Args:
            price_data: 价格数据
        Returns:
            记录ID或None
        """
        required_fields = ["hotel_id", "room_id", "check_in_date", "check_out_date", "price"]
        for field in required_fields:
            if field not in price_data:
                print("Missing required field: %s" % field)
                return None

        data = {
            "hotel_id": price_data["hotel_id"],
            "room_id": price_data["room_id"],
            "check_in_date": price_data["check_in_date"],
            "check_out_date": price_data["check_out_date"],
            "price": price_data["price"],
            "currency": price_data.get("currency", "CNY")
        }

        sql = """
        INSERT OR REPLACE INTO price_records
        (hotel_id, room_id, check_in_date, check_out_date, price, currency, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            data["hotel_id"],
            data["room_id"],
            data["check_in_date"],
            data["check_out_date"],
            data["price"],
            data["currency"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        self.execute(sql, params)
        return self.get_last_insert_id()

    def get_price_record(self, hotel_id, room_id, check_in_date, check_out_date):
        """
        获取价格记录
        Args:
            hotel_id: 酒店ID
            room_id: 房型ID
            check_in_date: 入住日期
            check_out_date: 离店日期
        Returns:
            价格记录或None
        """
        conditions = {
            "hotel_id": hotel_id,
            "room_id": room_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date
        }
        return self.find_one("price_records", conditions)

    def get_price_records_by_hotel(self, hotel_id, limit=100):
        """
        获取酒店价格记录
        Args:
            hotel_id: 酒店ID
            limit: 返回条数限制
        Returns:
            价格记录列表
        """
        return self.find_all(
            "price_records",
            {"hotel_id": hotel_id},
            order_by="created_at DESC",
            limit=limit
        )


# 全局数据库实例
_db_instance = None


def get_db_instance(db_path="data/xianyu.db"):
    """获取数据库实例（根据路径返回不同的实例）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    elif _db_instance.db_path != db_path:
        # 如果路径不同，创建新实例
        _db_instance = Database(db_path)
    return _db_instance
