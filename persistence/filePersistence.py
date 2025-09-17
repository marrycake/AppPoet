import json
from typing import Any, Dict, List, Optional
from .persistence import Persistence
import os


class FilePersistence(Persistence):

    def insert(self, data: Dict[str, Any]) -> int:
        self._data.append(data)
        self.save()
        return 1

    def insert_many(self, data_list: List[Dict[str, Any]]) -> int:
        self._data.extend(data_list)
        self.save()
        return len(data_list)

    def get_nested(self, item: dict, path: str) -> Any:
        """通过 'a.b.c' 获取嵌套字典/列表中的值"""
        keys = path.split('.')
        for key in keys:
            if isinstance(item, dict):
                item = item.get(key, None)
            else:
                return None
        return item

    def match_value(self, item_value: Any, filter_value: Any) -> bool:
        """支持列表包含或直接相等匹配"""
        if isinstance(item_value, list):
            return filter_value in item_value
        return item_value == filter_value

    def query(self, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if filter is None:
            return self._data.copy()
        result = []
        for item in self._data:
            match = True
            for k, v in filter.items():
                nested_value = self.get_nested(item, k)
                if not self.match_value(nested_value, v):
                    match = False
                    break
            if match:
                result.append(item)
        return result

    def update(self, filter: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        count = 0
        for item in self._data:
            match = True
            for k, v in filter.items():
                nested_value = self.get_nested(item, k)
                if not self.match_value(nested_value, v):
                    match = False
                    break
            if match:
                item.update(update_data)
                count += 1
        if count > 0:
            self.save()
        return count

    def delete(self, filter: Dict[str, Any]) -> int:
        original_len = len(self._data)
        new_data = []
        for item in self._data:
            match = True
            for k, v in filter.items():
                nested_value = self.get_nested(item, k)
                if not self.match_value(nested_value, v):
                    match = False
                    break
            if not match:
                new_data.append(item)
        self._data = new_data
        deleted_count = original_len - len(self._data)
        if deleted_count > 0:
            self.save()
        return deleted_count

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    def load(self) -> None:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        else:
            self._data = []

    def set_target(self, target: str) -> None:
        self.file_path = target
        self._data: List[Dict[str, Any]] = []
        self.load()
