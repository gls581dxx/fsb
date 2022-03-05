# !/usr/bin/env python
# coding=utf-8

import os
import ast
import json
import time
import redis
import datetime
import traceback
from threading import Thread

from dao_strategy.utils import convert
from dao_strategy.utils import dao_log
from dao_strategy.utils import send_sms
from dao_strategy.utils.account import Account
from dao_strategy.rpc.dao_quote import DaoQuote
from dao_strategy.rpc.dao_execute import DaoExecute
from dao_strategy.settings.config import cfg
from dao_strategy.db.redis import RedisClient
from dao_strategy.db.dt_models import StrategyInstance


class StrategyTemplate(object):

    author = ''

    def __init__(self, setting_dict):
        self.strategy_instance_id = setting_dict['strategy_instance_id']
        self.strategy_type = setting_dict['strategy_type']

        self.user_id = setting_dict['user_id']
        self.user_name = setting_dict['user_name']
        self.phone_zone_code = setting_dict['phone_zone_code']
        self.phone_num = setting_dict['phone_num']
        self.feishu_api = setting_dict['feishu_api']
        self.run_type = setting_dict['run_type']
        self.sms_send = setting_dict['sms_send']
        self.account_type = setting_dict['account_type']
        self.strategy_name = setting_dict['strategy_name']
        self.min_trade_num = setting_dict['min_trade_num']

        self.exchange = setting_dict['exchange']
        self.symbol = setting_dict['symbol']
        self.status_dict = setting_dict['status_dict']

        self.on_listen = True
        self.account = Account()

        self.type_list = setting_dict.get('type_list',
                         ['ticker', 'kline', 'depth'])
        self.key_name_list = []
        for type_ in self.type_list:
            if ('timer_' in type_):
                key_name = 'dao_{}'.format(type_)
            else:
                key_name = '{}_{}_{}'.format(self.exchange, self.symbol, type_)
            self.key_name_list.append(key_name)
        if self.exchange == 'ctp':
            self.trading_day = ''

        self.set_pid()

    def main_trade(self):
        redis_cfg = cfg['redis']['dao_quote']
        r = RedisClient(redis_cfg).redis
        p = r.pubsub()
        for key_name in self.key_name_list:
            p.subscribe(key_name)
        msg = ('time: {}, strategy_type: {}, strategy_name: {}, '
              'exchange: {}, symbol: {}').format(
              str(datetime.datetime.now()), self.strategy_type,
              self.strategy_name, self.exchange, self.symbol)
        print(msg)
        self.log_msg(msg)
        for item in p.listen():
            if (not self.on_listen):
                pass
            else:
                if item['type'] == 'message':
                    event_dict = item['data']
                    r.set('s', 32)
                    event_dict = json.loads(event_dict)
                    event_type = event_dict['event_type']
                    event_exchange = event_dict['exchange']
                    event_symbol = event_dict['symbol']
                    data = json.loads(event_dict['data'])
                    if event_type == 'ticker':
                        self.on_tick(data)
                    elif event_type == 'kline':
                        self.on_bar(data)
                    elif event_type == 'depth':
                        self.on_depth(data)
                    elif event_type == 'trade':
                        self.on_trade(data)
                    elif event_type == 'timer':
                        self.on_timer(data)

    def backtest(self, begin_time, end_time):
        begin_timestamp = int(convert.to_timestamp(begin_time))
        end_timestamp = int(convert.to_timestamp(end_time))
        period = '1min'
        dao_quote = DaoQuote()
        status, bars = dao_quote.get_backtest_kline_db(self.exchange,
                       self.symbol, period, begin_timestamp, end_timestamp)
        for i in range(20, len(bars)):
            data = bars[i-20:i]
            self.on_bar(data)
        return True

    def load_bar(self, num, end_timestamp):
        try:
            period = '1min'
            dao_quote = DaoQuote()
            status, bars = dao_quote.get_kline_db(self.exchange, self.symbol,
                           period, str(num), str(end_timestamp))
            if status == 0:
                raise Exception(bars)
        except Exception as e:
            exception_msg = traceback.format_exc()
            msg = 'load_bar, {}'.format(exception_msg)
            self.log_msg(msg, log_level='error')
            print(msg)
            bars = []
        for bar in bars:
            data = [bar, [111333, 2, 3, 4, 5, 6]]
            self.on_bar(data)

    def on_bar(self, data):
        pass

    def on_tick(self, data):
        pass

    def on_depth(self, data):
        pass

    def on_trade(self, data):
        pass

    def on_timer(self, data):
        pass

    def set_strategy_status_dict(self, status_dict):
        try:
            strategy_instance = StrategyInstance.objects.get(
                                id=self.strategy_instance_id)
            strategy_instance.status_dict = self.status_dict
            # print(self.status_dict)
            strategy_instance.save()
            return True
        except Exception as e:
            return False

    def is_close_today(self, trading_day, open_td_day):
        if trading_day == open_td_day:
            return True
        else:
            False

    def ctp_time_filter(self, dt=datetime.datetime.now()):
        if self.exchange != 'ctp':
            return True
        if (0 <= dt.hour < 9) or (dt.hour == 12) or (15 <= dt.hour < 21) or (dt.hour >= 23):
            # 非交易的小时
            return False
        elif dt.hour == 10:
            # 上午十点休息
            if 15 <= dt.minute <= 29:
                return False
            elif dt.minute == 14:
                if dt.second > 55:
                    return False
        elif dt.hour == 11 and dt.minute == 29 and dt.second > 55:
            return False
        elif dt.hour == 13:
            if dt.minute < 30:
                return False
        elif dt.hour == 14 and dt.minute == 59 and dt.second > 55:
            return False
        elif dt.hour == 22 and dt.minute == 59 and dt.second > 55:
            return False
        return True

    def execute_strategy_order(self, exchange, symbol, order_type, price, amount, exec_ts=0.0, close_today=True):
        money_num = 0
        if (self.strategy_type == 'future_strategy'):
            amount = amount
            if exchange == 'ctp':
                open_td_day = self.status_dict.get('open_td_day', '')
                close_today = self.is_close_today(self.trading_day, open_td_day)
        elif (self.strategy_type == 'spot_strategy'):
            amount = amount
        elif (self.strategy_type == 'conditional_strategy'):
            amount = amount
        else:
            amount = amount / price
        print(self.user_id, self.user_name, exchange, self.account_type,
              self.strategy_name, symbol, order_type, price, amount,
              money_num, close_today)
        if (self.run_type == 'real'):
            dao_execute = DaoExecute()
            trade_exec = dao_execute
            status, order_rst = trade_exec.execute_order(
                                self.user_id, exchange, self.account_type,
                                self.strategy_name, symbol, order_type,
                                str(price), str(amount), str(money_num),
                                str(exec_ts), self.strategy_instance_id,
                                close_today)
        elif (self.run_type == 'test'):
            order_rst = {}
            order_rst['order_id'] = 0
        if (self.sms_send == 'yes'):
            nationCode = self.phone_zone_code
            phoneNumber = self.phone_num
            strategy_name_ = self.strategy_name
            symbol_ = symbol.split('_')[0]
            if ('going' in order_type):
                status_ = '开'
            elif ('close' in order_type):
                status_ = '平'
            elif ('buy' in order_type):
                status_ = '买'
            elif ('sell' in order_type):
                status_ = '卖'
            else:
                status_ = '看'
            order_info = '{};{}'.format(symbol_, status_)
            rst = send_sms.send_order_reminder(nationCode, phoneNumber,
                  strategy_name_, order_info)
            print(rst)
        elif (self.sms_send == 'shu'):
            order_info = '{}:{}, 类型: {}, 价格: {}, 数量: {}'.format(
                         exchange, symbol, order_type, price, amount)
            rst = send_sms.send_feishu_order_reminder(self.feishu_api,
                  self.strategy_name, order_info)
        elif (self.sms_send == 'no'):
            pass
        return order_rst

    def reminder(self):
        nationCode = self.phone_zone_code
        phoneNumber = self.phone_num
        strategy_name_ = self.strategy_name
        symbol_ = self.symbol.split('_')[0]
        if (self.status == 'going_long'):
            status_ = '买'
        elif (self.status == 'close_long'):
            status_ = '卖'
        elif (self.status == 'pre_buy'):
            status_ = 'pre'
        order_info = '{};{}'.format(symbol_, status_)
        if (self.sms_send == 'yes'):
            rst = send_sms.send_order_reminder(nationCode, phoneNumber,
                  strategy_name_, order_info)
            print(rst)
        elif (self.sms_send == 'shu'):
            rst = send_sms.send_order_reminder(nationCode, phoneNumber,
                  strategy_name_, order_info)
            print(rst)
        elif (self.sms_send == 'no'):
            pass
        return None

    def fetch_open_orders(self, exchange, symbol):
        dao_execute = DaoExecute()
        trade_exec = dao_execute
        status, order_rst = trade_exec.fetch_open_orders(self.user_id,
                            exchange, self.account_type, self.strategy_name,
                            symbol)
        order_list = order_rst['order_list']
        return order_list

    def fetch_orders(self, exchange, symbol, order_id):
        if (order_id == 0):
            order_rst = []
            order_dict = {}
            order_dict['order_status'] = 'filled'
            order_rst.append(order_dict)
        elif (self.run_type == 'real'):
            dao_execute = DaoExecute()
            trade_exec = dao_execute
            status, order_rst = trade_exec.fetch_orders(self.user_id, exchange,
                                self.account_type, self.strategy_name, symbol,
                                str(order_id))
        elif (self.run_type == 'test'):
            order_rst = []
            order_dict = {}
            order_dict['order_status'] = 'filled'
            order_rst.append(order_dict)
        return order_rst

    def fetch_order_ex(self, exchange, symbol, order_id):
        if ((str(order_id) == '0') or (self.account_type == 'reg_backtest')):
            order_rst = []
            order_dict = {}
            order_dict['order_status'] = 'filled'
            order_rst.append(order_dict)
        elif (self.account_type == 'reg_emulator'):
            order_rst = self.fetch_orders(exchange, symbol, order_id)
        elif (self.run_type == 'real'):
            dao_execute = DaoExecute()
            trade_exec = dao_execute
            status, order_rst = trade_exec.fetch_order_ex(self.user_id,
                                exchange, self.account_type,
                                self.strategy_name, symbol, str(order_id))
        elif (self.run_type == 'test'):
            order_rst = []
            order_dict = {}
            order_dict['order_status'] = 'filled'
            order_rst.append(order_dict)
        return order_rst

    def cancel_order(self, exchange, symbol, order_id):
        if (self.run_type == 'real'):
            dao_execute = DaoExecute()
            trade_exec = dao_execute
            status, rst = trade_exec.cancel_order(self.user_id, exchange,
                          self.account_type, self.strategy_name, symbol,
                          str(order_id))
            result = rst['result']
        elif (self.run_type == 'test'):
            result = True
        return result

    def set_pid(self):
        pid = os.getpid()
        try:
            strategy_instance = StrategyInstance.objects.get(
                                id=self.strategy_instance_id)
            strategy_instance.pid = pid
            # print(self.status_dict)
            strategy_instance.save()
            return True
        except Exception as e:
            exception_msg = traceback.format_exc()
            msg = 'set_pid, {}'.format(exception_msg)
            self.log_msg(msg, log_level='error')

    def get_position_dict(self):
        strategy_instance = {}
        strategy_instance['user_id'] = self.user_id
        strategy_instance['user_name'] = self.user_name
        strategy_instance['account_type'] = self.account_type
        strategy_instance['strategy_name'] = self.strategy_name
        strategy_instance['exchange'] = self.exchange
        strategy_instance['symbol'] = self.symbol
        strategy_instance['id'] = self.strategy_instance_id
        position_dict = {}
        if (self.strategy_type == 'future_strategy'):

            position_dict = self.account.get_future_strategy_position(strategy_instance)
        elif (self.strategy_type == 'spot_strategy'):
            position_dict = self.account.get_spot_strategy_position(strategy_instance)
        else:
            position_dict = {}
        return position_dict

    def get_account(self, exchange, symbol):
        info = self.account.get_balance(self.user_id, exchange, self.account_type, self.strategy_name, symbol)
        data = info['data']
        return data

    def log_msg(self, msg, log_level='info'):
        log_msg = '{}, {}, {}, {}, {}'.format(self.strategy_name, msg,
                      self.user_name, self.exchange, self.symbol)
        log_dict = {}
        log_dict['user_name'] = self.user_name
        log_dict['user_id'] = self.user_id
        log_dict['phone_num'] = self.phone_num
        log_dict['strategy_name'] = self.strategy_name
        log_dict['strategy_instance_id'] = self.strategy_instance_id
        log_dict['strategy_type'] = self.strategy_type
        log_dict['account_type'] = self.account_type
        log_dict['exchange'] = self.exchange
        log_dict['symbol'] = self.symbol
        log_dict['log_type'] = 'strategy_log'
        log_dict['log_level'] = log_level
        msg_dict = {}
        msg_dict['msg'] = msg
        msg_dict['status_dict'] = self.status_dict
        log_dict['log_message'] = json.dumps(msg_dict)
        dao_log.save_log(log_dict)
        # print(log_msg)
        return True

    def stop_strategy(self):
        try:
            strategy_instance = StrategyInstance.objects.get(
                                id=self.strategy_instance_id)
            strategy_instance.status = 'stop'
            strategy_instance.save()
            return True
        except Exception as e:
            raise


