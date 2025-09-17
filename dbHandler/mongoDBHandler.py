from typing import Any, List, Dict
from pymongo import MongoClient
from pymongo.collection import Collection
from .dbHandler import DBHandler


class MongoDBHandler(DBHandler):
    """
    MongoDB 实现的 DBHandler
    """

    def __init__(self):
        self.client: MongoClient = None
        self.db = None

    def connect(self, connection_string: str) -> None:
        """
        建立数据库连接
        :param connection_string: MongoDB 连接字符串, 例如 "mongodb://localhost:27017/dbname"
        """
        self.client = MongoClient(connection_string)
        # 解析数据库名
        db_name = connection_string.rsplit("/", 1)[-1]
        self.db = self.client[db_name]

    def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def execute_query(self, collection_name: str, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        查询集合
        :param collection_name: 集合名
        :param filter: 查询条件 dict
        :return: 结果列表，每条记录为 dict
        """
        filter = filter or {}
        collection: Collection = self.db[collection_name]
        result = collection.find(filter)
        return list(result)

    def execute_non_query(self, collection_name: str, operation: str, data: Dict[str, Any], filter: Dict[str, Any] = None) -> int:
        """
        通用非查询操作
        :param collection_name: 集合名
        :param operation: 操作类型 "insert"/"update"/"delete"
        :param data: 数据 dict
        :param filter: 条件 dict (update/delete)
        :return: 影响的行数
        """
        collection: Collection = self.db[collection_name]
        if operation == "insert":
            result = collection.insert_one(data)
            return 1 if result.acknowledged else 0
        elif operation == "update":
            if filter is None:
                raise ValueError("update 操作必须提供 filter")
            result = collection.update_many(filter, {"$set": data})
            return result.modified_count
        elif operation == "delete":
            if filter is None:
                raise ValueError("delete 操作必须提供 filter")
            result = collection.delete_many(filter)
            return result.deleted_count
        else:
            raise ValueError(f"不支持的操作类型: {operation}")

    def insert(self, collection_name: str, data: Dict[str, Any]) -> int:
        return self.execute_non_query(collection_name, "insert", data)

    def update(self, collection_name: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> int:
        return self.execute_non_query(collection_name, "update", data, conditions)

    def delete(self, collection_name: str, conditions: Dict[str, Any]) -> int:
        return self.execute_non_query(collection_name, "delete", {}, conditions)

    def commit(self) -> None:
        """
        MongoDB 默认是自动提交事务（除非使用事务模式）
        """
        pass

    def rollback(self) -> None:
        """
        MongoDB 单操作默认无回滚，如果使用事务则需要事务支持
        """
        pass
