# !/usr/bin/env python
# coding=utf-8

import re
import json
import redis
import datetime

from dao_strategy.utils import convert
from dao_strategy.utils import trade
from dao_strategy.utils import global_var as g
from dao_strategy.settings import config
from dao_strategy.settings.config import cfg
from dao_strategy.db.redis import RedisClient


class StrategyTemplate(object):

    author = ''

    def __init__(self, setting_dict):
        self.open_position_dict = {}
        self.strategy_instance_id = setting_dict['strategy_instance_id']
        self.strategy_type = setting_dict['strategy_type']
        self.user_name = setting_dict['user_name']
        self.log_record = setting_dict['log_record']

        self.account_type = setting_dict['account_type']
        self.strategy_name = setting_dict['strategy_name']
        self.balance_end = setting_dict['balance_end']
        self.balance_front = setting_dict['balance_front']
        self.taker_fee_ratio = setting_dict['taker_fee_ratio']
        self.maker_fee_ratio = setting_dict['maker_fee_ratio']

        self.exchange = setting_dict['exchange']
        self.symbol = setting_dict['symbol']
        self.status_dict = setting_dict['status_dict']
        self.indicator_config = setting_dict.get('indicator_config', {})
        g.g_exchange = self.exchange
        g.g_symbol = self.symbol
        self.begin_timestamp = setting_dict['begin_timestamp']
        self.end_timestamp_hfd = setting_dict['end_timestamp']
        self.type_list = setting_dict.get('type_list',
                         ['ticker', 'kline'])
        self.set_position()
        self.set_pid()

    def main_trade(self):
        self.load_bar(self.load_bar_num, self.end_timestamp)
        redis_cfg = cfg['redis']['dao_quote']
        r = RedisClient(redis_cfg).redis
        p = r.pubsub()
        p.subscribe('quote')
        print(('time: {}, strategy_type: {}, strategy_name: {}, '
              'exchange: {}, symbol: {}').format(
              str(datetime.datetime.now()), self.strategy_type,
              self.strategy_name, self.exchange, self.symbol))
        for item in p.listen():
            if item['type'] == 'message':
                event_dict = item['data']
                r.set('s', 32)
                event_dict = json.loads(event_dict)
                event_type = event_dict['event_type']
                event_exchange = event_dict['exchange']
                event_symbol = event_dict['symbol']
                if ((self.exchange == event_exchange) and
                   (self.symbol == event_symbol)):
                    data = json.loads(event_dict['data'])
                    event_dict['data'] = data
                    if event_type == 'ticker':
                        self.on_tick(data)
                    elif event_type == 'kline':
                        self.on_bar(data)
                    if event_type == 'depth':
                        self.on_depth(data)
                else:
                    pass

    def backtest(self, bars):
        try:
            self.bm.count = 0
        except Exception as e:
            print('without bar_manager')

        if self.load_bar_action:
            load_bars = bars[:self.load_bar_num]
            for bar in load_bars:
                data = [bar, [111333, 2, 3, 4, 5, 6]]
                self.on_bar(data)
            bars = bars[self.load_bar_num:]

        type_list = []
        kline_type = False
        self._timer_type = False
        for i in self.type_list:
            if (i == 'kline'):
                kline_type = True
                type_list.append(config.HFT_BAR)
            elif ('ticker' == i):
                type_list.append(config.HFT_TICKER)
            elif ('depth' == i):
                type_list.append(config.HFT_DEPTH)
            elif ('depthall' == i):
                type_list.append(config.HFT_DEPTHALL)
            elif ('trade' == i):
                type_list.append(config.HFT_TRADE)
            elif ('timer' in i):
                self._timer_type = True

        if (kline_type):
            for i in range(20, len(bars)):
                data = bars[i-20:i]
                if (kline_type):
                    self.on_bar(data)
                if (self._timer_type):
                    ts = data[-1][0]
                    timer_dict = {}
                    timer_dict['ts'] = ts
                    timer_dict['time_now'] = convert.shift_time(ts)
                    self.on_timer(timer_dict)
        else:
            from dao_strategy.rpc.dao_quote import DaoQuote
            dao_quote = DaoQuote()
            print('dao_quote...')
            if (self.exchange == 'ctp'):
                seconds = 60 * 60  # 60 min per period
            else:
                seconds = 60 * 10  # 10 min per period
            for i in range(self.begin_timestamp, self.end_timestamp_hfd, seconds):
                begin_timestamp = i
                end_timestamp = i + seconds
                print('new batch')
                status, hfd_dict_list = dao_quote.get_hfd(self.exchange, self.symbol, type_list, begin_timestamp, end_timestamp)
                print('tick_num: ', len(hfd_dict_list),
                    convert.shift_time(begin_timestamp),
                    convert.shift_time(end_timestamp))

                for hfd_dict in hfd_dict_list:
                    self.set_hfd_dict(hfd_dict)

        return True

    def set_hfd_dict(self, hfd_dict):
        type_ = hfd_dict['t']
        if (type_ == config.HFT_BAR):
            self.on_bar([[1,2,3,4,5]])
        elif (type_ == config.HFT_TICKER):
            self.on_tick(hfd_dict)
        elif (type_ == config.HFT_DEPTH):
            self.on_depth(hfd_dict)
        elif (type_ == config.HFT_DEPTHALL):
            self.on_depthall(hfd_dict)
        elif (type_ == config.HFT_TRADE):
            self.on_trade(hfd_dict)
        if (self._timer_type):
            ts = time.time()
            timer_dict = {}
            timer_dict['ts'] = ts
            timer_dict['time_now'] = convert.shift_time(ts)
            self.on_timer(timer_dict)

    def load_bar(self, num, end_timestamp):
        self.load_bar_action = True
        self.load_bar_num = num
        self.load_bar_end_timestamp = end_timestamp
        return None

    def on_bar(self, data):
        pass

    def on_tick(self, data):
        pass

    def on_depth(self, data):
        pass

    def on_depthall(self, data):
        pass

    def on_trade(self, data):
        pass

    def set_strategy_status_dict(self, status_dict):
        return True

    def is_close_today(self, trading_day, open_td_day):
        return True

    def ctp_time_filter(self, dt=datetime.datetime.now()):
        return True

    def set_position(self):
        if (self.strategy_type == 'future_strategy'):
            if 'btc' in self.symbol:
                g.g_contract_value = 100
                self.g_contract_value = 100
            else:
                g.g_contract_value = 10
                self.g_contract_value = 10
        elif (self.strategy_type == 'spot_strategy'):
            g.g_balance_front = self.balance_front
            g.g_balance_end = self.balance_end
            self.g_balance_front = self.balance_front
            self.g_balance_end = self.balance_end

        g.g_balance = self.balance_end
        self.g_balance = self.balance_end

        if (self.exchange == 'ctp'):
            symbol_fee = re.findall(r'[0-9]+|[a-zA-Z]+', self.symbol)[0]
            fee_dict = cfg['ctp_fee_dict'][symbol_fee]

            self.g_fee_type = fee_dict['type']
            self.g_open_fee = fee_dict['open']
            self.g_close_fee = fee_dict['close']
            self.g_close_yest_fee = fee_dict['close_yest']
            self.g_tick_earn = fee_dict.get('tick_earn', 10)
        else:
            self.g_fee_ratio = self.taker_fee_ratio
        self.g_order_records = []
        # g_order_records new type; g_trade_records old type
        g.g_balance_range = []
        g.g_balance_range.append(g.g_balance)
        g.g_trade_records = []

        self.g_balance_range = []
        self.g_balance_range.append(self.g_balance)
        self.g_trade_records = []
        self.position_dict = {'long_qty': 0, 'long_avg_price': 0, 'long_position': 0,
                              'short_qty': 0, 'short_avg_price': 0, 'short_position': 0,
                              'balance_end': self.balance_end}
        return True

    def compute_indicator(self):
        in_dict = {}
        for indicator_name in self.indicator_config:
            param_list = self.indicator_config[indicator_name]
            indicator_func = getattr(self.bm, indicator_name)
            for param in param_list:
                key = '{}_{}'.format(indicator_name, param)
                in_dict[key] = indicator_func(param)
        g.g_param_1 = in_dict

    def execute_strategy_order(self, exchange, symbol, order_type, price, amount, exec_ts=0.0):
        if exchange == 'ctp':
            return self.execute_strategy_order_ctp(exchange, symbol, order_type, price, amount, exec_ts)

        elif exchange == 'okexf':
            return self.execute_strategy_order_coinf(exchange, symbol, order_type, price, amount, exec_ts)

        if (self.strategy_type == 'future_strategy'):
            amount = amount
        elif (self.strategy_type == 'spot_strategy'):
            amount = amount
        else:
            amount = amount / price
        coin = symbol.split('_')[0]
        time_now = convert.shift_time(exec_ts)
        if ('going' in order_type):
            self.open_position_dict['quantity'] = amount
            self.open_position_dict['open_price'] = price
            self.open_position_dict['open_time'] = time_now

            self.compute_indicator()

        elif ('close' in order_type):
            open_quantity = self.open_position_dict['quantity']
            open_price = self.open_position_dict['open_price']
            open_time = self.open_position_dict['open_time']
            g.g_quantity = amount
            g.g_open_price = open_price
            g.g_time_now = open_time
            if ('long' in order_type):
                trade.market_going_long(coin)
            elif ('short' in order_type):
                trade.market_going_short(coin)

            g.g_quantity = amount
            g.g_close_price = price
            g.g_time_now = time_now
            g.g_type = 'case_one'
            if ('long' in order_type):
                trade.market_close_long(coin)
            elif ('short' in order_type):
                trade.market_close_short(coin)
            self.open_position_dict['quantity'] -= amount
        elif ('buy' in order_type):
            self.compute_indicator()

            g.g_quantity = amount
            g.g_buy_price = price
            g.g_time_now = time_now
            trade.market_buy(symbol)
        elif ('sell' in order_type):
            g.g_quantity = amount
            g.g_sell_price = price
            g.g_time_now = time_now
            g.g_type = 'case_one'
            trade.market_sell(symbol)

        money_num = 0
        msg = '{}, {}, {}, {}'.format(self.user_name, exchange,
              self.account_type, self.strategy_name, symbol,
              order_type, price, amount, money_num)
        self.log_msg(msg)
        order_rst = {}
        order_rst['order_id'] = 0
        return order_rst

    def execute_strategy_order_ctp(self, exchange, symbol, order_type, price, amount, exec_ts=0.0):
        time_now = convert.shift_time(exec_ts)
        deal_money = price * amount
        fee = self.compute_fee_ctp(amount, deal_money*self.g_tick_earn)
        if 'going_long' in order_type:
            direct = 'open'
            # compute long_avg_price
            long_qty = self.position_dict['long_qty']
            if long_qty > 0:
                long_avg_price = self.position_dict['long_avg_price']
                new_long_qty = long_qty + amount
                new_long_avg_price = ((long_qty*long_avg_price) + deal_money) / new_long_qty
                self.position_dict['long_qty'] = new_long_qty
                self.position_dict['long_avg_price'] = new_long_avg_price
            else:
                self.position_dict['long_qty'] = amount
                self.position_dict['long_avg_price'] = price
            # balance update
            self.position_dict['balance_end'] -= fee
            self.compute_indicator()
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', g.g_param_1, g.g_param_2, g.g_param_3])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        elif 'close_long' in order_type:
            direct = 'close'
            self.position_dict['long_qty'] -= amount
            # balance update
            self.position_dict['balance_end'] -= fee
            earn = (price - self.position_dict['long_avg_price']) * amount * self.g_tick_earn
            self.position_dict['balance_end'] += earn
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', {}, {}, {}])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        elif 'going_short' in order_type:
            direct = 'open'
            # compute short_avg_price
            short_qty = self.position_dict['short_qty']
            if short_qty > 0:
                short_avg_price = self.position_dict['short_avg_price']
                new_short_qty = short_qty + amount
                new_short_avg_price = ((short_qty*short_avg_price) + deal_money) / new_short_qty
                self.position_dict['short_qty'] = new_short_qty
                self.position_dict['short_avg_price'] = new_short_avg_price
            else:
                self.position_dict['short_qty'] = amount
                self.position_dict['short_avg_price'] = price
            # balance update
            self.position_dict['balance_end'] -= fee
            self.compute_indicator()
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', g.g_param_1, g.g_param_2, g.g_param_3])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        elif 'close_short' in order_type:
            direct = 'close'
            self.position_dict['short_qty'] -= amount
            # balance update
            self.position_dict['balance_end'] -= fee
            earn = (self.position_dict['short_avg_price'] - price) * amount * self.g_tick_earn
            self.position_dict['balance_end'] += earn
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', {}, {}, {}])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        else:
            pass

        money_num = 0
        msg = '{}, {}, {}, {}'.format(self.user_name, exchange,
              self.account_type, self.strategy_name, symbol,
              order_type, price, amount, money_num)
        self.log_msg(msg)
        order_rst = {}
        order_rst['order_id'] = 0
        return order_rst

    def compute_fee_ctp(self, amount, deal_money):
        if self.g_fee_type == 'num':
            fee = self.g_open_fee * amount
        else:
            fee = self.g_open_fee * self.g_tick_earn * deal_money
        return fee

    def execute_strategy_order_coinf(self, exchange, symbol, order_type, price, amount, exec_ts=0.0):
        # coin futures based on coin
        time_now = convert.shift_time(exec_ts)
        fee = self.compute_fee_coinf(amount, price)
        if 'going_long' in order_type:
            direct = 'open'
            long_qty = self.position_dict['long_qty']
            if long_qty > 0:
                self.position_dict['long_position'] += (self.g_contract_value * amount / price)
                long_avg_price = self.position_dict['long_avg_price']
                new_long_qty = long_qty + amount
                new_long_avg_price = self.g_contract_value * self.position_dict['long_qty'] / self.position_dict['long_position']
                self.position_dict['long_qty'] = new_long_qty
                self.position_dict['long_avg_price'] = new_long_avg_price
            else:
                self.position_dict['long_qty'] = amount
                self.position_dict['long_avg_price'] = price
            # balance update
            self.position_dict['balance_end'] -= fee
            self.compute_indicator()
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', g.g_param_1, g.g_param_2, g.g_param_3])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        elif 'close_long' in order_type:
            direct = 'close'
            self.position_dict['long_qty'] -= amount
            # balance update
            self.position_dict['balance_end'] -= fee
            earn = (self.g_contract_value/self.position_dict['long_avg_price'] - self.g_contract_value/price) * amount
            self.position_dict['balance_end'] += earn
            close_position = self.g_contract_value * amount / price
            self.position_dict['long_position'] = self.position_dict['long_position'] - close_position - earn
            if (self.position_dict['long_qty'] == 0):
                self.position_dict['long_position'] = 0
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', {}, {}, {}])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        elif 'going_short' in order_type:
            direct = 'open'
            # compute short_avg_price
            short_qty = self.position_dict['short_qty']
            if short_qty > 0:
                positions_dict['short_position'] += self.g_contract_value * amount / price
                short_avg_price = self.position_dict['short_avg_price']
                new_short_qty = short_qty + amount
                new_short_avg_price = self.g_contract_value * self.position_dict['short_qty'] / self.position_dict['short_position']
                self.position_dict['short_qty'] = new_short_qty
                self.position_dict['short_avg_price'] = new_short_avg_price
            else:
                self.position_dict['short_qty'] = amount
                self.position_dict['short_avg_price'] = price
            # balance update
            self.position_dict['balance_end'] -= fee
            self.compute_indicator()
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', g.g_param_1, g.g_param_2, g.g_param_3])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        elif 'close_short' in order_type:
            direct = 'close'
            self.position_dict['short_qty'] -= amount
            # balance update
            self.position_dict['balance_end'] -= fee
            earn = (self.g_contract_value/price - self.g_contract_value/self.position_dict['short_avg_price']) * amount
            self.position_dict['balance_end'] += earn
            close_position = self.g_contract_value * amount / price
            self.position_dict['short_position'] = self.position_dict['short_position'] - close_position - earn
            if (self.positions_dict['short_qty'] == 0):
                self.positions_dict['short_position'] = 0
            g.g_trade_records.append([time_now, price, direct, fee, self.position_dict['balance_end'], '', {}, {}, {}])
            order_dict = {}
            order_dict['order_time'] = time_now
            order_dict['exchange'] = exchange
            order_dict['symbol'] = symbol
            order_dict['order_type'] = order_type
            order_dict['price'] = price
            order_dict['quantity'] = amount
            order_dict['fee'] = fee
            order_dict['balance_end'] = self.position_dict['balance_end']
            self.g_order_records.append(order_dict)
        else:
            pass
        money_num = 0
        msg = '{}, {}, {}, {}'.format(self.user_name, exchange,
              self.account_type, self.strategy_name, symbol,
              order_type, price, amount, money_num)
        self.log_msg(msg)
        order_rst = {}
        order_rst['order_id'] = 0
        return order_rst

    def compute_fee_coinf(self, amount, price):
        fee = self.g_contract_value * amount / price * self.g_fee_ratio
        return fee

    def reminder(self):
        return None

    def fetch_orders(self, exchange, symbol, order_id):
        order_rst = []
        order_dict = {}
        order_dict['order_status'] = 'filled'
        order_rst.append(order_dict)
        return order_rst

    def set_pid(self):
        return True

    def get_position_dict(self):
        position_dict = {}
        return position_dict

    def log_msg(self, msg):
        log_msg = '{}, {}, {}, {}, {}'.format(
                  self.strategy_name, msg, self.user_name,
                  self.exchange, self.symbol)
        if self.log_record:
            print(log_msg)


