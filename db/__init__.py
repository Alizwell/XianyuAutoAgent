#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模块
提供数据库连接和操作接口
"""
from .database import Database, get_db_instance

__all__ = [
    "Database",
    "get_db_instance"
]
