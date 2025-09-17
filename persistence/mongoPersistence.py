from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from .persistence import Persistence
import uuid


class MongoPersistence(Persistence):
    """
    MongoDB 持久化，仅使用单集合存储。
    每条数据都有唯一的 apkId。
    """

    def __init__(self, uri: str, database: str):
        self.client = MongoClient(uri)
        self.db = self.client[database]
        self.main_collection_name: Optional[str] = None  # 主集合

    # ---------------------- 集合设置 ----------------------
    def set_target(self, target: str) -> None:
        """设置主集合名"""

        self.main_collection_name = target
        return target in self.db.list_collection_names()

        # ---------------------- 插入 ----------------------

    def insert(self, data: Dict[str, Any]) -> int:
        if not self.main_collection_name:
            raise ValueError("请先调用 set_target 设置主集合名")

        result = self.db[self.main_collection_name].insert_one(data)
        return 1 if result.acknowledged else 0

    def insert_many(self, data_list: List[Dict[str, Any]]) -> int:
        if not self.main_collection_name:
            raise ValueError("请先调用 set_target 设置主集合名")

        docs = []
        for data in data_list:
            app_id = str(uuid.uuid4())
            main_doc = {"apkId": app_id}
            main_doc.update(data)
            docs.append(main_doc)

        result = self.db[self.main_collection_name].insert_many(docs)
        return len(result.inserted_ids)

    # ---------------------- 查询 ----------------------
    def query(self, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.main_collection_name:
            raise ValueError("请先调用 set_target 设置主集合名")

        filter = filter or {}
        return list(self.db[self.main_collection_name].find(filter))

    # ---------------------- 更新 ----------------------
    def update(self, filter: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        if not self.main_collection_name:
            raise ValueError("请先调用 set_target 设置主集合名")
        result = self.db[self.main_collection_name].update_many(
            filter, {"$set": update_data}
        )
        return result.modified_count

    # ---------------------- 删除 ----------------------
    def delete(self, filter: Dict[str, Any]) -> int:
        if not self.main_collection_name:
            raise ValueError("请先调用 set_target 设置主集合名")

        result = self.db[self.main_collection_name].delete_many(filter)
        return result.deleted_count

    # ---------------------- JSON 文件接口（MongoDB无需操作） ----------------------
    def save(self) -> None:
        """MongoDB 不需要保存"""
        pass

    def load(self) -> None:
        """MongoDB 不需要加载"""
        pass
