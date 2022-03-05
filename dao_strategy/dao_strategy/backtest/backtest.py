import copy
import time
import json
import base64
import pathlib
import datetime
import traceback
import importlib
import numpy as np

from dao_strategy.utils import log
from dao_strategy.utils import convert
from dao_strategy.utils import drawing
from dao_strategy.utils import permutation_test
from dao_strategy.utils import global_var as g
from dao_strategy.settings.config import cfg
from dao_strategy.rpc.dao_quote import DaoQuote
from dao_strategy.db.redis import RedisClient
from dao_strategy.db.ds_models import (StrategyFile, StrategyJob, StrategyTask)


def get_quote(exchange, symbol, begin_timestamp, end_timestamp, strategy_type, strategy_job_id, cache=True):
    redis = get_redis_quote()
    key_name_ok = 'quote_{}.ok'.format(strategy_job_id)
    key_name = 'quote_{}'.format(strategy_job_id)
    quote_local = False
    if (not redis.exists(key_name_ok)) or (cache is False):
        if cache:
            redis.set_value(key_name_ok, 'ing')
        bars = []
        if exchange == 'stock':
            period = '1d'
        else:
            period = '1min'
        dao_quote = DaoQuote()
        if (strategy_type == 'arbitrage_strategy'):
            exchange_a = exchange
            symbol_a = symbol
            status, bars_a = dao_quote.get_backtest_kline_db(exchange_a, symbol_a,
                             period, begin_timestamp, end_timestamp)
            exchange_b = exchange.split('f')[0]
            symbol_b = symbol.split('-')[0] + 't'
            status, bars_b = dao_quote.get_backtest_kline_db(exchange_b, symbol_b,
                             period, begin_timestamp, end_timestamp)
            if (len(bars_a) != len(bars_b)):
                raise ValueError('length not equal')
            else:
                pass
            bars = convert.spread_lines(bars_a, bars_b)
        else:
            status, bars = dao_quote.get_backtest_kline_db(exchange, symbol,
                           period, begin_timestamp, end_timestamp)
        quote_local = True
        if cache:
            redis.set_value(key_name, json.dumps(bars))
            redis.set_value(key_name_ok, 'done')
    else:
        while True:
            if redis.get_value(key_name_ok) == 'done':
                if quote_local:
                    break
                else:
                    bars = redis.get_value(key_name)
                    bars = json.loads(bars)
                    break
            else:
                time.sleep(1)
    return bars


def backtest_main(strategy_task_dict):
    if (strategy_task_dict['log_record'] == 'yes'):
        strategy_task_dict['log_record'] = True
    else:
        strategy_task_dict['log_record'] = False
    strategy_type = strategy_task_dict['strategy_type']

    exchange = strategy_task_dict['exchange']
    symbol = strategy_task_dict['symbol']
    begin_time = strategy_task_dict['begin_time']
    period = strategy_task_dict['period']
    begin_timestamp = convert.to_timestamp(begin_time)
    begin_timestamp = str(int(begin_timestamp) - 60*(period + 1))
    end_time = strategy_task_dict['end_time']
    end_timestamp = convert.to_timestamp(end_time)
    strategy_task_dict['begin_timestamp'] = begin_timestamp
    strategy_task_dict['end_timestamp'] = end_timestamp
    strategy_job_id = strategy_task_dict['strategy_job_id']

    sj = StrategyJob.objects.get(id=strategy_job_id)
    if ',' in sj.symbol or ',' in sj.exchange:
        cache = False
    else:
        cache = True
    bars = get_quote(exchange, symbol, begin_timestamp, end_timestamp, strategy_type, strategy_job_id, cache)

    class_name = 'CtaStrategy'

    file_path = strategy_task_dict['file_path']
    filename = strategy_task_dict['filename']

    backtest_strategy = (file_path + filename[:-3]).replace('/', '.')
    file_module = importlib.import_module(backtest_strategy)
    StrategyInstanceClass = getattr(file_module, class_name)

    setting_dict = strategy_task_dict
    strategy_instance = StrategyInstanceClass(setting_dict)
    strategy_instance.backtest(bars)
    order_records = g.g_trade_records
    n_order_records = strategy_instance.g_order_records

    return order_records, n_order_records