class HftTemplate(StrategyTemplate):

    def backtest(self, bars):
        from dao_strategy.rpc.dao_quote import DaoQuote
        dao_quote = DaoQuote()
        print('dao_quote...')

        if (self.strategy_type == 'future_strategy'):
            if 'btc' in self.symbol:
                g.g_contract_value = 100
            else:
                g.g_contract_value = 10
            g.g_balance = self.balance_end
        elif (self.strategy_type == 'spot_strategy'):
            g.g_balance_front = self.balance_front
            g.g_balance_end = self.balance_end
            g.g_balance = self.balance_end

        g.g_fee_ratio = self.taker_fee_ratio
        g.g_balance_range = []
        g.g_balance_range.append(g.g_balance)
        g.g_trade_records = []

        try:
            self.bm.count = 0
        except Exception as e:
            print('without bar_manager')

        type_list = []
        timer_type = False
        for i in self.type_list:
            if (i == 'kline'):
                type_list.append(config.HFT_BAR)
            elif ('ticker' == i):
                type_list.append(config.HFT_TICKER)
            elif ('depth' == i):
                type_list.append(config.HFT_DEPTH)
            elif ('depthall' == i):
                type_list.append(config.HFT_DEPTHALL)
            elif ('trade' == i):
                type_list.append(config.HFT_TRADE)
            elif ('timer' in i):
                timer_type = True

        seconds = 60 * 10  # 10 min per period
        for i in range(self.begin_timestamp, self.end_timestamp_hfd, seconds):
            begin_timestamp = i
            end_timestamp = i + seconds
            print('new batch')
            status, hfd_dict_list = dao_quote.get_hfd(self.exchange, self.symbol, type_list, begin_timestamp, end_timestamp)
            print('tick_num: ', len(hfd_dict_list),
                convert.shift_time(begin_timestamp),
                convert.shift_time(end_timestamp))

            for hfd_dict in hfd_dict_list:
                type_ = hfd_dict['t']
                if (type_ == config.HFT_BAR):
                    self.on_bar([[1,2,3,4,5]])
                elif (type_ == config.HFT_TICKER):
                    self.on_tick(hfd_dict)
                elif (type_ == config.HFT_DEPTH):
                    self.on_depth(hfd_dict)
                elif (type_ == config.HFT_DEPTHALL):
                    self.on_depthall(hfd_dict)
                elif (type_ == config.HFT_TRADE):
                    self.on_trade(hfd_dict)
                if (timer_type):
                    ts = time.time()
                    timer_dict = {}
                    timer_dict['ts'] = ts
                    timer_dict['time_now'] = convert.shift_time(ts)
                    self.on_timer(timer_dict)
        return True
