import time
import pathmagic

from dao_strategy.db import dt_mongo



def test_get_client():
    client = dt_mongo.get_client()
    return client


def test_get_local_ip():
    ip = dt_mongo.get_local_ip()
    print(ip)


def test_get_primary():
    client = dt_mongo.get_client()
    limit = 5
    while True:
        primary_list = dt_mongo.get_primary(client)
        print(primary_list)
        if limit < 0:
            break
        limit -= 1
        time.sleep(1)


def test_fresh_primary():
    dt_mongo.fresh_primary()


def test_is_primary():
    is_primary = dt_mongo.is_primary()
    print(is_primary)


def test_get_nodes():
    client = test_get_client()
    limit = 5
    while True:
        node_list = dt_mongo.get_nodes(client)
        print(node_list)
        if limit < 0:
            break
        limit -= 1
        time.sleep(1)


def test_find():
    client = test_get_client()
    db = client['dao_trade']
    tmp_collect = db['user']
    print(tmp_collect)
    print(tmp_collect.find_one({}))


def main():
    test_get_local_ip()
    test_get_primary()
    test_fresh_primary()
    test_is_primary()
    test_get_nodes()
    test_find()


if __name__ == '__main__':
    main()