def backtest_d():
    print('[*] backtest_d progress running...')
    key_name = 'strategy_task'
    file_path = 'dao_strategy/backtest/strategy_files/'
    redis = get_redis()
    while True:
        params = redis.brpop(key_name)
        params = params[1].decode('utf-8')
        params = json.loads(params)
        strategy_job_id = params['strategy_job_id']
        strategy_task_id = params['strategy_task_id']

        strategy_type = params['strategy_type']
        direction = params['direction']

        order_records = []
        n_order_records = []
        cost_function_dict = {}
        balance_dict_list = [{'balance_num': 0.0}]
        trade_records = []
        try:
            print('[*] {}, processing: {}'.format(datetime.datetime.now(), strategy_task_id))
            st = StrategyTask.objects.get(id=strategy_task_id)
            filename = 'file_{}.py'.format(strategy_job_id)
            if not pathlib.Path(file_path + filename).exists():
                sj = StrategyJob.objects.get(id=strategy_job_id)
                file_content = base64.b64decode(sj.file_content)
                file_content = file_content.decode('utf8')
                with open(file_path + filename, 'w') as f:
                    f.write(file_content)
            st.file_path = file_path
            st.filename = filename
            st.save()
            strategy_task_dict = st.to_dict()
            strategy_task_dict['strategy_instance_id'] = strategy_task_dict['id']
            strategy_task_dict['account_type'] = 'reg_backtest'
            strategy_task_dict['status_dict'] = {}
            order_records, n_order_records = backtest_main(strategy_task_dict)

            if (len(order_records) != 0):
                if (strategy_type == 'arbitrage_strategy'):
                    cost_function_dict, balance_dict_list, trade_records = log.generate_arbitrage_trade_log(order_records)
                else:
                    if (direction == 'long'):
                        cost_function_dict, balance_dict_list, trade_records = log.generate_trade_log(order_records)
                    elif (direction == 'short'):
                        cost_function_dict, balance_dict_list, trade_records = log.generate_short_trade_log(order_records)
                # generate indicator permutation_test pdf
                if st.indicator_config != {}:
                    in_dict = permutation_test.p_test_indicator(trade_records)
                    file_name = 'in_test_{}.pdf'.format(str(strategy_task_id))
                    filename = file_path + file_name
                    drawing.save_all_in_test_pdf(filename, in_dict)

            exception = 0
            exception_msg = 'None'
            status = 'done'
        except Exception as e:
            exception = 1
            exception_msg = traceback.format_exc()
            status = 'error'
            print('exception: {}'.format(exception))
            print('[*] backtest_d, {}'.format(traceback.format_exc()))
        st = StrategyTask.objects.get(id=strategy_task_id)
        st.exception = exception
        st.exception_msg = exception_msg

        if len(balance_dict_list) > 0:
            st.balance = balance_dict_list[-1]['balance_num']
        if cost_function_dict != {}:
            st.case_1 = cost_function_dict['case_1']
            st.case_2 = cost_function_dict['case_2']
            st.init_fund = cost_function_dict['init_fund']
            st.total_earn = cost_function_dict['total_earn']
            st.fee_sum = cost_function_dict['fee_sum']
            st.pure_earn = cost_function_dict['pure_earn']
            st.earn_num = cost_function_dict['earn_num']
            st.loss_num = cost_function_dict['loss_num']
            st.win_ratio = cost_function_dict['win_ratio']
            st.avg_earn = cost_function_dict['avg_earn']
            st.avg_loss = cost_function_dict['avg_loss']
            st.earn_loss_ratio = cost_function_dict['earn_loss_ratio']
            st.earn_max = cost_function_dict['earn_max']
            st.loss_max = cost_function_dict['loss_max']
            st.max_back_ratio = cost_function_dict['max_back_ratio']
            st.avg_hodl_time = cost_function_dict['avg_hodl_time']
            st.avg_earn_hodl_time = cost_function_dict['avg_earn_hodl_time']
            st.avg_loss_hodl_time = cost_function_dict['avg_loss_hodl_time']
            st.trade_records = trade_records
        st.order_records = order_records
        st.n_order_records = n_order_records
        st.balance_range = balance_dict_list
        st.status = status
        st.save()


def get_symbol_exchange_dict(exchange_list):
    symbol_exchange_dict = {}
    for exchange in exchange_list:
        key = '{}_symbols'.format(exchange)
        for symbol_dict in cfg[key]:
            symbol = symbol_dict['symbol_id']
            if symbol not in symbol_exchange_dict:
                symbol_exchange_dict[symbol] = exchange
    return symbol_exchange_dict


def get_exchange_symbol_dict(exchange, symbol):
    exchange_symbol_dict = {}

    if (',' not in exchange) and (',' not in symbol):
        exchange_symbol_dict[exchange] = [symbol]
    else:
        exchange_list = exchange.split(',')
        symbol_list = symbol.split(',')
        symbol_exchange_dict = get_symbol_exchange_dict(exchange_list)
        for symbol in symbol_list:
            exchange = symbol_exchange_dict[symbol]
            if exchange in exchange_symbol_dict:
                exchange_symbol_dict[exchange].append(symbol)
            else:
                exchange_symbol_dict[exchange] = [symbol]
    return exchange_symbol_dict


