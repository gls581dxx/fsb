#!/usr/bin/env python
# coding=utf-8

import time
import talib
import numpy as np

try:
    # for live
    from dao_strategy.utils import convert
    from dao_strategy.utils.quote_manage import (BarManager, BarGenerator)
    from dao_strategy.live.strategy_template import StrategyTemplate
except ImportError:
    # for backtest
    from strategy_research.util import convert
    from strategy_research.util.quote_manage import (BarManager, BarGenerator)
    from strategy_research.strategy.strategy_template import StrategyTemplate


class Strategy_7(StrategyTemplate):

    author = 'xia0shi'

    def __init__(self, setting_dict):
        self.period = '1min'
        self.period_list = [self.period]
        period = '1hour'
        self.one_time_buy = setting_dict['one_time_buy']
        setting_dict['type_list'] = ['kline', 'timer_3s']
        super().__init__(setting_dict)
        self.stop_loss = 1
        self.param_1 = setting_dict.get('param_1', 21)
        self.param_1 = int(self.param_1)
        self.param_2 = setting_dict.get('param_2', 2.7)
        self.up_price = 1000000
        self.ordered = 0
        self.status = 'close_long'
        if self.status_dict != {}:
            self.stop_earn = self.status_dict.get('stop_earn', 0)
            self.stop_loss = self.status_dict.get('stop_loss', self.stop_loss)
            self.ordered = self.status_dict.get('ordered', self.ordered)
            self.up_price = self.status_dict.get('up_price', self.up_price)
            self.status = self.status_dict.get('status', 'close_long')
        else:
            self.status = 'close_long'
            self.status_dict = {}
            self.status_dict['status'] = self.status
            self.status_dict['stop_loss'] = self.stop_loss
            self.set_strategy_status_dict(self.status_dict)
        self.bm = BarManager(150)
        self.bg = BarGenerator(self.on_bar, period, self.on_1hour_bar)
        self.end_timestr = setting_dict.get('begin_time', convert.shift_time(time.time()))
        # self.end_timestr = '2019-07-01 00:00:00'
        self.end_timestamp = int(convert.to_timestamp(self.end_timestr))
        self.load_bar(9100, self.end_timestamp)

    def on_bar(self, period, data):
        bar_data = data[-2]
        self.bg.update_bar(bar_data)

        timestamp = data[-1][0]
        if (timestamp == 111333):
            return None
        timestamp = timestamp/1000
        time_now = convert.shift_time(timestamp)
        last_price = float(bar_data[4])
        if (self.status == 'close_long'):
            if ((last_price > self.up_price) and (self.ordered == 0)):
                self.stop_earn = last_price*(1+0.021)
                # self.stop_loss = l1
                self.status = 'pre_long'
                self.ordered = 1
                order_type = 'buy_market'
                price = last_price
                amount = self.one_time_buy/last_price
                exec_ts = timestamp
                order_rst = self.execute_strategy_order(self.exchange,
                            self.symbol, order_type, price, amount, exec_ts)
                order_id = order_rst['order_id']
                self.status_dict['status'] = self.status
                self.status_dict['ordered'] = self.ordered
                self.status_dict['order_id'] = order_id
                self.status_dict['stop_earn'] = self.stop_earn
                self.status_dict['stop_loss'] = self.stop_loss
                msg = '{}, {}, {}, {}'.format(time_now, self.status, self.stop_earn, self.stop_loss)
                self.log_msg(msg)
                self.set_strategy_status_dict(self.status_dict)
        elif (self.status == 'going_long'):
            if (last_price >= self.stop_earn):
                self.status = 'pre_close'
                order_type = 'sell_market'
                price = last_price
                amount = self.one_time_buy/last_price
                exec_ts = timestamp
                order_rst = self.execute_strategy_order(self.exchange,
                            self.symbol, order_type, price, amount, exec_ts)
                order_id = order_rst['order_id']
                self.status_dict['status'] = self.status
                self.status_dict['order_id'] = order_id
                msg = '{}, {}, {}'.format(time_now, 'stop_earn', self.status)
                self.log_msg(msg)
                self.set_strategy_status_dict(self.status_dict)
            elif (last_price <= self.stop_loss):
                self.status = 'pre_close'
                order_type = 'sell_market'
                price = last_price
                amount = self.one_time_buy/last_price
                exec_ts = timestamp
                order_rst = self.execute_strategy_order(self.exchange,
                            self.symbol, order_type, price, amount, exec_ts)
                order_id = order_rst['order_id']
                self.status_dict['status'] = self.status
                self.status_dict['order_id'] = order_id
                msg = '{}, {}, {}'.format(time_now, 'stop_loss', self.status)
                self.log_msg(msg)
                self.set_strategy_status_dict(self.status_dict)

    def on_1hour_bar(self, bar):
        self.bm.update_bar(bar)

        if not self.bm.inited:
            return None

        timestamp = bar[0]/1000 + 60*60
        time_now = convert.shift_time(timestamp)
        last_price = float(bar[4])
        if (timestamp < self.end_timestamp):
            print(time_now, last_price)
            return None

        low_list = self.bm.low

        timeperiod = 11
        l1 = 100000
        for j in range(-timeperiod, -1):
            l1 = min(l1, low_list[j])

        if (self.status == 'close_long'):
            close_list = self.bm.close[-self.param_1:]
            std_value = np.std(close_list)
            mas = np.mean(close_list)
            self.up_price = mas+self.param_2*std_value
            self.stop_loss = l1
            self.ordered = 0
            self.status_dict['ordered'] = self.ordered
            self.status_dict['stop_loss'] = self.stop_loss
            self.status_dict['up_price'] = self.up_price
            self.set_strategy_status_dict(self.status_dict)

        elif (self.status == 'going_long'):
            stop_loss_ = self.stop_loss
            self.stop_loss = max(self.stop_loss, l1)
            self.status_dict['stop_loss'] = self.stop_loss
            msg = '{}, {}, {}'.format(time_now, stop_loss_, self.stop_loss)
            self.log_msg(msg)
            self.set_strategy_status_dict(self.status_dict)

    def on_timer(self, data):
        if (self.status == 'pre_long'):
            order_id = self.status_dict['order_id']
            order_rst = self.fetch_orders(self.exchange, self.symbol, order_id)
            order_status = order_rst[0]['order_status']
            if (order_status == 'filled'):
                self.status = 'going_long'
                self.status_dict['status'] = self.status
                self.set_strategy_status_dict(self.status_dict)
                time_now = data['time_now']
                msg = '{}, {}'.format(time_now, self.status)
                self.log_msg(msg)
        elif (self.status == 'pre_close'):
            order_id = self.status_dict['order_id']
            if (order_id != 0):
                order_rst = self.fetch_orders(self.exchange, self.symbol, order_id)
                order_status = order_rst[0]['order_status']
            elif (order_id == 0):
                order_status = 'filled'
            if (order_status == 'filled'):
                self.status = 'close_long'
                self.status_dict['status'] = self.status
                self.set_strategy_status_dict(self.status_dict)
                time_now = data['time_now']
                msg = '{}, {}'.format(time_now, self.status)
                self.log_msg(msg)
