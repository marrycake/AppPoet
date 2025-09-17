from abc import ABC, abstractmethod
from typing import Any, List, Dict


class DBHandler(ABC):
    """
    抽象数据库操作接口
    """

    @abstractmethod
    def connect(self, connection_string: str) -> None:
        """
        建立数据库连接
        :param connection_string: 数据库连接字符串
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        关闭数据库连接
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        执行查询语句并返回结果
        :param query: SQL 查询语句
        :param params: 可选的查询参数
        :return: 查询结果列表（每条记录用 dict 表示）
        """
        pass

    @abstractmethod
    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """
        执行非查询语句（INSERT, UPDATE, DELETE 等）
        :param query: SQL 语句
        :param params: 可选参数
        :return: 影响的行数
        """
        pass

    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        插入记录
        :param table: 表名
        :param data: 插入的数据（键为列名，值为对应值）
        :return: 影响的行数
        """
        pass

    @abstractmethod
    def update(self, table: str, data: Dict[str, Any], conditions: str, params: tuple = ()) -> int:
        """
        更新记录
        :param table: 表名
        :param data: 要更新的数据（键为列名，值为新值）
        :param conditions: WHERE 条件
        :param params: WHERE 条件参数
        :return: 影响的行数
        """
        pass

    @abstractmethod
    def delete(self, table: str, conditions: str, params: tuple = ()) -> int:
        """
        删除记录
        :param table: 表名
        :param conditions: WHERE 条件
        :param params: WHERE 条件参数
        :return: 影响的行数
        """
        pass

    @abstractmethod
    def commit(self) -> None:
        """
        提交事务
        """
        pass

    @abstractmethod
    def rollback(self) -> None:
        """
        回滚事务
        """
        pass