class HftTemplate(StrategyTemplate):

    def main_trade(self):
        print(('time: {}, strategy_type: {}, strategy_name: {}, '
              'exchange: {}, symbol: {}').format(
              str(datetime.datetime.now()), self.strategy_type,
              self.strategy_name, self.exchange, self.symbol))
        key_name_dict_list = []
        for key_name in self.key_name_list:
            key_name_split = key_name.split('_')
            exchange, event_type = key_name_split[0], key_name_split[-1]
            symbol = '_'.join(key_name_split[1:-1])
            key_name_dict = {}
            key_name_dict['exchange'] = exchange
            key_name_dict['symbol'] = symbol
            key_name_dict['event_type'] = event_type
            key_name_dict_list.append(key_name_dict)
        last_tick_timestamp = 0
        last_bar_timestamp = 0
        last_depth_timestamp = 0
        period = '1min'
        while True:
            for key_name_dict in key_name_dict_list:
                exchange = key_name_dict['exchange']
                symbol = key_name_dict['symbol']
                if (key_name_dict['event_type'] == 'ticker'):
                    data = self.get_tick(exchange, symbol)
                    tick_timestamp = data['ts']
                    if (tick_timestamp > last_tick_timestamp):
                        self.on_tick(data)
                        last_tick_timestamp = tick_timestamp
                elif (key_name_dict['event_type'] == 'kline'):
                    dao_quote = DaoQuote()
                    data = dao_quote.get_kline_local(exchange, symbol)
                    bar_timestamp = data[-1][0]
                    if (bar_timestamp > last_bar_timestamp):
                        self.on_bar(data)
                        last_bar_timestamp = bar_timestamp
                elif (key_name_dict['event_type'] == 'depth'):
                    data = self.get_depth(exchange, symbol)
                    if ('ts' not in data):
                        continue
                    depth_timestamp = data['ts']
                    if (depth_timestamp > last_depth_timestamp):
                        self.on_depth(data)
                        last_depth_timestamp = depth_timestamp
            time.sleep(0.07)

    def get_tick(self, exchange, symbol):
        dao_quote = DaoQuote()
        data = dao_quote.get_ticker(exchange, symbol)
        return data

    def get_depth(self, exchange, symbol):
        dao_quote = DaoQuote()
        data = dao_quote.get_depth(exchange, symbol)
        return data


