#!/usr/bin/env python
# coding=utf-8

import time
import talib
import traceback
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


class CtaStrategy(DirTemplate):

    author = 'xia0shi'

    def __init__(self, setting_dict):
        '''OKB_USDT HFT
        '''
        self.period = setting_dict.get('period', 3)
        self.one_time_buy = setting_dict['one_time_buy']
        setting_dict['type_list'] = ['ticker', 'depth']
        self.jump = 0.0001
        self.large_vol = 1100
        self.stop_vol = 100
        self.profit_ratio = 0.0017
        bar_num = 50
        super().__init__(setting_dict)
        self.stop_loss = 1
        self.status = 'close_short'
        self.recent_high_status = False
        if self.status_dict != {}:
            self.order_id = self.status_dict.get('order_id', 0)
            self.stop_loss = self.status_dict.get('stop_loss', self.stop_loss)
            self.stop_earn = self.status_dict.get('stop_earn', 100)
            self.open_price = self.status_dict.get('open_price', 2.95)
            self.status = self.status_dict.get('status', 'close_short')
            self.recent_high_status = self.status_dict.get('recent_high_status', False)
            self.coin_num = self.status_dict.get('coin_num', 83)
        else:
            self.status = 'close_short'
            self.status_dict = {}
            self.coin_num = self.status_dict.get('coin_num', 83)
            self.status_dict['status'] = self.status
            self.set_strategy_status_dict(self.status_dict)
        self.bm = BarManager(bar_num)
        self.bg = BarGenerator(self.on_bar_local, self.period, self.on_xmin_bar)

    def get_recent_high(self, bars, jump):
        high_list = [i[2] for i in bars[-4:-1]]
        recent_high = max(high_list)
        for high in high_list:
            if (high % jump > 2):
                recent_high_status = False
                return recent_high_status, recent_high
        recent_high_status = True
        return recent_high_status, recent_high

    def on_bar_local(self, bar):
        self.bg.update_bar(bar)
        self.bm.update_bar(bar)

        if not self.bm.inited:
            return None
        self.on_bar(self.bm.bars)

    def on_xmin_bar(self, bar):
        pass

    def on_bar(self, data):
        self.recent_high_status, self.recent_high = self.get_recent_high(
                                                    data, self.jump)
        try:
            timestamp = data[-1][0]/1000
            last_price = data[-1][4]

            balance_dict = self.get_account(self.exchange, self.symbol)
            coin_num = balance_dict['coin']['balance']
            # basecoin_num = balance_dict['data']['basecoin']['balance']
            coin_diff = coin_num - self.coin_num
            if (coin_diff > 0.5*self.one_time_buy):
                exchange = self.exchange
                symbol = self.symbol
                order_type = 'sell_limit'
                price = last_price + self.jump*1
                amount = self.one_time_buy
                exec_ts = timestamp
                order_rst = self.execute_strategy_order(exchange, symbol,
                            order_type, price, amount, exec_ts)
                order_id = order_rst['order_id']
                time_now = convert.shift_time(timestamp)
                msg = 'status: {}, time: {}'.format('balance position sell_limit', time_now)
                self.log_msg(msg)
                time.sleep(10)
                rst = self.cancel_order(self.exchange, self.symbol, order_id)
                msg = 'status: {}, {}, time: {}, rst: {}'.format('cancel_order on_bar', order_id, time_now, rst)
                self.log_msg(msg)
            elif (coin_diff < -1.5*self.one_time_buy):
                exchange = self.exchange
                symbol = self.symbol
                order_type = 'buy_limit'
                price = last_price - self.jump*1
                amount = self.one_time_buy
                exec_ts = timestamp
                order_rst = self.execute_strategy_order(exchange, symbol,
                            order_type, price, amount, exec_ts)
                order_id = order_rst['order_id']
                time_now = convert.shift_time(timestamp)
                msg = 'status: {}, time: {}'.format('balance position buy_limit', time_now)
                self.log_msg(msg)
                time.sleep(10)
                rst = self.cancel_order(self.exchange, self.symbol, order_id)
                msg = 'status: {}, {}, time: {}, rst: {}'.format('cancel_order on_bar', order_id, time_now, rst)
                self.log_msg(msg)
        except Exception as e:
            log_msg = traceback.format_exc()
            msg = 'on_bar, {}'.format(log_msg)
            self.log_msg(msg)
        return None

    def on_tick(self, data):
        self.bg.update_tick(data)
        self.on_listen = False
        try:
            if (self.status == 'pre_short'):
                time.sleep(1)
                order_id = self.status_dict['order_id']
                order_rst = self.fetch_order_ex(self.exchange, self.symbol, order_id)
                order_status = order_rst[0]['order_status']
                if (order_status == 'filled'):
                    self.status = 'going_short'
                    self.status_dict['status'] = self.status
                    self.set_strategy_status_dict(self.status_dict)
                    timestamp = data['ts']/1000
                    time_now = convert.shift_time(timestamp)
                    msg = 'status: {}, time: {}'.format(self.status, time_now)
                    self.log_msg(msg)
                elif (order_status == 'pending'):
                    last_price = float(data['last'])
                    if (((not self.recent_high_status) and (last_price < self.open_price - self.jump*15)) or
                       (last_price < self.open_price - self.jump*35)):
                        timestamp = data['ts']/1000
                        time_now = convert.shift_time(timestamp)
                        time.sleep(1)
                        rst = self.cancel_order(self.exchange, self.symbol, order_id)
                        msg = 'status: {}, {}, time: {}, rst: {}'.format('cancel_order on_tick pre_short pending', order_id, time_now, rst)
                        self.log_msg(msg)
                        time.sleep(1.5)
                        order_rst = self.fetch_order_ex(self.exchange, self.symbol, order_id)
                        quantity_treaded = order_rst[0].get('quantity_treaded', 0)
                        amount = quantity_treaded
                        if (amount == 0):
                            self.status = 'close_short'
                        elif (0< amount <1):
                            self.status = 'close_short'
                        else:
                            exchange = self.exchange
                            symbol = self.symbol
                            order_type = 'buy_limit'
                            price = self.open_price
                            exec_ts = timestamp
                            order_rst = self.execute_strategy_order(exchange, symbol,
                                        order_type, price, amount, exec_ts)
                            order_id = order_rst['order_id']
                            self.status = 'pre_close'
                            self.status_dict['order_id'] = order_id
                        self.status_dict['status'] = self.status
                        self.set_strategy_status_dict(self.status_dict)
                        msg = 'status: {}, amount: {}, time: {}'.format(self.status, amount, time_now)
                        self.log_msg(msg)
                    time.sleep(3)
                elif (order_status == 'cancelled'):
                    timestamp = data['ts']/1000
                    time_now = convert.shift_time(timestamp)
                    self.status = 'close_short'
                    self.status_dict['status'] = self.status
                    self.set_strategy_status_dict(self.status_dict)
                    msg = 'status: {}, time: {}'.format(self.status, time_now)
                    self.log_msg(msg)
                else:
                    time.sleep(3)
            elif (self.status == 'pre_close'):
                time.sleep(0.5)
                order_id = self.status_dict['order_id']
                order_rst = self.fetch_order_ex(self.exchange, self.symbol, order_id)
                order_status = order_rst[0]['order_status']
                if (order_status == 'filled'):
                    self.status = 'close_short'
                    self.status_dict['status'] = self.status
                    self.set_strategy_status_dict(self.status_dict)
                    timestamp = data['ts']/1000
                    time_now = convert.shift_time(timestamp)
                    msg = 'status: {}, time: {}'.format(self.status, time_now)
                    self.log_msg(msg)
                else:
                    last_price = float(data['last'])
                    if (last_price > self.stop_loss):
                        timestamp = data['ts']/1000
                        time_now = convert.shift_time(timestamp)
                        self.status = 'pre_close'
                        rst = self.cancel_order(self.exchange, self.symbol, order_id)
                        msg = 'status: {}, {}, time: {}, rst: {}'.format('cancel_order on_tick pre_close stop_loss', order_id, time_now, rst)
                        self.log_msg(msg)
                        time.sleep(1.5)
                        order_rst = self.fetch_order_ex(self.exchange, self.symbol, order_id)
                        quantity_treaded = order_rst[0].get('quantity_treaded', 0)
                        amount = self.one_time_buy - quantity_treaded
                        if (amount == 0):
                            self.status = 'close_short'
                        elif (0< amount <1):
                            self.status = 'close_short'
                        else:
                            exchange = self.exchange
                            symbol = self.symbol
                            order_type = 'buy_market'
                            price = self.stop_earn
                            exec_ts = timestamp
                            order_rst = self.execute_strategy_order(exchange, symbol,
                                        order_type, price, amount, exec_ts)
                            order_id = order_rst['order_id']
                            self.status = 'pre_close'
                            self.status_dict['order_id'] = order_id
                            time.sleep(30)
                        self.status_dict['status'] = self.status
                        self.set_strategy_status_dict(self.status_dict)
                        msg = 'status: {}, time: {}'.format(self.status, time_now)
                        self.log_msg(msg)
                    time.sleep(3)
            elif (self.status == 'going_short'):
                self.status = 'pre_close'
                timestamp = data['ts'] / 1000
                time_now = convert.shift_time(timestamp)

                exchange = self.exchange
                symbol = self.symbol
                order_type = 'buy_limit'
                price = self.stop_earn
                amount = self.one_time_buy
                exec_ts = timestamp
                order_rst = self.execute_strategy_order(exchange, symbol,
                            order_type, price, amount, exec_ts)
                order_id = order_rst['order_id']
                self.status_dict['order_id'] = order_id
                self.status_dict['status'] = self.status
                self.set_strategy_status_dict(self.status_dict)
                msg = 'status: {}, time: {}'.format(self.status, time_now)
                self.log_msg(msg)
            else:
                pass
        except Exception as e:
            log_msg = traceback.format_exc()
            msg = 'on_tick, {}'.format(log_msg)
            self.log_msg(msg)
        time.sleep(0.1)
        self.on_listen = True
        return None

    def on_depth(self, data):
        self.on_listen = False
        try:
            ask_vol = 0
            data['asks'].reverse()
            ask_1 = float(data['asks'][0][0])
            ask_2 = float(data['asks'][1][0])
            for i in range(0, 2):
                ask_vol += float(data['asks'][i][1])

            if (self.status == 'close_short'):
                if not self.recent_high_status:
                    self.on_listen = True
                    return None
                if (ask_vol <= self.large_vol):
                    self.on_listen = True
                    return None
                self.status = 'pre_short'
                timestamp = data['ts'] / 1000
                time_now = convert.shift_time(timestamp)

                self.ask_2 = ask_2

                self.open_price = ask_1 - self.jump
                exchange = self.exchange
                symbol = self.symbol
                order_type = 'sell_limit'
                price = self.open_price
                amount = self.one_time_buy
                exec_ts = timestamp
                order_rst = self.execute_strategy_order(exchange, symbol,
                            order_type, price, amount, exec_ts)
                order_id = order_rst['order_id']
                self.stop_earn = self.open_price * (1 - self.profit_ratio)
                self.stop_loss = self.recent_high + self.jump * 5
                self.status_dict['order_id'] = order_id
                self.status_dict['status'] = self.status
                self.status_dict['open_price'] = self.open_price
                self.status_dict['stop_earn'] = self.stop_earn
                self.status_dict['stop_loss'] = self.stop_loss
                self.set_strategy_status_dict(self.status_dict)
                msg = 'status: {}, time: {}'.format(self.status, time_now)
                self.log_msg(msg)
                time.sleep(3)
            elif (self.status == 'pre_short'):
                order_id = self.status_dict['order_id']
                order_rst = self.fetch_order_ex(self.exchange, self.symbol, order_id)
                order_status = order_rst[0]['order_status']
                if (order_status == 'filled'):
                    self.status = 'going_short'
                    self.status_dict['status'] = self.status
                    self.set_strategy_status_dict(self.status_dict)
                    timestamp = data['ts']/1000
                    time_now = convert.shift_time(timestamp)
                    msg = 'status: {}, time: {}'.format(self.status, time_now)
                    self.log_msg(msg)
                elif (order_status == 'pending'):
                    if ((ask_vol > self.large_vol/2) and (ask_1 >= self.open_price+self.jump*2)):
                        timestamp = data['ts'] / 1000
                        time_now = convert.shift_time(timestamp)
                        time.sleep(1)
                        rst = self.cancel_order(self.exchange, self.symbol, order_id)
                        msg = 'status: {}, {}, time: {}, rst: {}'.format('cancel_order', order_id, time_now, rst)
                        self.log_msg(msg)
                        time.sleep(1.5)
                        order_rst = self.fetch_order_ex(self.exchange, self.symbol, order_id)
                        # quantity = order_rst[0].get('quantity', 0)
                        quantity_treaded = order_rst[0].get('quantity_treaded', 0)
                        amount = quantity_treaded
                        if (amount == 0):
                            self.status = 'close_short'
                        elif (0< amount <1):
                            self.status = 'close_short'
                        else:
                            self.open_price = ask_1 - self.jump
                            exchange = self.exchange
                            symbol = self.symbol
                            order_type = 'sell_limit'
                            price = self.open_price
                            exec_ts = timestamp
                            order_rst = self.execute_strategy_order(exchange, symbol,
                                        order_type, price, amount, exec_ts)
                            order_id = order_rst['order_id']
                            self.status = 'pre_short'
                            self.status_dict['order_id'] = order_id
                        self.status_dict['status'] = self.status
                        self.set_strategy_status_dict(self.status_dict)
                        msg = 'status: {}, amount: {}, time: {}'.format(self.status, amount, time_now)
                        self.log_msg(msg)
                    time.sleep(3)
            elif (self.status in ['going_short', 'pre_close']):
                ask_vol = 0
                for ask_list in data['asks']:
                    ask_vol += float(ask_list[1])
                    if (ask_list[0] > self.ask_2):
                        break
                if (ask_vol < self.stop_vol):
                    timestamp = data['ts']/1000
                    time_now = convert.shift_time(timestamp)
                    self.status = 'pre_close'
                    order_id = self.status_dict['order_id']
                    rst = self.cancel_order(self.exchange, self.symbol, order_id)
                    msg = 'status: {}, {}, time: {}, rst: {}'.format('cancel_order on_depth going_short stop_vol', order_id, time_now, rst)
                    self.log_msg(msg)
                    time.sleep(1.5)
                    order_rst = self.fetch_order_ex(self.exchange, self.symbol, order_id)
                    quantity_treaded = order_rst[0].get('quantity_treaded', 0)
                    amount = self.one_time_buy - quantity_treaded
                    if (amount == 0):
                        self.status = 'close_short'
                    elif (0< amount <1):
                        self.status = 'close_short'
                    else:
                        exchange = self.exchange
                        symbol = self.symbol
                        order_type = 'buy_market'
                        price = self.stop_earn
                        exec_ts = timestamp
                        order_rst = self.execute_strategy_order(exchange, symbol,
                                    order_type, price, amount, exec_ts)
                        order_id = order_rst['order_id']
                        self.status = 'pre_close'
                        self.status_dict['order_id'] = order_id
                        time.sleep(30)
                    self.status_dict['status'] = self.status
                    self.set_strategy_status_dict(self.status_dict)
                    msg = 'status: {}, time: {}'.format(self.status, time_now)
                    self.log_msg(msg)
                time.sleep(1)
            else:
                time.sleep(3)
        except Exception as e:
            log_msg = traceback.format_exc()
            msg = 'on_tick, {}'.format(log_msg)
            self.log_msg(msg)
        time.sleep(0.1)
        self.on_listen = True
        return None
