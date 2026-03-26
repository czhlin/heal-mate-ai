"""
数据访问基础设施 (Data Access Infrastructure): 数据库连接池/工厂

提供最基础的底层连接支撑。当前基于 SQLite 提供简单的连接工厂方法。
随着系统演进（例如切分读写库或迁移至 PostgreSQL/MySQL），
此处可以无缝升级为 SQLAlchemy 连接池，上层 Repository 代码可保持稳定。
"""

import sqlite3

from config import DB_PATH


def connect():
    """
    获取一个瞬态数据库连接实例。
    调用方需要负责关闭连接或使用上下文管理器 (with context)。
    """
    return sqlite3.connect(DB_PATH)
