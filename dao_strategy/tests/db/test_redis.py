import pathmagic

from dao_strategy.settings.config import cfg
from dao_strategy.db.redis import RedisClient


class testRedisClient(object):

    def __init__(self):
        self.redis = self.test_get_redis()

    def test_get_redis(self):
        # redis_cfg = {}
        # redis_cfg['host'] = '127.0.0.1'
        # redis_cfg['port'] = 6379
        # redis_cfg['password'] = ''

        redis_cfg = cfg['redis']['dao_quote']
        print('cfg: ', redis_cfg)
        redis = RedisClient(redis_cfg)
        return redis

    def test_set_value(self):
        key_name = 'test_key'
        value = 'test_value'
        rst = self.redis.set_value(key_name, value)
        print('[*] test_set_value, {}'.format(rst))

    def test_get_value(self):
        key_name = 'test_key'
        rst = self.redis.get_value(key_name)
        print('[*] test_get_value, {}'.format(rst))

    def test_exists(self):
        key_name_list = ['test_key', 'test_key_1']
        for key_name in key_name_list:
            print('[*] {}: {}'.format(key_name, self.redis.exists(key_name)))

    def main(self):
        self.test_set_value()
        self.test_get_value()
        self.test_exists()


def main():
    trc = testRedisClient()
    trc.main()


if __name__ == '__main__':
    main()
