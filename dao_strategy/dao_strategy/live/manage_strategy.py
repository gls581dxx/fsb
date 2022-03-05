#!/usr/bin/env python
# coding=utf-8

import os
import ast
import sys
import time
import json
import redis
import psutil
import datetime
import traceback
import importlib
import optparse
sys.path.append('../../')

from dao_strategy.db import dt_mongo
from dao_strategy.utils import dao_log
from dao_strategy.utils import send_sms
from dao_strategy.db.dt_models import (User, StrategyInstance)


def start_one_strategy_instance(run_type, sms_send, strategy_instance_id):
    strategy_instance = StrategyInstance.objects.get(
                        id=strategy_instance_id)
    strategy_type = strategy_instance.strategy_type
    user_id = strategy_instance.user_id
    user_name = strategy_instance.user_name
    account_type = strategy_instance.account_type
    exchange = strategy_instance.exchange
    symbol = strategy_instance.symbol
    exchange_2 = strategy_instance.exchange_2
    symbol_2 = strategy_instance.symbol_2
    spread_usdt = float(strategy_instance.spread_usdt)
    min_trade_num = strategy_instance.min_trade_num
    one_time_buy = strategy_instance.one_time_buy
    sms_send_ = strategy_instance.sms_send
    if (sms_send == 'yes'):
        sms_send = sms_send_

    user = User.objects.get(id=user_id)
    setting_dict = {}
    setting_dict['strategy_instance_id'] = strategy_instance_id
    setting_dict['strategy_type'] = strategy_type
    setting_dict['user_name'] = user_name
    setting_dict['user_id'] = str(user.id)
    phone_zone_code = user.phone_zone_code
    phone_num = user.phone_num
    feishu_api = user.feishu_api
    setting_dict['phone_zone_code'] = phone_zone_code
    setting_dict['phone_num'] = phone_num
    setting_dict['feishu_api'] = feishu_api
    setting_dict['run_type'] = run_type
    setting_dict['sms_send'] = sms_send
    setting_dict['account_type'] = account_type

    setting_dict['exchange'] = exchange
    setting_dict['symbol'] = symbol
    setting_dict['exchange_a'] = exchange
    setting_dict['symbol_a'] = symbol
    setting_dict['exchange_b'] = exchange_2
    setting_dict['symbol_b'] = symbol_2
    setting_dict['spread_usdt'] = spread_usdt
    setting_dict['min_trade_num'] = min_trade_num
    setting_dict['one_time_buy'] = one_time_buy
    setting_dict['param_dict'] = ast.literal_eval(str(strategy_instance.param_dict))
    setting_dict['status_dict'] = ast.literal_eval(str(strategy_instance.status_dict))
    if (strategy_type == 'fs_arbitrage_strategy'):
        strategy_name = str(strategy_instance.id)
        setting_dict['strategy_name'] = strategy_name
        strategy_type = 'arbitrage'
        strategy_file = 'strategy_1'
        class_name = 'FutureSpotArbitrage'
    elif (strategy_type == 'ff_arbitrage_strategy'):
        strategy_name = str(strategy_instance.id)
        setting_dict['strategy_name'] = strategy_name
        strategy_type = 'arbitrage'
        strategy_file = 'strategy_3'
        class_name = 'FutureFutureArbitrage'
    elif (strategy_type == 'spot_arbitrage_strategy'):
        strategy_name = str(strategy_instance.id)
        setting_dict['strategy_name'] = strategy_name
        strategy_type = 'arbitrage'
        strategy_file = 'strategy_5'
        class_name = 'SpotSpotArbitrage'
    elif (strategy_type == 'future_strategy'):
        strategy_name = strategy_instance.strategy_name
        setting_dict['strategy_name'] = strategy_name
        strategy_type = 'future_strategy'
        strategy_file = strategy_name
        class_name = 'CtaStrategy'
    elif (strategy_type == 'spot_strategy'):
        strategy_name = strategy_instance.strategy_name
        setting_dict['strategy_name'] = strategy_name
        strategy_type = 'spot_strategy'
        strategy_file = strategy_name
        class_name = 'CtaStrategy'
    elif (strategy_type == 'conditional_strategy'):
        strategy_name = strategy_instance.strategy_name
        setting_dict['strategy_name'] = str(strategy_instance.id)
        strategy_type = 'conditional'
        strategy_file = strategy_name
        class_name = strategy_name.split('_')[0].capitalize() + \
                     strategy_name.split('_')[1].capitalize()
    else:
        pass
    try:
        file_module = importlib.import_module('dao_strategy.live.{}.{}'.format(
                      strategy_type, strategy_file))
        StrategyInstanceClass = getattr(file_module, class_name)
        strategy_instance_main = StrategyInstanceClass(setting_dict)
        strategy_instance_main.main_trade()
    except Exception as e:
        print('failed', setting_dict['strategy_instance_id'], user_name, strategy_type, strategy_file)
        if (sms_send == 'yes' or sms_send == 'shu'):
            nationCode = phone_zone_code
            phoneNumber = phone_num
            reminder_type = 'err'
            send_sms.send_strategy_reminder(nationCode, phoneNumber, strategy_name, reminder_type)
        strategy_instance.status = 'error'
        strategy_instance.save()
        exception_msg = traceback.format_exc()
        msg = exception_msg
        log_msg = '{}, {}, {}, {}, {}'.format(strategy_name, msg,
                  user_name, exchange, symbol)
        log_dict = {}
        log_dict['user_name'] = user_name
        log_dict['user_id'] = strategy_instance.user_id
        log_dict['phone_num'] = phone_num
        log_dict['strategy_name'] = strategy_name
        log_dict['strategy_instance_id'] = str(strategy_instance.id)
        log_dict['strategy_type'] = strategy_type
        log_dict['account_type'] = account_type
        log_dict['exchange'] = exchange
        log_dict['symbol'] = symbol
        log_dict['log_type'] = 'strategy_log'
        log_dict['log_level'] = 'error'
        msg_dict = {}
        msg_dict['msg'] = msg
        msg_dict['status_dict'] = {}
        log_dict['log_message'] = json.dumps(msg_dict)
        dao_log.save_log(log_dict)
        return None


