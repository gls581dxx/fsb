import os
import ast
import sys
import copy
import json
import time
import hmac
import base64
import hashlib
import requests
import traceback
import importlib
import numpy as np
from bson.objectid import ObjectId

from dao_strategy.utils import convert
from dao_strategy.db.dt_models import User
from dao_strategy.db.ds_models import (StrategyFile, StrategyJob, StrategyTask)
from dao_strategy.rpc.dao_quote import DaoQuote


# from strategy_research.util import db_mongo
# from strategy_research.util.redis_cache import redis_cache

# from strategy_research.indicator import matlab_test
# from strategy_research.indicator import indicator_backtest
# from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)


def backtest_task_rst(task_config_id, task_type, exception, exception_msg):
    exception = int(exception)
    print('backtest_task_rst')
    if (exception == 1):
        if (task_type == 'strategy_task'):
            strategy_config_id = ObjectId(task_config_id)
            strategy_config = StrategyConfig.objects.get(id=strategy_config_id)
            strategy_config.exception = exception
            strategy_config.exception_msg = exception_msg
            strategy_config.status = 'running'
            strategy_config.save()
        elif (task_type == 'indicator_task'):
            indicator_config_id = ObjectId(task_config_id)
            indicator_config = IndicatorConfig.objects.get(id=indicator_config_id)
            indicator_config.exception = exception
            indicator_config.exception_msg = exception_msg
            indicator_config.status = 'running'
            indicator_config.save()
    else:
        key_name = 'backtestd'
        value = {}
        value['event_type'] = 'backtest_task_rst'
        value['task_config_id'] = task_config_id
        value['task_type'] = task_type
        value['exception'] = exception
        value['exception_msg'] = exception_msg
        value = json.dumps(value)
        redis_cache.lpush_redis(key_name, value)
    status = 1
    data = 'ok'
    return status, data


def backtest_task_rst_part(task_config_id, task_type, param_dict, statistic_dict, order_records, exception, exception_msg, n_order_records=[]):
    exception = int(exception)
    print('backtest_task_rst_part')
    if (exception == 1):
        strategy_config_id = ObjectId(task_config_id)
        if (task_type == 'strategy_task_rst'):
            strategy_config = StrategyConfig.objects.get(id=strategy_config_id)
            cost_function_dict = {}
            balance_dict_list = [{'balance_num': 0.0}]
            trade_records = []

            strategy_instance_dict = ast.literal_eval(strategy_config.to_json())
            strategy_instance_dict['strategy_instance_id'] = strategy_instance_dict['_id']['$oid']
            strategy_instance_dict['strategy_file_id'] = strategy_instance_dict['strategy_file_id']['$oid']
            del strategy_instance_dict['_id']
            del strategy_instance_dict['strategy_datetime']
            strategy_instance_dict['user_id'] = strategy_instance_dict['user_id']['$oid']
            param_dict = json.loads(param_dict)
            strategy_instance_dict.update(param_dict)

            collection_dict = copy.deepcopy(strategy_instance_dict)
            collection_dict['strategy_instance_id'] = strategy_config_id
            collection_dict['balance'] = balance_dict_list[-1]['balance_num']
            collection_dict.update(cost_function_dict)
            collection_dict['order_records'] = order_records
            collection_dict['n_order_records'] = n_order_records
            collection_dict['trade_records'] = trade_records
            collection_dict['balance_range'] = balance_dict_list
            collection_dict['exception'] = exception
            collection_dict['exception_msg'] = exception_msg

            collection_name = 'backtest_records'
            db_mongo.save_mongo(collection_name, collection_dict)
        elif (task_type == 'indicator_task_rst'):
            indicator_config = IndicatorConfig.objects.get(id=strategy_config_id)
            cost_function_dict = {}
            balance_dict_list = [{'balance_num': 0.0}]
            trade_records = []

            indicator_config_dict = ast.literal_eval(indicator_config.to_json())
            indicator_config_dict['indicator_config_id'] = indicator_config_dict['_id']['$oid']
            indicator_config_dict['indicator_file_id'] = indicator_config_dict['indicator_file_id']['$oid']
            del indicator_config_dict['_id']
            del indicator_config_dict['indicator_datetime']
            indicator_config_dict['user_id'] = indicator_config_dict['user_id']['$oid']
            param_dict = json.loads(param_dict)
            indicator_config_dict.update(param_dict)

            backtest_record_dict = copy.deepcopy(indicator_config_dict)
            backtest_record_dict['balance'] = balance_dict_list[-1]['balance_num']
            statistic_dict = json.loads(statistic_dict)
            backtest_record_dict.update(statistic_dict)
            backtest_record_dict.update(cost_function_dict)
            backtest_record_dict['order_records'] = order_records
            backtest_record_dict['n_order_records'] = n_order_records
            backtest_record_dict['trade_records'] = trade_records
            backtest_record_dict['balance_range'] = balance_dict_list
            backtest_record_dict['exception'] = exception
            backtest_record_dict['exception_msg'] = exception_msg
            indicator_backtest.save_indicator_backtest_record(backtest_record_dict)
    else:
        key_name = 'backtestd'
        value = {}
        value['event_type'] = 'backtest_task_rst_part'
        value['task_config_id'] = task_config_id
        value['task_type'] = task_type
        value['param_dict'] = param_dict
        value['statistic_dict'] = statistic_dict
        value['order_records'] = order_records
        value['n_order_records'] = n_order_records
        value['exception'] = exception
        value['exception_msg'] = exception_msg
        value = json.dumps(value)
        redis_cache.lpush_redis(key_name, value)
    status = 1
    data = 'ok'
    return status, data


