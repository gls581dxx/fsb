import time
import socket
import pymongo
import traceback

from dao_strategy.db.redis import RedisClient
from dao_strategy.settings.config import cfg


def get_client():
    db_name = 'dao_trade'
    mongo_cfg = cfg['mongo'][db_name]
    mode = mongo_cfg['mode']
    connstr = mongo_cfg['connstr']
    db_name = mongo_cfg['db_name']
    db_user = mongo_cfg['db_user']
    db_pwd = mongo_cfg['db_pwd']

    repl_name = mongo_cfg['repl_name']
    client = pymongo.MongoClient(host=connstr.format(db_user, db_pwd, db_name),
                                 # ssl=True, ssl_cert_reqs=ssl.CERT_NONE,
                                 replicaset=repl_name)
    return client


def get_local_ip():
    addr1 = '223.5.5.5'
    addr2 = '114.114.114.114'
    limit = 5
    addr = addr1

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((addr, 80))
            ip = s.getsockname()[0]
            break
        except Exception as e:
            limit -= 1
            if limit < 3:
                addr = addr2
            if limit < 0:
                ip = '*'
                print('[*] get_local_ip: {}'.format(traceback.format_exc()))
                break
    return ip


def get_primary(client):
    try:
        primary_list = [client.primary]
    except Exception as e:
        primary_list = []
    return primary_list


def fresh_primary():
    redis_cfg = cfg['redis']['dao_quote']
    print('redis cfg: ', redis_cfg)
    redis = RedisClient(redis_cfg)
    local_ip = get_local_ip()
    if local_ip == '*':
        print('[*] fresh_primary failed, local ip : {}'.format(local_ip))
        sys.exit(0)
    rst = redis.set_value('db_local', local_ip)

    client = get_client()
    while True:
        try:
            primary_list = get_primary(client)
            if len(primary_list) > 0:
                key_name = 'db_primary'
                value = '{}:{}'.format(primary_list[0][0], primary_list[0][1])
                rst = redis.set_value(key_name, value)

                key_name = 'is_primary'
                if local_ip == primary_list[0][0]:
                    value = 'yes'
                else:
                    value = 'no'
                rst = redis.set_value(key_name, value)
        except Exception as e:
            print(traceback.format_exc())
        time.sleep(1)


def is_primary():
    redis_cfg = cfg['redis']['dao_quote']
    redis = RedisClient(redis_cfg)
    key_name = 'is_primary'
    try:
        rst = redis.get_value(key_name)
    except Exception as e:
        rst = 'none'
    return rst


def get_secondaries(client):
    try:
        secondaries_list = list(client.secondaries)
    except Exception as e:
        secondaries_list = []
    return secondaries_list


def get_nodes(client):
    try:
        node_list = list(client.nodes)
    except Exception as e:
        node_list = []
    return node_list