class DirTemplate(StrategyTemplate):

    def main_trade(self):
        print(('time: {}, strategy_type: {}, strategy_name: {}, '
              'exchange: {}, symbol: {}').format(
              str(datetime.datetime.now()), self.strategy_type,
              self.strategy_name, self.exchange, self.symbol))

        # self.thread_wss = Thread(target=self.gen_wss_quote, args=())
        # self.thread_bar = Thread(target=self.gen_on_bar, args=())
        # self.thread_wss.setDaemon(True)
        # self.thread_bar.setDaemon(True)
        # self.thread_wss.start()
        # self.thread_bar.start()
        self.gen_wss_quote()
        # self.gen_on_bar()

    def gen_wss_quote(self):
        from dao_trade.util.exchange_api.okex import wss_okex

        wss_okex_ins = wss_okex.WssOkex(self.key_name_list, self.on_tick,
                       self.on_depth, self.on_trade)

    def gen_on_bar(self):
        last_bar_timestamp = 0
        while True:
            dao_quote = DaoQuote()
            data = dao_quote.get_kline(self.exchange, self.symbol)
            bar_timestamp = data[-1][0]
            if (bar_timestamp > last_bar_timestamp):
                self.on_bar(data)
                last_bar_timestamp = bar_timestamp
            time.sleep(0.1)


