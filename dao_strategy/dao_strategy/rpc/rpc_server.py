import os
import ast
import sys
import json
import time
import math
import uuid
import hmac
import base64
import psutil
import hashlib
import datetime
import thriftpy2
import traceback
from bson.objectid import ObjectId
from thriftpy2.rpc import make_server

from dao_strategy.utils import convert
from dao_strategy.settings.config import cfg
from dao_strategy.utils.account import Account
from dao_strategy.rpc.dao_quote import DaoQuote
from dao_strategy.rpc.dao_execute import DaoExecute
from dao_strategy.db.dt_models import (User, Order, StrategyClass, StrategyInstance)
from dao_strategy.db.ds_models import (StrategyFile, StrategyJob, StrategyTask)
from dao_strategy.backtest import strategy_backtest

class Dispatcher(object):

    def __init__(self):
        self.account = Account()
        self.api_key_dict = cfg['rpc_token']
        if self.api_key_dict == {}:
            print('[*] api_key_dict is null !')
            sys.exit(0)

    def check_sig(self, *args):
        req_sig = args[0]
        if req_sig == '':
            return False
        api_key, req_sig = req_sig.split('.')
        secret_key = self.api_key_dict[api_key]
        content = ','.join(args[1:])

        sig = hmac.new(secret_key.encode("utf8"),
                       msg=content.encode("utf8"),
                       digestmod=hashlib.sha256).hexdigest()
        if req_sig == sig:
            return True
        else:
            return False

    def ret_resp(self, status, data):
        resp = {}
        resp['status'] = status
        resp['data'] = data
        return json.dumps(resp)

    def get_page_rst(self, total_count, page_num, page_limit):
        total_page_num = total_count / page_limit
        total_page_num = math.ceil(total_page_num)
        page_num_list = list(range(1, total_page_num+1))
        if (total_page_num > 5):
            if (page_num <= 3):
                page_num_list_ = list(range(1, 6))
            else:
                page_num_list_ = page_num_list[page_num-3:page_num+2]
                if len(page_num_list_) < 5:
                    page_num_list_ = page_num_list[-5:]
            page_num_list = page_num_list_
        return page_num_list

    def get_strategies(self, sig, strategy_type, page_num, page_limit):
        if not self.check_sig(sig, 'get_strategies', strategy_type, page_num,
                              page_limit):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        page_limit = int(page_limit)
        page_num = int(page_num)
        offset = (page_num - 1) * page_limit
        total_count = StrategyClass.objects.filter(
                      strategy_type=strategy_type).count()
        scs = StrategyClass.objects.filter(strategy_type=strategy_type
              ).skip(offset).limit(page_limit).order_by('strategy_timestamp')
        strategy_dict_list = [sc.to_dict() for sc in scs]
        page_num_list = self.get_page_rst(total_count, page_num, page_limit)

        data = {}
        data['page_num'] = page_num
        data['page_num_list'] = page_num_list
        data['strategy_dict_list'] = strategy_dict_list
        return self.ret_resp(1, data)

    def run_strategy(self, sig, user_id, strategy_instance_id, exchange, account_type, strategy_type, strategy_name, symbol, one_time_buy, sms_send):
        if not self.check_sig(sig, 'run_strategy', user_id,
                              strategy_instance_id, exchange, account_type,
                              strategy_type, strategy_name, symbol,
                              one_time_buy, sms_send):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        status = 1
        data = ''
        exchange = exchange.lower()
        user = User.objects.get(id=user_id)
        if (strategy_instance_id == '--'):
            strategy_instance = StrategyInstance()
            strategy_instance.user_name = user.user_name
            strategy_instance.user_id = user.id
            strategy_instance.phone_num = user.phone_num
            strategy_instance.exchange = exchange
            strategy_instance.account_type = account_type
            strategy_instance.strategy_name = strategy_name
            strategy_instance.strategy_type = strategy_type
            strategy_instance.symbol = symbol
            strategy_instance.one_time_buy = float(one_time_buy)
            strategy_instance.sms_send = sms_send
            strategy_instance.status = 'running'
            strategy_instance.save()
            data = '策略添加成功'
        else:
            try:
                strategy_instance = StrategyInstance.objects.get(user_id=user_id, id=strategy_instance_id)
                strategy_instance.exchange = exchange
                strategy_instance.account_type = account_type
                strategy_instance.strategy_name = strategy_name
                strategy_instance.strategy_type = strategy_type
                strategy_instance.symbol = symbol
                strategy_instance.sms_send = sms_send
                strategy_instance.one_time_buy = float(one_time_buy)
                strategy_instance.status = 'running'
                strategy_instance.save()
                pid = strategy_instance.pid
                pid_status = psutil.pid_exists(pid)
                if (pid_status is True):
                    os.system('kill {}'.format(pid))
                data = '策略修改成功'
            except Exception as e:
                status = 0
                data = 'run_strategy err: {}'.format(traceback.format_exc())
        return self.ret_resp(status, data)

    def control_strategy(self, sig, user_id, strategy_instance_id, order):
        if not self.check_sig(sig, 'control_strategy', user_id,
                              strategy_instance_id, order):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        strategy_instance = StrategyInstance.objects.get(
                            user_id=user_id, id=strategy_instance_id)
        status_dict = strategy_instance.status_dict
        edit = 0
        if (order == 'start'):
            status = 'running'
            character = '启动'
        elif (order == 'stop'):
            status = 'stop'
            character = '停止'
        elif (order == 'cover'):
            status = 'stop'
            status_resp, data = self.cover_strategy_instance(strategy_instance)
            character = '平仓, 如果没平, 稍后再试'
        elif ('edit' in order):
            status = 'running'
            character = '编辑'
            status_dict_str = order.split('&')[1:]
            for status_kv in status_dict_str:
                k, v = status_kv.split('=')
                try:
                    status_dict[k] = float(v)
                except Exception as e:
                    status_dict[k] = v
            edit = 1
        strategy_instance.status = status
        strategy_instance.status_dict = status_dict
        strategy_instance.save()
        if (edit == 1):
            pid = strategy_instance.pid
            pid_status = psutil.pid_exists(pid)
            if (pid_status is True):
                os.system('kill {}'.format(pid))

        data = '策略已{}'.format(character)
        return self.ret_resp(1, data)

    def get_strategy_instance(self, sig, user_id, strategy_type, status, page_num, page_limit):
        if not self.check_sig(sig, 'get_strategy_instance', user_id,
                              strategy_type, status, page_num, page_limit):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        page_limit = int(page_limit)
        page_num = int(page_num)
        offset = (page_num - 1) * page_limit
        total_count = StrategyInstance.objects.filter(
                      user_id=user_id, strategy_type=strategy_type,
                      status=status).count()
        sis = StrategyInstance.objects.filter(user_id=user_id,
              strategy_type=strategy_type, status=status
              ).skip(offset).limit(page_limit).order_by('-strategy_timestamp')
        page_num_list = self.get_page_rst(total_count, page_num, page_limit)

        strategy_instance_list = []
        for si in sis:
            strategy_instance = si.to_dict()
            exchange = strategy_instance['exchange']
            account_type = strategy_instance['account_type']
            strategy_name = strategy_instance['strategy_name']
            symbol = strategy_instance['symbol']
            sms_send = strategy_instance.get('sms_send', 'yes')
            strategy_instance['sms_send'] = sms_send
            if (strategy_instance['account_type'] == 'reg_emulator'):
                if (strategy_type == 'fs_arbitrage_strategy'):
                    strategy_instance['position'] = 0
                    strategy_instance['balance'] = 0
                elif (strategy_type == 'ff_arbitrage_strategy'):
                    strategy_instance['position'] = 0
                    strategy_instance['balance'] = 0
                else:
                    status, data = self.account.get_reg_emu_balance(strategy_instance)
                    if (status == 0):
                        continue
                    balance_dict = data
                    coin_dict = balance_dict['coin']
                    basecoin_dict = balance_dict['basecoin']
                    strategy_instance['position'] = coin_dict['balance']
                    dao_quote = DaoQuote()
                    ticker = dao_quote.get_ticker(exchange, symbol)
                    # ticker = {}
                    last_price = float(ticker.get('last', 0))
                    strategy_instance['balance'] = basecoin_dict['balance'] + coin_dict['balance']*last_price
            else:
                if ('arbitrage' in strategy_type):
                    strategy_name = strategy_instance['id']
                    exchange_2 = strategy_instance['exchange_2']
                    symbol = strategy_instance['symbol']
                    symbol_2 = strategy_instance['symbol_2']
                    if ((exchange == 'okexf') and (exchange_2 == 'okexf')):
                        capital_dict_list = self.account.get_future_future_strategy_balance(strategy_instance)
                        position_dict = self.account.get_future_future_strategy_position(strategy_instance)
                        # for capital_dict in capital_dict_list:
                        #     print(capital_dict)
                        balance = capital_dict_list[-1]['capital']
                        strategy_instance['position'] = ('long: {}, short: {}|'
                            'long: {}, short: {}').format(position_dict[symbol]['long'],
                            position_dict[symbol]['short'], position_dict[symbol_2]['long'],
                            position_dict[symbol_2]['short'])
                        strategy_instance['balance'] = round(balance, 7)
                    elif ((exchange == 'okexf') and (exchange_2 == 'okex')):
                        capital_dict_list = self.account.get_future_spot_strategy_balance(strategy_instance)
                        position_dict = self.account.get_future_spot_strategy_position(strategy_instance)
                        # for capital_dict in capital_dict_list:
                        #     print(capital_dict)
                        balance = capital_dict_list[-1]['capital']
                        strategy_instance['position'] = ('long: {}, short: {}|'
                            'long: {}, short: {}').format(position_dict[symbol]['long'],
                            position_dict[symbol]['short'], position_dict[symbol_2]['long'],
                            position_dict[symbol_2]['short'])
                        strategy_instance['balance'] = round(balance, 7)
                    else:
                        strategy_instance['position'] = 0
                        strategy_instance['balance'] = 0
                elif ('future_strategy' == strategy_type):
                    try:
                        capital_dict_list = self.account.get_future_strategy_balance(strategy_instance)
                        position_dict = self.account.get_future_strategy_position(strategy_instance)
                        balance = capital_dict_list[-1]['capital']
                        strategy_instance['position'] = ('long: {}, short: {}').format(
                                                         position_dict[symbol]['long'],
                                                         position_dict[symbol]['short'])
                    except Exception as e:
                        print(traceback.format_exc())
                        balance = 0.0
                        strategy_instance['position'] = 'long: {}, short: {}'.format(0, 0)
                    strategy_instance['balance'] = round(balance, 7)
                elif ('spot_strategy' == strategy_type):
                    capital_dict_list = self.account.get_spot_strategy_balance(strategy_instance)
                    position_dict = self.account.get_spot_strategy_position(strategy_instance)
                    balance = capital_dict_list[-1]['capital']
                    strategy_instance['position'] = ('long: {}, short: {}').format(
                                                     position_dict[symbol]['long'],
                                                     position_dict[symbol]['short'])
                    strategy_instance['balance'] = round(balance, 7)
            # else:
            #     strategy_instance['position'] = 0
            #     strategy_instance['balance'] = 0
            order_status_list = ['filled']
            orders_num = Order.objects.filter(user_id=user_id,
                         strategy_instance_id=strategy_instance['id'],
                         order_status__in=order_status_list).count()
            strategy_instance['orders_num'] = orders_num
            strategy_instance['status_dict'] = strategy_instance.get('status_dict', '{}')

            strategy_instance_list.append(strategy_instance)
        data = {}
        data['page_num'] = page_num
        data['page_num_list'] = page_num_list
        data['strategy_instance_list'] = strategy_instance_list
        return self.ret_resp(1, data)

    def submit_arbitrage_strategy(self, sig, user_id, exchange_a, exchange_b, account_type_a, account_type_b, strategy_type, symbol_a, symbol_b, spread_usdt, max_trade_num, min_trade_num):
        if not self.check_sig(sig, 'submit_arbitrage_strategy', user_id,
                              exchange_a, exchange_b, account_type_a,
                              account_type_b, strategy_type, symbol_a,
                              symbol_b, spread_usdt, max_trade_num,
                              min_trade_num):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        status = 1
        exchange_a = exchange_a.lower()
        exchange_b = exchange_b.lower()
        user = User.objects.get(id=user_id)
        try:
            strategy_instance = StrategyInstance()
            strategy_instance.user_name = str(user.user_name)
            strategy_instance.user_id = user.id
            strategy_instance.phone_num = user.phone_num
            strategy_instance.exchange = exchange_a
            strategy_instance.exchange_2 = exchange_b
            strategy_instance.account_type = account_type_a
            strategy_instance.account_type_2 = account_type_b
            strategy_instance.strategy_type = strategy_type
            strategy_instance.symbol = symbol_a
            strategy_instance.symbol_2 = symbol_b
            strategy_instance.spread_usdt = float(spread_usdt)
            strategy_instance.max_trade_num = float(max_trade_num)
            strategy_instance.min_trade_num = float(min_trade_num)
            strategy_instance.status = 'running'
            # strategy_instance.status_dict = {}
            strategy_instance.save()
            data = '策略添加成功!'
        except Exception as e:
            status = 0
            data = '策略添加失败!'
        return self.ret_resp(status, data)

    def get_strategy_pnl(self, sig, user_id, strategy_instance_id):
        if not self.check_sig(sig, 'get_strategy_pnl', user_id,
                              strategy_instance_id):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        status = 1
        user = User.objects.get(id=user_id)
        try:
            strategy_instance = StrategyInstance.objects.get(
                                user_id=user_id, id=strategy_instance_id)
            strategy_instance = strategy_instance.to_dict()
            strategy_type = strategy_instance['strategy_type']
            capital_dict_list = []
            if ('future_strategy' == strategy_type):
                capital_dict_list = self.account.get_future_strategy_balance(strategy_instance)
            elif ('spot_strategy' == strategy_type):
                capital_dict_list = self.account.get_spot_strategy_balance(strategy_instance)
            elif ('arbitrage' in strategy_type):
                capital_dict_list = self.account.get_future_future_strategy_balance(strategy_instance)
            else:
                capital_dict_list = []
            data = capital_dict_list
        except Exception as e:
            status = 0
            data = '查询PnL失败, {}'.format(traceback.format_exc())
        return self.ret_resp(status, data)

    def submit_conditional_strategy(self, sig, user_id, exchange, account_type, strategy_type, strategy_name, symbol, one_time_buy, sms_send, param):
        if not self.check_sig(sig, 'submit_conditional_strategy', user_id,
                              exchange, account_type, strategy_type,
                              strategy_name, symbol, one_time_buy, sms_send,
                              param):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        status = 1
        exchange = exchange.lower()
        user = User.objects.get(id=user_id)
        try:
            param_dict = {}
            param_dict_str = param.split('&')
            for param_kv in param_dict_str:
                k, v = param_kv.split('=')
                try:
                    param_dict[k] = float(v)
                except Exception as e:
                    param_dict[k] = v
            strategy_instance = StrategyInstance()
            strategy_instance.user_name = str(user.user_name)
            strategy_instance.user_id = user.id
            strategy_instance.phone_num = user.phone_num
            strategy_instance.exchange = exchange
            strategy_instance.account_type = account_type
            strategy_instance.strategy_type = strategy_type
            strategy_instance.strategy_name = strategy_name
            strategy_instance.symbol = symbol
            strategy_instance.one_time_buy = float(one_time_buy)
            strategy_instance.sms_send = sms_send
            strategy_instance.param_dict = param_dict
            strategy_instance.status = 'running'
            strategy_instance.save()
            data = '策略添加成功!'
        except Exception as e:
            status = 0
            data = '策略添加失败!'
        return self.ret_resp(status, data)

    def cover_strategy_instance(strategy_instance):
        strategy_instance = strategy_instance.to_dict()
        strategy_instance_id = strategy_instance['id']
        user_id = strategy_instance['user_id']
        account_type = strategy_instance['account_type']
        exchange = strategy_instance['exchange']
        exchange_2 = strategy_instance['exchange_2']
        symbol = strategy_instance['symbol']
        symbol_2 = strategy_instance['symbol_2']
        strategy_name = strategy_instance['id']
        strategy_type = strategy_instance['strategy_type']
        position_dict = {}
        if (strategy_type == 'fs_arbitrage_strategy'):
            position_dict = {}
        elif (strategy_type == 'ff_arbitrage_strategy'):
            position_dict = self.account.get_future_future_strategy_position(strategy_instance)
        elif (strategy_type == 'future_strategy'):
            strategy_name = strategy_instance['strategy_name']
            position_dict = self.account.get_future_strategy_position(strategy_instance)
        elif (strategy_type == 'spot_strategy'):
            strategy_name = strategy_instance['strategy_name']
            position_dict = self.account.get_spot_strategy_position(strategy_instance)
        else:
            position_dict = {}
        rst = self.cover_position_dict(user_id, account_type, strategy_name,
              strategy_type, exchange, exchange_2, symbol, symbol_2,
              position_dict, strategy_instance_id)
        status = 1
        data = 'ok'
        return status, data

    def cover_position_dict(self, user_id, account_type, strategy_name, strategy_type, exchange, exchange_2, symbol, symbol_2, position_dict, strategy_instance_id):
        if (position_dict == {}):
            msg = 'null position_dict'
        else:
            dao_execute = DaoExecute()
            trade_exec = dao_execute
            money_num = 0
            exec_ts = time.time()
            price = '1'
            if (symbol in position_dict):
                if (position_dict[symbol]['long'] > 0):
                    if (strategy_type == 'future_strategy'):
                        order_type = 'market_close_long'
                    elif (strategy_type == 'spot_strategy'):
                        order_type = 'sell_market'
                    amount = position_dict[symbol]['long']
                    status, data = dao_execute.execute_order(user_id, exchange,
                                   account_type,strategy_name, symbol,
                                   order_type, price, amount, money_num,
                                   exec_ts, strategy_instance_id)
                    print(status, data)
                    if ((resp['order_id'] == 0) and ('quarter' in symbol)):
                        symbol = symbol.split('quarter')[0] + 'next_week'
                        status, data = dao_execute.execute_order(user_id,
                                       exchange, account_type, strategy_name,
                                       symbol, order_type, price, amount,
                                       money_num, exec_ts,
                                       strategy_instance_id)
                        print(status, data)
                if (position_dict[symbol]['short'] > 0):
                    if (strategy_type == 'future_strategy'):
                        order_type = 'market_close_short'
                    elif (strategy_type == 'spot_strategy'):
                        order_type = 'buy_market'
                    amount = position_dict[symbol]['short']
                    resp = dao_execute.execute_order(user_id, exchange, account_type,
                                                     strategy_name, symbol, order_type,
                                                     price, amount, money_num, exec_ts,
                                                     strategy_instance_id)
                    print(resp)
            if (symbol_2 in position_dict):
                if (position_dict[symbol_2]['long'] > 0):
                    if (strategy_type == 'future_strategy'):
                        order_type = 'market_close_long'
                    elif (strategy_type == 'spot_strategy'):
                        order_type = 'sell_market'
                    amount = position_dict[symbol_2]['long']
                    resp = trade_exec.execute_order(user_id, exchange_2, account_type,
                                                    strategy_name, symbol_2, order_type,
                                                    price, amount, money_num, exec_ts,
                                                    strategy_instance_id)
                    print(resp)
                if (position_dict[symbol_2]['short'] > 0):
                    if (strategy_type == 'future_strategy'):
                        order_type = 'market_close_short'
                    elif (strategy_type == 'spot_strategy'):
                        order_type = 'buy_market'
                    amount = position_dict[symbol_2]['short']
                    resp = trade_exec.execute_order(user_id, exchange_2, account_type,
                                                    strategy_name, symbol_2, order_type,
                                                    price, amount, money_num, exec_ts,
                                                    strategy_instance_id)
                    print(resp)
            msg = 'covered position_dict'
        return msg

    def get_strategy_files(self, sig, user_id, page_num, page_limit):
        if not self.check_sig(sig, 'get_strategy_files', user_id, page_num,
                              page_limit):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        page_limit = int(page_limit)
        page_num = int(page_num)
        offset = (page_num - 1) * page_limit
        total_count = StrategyFile.objects.filter(user_id=user_id, delete_status__ne=1).count()
        sfs = StrategyFile.objects.filter(user_id=user_id, delete_status__ne=1
              ).skip(offset).limit(page_limit).exclude('strategy_file_datetime', 'file_content').order_by('strategy_timestamp')
        strategy_dict_list = [sf.to_dict() for sf in sfs]
        page_num_list = self.get_page_rst(total_count, page_num, page_limit)

        data = {}
        data['page_num'] = page_num
        data['page_num_list'] = page_num_list
        data['file_list'] = strategy_dict_list
        return self.ret_resp(1, data)

    def manage_strategy_file(self, sig, action, user_id, strategy_file_id, file_nick_name, file_content, file_description):
        if not self.check_sig(sig, 'manage_strategy_file', action, user_id,
                              strategy_file_id, file_nick_name, file_content,
                              file_description):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        data = 'no action'
        if action == 'save':
            user = User.objects.get(id=user_id)
            strategy_file = StrategyFile()
            strategy_file.user_name = user.user_name
            strategy_file.user_id = user.id
            strategy_file.phone_num = user.phone_num
            strategy_file.file_nick_name = file_nick_name
            strategy_file.file_content = file_content
            strategy_file.file_description = file_description
            strategy_file.save()
            data = '存储成功'
        elif action == 'update':
            if (strategy_file_id == ''):
                data = '新策略点击另存'
                return self.ret_resp(0, data)
            strategy_file = StrategyFile.objects.get(user_id=user_id,
                            id=strategy_file_id)
            strategy_file.last_timestamp = time.time()
            strategy_file.file_nick_name = file_nick_name
            strategy_file.file_content = file_content
            strategy_file.file_description = file_description
            strategy_file.save()
            data = '更新成功'
        elif action == 'delete':
            strategy_file = StrategyFile.objects.get(user_id=user_id,
                            id=strategy_file_id)
            strategy_file.delete_status = 1
            strategy_file.save()
            data = '删除成功'
        elif action == 'get':
            strategy_file = StrategyFile.objects.get(user_id=user_id,
                            id=strategy_file_id)
            data = {}
            data['strategy_file_id'] = str(strategy_file.id)
            data['file_nick_name'] = strategy_file.file_nick_name
            data['file_description'] = strategy_file.file_description
            data['file_content'] = strategy_file.file_content
        return self.ret_resp(1, data)

    def submit_strategy_job(self, sig, strategy_name, user_id, begin_time, end_time, period, exchange, symbol, exchange_2, symbol_2, one_time_buy, direction, log_record, strategy_type, balance_end, balance_front, taker_fee_ratio, maker_fee_ratio, strategy_file_id, param_1_start, param_1_end, param_1_step, param_2_start, param_2_end, param_2_step, indicator_config):
        if not self.check_sig(sig, 'submit_strategy_job', strategy_name, user_id, begin_time, end_time, period, exchange, symbol, exchange_2, symbol_2, one_time_buy, direction, log_record, strategy_type, balance_end, balance_front, taker_fee_ratio, maker_fee_ratio, strategy_file_id, param_1_start, param_1_end, param_1_step, param_2_start, param_2_end, param_2_step, indicator_config):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        # add check params logic
        if param_1_start == '' or param_2_start == '':
            data = '传入参数初值不能空'
            return self.ret_resp(0, data)
        exchange = exchange.lower()
        strategy_file_id = ObjectId(strategy_file_id)
        user = User.objects.get(id=user_id)
        strategy_job = StrategyJob()
        strategy_job.strategy_name = strategy_name
        strategy_job.user_name = str(user.user_name)
        strategy_job.user_id = user.id
        strategy_job.begin_time = begin_time
        strategy_job.end_time = end_time
        strategy_job.period = int(period)
        strategy_job.exchange = exchange
        strategy_job.symbol = symbol
        strategy_job.exchange_2 = exchange_2
        strategy_job.symbol_2 = symbol_2
        strategy_job.one_time_buy = float(one_time_buy)
        strategy_job.direction = direction
        strategy_job.log_record = log_record
        strategy_job.strategy_type = strategy_type
        strategy_job.balance_end = float(balance_end)
        strategy_job.balance_front = float(balance_front)
        strategy_job.taker_fee_ratio = float(taker_fee_ratio)/100
        strategy_job.maker_fee_ratio = float(maker_fee_ratio)/100
        strategy_job.strategy_file_id = strategy_file_id
        strategy_job.param_1_start = param_1_start
        strategy_job.param_1_end = param_1_end
        strategy_job.param_1_step = param_1_step
        strategy_job.param_2_start = param_2_start
        strategy_job.param_2_end = param_2_end
        strategy_job.param_2_step = param_2_step
        if (indicator_config == ''):
            indicator_config = {}
        else:
            indicator_config = ast.literal_eval(indicator_config)
        strategy_job.indicator_config = indicator_config

        strategy_file = StrategyFile.objects.get(user_id=user_id,
                        id=strategy_file_id)
        strategy_job.file_nick_name = strategy_file.file_nick_name
        strategy_job.file_content = strategy_file.file_content
        strategy_job.file_description = strategy_file.file_description

        strategy_job.status = 'new'
        strategy_job.save()
        data = '回测任务已提交'
        return self.ret_resp(1, data)

    def get_strategy_jobs(self, sig, user_id, strategy_file_id, page_num, page_limit):
        if not self.check_sig(sig, 'get_strategy_jobs', user_id,
                              strategy_file_id, page_num, page_limit):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        if strategy_file_id == '':
            data = '没有选中策略!'
            return self.ret_resp(0, data)
        page_limit = int(page_limit)
        page_num = int(page_num)
        offset = (page_num - 1) * page_limit
        total_count = StrategyJob.objects.filter(user_id=user_id, strategy_file_id=strategy_file_id).count()
        sjs = StrategyJob.objects.filter(user_id=user_id, strategy_file_id=strategy_file_id
              ).skip(offset).limit(page_limit).exclude('file_content').order_by('-strategy_timestamp')
        job_dict_list = [sj.to_dict() for sj in sjs]
        page_num_list = self.get_page_rst(total_count, page_num, page_limit)

        data = {}
        data['page_num'] = page_num
        data['page_num_list'] = page_num_list
        data['config_list'] = job_dict_list
        return self.ret_resp(1, data)

    def manage_strategy_job(self, sig, action, user_id, strategy_job_id):
        if not self.check_sig(sig, 'manage_strategy_job', action, user_id,
                              strategy_job_id):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        data = 'no action'
        if action == 'gen_rst':
            exception = 0
            exception_msg = 'none'
            strategy_job = StrategyJob.objects.get(user_id=user_id, id=strategy_job_id)
            strategy_job.exception = exception
            strategy_job.exception_msg = exception_msg
            strategy_job.status = 'running'
            strategy_job.save()
            data = 'ok'
        elif action == 'delete':
            rst = StrategyJob.objects(user_id=user_id, id=strategy_job_id).delete()
            if (rst == 1):
                data = '配置删除成功！'
            else:
                data = '删除失败, {}'.format(rst)
        elif action == 'get_code':
            strategy_job = StrategyJob.objects.get(user_id=user_id, id=strategy_job_id)
            data = {}
            data['strategy_file_id'] = 'history file'
            data['file_nick_name'] = strategy_job.file_nick_name
            data['file_description'] = strategy_job.file_description
            data['file_content'] = strategy_job.file_content
        elif action == 'get_exception':
            strategy_job = StrategyJob.objects.get(user_id=user_id, id=strategy_job_id)
            data = {}
            data['exception'] = strategy_job.exception
            data['exception_msg'] = strategy_job.exception_msg
        return self.ret_resp(1, data)

    def get_strategy_tasks(self, sig, user_id, strategy_job_id, page_num, page_limit):
        if not self.check_sig(sig, 'get_strategy_tasks', user_id,
                              strategy_job_id, page_num, page_limit):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        page_limit = int(page_limit)
        page_num = int(page_num)
        offset = (page_num - 1) * page_limit
        total_count = StrategyTask.objects.filter(user_id=user_id, strategy_job_id=strategy_job_id).count()
        sts = StrategyTask.objects.filter(user_id=user_id, strategy_job_id=strategy_job_id
              ).skip(offset).limit(page_limit).order_by('strategy_timestamp')
        task_dict_list = [st.to_dict() for st in sts]
        page_num_list = self.get_page_rst(total_count, page_num, page_limit)

        data = {}
        data['page_num'] = page_num
        data['page_num_list'] = page_num_list
        data['record_list'] = task_dict_list
        return self.ret_resp(1, data)

    def manage_strategy_task(self, sig, action, user_id, strategy_task_id):
        if not self.check_sig(sig, 'manage_strategy_task', action, user_id,
                              strategy_task_id):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        data = 'no action'
        if action == 'trade_pnl':
            strategy_task = StrategyTask.objects.exclude('n_order_records', 'order_records').get(user_id=user_id, id=strategy_task_id)
            if len(strategy_task.trade_records) > 0:
                trade_records = strategy_task.trade_records
                timestamp_list = []
                price_list = []
                balance_list = []
                for trade_record in trade_records:
                    timestamp = convert.to_timestamp(trade_record[3])
                    timestamp_list.append(timestamp)
                    price_list.append(trade_record[4])
                    balance_list.append(trade_record[8])

                trade_num = strategy_task.earn_num + strategy_task.loss_num
                balance = round(strategy_task.balance, 3)
                title = ('s: {}.{}, p1:{}|p2:{}, balance:{}, nums:{}, '
                        'wr:{}, elr:{}').format(strategy_task.exchange,
                        strategy_task.symbol, strategy_task.param_1,
                        strategy_task.param_2, balance,
                        trade_num, strategy_task.win_ratio,
                        strategy_task.earn_loss_ratio)
            else:
                title = '回测期间没有交易'
                timestamp_list = []
                price_list = []
                balance_list = []
            data = {}
            data['title'] = title
            data['timestamp_list'] = timestamp_list
            data['price_list'] = price_list
            data['balance_list'] = balance_list
        elif action == 'trade_chart':
            title = '回测期间没有交易'
            bars = []
            entry_list = []
            exit_list = []

            strategy_task = StrategyTask.objects.exclude('n_order_records', 'order_records').get(user_id=user_id, id=strategy_task_id)
            if len(strategy_task.trade_records) > 0:
                trade_num = strategy_task.earn_num + strategy_task.loss_num
                balance = round(strategy_task.balance, 3)
                title = ('p1: {}, p2: {}, balance: {}, nums: {}, '
                         'wr: {}, elr: {}').format(strategy_task.param_1,
                        strategy_task.param_2, balance,
                        trade_num, strategy_task.win_ratio,
                        strategy_task.earn_loss_ratio)
                exchange = strategy_task.exchange
                symbol = strategy_task.symbol
                if exchange == 'stock':
                    period = '1d'
                else:
                    period = '1min'
                begin_time = strategy_task.begin_time
                end_time = strategy_task.end_time
                begin_time = begin_time.split(' ')[0] + ' 00:00:00'
                begin_timestamp = int(convert.to_timestamp(begin_time))
                end_timestamp = int(convert.to_timestamp(end_time))
                strategy_type = strategy_task.strategy_type
                dao_quote = DaoQuote()
                if (strategy_type == 'arbitrage_strategy'):
                    exchange_a = exchange
                    symbol_a = symbol
                    status_a, bars_a = dao_quote.get_backtest_kline_db(exchange_a, symbol_a, period,
                                     str(begin_timestamp), str(end_timestamp))
                    exchange_b = exchange.split('f')[0]
                    symbol_b = symbol.split('-')[0] + 't'
                    status_b, bars_b = dao_quote.get_backtest_kline_db(exchange_b, symbol_b, period,
                                     str(begin_timestamp), str(end_timestamp))
                    if (len(bars_a) != len(bars_b)):
                        data = 'length not equal'
                        return self.ret_resp(0, data)
                    if (status_a == 0) or (status_b == 0):
                        data = '{} {}'.format(bars_a, bars_b)
                        return self.ret_resp(0, data)
                    bars = convert.spread_lines(bars_a, bars_b)
                else:
                    status, bars = dao_quote.get_backtest_kline_db(exchange, symbol, period,
                                   str(begin_timestamp), str(end_timestamp))
                    if status == 0:
                        return self.ret_resp(0, bars)
                period = strategy_task.period
                if (period != 1):
                    bars = convert.combine_lines_3(bars, period)
                for trade_record in strategy_task.trade_records:
                    entry_time = trade_record[0]
                    entry_timestamp = convert.to_timestamp(entry_time)
                    entry_price = trade_record[1]

                    exit_time = trade_record[3]
                    exit_timestamp = convert.to_timestamp(exit_time)
                    exit_price = trade_record[4]

                    entry_list.append([int(entry_timestamp)*1000, entry_price])
                    exit_list.append([int(exit_timestamp)*1000, exit_price])

            status = 1
            data = {}
            data['title'] = title
            data['bars'] = bars
            data['entry_list'] = entry_list
            data['exit_list'] = exit_list
        elif action == 'trade_records':
            strategy_task = StrategyTask.objects.exclude('n_order_records', 'order_records').get(user_id=user_id, id=strategy_task_id)
            trade_records = []
            if len(strategy_task.trade_records) > 0:
                for trade_record in strategy_task.trade_records:
                    del trade_record[10]
                    trade_records.append(trade_record)
            data = {}
            data['trade_records'] = trade_records
            data['exchange'] = strategy_task.exchange
            data['symbol'] = strategy_task.symbol
            data['param_1'] = strategy_task.param_1
            data['param_2'] = strategy_task.param_2
        elif action == 'order_records':
            strategy_task = StrategyTask.objects.exclude('trade_records', 'order_records').get(user_id=user_id, id=strategy_task_id)
            data = {}
            data['order_records'] = strategy_task.n_order_records
            data['exchange'] = strategy_task.exchange
            data['symbol'] = strategy_task.symbol
            data['param_1'] = strategy_task.param_1
            data['param_2'] = strategy_task.param_2
        elif action == 'trade_records_exception':
            strategy_task = StrategyTask.objects.exclude('trade_records', 'order_records', 'n_order_records').get(user_id=user_id, id=strategy_task_id)
            data = {}
            data['exception'] = strategy_task.exception
            data['exception_msg'] = strategy_task.exception_msg
        elif action == 'delete_backtest_record':
            rst = StrategyTask.objects.get(user_id=user_id, id=strategy_task_id).delete()
            if (rst == 1):
                data = '配置删除成功！'
            else:
                data = '删除失败, {}'.format(rst)
        return self.ret_resp(1, data)

    def get_file(self, sig, user_id, file_name):
        if not self.check_sig(sig, 'get_file', user_id, file_name):
            data = 'wrong sig'
            return self.ret_resp(0, data)
        # file_id = file_name.split('_')[-1].split('.')[0]
        # if 'params_fig_' in file_name:
        #     if StrategyJob.objects.filter(id=file_id, user_id=user_id).first() is None:
        #         data = 'file not found'
        #         return self.ret_resp(0, data)
        # elif 'in_test_' in file_name:
        #     if StrategyTask.objects.filter(id=file_id, user_id=user_id).first() is None:
        #         data = 'file not found'
        #         return self.ret_resp(0, data)
        data = {}
        file_path = 'dao_strategy/backtest/strategy_files/'
        filename = file_path + file_name
        file_content = ''
        with open(filename, 'rb') as f:
            file_content = f.read()
        file_content = base64.b64encode(file_content)
        file_content = file_content.decode('utf8')
        data['file_content'] = file_content
        return self.ret_resp(1, data)

    def get_file_node(self, sig, user_id, file_name):
        # 'in_test_{}.pdf'.format(str(strategy_task_id))
        # processor_ip in StrategyTask
        # with distribute

        # file_name = 'params_fig_{}.pdf'.format(str(sj.id))
        # ip with monitor
        pass


def run():
    rpc_node = cfg['rpc_node']
    host = rpc_node['ip']
    port = rpc_node['port']
    print('[*] {}:{}, server running'.format(host, port))
    ds_thrift = thriftpy2.load("dao_strategy/rpc/dao_strategy.thrift", module_name="ds_thrift")
    server = make_server(ds_thrift.DaoStrategy, Dispatcher(), host, port, client_timeout=10000)
    server.serve()
