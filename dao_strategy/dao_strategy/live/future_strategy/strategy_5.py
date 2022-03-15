#!/usr/bin/env python
# coding=utf-8

import time
import talib
import numpy as np

from . import (convert, BarManager, BarGenerator, StrategyTemplate)


class CtaStrategy(StrategyTemplate):

    author = 'greatshi'

    def __init__(self, setting_dict):
        '''
        test trading system
        '''
        self.period = setting_dict.get('period', 3)
        self.offset = self.period
        self.one_time_buy = setting_dict['one_time_buy']
        setting_dict['type_list'] = ['kline', 'timer_3s']
        bar_num = 10
        super().__init__(setting_dict)

        self.counter = 1
        self.status = 'close_long'
        if self.status_dict != {}:
            self.status = self.status_dict.get('status', 'close_long')
        else:
            self.status = 'close_long'
            self.status_dict = {}
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
        self.bm = BarManager(bar_num)
        self.bg = BarGenerator(self.on_bar, self.period, self.on_xmin_bar)
        self.end_timestr = setting_dict.get('begin_time', convert.shift_time(time.time()))
        self.end_timestamp = int(convert.to_timestamp(self.end_timestr))
        self.load_bar((bar_num + 1) * self.offset, self.end_timestamp)

    def on_bar(self, data):
        bar_data = data[-2]
        self.bg.update_bar(bar_data)
        timestamp = data[-1][0]
        if (timestamp == 111333):
            return None

    def on_xmin_bar(self, bar):
        self.bm.update_bar(bar)

        if not self.bm.inited:
            return None

        if not self.ctp_time_filter():
            return None

        timestamp = bar[0]/1000 + 60*self.offset
        time_now = convert.shift_time(timestamp)
        last_price = float(bar[4])
        if (timestamp < self.end_timestamp):
            print(time_now, last_price)
            return None

        if (self.status == 'close_long'):
            if self.counter > 4:
                return None
            self.status = 'pre_long'
            order_type = 'market_going_long'
            price = last_price
            half_amount = 0
            amount = self.one_time_buy
            exec_ts = timestamp
            order_rst = self.execute_strategy_order(self.exchange,
                        self.symbol, order_type, price, amount, exec_ts)
            order_id = order_rst['order_id']
            self.status_dict['order_id'] = order_id
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)
        elif (self.status == 'going_long'):
            self.status = 'pre_close'
            order_type = 'market_close_long'
            price = last_price
            amount = self.one_time_buy
            exec_ts = timestamp
            order_rst = self.execute_strategy_order(self.exchange,
                        self.symbol, order_type, price, amount, exec_ts)
            order_id = order_rst['order_id']
            self.status_dict['status'] = self.status
            self.status_dict['order_id'] = order_id
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)
        self.counter += 1


    def on_timer(self, data):
        if ('pre_' in self.status):
            order_id = self.status_dict['order_id']
            order_rst = self.fetch_orders(self.exchange, self.symbol, order_id)
            order_status = order_rst[0]['order_status']
            if (self.status == 'pre_long'):
                if (order_status == 'filled'):
                    self.status = 'going_long'
                elif (order_status == 'cancelled'):
                    self.status = 'close_long'
            elif (self.status == 'pre_close'):
                if (order_status == 'filled'):
                    self.status = 'close_long'
                elif (order_status == 'cancelled'):
                    self.status = 'going_long'
            if (pre_self_status != self.status):
                self.status_dict['status'] = self.status
                self.set_strategy_status_dict(self.status_dict)
                time_now = data['time_now']
                msg = 'status: {}, time: {}'.format(self.status, time_now)
                self.log_msg(msg)