def manage_strategy_instance(run_type, sms_send, multi='no'):
    first = 1
    print('[*] running with multi: {}'.format(multi))
    if multi == 'yes':
        while True:
            is_primary = dt_mongo.is_primary()
            if is_primary == 'yes':
                print('[*]is_primary: {}, running'.format(is_primary))
                break
            time.sleep(1)
    while True:
        strategy_instances = StrategyInstance.objects.all()
        for strategy_instance in strategy_instances:
            strategy_instance_id = str(strategy_instance.id)
            status = strategy_instance.status
            pid = strategy_instance.pid
            pid_status = psutil.pid_exists(pid)
            if (pid_status is True):
                if (status == 'running'):
                    pass
                elif (status == 'stop'):
                    os.system('kill {}'.format(pid))
            elif (pid_status is False):
                if (status == 'running'):
                    if multi == 'yes':
                        is_primary = dt_mongo.is_primary()
                        if is_primary == 'yes':
                            os.system('python manage_strategy.py -t {} -s {} -n {} &'.format(
                                      run_type, sms_send, strategy_instance_id))
                    else:
                        os.system('python manage_strategy.py -t {} -s {} -n {} &'.format(
                                  run_type, sms_send, strategy_instance_id))
                elif (status == 'stop'):
                    pass
            first = 0
        if (first == 1):
            time.sleep(37)
        else:
            time.sleep(15)


def main():
    run_type = ''
    sms_send = ''
    strategy_instance_id = ''
    multi = 'no'
    parser = optparse.OptionParser()
    parser.add_option("-t", "--type", dest="run_type", help="test/real")
    parser.add_option("-s", "--sms", dest="sms_send", type='string', help="yes/no")
    parser.add_option("-m", "--multi", dest="multi", type='string', help="yes/no")
    parser.add_option("-n", "--new", dest="new_si", type='string', help="strategy instance id")
    (options, args) = parser.parse_args()
    if options.run_type != None:
        param = options.run_type
        if (param == 'real'):
            run_type = 'real'
        elif (param == 'test'):
            run_type = 'test'
        else:
            print('unknown run_type, real/test')
    if options.sms_send != None:
        param = options.sms_send
        if (param == 'yes'):
            sms_send = 'yes'
        elif (param == 'no'):
            sms_send = 'no'
        else:
            print('unknown sms_send, yes/no')
    if options.multi != None:
        param = options.multi
        if (param == 'yes'):
            multi = 'yes'
        elif (param == 'no'):
            multi = 'no'
        else:
            print('unknown multi, yes/no')
    if options.new_si != None:
        param = options.new_si
        if (len(param) == 24):
            strategy_instance_id = param
        else:
            print('wrong strategy_instance id')
    if ((run_type in ['test', 'real']) and (sms_send in ['yes', 'no']) and (options.new_si == None)):
        try:
            manage_strategy_instance(run_type, sms_send, multi)
        except (KeyboardInterrupt):
            filename = os.path.basename(__file__)
            print('')
            print('[*] strategy_instances still running')
            print('[*] to stop strategy_instances, just kill pid')
            print(os.system('ps -ax|grep "{} -t"'.format(filename)))

    elif (len(strategy_instance_id) == 24):
        start_one_strategy_instance(run_type, sms_send, strategy_instance_id)
    else:
        filename = os.path.basename(__file__)
        print('need set param, such as:')
        print('python {} -t real -s yes'.format(filename))
        print('python {} -t real -s yes -m yes'.format(filename))
        print('python {} -t test -s no'.format(filename))


if __name__ == '__main__':
    main()