def get_strategy_config_exception(user_name, strategy_config_id):
    strategy_config_id = ObjectId(strategy_config_id)
    strategy_config = StrategyConfig.objects.get(user_name=user_name,
                      id=strategy_config_id)
    data = {}
    data['exception'] = strategy_config.exception
    data['exception_msg'] = strategy_config.exception_msg
    return data


def delete_strategy_config(user_name, strategy_config_id):
    strategy_config_id = ObjectId(strategy_config_id)
    rst = StrategyConfig.objects(user_name=user_name,
          id=strategy_config_id).delete()
    if (rst == 1):
        data = '配置删除成功！'
    else:
        data = '删除失败, {}'.format(rst)
    return data


def get_backtest_records(user_name, strategy_instance_id, page_num, page_limit):
    strategy_instance_id = ObjectId(strategy_instance_id)
    collection_name = 'backtest_records'
    backtest_records_col = db_mongo.get_collection(collection_name)
    page_num = int(page_num)
    page_limit = int(page_limit)
    skip = (page_num - 1) * page_limit
    rst = backtest_records_col.find({'strategy_instance_id':
          strategy_instance_id, 'user_name': user_name},
          ['_id', 'param_1', 'param_2', 'pure_earn',
          'max_back_ratio', 'earn_loss_ratio', 'win_ratio',
          'earn_num', 'loss_num', 'total_earn', 'exception',
          'exception_msg']).sort([('param_1', 1), ('param_2', 1)]).skip(skip).limit(page_limit)
    backtest_records = rst
    total_nums = backtest_records_col.find({'strategy_instance_id':
          strategy_instance_id, 'user_name': user_name}).count()
    total_pages = total_nums / page_limit
    if (total_pages % 1 > 0):
        total_pages = int(total_pages) + 1
    total_pages = int(total_pages)
    page_num_list = list(range(1, total_pages+1))
    if (total_pages > 5):
        if (page_num-2 < 1):
            page_num_list = list(range(1, 6))
        elif (page_num+2 > total_pages):
            page_num_list = list(range(page_num-4, page_num+1))
        else:
            page_num_list = list(range(page_num-2, page_num+3))
    data = {}
    data['page_num'] = page_num
    data['page_num_list'] = page_num_list
    record_dict_list = []
    for record_dict in backtest_records:
        record_dict['backtest_id'] = str(record_dict['_id'])
        record_dict['sharpe'] = '***'
        record_dict['profit_factor'] = '***'
        del record_dict['_id']
        if ('pure_earn' not in record_dict):
            record_dict['pure_earn'] = '没有'
            record_dict['sharpe'] = '交易'
        record_dict_list.append(record_dict)
    data['record_list'] = record_dict_list
    return data


def get_order_records(user_name, backtest_id):
    backtest_id = ObjectId(backtest_id)
    collection_name = 'backtest_records'
    backtest_records_col = db_mongo.get_collection(collection_name)
    rst = backtest_records_col.find(
          {'_id': backtest_id, 'user_name': user_name},
          ['n_order_records', 'exchange', 'symbol', 'param_1', 'param_2']
          ).sort([('param_1', 1), ('param_2', 1)])
    order_records = []
    for i in rst:
        if ('n_order_records' in i):
            exchange = i['exchange']
            symbol = i['symbol']
            param_1 = i['param_1']
            param_2 = i['param_2']
            order_records = i['n_order_records']
    rst = {}
    rst['order_records'] = order_records
    rst['exchange'] = exchange
    rst['symbol'] = symbol
    rst['param_1'] = param_1
    rst['param_2'] = param_2
    return rst


