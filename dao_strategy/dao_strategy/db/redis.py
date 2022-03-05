import redis


class RedisClient(object):

    def __init__(self, cfg):
        host = cfg['host']
        port = cfg['port']
        pwd = cfg.get('password', '')
        pool = redis.ConnectionPool(host=host, port=port, password=pwd, db=0)
        self.redis = redis.StrictRedis(connection_pool=pool)

    def set_value(self, key_name, value):
        self.redis[key_name] = str(value)
        return True

    def get_value(self, key_name):
        value = self.redis[key_name]
        value = value.decode('utf-8')
        return value

    def exists(self, key_name):
        value = self.redis.exists(key_name)
        if value == 1:
            return True
        else:
            return False
