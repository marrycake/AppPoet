import json
import redis


class Memory:
    def __init__(self, host, port, password):
        self.redis = redis.Redis(
            host=host,      # Redis 服务器地址
            port=port,              # Redis端口
            password=password,          # 如果设置了密码
            decode_responses=True      # 自动将 bytes 解码为 str
        )

    def set(self, key, value):
        """设置键值对"""
        self.redis.set(key, value)

    def get(self, key):
        """获取键对应的值"""
        return self.redis.get(key)

    def delete(self, key):
        """删除指定键"""
        self.redis.delete(key)

    def exists(self, key):
        """检查键是否存在"""
        return self.redis.exists(key)

    def hset(self, main_key, field, value):
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value)
        self.redis.hset(main_key, field, value)

    def hget(self, main_key, field):
        value = self.redis.hget(main_key, field)
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def hdel(self, main_key, field):
        self.redis.hdel(main_key, field)

    def hexists(self, main_key, field):
        return self.redis.hexists(main_key, field)