def get_trade_records(user_name, backtest_id):
    backtest_id = ObjectId(backtest_id)
    collection_name = 'backtest_records'
    backtest_records_col = db_mongo.get_collection(collection_name)
    rst = backtest_records_col.find(
          {'_id': backtest_id, 'user_name': user_name},
          ['trade_records', 'exchange', 'symbol', 'param_1', 'param_2']
          ).sort([('param_1', 1), ('param_2', 1)])
    trade_records = []
    for i in rst:
        if ('trade_records' in i):
            trade_records_old = i['trade_records']
            for trade_record in trade_records_old:
                del trade_record[10]
                trade_records.append(trade_record)
            exchange = i['exchange']
            symbol = i['symbol']
            param_1 = i['param_1']
            param_2 = i['param_2']
    rst = {}
    rst['trade_records'] = trade_records
    rst['exchange'] = exchange
    rst['symbol'] = symbol
    rst['param_1'] = param_1
    rst['param_2'] = param_2
    return rst


def get_trade_records_exception(user_name, backtest_id):
    backtest_id = ObjectId(backtest_id)
    collection_name = 'backtest_records'
    backtest_records_col = db_mongo.get_collection(collection_name)
    rst = backtest_records_col.find(
          {'_id': backtest_id, 'user_name': user_name},
          ['exception', 'exception_msg'])
    rst = rst[0]
    data = {}
    data['exception'] = rst['exception']
    data['exception_msg'] = rst['exception_msg']
    return data


def delete_backtest_record(user_name, backtest_id):
    backtest_id = ObjectId(backtest_id)
    collection_name = 'backtest_records'
    backtest_records_col = db_mongo.get_collection(collection_name)
    rst = backtest_records_col.remove({'_id': backtest_id, 'user_name': user_name})
    if (rst['n'] == 1):
        data = '删除成功！'
    else:
        data = '删除失败: {}'.format(str(rst))
    return data


def get_trade_pnl(user_name, backtest_id):
    backtest_id = ObjectId(backtest_id)
    collection_name = 'backtest_records'
    backtest_records = db_mongo.get_collection(collection_name)
    rst = backtest_records.find({'_id': backtest_id})
    one_rst = rst[0]
    if ('earn_num' in one_rst):
        trade_records = one_rst['trade_records']
        param_1 = one_rst['param_1']
        param_2 = one_rst['param_2']
        trade_num = one_rst['earn_num'] +\
                    one_rst['loss_num']
        win_ratio = one_rst['win_ratio']
        earn_loss_ratio = one_rst.get('earn_loss_ratio', 0)
        balance = round(one_rst['balance'], 3)
        timestamp_list = []
        price_list = []
        balance_list = []
        for trade_record in trade_records:
            date = trade_record[3]
            timestamp = convert.to_timestamp(date)
            timestamp_list.append(timestamp)
            price_list.append(trade_record[4])
            balance_list.append(trade_record[8])
        title = ('p1: {}, p2: {}, balance: {}, nums: {}, '
                'wr: {}, elr: {}').format(param_1, param_2, balance,
                trade_num, win_ratio, earn_loss_ratio)
    else:
        title = '回测期间没有交易'
        timestamp_list = []
        price_list = []
        balance_list = []
    rst = {}
    rst['title'] = title
    rst['timestamp_list'] = timestamp_list
    rst['price_list'] = price_list
    rst['balance_list'] = balance_list
    return rst


