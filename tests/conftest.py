import os
import sqlite3
import tempfile

import pytest

from repos import migrations


@pytest.fixture(scope="session", autouse=True)
def test_db_setup():
    """
    全局测试夹具：
    在运行所有测试之前，将数据库路径替换为临时文件，并运行表结构迁移，
    确保测试在隔离的环境中运行，不污染真实数据库。
    """
    # 强制将测试期间的 DB_PATH 指向临时文件
    fd, temp_db = tempfile.mkstemp(suffix=".sqlite")

    # 注入到 config 中以供 repos 引用
    import config

    original_db_path = config.DB_PATH
    config.DB_PATH = temp_db

    # 初始化表结构
    migrations.init_db()

    yield temp_db

    # 清理
    os.close(fd)
    os.remove(temp_db)
    config.DB_PATH = original_db_path


@pytest.fixture(autouse=True)
def clean_db(test_db_setup):
    """
    每个测试用例运行后，清空所有表的数据，保证用例之间的独立性。
    """
    yield
    import config

    conn = sqlite3.connect(config.DB_PATH)
    tables = ["auth", "auth_sessions", "users", "plans", "daily_tasks", "check_ins", "user_state"]
    for table in tables:
        try:
            conn.execute(f"DELETE FROM {table}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()