class CtpTemplate(StrategyTemplate):

    def __init__(self, setting_dict):
        from dao_trade.util.crypto.api_crypt import user_api
        import platform

        super().__init__(setting_dict)
        api_dict = user_api.get_api_dict(self.user_id, self.exchange, self.account_type)
        broker_id = api_dict['broker_id']
        td_address = api_dict['td_address']
        api_key = api_dict['api_key']
        secret_key = api_dict['secret_key']
        ctp_app_id = api_dict['ctp_app_id']
        ctp_auth_code = api_dict['ctp_auth_code']
        os_version = platform.platform()
        if ('Linux' not in os_version):
            self.trade_spi = ''
        else:
            from dao_trade.microservices.trade_execution import trade_ctp
            self.trade_spi = trade_ctp.get_trade_spi(td_address, broker_id, api_key, secret_key, ctp_app_id, ctp_auth_code)

    def execute_strategy_order(self, exchange, symbol, order_type, price, amount, exec_ts=0.0):
        amount = int(amount)
        money_num = 0
        print(self.user_name, exchange, self.account_type,
              self.strategy_name, symbol, order_type,
              price, amount, money_num)
        if (self.run_type == 'real'):
            if ('.' not in symbol):
                if (symbol in ['c2005', 'c2009', 'a2005', 'a2009', 'l2005', 'l2009', 'p2005', 'p2009']):
                    symbol = 'DCE.{}'.format(symbol)
                else:
                    symbol = 'SHEF.{}'.format(symbol)
            order_rst = self.trade_spi.execute_order(self.user_id, exchange,
                                                     self.account_type,
                                                     self.strategy_name, symbol,
                                                     order_type, price, amount,
                                                     money_num, exec_ts)
        elif (self.run_type == 'test'):
            order_rst = {}
            order_rst['order_id'] = 0
        if (self.sms_send == 'yes'):
            nationCode = self.phone_zone_code
            phoneNumber = self.phone_num
            strategy_name_ = self.strategy_name
            symbol_ = symbol.split('_')[0]
            if ('going' in order_type):
                status_ = '开'
            elif ('close' in order_type):
                status_ = '平'
            else:
                status_ = '看'
            order_info = '{};{}'.format(symbol_, status_)
            rst = send_sms.send_order_reminder(nationCode, phoneNumber,
                  strategy_name_, order_info)
            print(rst)
        elif (self.sms_send == 'no'):
            pass
        return order_rst

    def cancel_order(self, exchange, symbol, order_id):
        if (self.run_type == 'real'):
            rst = self.trade_spi.cancel_order(self.user_id, exchange,
                  self.account_type, self.strategy_name, symbol, str(order_id))
            result = rst['result']
        elif (self.run_type == 'test'):
            result = True
        return result

    def fetch_order_ex(self, exchange, symbol, order_id):
        return None
