from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Persistence(ABC):
    """
    通用持久化接口，兼容 JSON 文件和 MongoDB 数据库。
    """

    @abstractmethod
    def insert(self, data: Dict[str, Any]) -> Any:
        """
        插入一条数据
        :param data: 待插入的数据
        :return: 插入操作的结果(如ID或状态)
        """
        pass

    @abstractmethod
    def insert_many(self, data_list: List[Dict[str, Any]]) -> Any:
        """
        插入多条数据
        :param data_list: 待插入的数据列表
        :return: 插入操作的结果
        """
        pass

    @abstractmethod
    def query(self, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        查询数据
        :param filter: 查询条件
        :return: 查询结果列表
        """
        pass

    @abstractmethod
    def update(self, filter: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        """
        更新数据
        :param filter: 更新条件
        :param update_data: 更新内容
        :return: 更新的记录数量
        """
        pass

    @abstractmethod
    def delete(self, filter: Dict[str, Any]) -> int:
        """
        删除数据
        :param filter: 删除条件
        :return: 删除的记录数量
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """
        保存数据（主要用于 JSON 文件）
        """
        pass

    @abstractmethod
    def load(self) -> None:
        """
        加载数据（主要用于 JSON 文件）
        """
        pass

    @abstractmethod
    def set_target(self, target: str) -> None:
        """
        设置存储目标
        - 对 JSON 文件：改变文件路径
        - 对 MongoDB: 改变操作的集合名
        :param target: JSON 文件路径 或 MongoDB 集合名
        """
        pass