def send_task():
    while True:
        try:
            sjs = StrategyJob.objects.filter(status='new').exclude('file_content').limit(30)
            for sj in sjs:
                try:
                    exchange_symbol_dict = get_exchange_symbol_dict(sj.exchange, sj.symbol)

                    for exchange in exchange_symbol_dict.keys():
                        for symbol in exchange_symbol_dict[exchange]:
                            param_1_start = float(sj.param_1_start)
                            if (sj.param_1_end == ""):
                                param_1_step = 1
                                param_1_end = param_1_start + param_1_step
                            else:
                                param_1_step = float(sj.param_1_step)
                                param_1_end = float(sj.param_1_end) + param_1_step
                            param_2_start = float(sj.param_2_start)
                            if (sj.param_2_end == ""):
                                param_2_step = 1
                                param_2_end = param_2_start + param_2_step
                            else:
                                param_2_step = float(sj.param_2_step)
                                param_2_end = float(sj.param_2_end) + param_2_step
                            for param_1 in np.arange(param_1_start, param_1_end, param_1_step):
                                for param_2 in np.arange(param_2_start, param_2_end, param_2_step):
                                    st = StrategyTask()
                                    st.strategy_name = sj.strategy_name
                                    st.strategy_job_id = sj.id
                                    st.user_name = sj.user_name
                                    st.user_id = sj.user_id
                                    st.begin_time = sj.begin_time
                                    st.end_time = sj.end_time
                                    st.period = sj.period
                                    st.period_list = sj.period_list
                                    st.exchange = exchange
                                    st.symbol = symbol
                                    st.exchange_2 = sj.exchange_2
                                    st.symbol_2 = sj.symbol_2
                                    st.one_time_buy = sj.one_time_buy
                                    st.direction = sj.direction
                                    st.log_record = sj.log_record
                                    st.strategy_type = sj.strategy_type
                                    st.balance_end = sj.balance_end
                                    st.balance_front = sj.balance_front
                                    st.taker_fee_ratio = sj.taker_fee_ratio
                                    st.maker_fee_ratio = sj.maker_fee_ratio
                                    st.param_1 = param_1
                                    st.param_2 = param_2
                                    st.indicator_config = sj.indicator_config
                                    st.status = 'new'
                                    st.save()
                            sj.status = 'wait'
                            sj.save()
                except Exception as e:
                    print('[*] sj loop, err: {}'.format(traceback.format_exc()))
        except Exception as e:
            print('[*] {}, err: {}'.format('send_task', traceback.format_exc()))
        time.sleep(1)


def push_task():
    key_name = 'strategy_task'
    while True:
        try:
            redis = get_redis()
            sts = StrategyTask.objects.filter(status='new').limit(10)
            for st in sts:
                params = json.dumps(st.to_dict())
                redis.lpush(key_name, params)
                st.status = 'wait'
                st.save()
        except Exception as e:
            print('[*] {}, err: {}'.format('send_task', traceback.format_exc()))
        time.sleep(1)


def get_redis_quote():
    redis_cfg = cfg['redis']['dao_strategy']
    return RedisClient(redis_cfg)


def get_redis():
    redis_cfg = cfg['redis']['dao_strategy']
    redis = RedisClient(redis_cfg).redis
    return redis


def monitor():
    file_path = 'dao_strategy/backtest/strategy_files/'
    while True:
        try:
            sjs = StrategyJob.objects.filter(status__ne='done').exclude('file_content').limit(30)
            for sj in sjs:
                try:
                    print('[*] processing {} {} {}'.format(str(sj.id), sj.exchange, sj.symbol))
                    break_sj = False
                    strategy_tasks = StrategyTask.objects.filter(strategy_job_id=sj.id).exclude('indicator_config', 'order_records', 'trade_records', 'balance_range')
                    for st in strategy_tasks:
                        if st.status in ['wait', 'ing']:
                            sj.status = 'ing'
                            sj.save()
                            break_sj = True
                            break
                    if not break_sj:
                        st_count = StrategyTask.objects.filter(strategy_job_id=sj.id).count()
                        if st_count == 0:
                            continue
                        sj.status = 'done'
                        sj.save()
                        file_name = 'params_fig_{}.pdf'.format(str(sj.id))
                        filename = file_path + file_name
                        strategy_tasks = StrategyTask.objects.filter(strategy_job_id=sj.id).exclude('indicator_config', 'order_records', 'balance_range')
                        drawing.save_params_fig(filename, strategy_tasks)
                except Exception as e:
                    print('[*] sj loop, err: {}'.format(traceback.format_exc()))
        except Exception as e:
            print('[*] {}, err: {}'.format('monitor', traceback.format_exc()))
        time.sleep(1)