def get_trade_chart(user_name, backtest_id):
    backtest_id = ObjectId(backtest_id)
    collection_name = 'backtest_records'
    backtest_records = db_mongo.get_collection(collection_name)
    rst = backtest_records.find({'_id': backtest_id})
    one_rst = rst[0]

    title = '回测期间没有交易'
    bars = []
    entry_list = []
    exit_list = []

    if ('earn_num' in one_rst):
        trade_records = one_rst['trade_records']
        param_1 = one_rst['param_1']
        param_2 = one_rst['param_2']
        trade_num = one_rst['earn_num'] +\
                    one_rst['loss_num']
        win_ratio = one_rst['win_ratio']
        earn_loss_ratio = one_rst.get('earn_loss_ratio', 0)
        balance = round(one_rst['balance'], 3)
        exchange = one_rst['exchange']
        symbol = one_rst['symbol']
        if exchange == 'stock':
            period = '1d'
        else:
            period = '1min'
        begin_time = one_rst['begin_time']
        end_time = one_rst['end_time']
        begin_time = begin_time.split(' ')[0] + ' 00:00:00'
        begin_timestamp = int(convert.to_timestamp(begin_time))
        end_timestamp = int(convert.to_timestamp(end_time))
        strategy_type = one_rst['strategy_type']
        dao_quote = DaoQuote()
        if (strategy_type == 'arbitrage_strategy'):
            exchange_a = exchange
            symbol_a = symbol
            status, bars_a = dao_quote.get_backtest_kline_db(exchange_a,
                             symbol_a, period, begin_timestamp, end_timestamp)
            exchange_b = exchange.split('f')[0]
            symbol_b = symbol.split('-')[0] + 't'
            status, bars_b = dao_quote.get_backtest_kline_db(exchange_b,
                             symbol_b, period, begin_timestamp, end_timestamp)
            if (len(bars_a) != len(bars_b)):
                status = 0
                data = 'length not equal'
                return status, data
            bars = convert.spread_lines(bars_a, bars_b)
        else:
            status, bars = dao_quote.get_backtest_kline_db(exchange, symbol,
                           period, begin_timestamp, end_timestamp)
        period = one_rst.get('period', 1)
        if (period == 1):
            pass
        else:
            # period = '{}min'.format(period)
            bars = convert.combine_lines_3(bars, period)
        for trade_record in trade_records:
            entry_time = trade_record[0]
            entry_timestamp = convert.to_timestamp(entry_time)
            entry_price = trade_record[1]

            exit_time = trade_record[3]
            exit_timestamp = convert.to_timestamp(exit_time)
            exit_price = trade_record[4]

            entry_list.append([int(entry_timestamp)*1000, entry_price])
            exit_list.append([int(exit_timestamp)*1000, exit_price])

        title = ('p1: {}, p2: {}, balance: {}, nums: {}, '
                'wr: {}, elr: {}').format(param_1, param_2, balance,
                trade_num, win_ratio, earn_loss_ratio)
    else:
        pass

    status = 1
    data = {}
    data['title'] = title
    data['bars'] = bars
    data['entry_list'] = entry_list
    data['exit_list'] = exit_list
    return status, data


def download_backtest_strategy_rst(user_name, strategy_instance_id):
    strategy_instance_id = ObjectId(strategy_instance_id)
    strategy_config_id = strategy_instance_id
    strategy_config = StrategyConfig.objects.get(id=strategy_config_id)
    file_path = strategy_config.backtest_strategy_rst_file_path
    file_name = strategy_config.backtest_strategy_rst_file_name
    return file_path, file_name


def download_indicator_strategy_rst(user_name, backtest_id):
    collection_name = 'backtest_records'
    backtest_records = db_mongo.get_collection(collection_name)
    backtest_id = ObjectId(backtest_id)
    rst = backtest_records.find({'_id': backtest_id},
                                ['indicator_strategy_rst_file_path',
                                'indicator_strategy_rst_file_name'])
    file_path = rst[0]['indicator_strategy_rst_file_path']
    file_name = rst[0]['indicator_strategy_rst_file_name']
    return file_path, file_name


def download_monte_carlo_strategy_rst(user_name, backtest_id):
    collection_name = 'backtest_records'
    backtest_records = db_mongo.get_collection(collection_name)
    backtest_id = ObjectId(backtest_id)
    rst = backtest_records.find({'_id': backtest_id},
                                ['indicator_test_rst_file_path',
                                'indicator_test_rst_file_name'])

    file_path = rst[0]['indicator_test_rst_file_path']
    file_name = rst[0]['indicator_test_rst_file_name']
    return file_path, file_name


def gen_monte_carlo_strategy_rst(user_name, backtest_id):
    key_name = 'backtestd'
    collection_name = 'backtest_records'
    backtest_records = db_mongo.get_collection(collection_name)
    rst = backtest_records.find({'_id': ObjectId(backtest_id)})
    i = rst[0]
    file_path = 'strategy_research/strategy/strategy_files/'
    file_name = 'in_test_{}.pdf'.format(str(backtest_id))
    i['indicator_test_rst_file_path'] = file_path
    i['indicator_test_rst_file_name'] = file_name
    result = backtest_records.save(i)
    value = {}
    value['event_type'] = 'in_test_pdf'
    value['backtest_id'] = backtest_id
    value = json.dumps(value)
    redis_cache.lpush_redis(key_name, value)
    data = 'ok'
    return data
