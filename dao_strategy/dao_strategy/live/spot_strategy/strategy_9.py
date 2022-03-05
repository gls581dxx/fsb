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
    from dao_backtest.util import convert
    from dao_backtest.util.quote_manage import (BarManager, BarGenerator)
    from dao_backtest.services.strategy_template import StrategyTemplate


class CtaStrategy(StrategyTemplate):

    author = 'xia0shi'

    def __init__(self, setting_dict):
        self.period = setting_dict.get('period', 30)
        self.offset = self.period
        self.one_time_buy = setting_dict['one_time_buy']
        setting_dict['type_list'] = ['kline', 'timer_3s']
        bar_num = 500
        self.coin_buy_amount = 0
        super().__init__(setting_dict)
        self.stop_loss = 1
        self.status = 'close_long'
        if self.status_dict != {}:
            self.dif_1 = self.status_dict.get('dif_1', 0)
            self.dea_1 = self.status_dict.get('dea_1', 0)
            self.low_price_1 = self.status_dict.get('low_price_1', 0)
            self.dif_2 = self.status_dict.get('dif_2', 0)
            self.dea_2 = self.status_dict.get('dea_2', 0)
            self.low_price_2 = self.status_dict.get('low_price_2', 0)
            self.stop_loss = self.status_dict.get('stop_loss', self.stop_loss)
            self.status = self.status_dict.get('status', 'close_long')
            self.coin_buy_amount = self.status_dict.get('coin_buy_amount', 0)
            self.half_amount = self.status_dict.get('half_amount', 0)
        else:
            self.status = 'close_long'
            self.status_dict = {}
            self.status_dict['status'] = self.status
            self.status_dict['stop_loss'] = self.stop_loss
            self.set_strategy_status_dict(self.status_dict)
        self.bm = BarManager(bar_num)
        self.bg = BarGenerator(self.on_bar, self.period, self.on_xmin_bar)
        self.end_timestr = setting_dict.get('begin_time', convert.shift_time(time.time()))
        # self.end_timestr = '2019-10-01 00:00:00'
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

        timestamp = bar[0]/1000 + 60*self.offset
        time_now = convert.shift_time(timestamp)
        last_price = float(bar[4])
        if (timestamp < self.end_timestamp):
            print(time_now, last_price)
            return None

        low_list = self.bm.low

        price_div_ma_30 = self.bm.price_div_ma(30)
        price_div_ma_60 = self.bm.price_div_ma(60)
        price_div_ma_120 = self.bm.price_div_ma(120)
        dif, dea, macd_line = talib.MACD(self.bm.close)

        if ((price_div_ma_120 > 1) and ((self.status == 'new_begin') or
           (self.status == 'low_price_1') or (self.status == 'low_price_2') or
           (self.status == 'pre_buy'))):
            self.status = 'close_long'
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)

        if ((self.status == 'close_long') and
           (dif[-1] < 0) and (dea[-1] < 0) and (price_div_ma_30 < 1) and
           (price_div_ma_60 < 1) and (price_div_ma_120 < 1)):
            self.status = 'new_begin'
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)

        if (self.status == 'new_begin'):
            self.dif_1 = dif[-1]
            self.dea_1 = dea[-1]
            self.low_price_1 = low_list[-1]
            for j in range(-49, -1):
                try:
                    # 找macd的低点 在此刻--macd金叉之前 找这段时间k线低点 俩低不同时
                    # print('time: {}, kline: {}'.format(g.g_time_now, klines[j]))
                    self.low_price_1 = min(self.low_price_1, low_list[j])
                    self.dif_1 = min(self.dif_1, dif[j])
                    self.dea_1 = min(self.dea_1, dea[j])
                    if (dif[j] > dea[j]) and (dif[j-1] < dea[j-1]):
                        # 这个限制应该去掉更好啊
                        # status = 'low_price_1'
                        # i = j
                        # 后一个低点应该在这个金叉之后寻找
                        break
                except:
                    pass
            self.status = 'low_price_1'
            self.status_dict['dif_1'] = self.dif_1
            self.status_dict['dea_1'] = self.dea_1
            self.status_dict['low_price_1'] = self.low_price_1
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)
        if ((self.status == 'low_price_1') and
           (low_list[-1] < self.low_price_1) and
           (dif[-1] < 0) and (dea[-1] < 0) and (price_div_ma_30 < 1) and
           (price_div_ma_60 < 1) and (price_div_ma_120 < 1)):
            self.low_price_2 = low_list[-1]
            self.dif_2 = dif[-1]
            self.dea_2 = dea[-1]
            self.stop_loss = self.low_price_2
            self.status = 'low_price_2'
            if ((self.dif_2 < self.dif_1) or (self.dea_2 < self.dea_1)):
                self.status = 'close_long'
            self.status_dict['dif_2'] = self.dif_2
            self.status_dict['dea_2'] = self.dea_2
            self.status_dict['low_price_2'] = self.low_price_2
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)
        if ((self.status == 'low_price_2') and
           ((self.dif_2 > self.dif_1) or (self.dea_2 > self.dea_1)) and
           (self.status != 'pre_buy')):
            self.status = 'pre_buy'
            self.reminder()
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)

        if ((self.status == 'pre_buy') and (dif[-1] < dea[-1]) and
           (self.low_price_2 > low_list[-1])):
            self.low_price_2 = low_list[-1]
            # macd的柱子与k线不必一致
            self.dif_2 = dif[-1]
            self.dea_2 = dea[-1]
            if ((self.status == 'pre_buy') and
               ((self.dif_2 < self.dif_1) or (self.dea_2 < self.dea_1))):
                self.status = 'close_long'
                msg = 'status: {}, time: {}'.format(self.status, time_now)
                self.log_msg(msg)
            self.status_dict['dif_2'] = self.dif_2
            self.status_dict['dea_2'] = self.dea_2
            self.status_dict['low_price_2'] = self.low_price_2
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format('change low_price_2', time_now)
            self.log_msg(msg)

        if ((self.status == 'pre_buy') and
           (dif[-1] > dea[-1]) and (dif[-1-1] < dea[-1-1])):
            self.status = 'pre_long'
            order_type = 'buy_market'
            price = last_price
            half_amount = 0
            self.coin_buy_amount = self.one_time_buy/price
            amount = self.coin_buy_amount
            exec_ts = timestamp
            order_rst = self.execute_strategy_order(self.exchange,
                        self.symbol, order_type, price, amount, exec_ts)
            order_id = order_rst['order_id']
            self.stop_loss = self.low_price_2
            self.status_dict['order_id'] = order_id
            self.status_dict['status'] = self.status
            self.status_dict['coin_buy_amount'] = self.coin_buy_amount
            self.status_dict['half_amount'] = half_amount
            self.status_dict['stop_loss'] = self.stop_loss
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)
        if ((self.status == 'going_long') and (price_div_ma_120 > 1)):
            self.status = 'pre_sell'
            order_type = 'sell_market'
            price = last_price
            half_amount = self.coin_buy_amount/2
            amount = half_amount
            exec_ts = timestamp
            order_rst = self.execute_strategy_order(self.exchange,
                        self.symbol, order_type, price, amount, exec_ts)
            order_id = order_rst['order_id']
            self.status_dict['status'] = self.status
            self.status_dict['half_amount'] = half_amount
            self.status_dict['order_id'] = order_id
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)
        elif ((self.status == 'pre_sell') and
            ((dif[-1] < dea[-1]) and (dif[-1-1] > dea[-1-1]))):
            self.status = 'pre_close'
            order_type = 'sell_market'
            price = last_price
            half_amount = self.status_dict['half_amount']
            amount = self.coin_buy_amount - half_amount
            exec_ts = timestamp
            order_rst = self.execute_strategy_order(self.exchange,
                        self.symbol, order_type, price, amount, exec_ts)
            order_id = order_rst['order_id']
            self.status_dict['status'] = self.status
            self.status_dict['order_id'] = order_id
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)
        elif ((self.status == 'going_long') and (last_price < self.stop_loss)):
            self.status = 'pre_close'
            order_type = 'sell_market'
            price = last_price
            half_amount = self.status_dict['half_amount']
            amount = self.coin_buy_amount - half_amount
            exec_ts = timestamp
            order_rst = self.execute_strategy_order(self.exchange,
                        self.symbol, order_type, price, amount, exec_ts)
            order_id = order_rst['order_id']
            self.status_dict['status'] = self.status
            self.status_dict['order_id'] = order_id
            self.set_strategy_status_dict(self.status_dict)
            msg = 'status: {}, time: {}'.format(self.status, time_now)
            self.log_msg(msg)

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
                msg = 'status: {}, time: {}'.format(self.status, time_now)
                self.log_msg(msg)
        elif (self.status == 'pre_close'):
            order_id = self.status_dict['order_id']
            order_rst = self.fetch_orders(self.exchange, self.symbol, order_id)
            order_status = order_rst[0]['order_status']
            if (order_status == 'filled'):
                self.status = 'close_long'
                self.status_dict['status'] = self.status
                self.set_strategy_status_dict(self.status_dict)
                time_now = data['time_now']
                msg = 'status: {}, time: {}'.format(self.status, time_now)
                self.log_msg(msg)
