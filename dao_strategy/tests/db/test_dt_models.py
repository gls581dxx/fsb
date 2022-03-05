import time
import pathmagic

from dao_strategy.db.dt_models import (User, Order, StrategyClass, StrategyInstance)


def test_user():
    users = User.objects.filter()
    for user in users:
        print(user.created_time, user.user_name, user.feishu_api, user.agree)
        print(user.to_json())
        if user.user_name == '155302999':
            user.agree = '1'
            user.save()


def test_write_concern():
    t1 = time.time()
    user = User()
    user.user_name = '155999'
    user.phone_num = '155999'
    user.phone_zone_code = '86'
    user.password = 'nopwd'
    user.sms_vcode = '9999'
    user.img_vcode = '9999'
    user.ex_aes_key = ''
    user.invitor = ''
    user.feishu_api = 'hhh'
    user.agree = 'yes'
    user.google_auth_secret = ''
    user.exchange = {}
    user.save()
    # user.save(write_concern={"w": 2})
    print(time.time() - t1)


def test_order():
    orders = Order.objects.filter().limit(5)
    for order in orders:
        print(order.to_json())


def test_strategy_class():
    scs = StrategyClass.objects.filter().limit(5)
    for sc in scs:
        print(sc.to_json())


def test_strategy_instance():
    sis = StrategyInstance.objects.filter().limit(5)
    for si in sis:
        print(si.to_json())


def main():
    # test_user()
    test_write_concern()
    # test_order()
    # test_strategy_class()
    # test_strategy_instance()
    print('test pass')


if __name__ == '__main__':
    main()
