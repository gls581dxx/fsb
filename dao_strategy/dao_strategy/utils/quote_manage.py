import copy
import talib
import datetime
import numpy as np


class BarManager(object):

    def __init__(self, length=100):
        self.count = 0
        self.length = length
        self.inited = False

        init_list = np.zeros(length)

        self.bar_list = [[1, 1, 1, 1, 1, 1]] * length
        self.ts_list = copy.deepcopy(init_list)
        self.open_list = copy.deepcopy(init_list)
        self.high_list = copy.deepcopy(init_list)
        self.low_list = copy.deepcopy(init_list)
        self.close_list = copy.deepcopy(init_list)
        self.volume_list = copy.deepcopy(init_list)

    def update_bar(self, bar):
        if (self.bar_list[-1][0] == bar[0]):
            return None
        self.count += 1
        if not self.inited and self.count >= self.length:
            self.inited = True

        self.bar_list[:-1] = self.bar_list[1:]
        self.ts_list[:-1] = self.ts_list[1:]
        self.open_list[:-1] = self.open_list[1:]
        self.high_list[:-1] = self.high_list[1:]
        self.low_list[:-1] = self.low_list[1:]
        self.close_list[:-1] = self.close_list[1:]
        self.volume_list[:-1] = self.volume_list[1:]

        self.bar_list[-1] = bar
        self.ts_list[-1] = bar[0]
        self.open_list[-1] = bar[1]
        self.high_list[-1] = bar[2]
        self.low_list[-1] = bar[3]
        self.close_list[-1] = bar[4]
        self.volume_list[-1] = bar[5]

    @property
    def bars(self):
        return self.bar_list

    @property
    def timestamps(self):
        return self.ts_list

    @property
    def open(self):
        return self.open_list

    @property
    def high(self):
        return self.high_list

    @property
    def low(self):
        return self.low_list

    @property
    def close(self):
        return self.close_list

    @property
    def volume(self):
        return self.volume_list

    def ma(self, n, array=False):
        result = talib.MA(self.close, n)
        if array:
            return result
        return result[-1]

    def macd(self, fast_period, slow_period, signal_period, array=False):
        macd, signal, hist = talib.MACD(
            self.close, fast_period, slow_period, signal_period
        )
        if array:
            return macd, signal, hist
        return macd[-1], signal[-1], hist[-1]

    def atr(self, timeperiod, array=False):
        result = talib.ATR(self.high, self.low, self.close, timeperiod)
        if array:
            return result
        return result[-1]

    def rsi(self, timeperiod, array=False):
        result = talib.RSI(self.close, timeperiod)
        if array:
            return result
        return result[-1]

    def rsi_open(self, timeperiod, array=False):
        result = talib.RSI(self.open, timeperiod)
        if array:
            return result
        return result[-1]

    def rsi_high(self, timeperiod, array=False):
        result = talib.RSI(self.high, timeperiod)
        if array:
            return result
        return result[-1]

    def rsi_low(self, timeperiod, array=False):
        result = talib.RSI(self.low, timeperiod)
        if array:
            return result
        return result[-1]

    def price_div_ma(self, param, array=False):
        if not array:
            close_list = self.close[-param:]
            mean_value = np.mean(close_list)
            result = close_list[-1] / mean_value
        elif array:
            ma_array = talib.MA(self.close, param)
            result = self.close / ma_array
        return result


class BarGenerator(object):

    def __init__(self, on_bar, period, on_x_bar, offset_bar=0):
        self.bar = None
        self.x_bar = None
        self.on_bar = on_bar
        self.offset_bar = offset_bar + 1
        period = str(period)
        if ('min' in period):
            k_bars = int(period.split('min')[0])
        elif ('hour' in period):
            k_bars = int(period.split('hour')[0]) * 60
        else:
            k_bars = int(period)
        self.k_bars = k_bars
        self.on_x_bar = on_x_bar

        self.last_tick = None
        self.last_bar = None

    def update_tick(self, tick_data):
        new_minute = False

        if not tick_data['last']:
            return None

        if not self.bar:
            new_minute = True
        elif int(self.bar[0]/60000) != int(tick_data['ts']/60000):
            self.on_bar(self.bar)
            new_minute = True

        if new_minute:
            self.bar = [int(tick_data['ts']/60000) * 60000,
                        float(tick_data['last']),
                        float(tick_data['last']),
                        float(tick_data['last']),
                        float(tick_data['last']),
                        0.0]
        else:
            self.bar[2] = max(self.bar[2], float(tick_data['last']))
            self.bar[3] = min(self.bar[3], float(tick_data['last']))
            self.bar[4] = float(tick_data['last'])

        if self.last_tick:
            volume_change = float(tick_data['vol']) - float(self.last_tick['vol'])
            self.bar[5] += max(volume_change, 0)

        self.last_tick = tick_data

    def update_bar(self, bar_data):
        """
        Update 1 minute bar into generator
        """
        timestamp = bar_data[0] / 1000
        bar_dt = datetime.datetime.fromtimestamp(timestamp)

        if not self.x_bar:
            self.x_bar = bar_data
            self.x_bar.append(bar_dt)
        else:
            self.x_bar[2] = max(self.x_bar[2], bar_data[2])
            self.x_bar[3] = min(self.x_bar[3], bar_data[3])
            self.x_bar[5] += float(bar_data[5])

        self.x_bar[4] = bar_data[4]

        finished = False
        if not (bar_dt.minute + self.offset_bar) % self.k_bars:
            finished = True

        if finished:
            self.x_bar.pop(-1)
            self.on_x_bar(self.x_bar)
            self.x_bar = None


class TradeManager(object):

    def __init__(self, length=100):
        self.count = 0
        self.length = length
        self.inited = False

        init_list = np.zeros(length)

        self.bar_list = [[0, 0, 0]] * length
        self.ts_list = copy.deepcopy(init_list)
        self.buy_list = copy.deepcopy(init_list)
        self.sell_list = copy.deepcopy(init_list)

    def update_bar(self, bar):
        if (self.bar_list[-1][0] == bar[0]):
            return None
        self.count += 1
        if not self.inited and self.count >= self.length:
            self.inited = True

        self.bar_list[:-1] = self.bar_list[1:]
        self.ts_list[:-1] = self.ts_list[1:]
        self.buy_list[:-1] = self.buy_list[1:]
        self.sell_list[:-1] = self.sell_list[1:]

        self.bar_list[-1] = bar
        self.ts_list[-1] = bar[0]
        self.buy_list[-1] = bar[1]
        self.sell_list[-1] = bar[2]


class TradeGenerator(object):

    def __init__(self, on_bar, period, on_x_bar):
        self.basic_period = 60 * 1000
        self.bar = None
        self.x_bar = None
        self.on_bar = on_bar
        period = str(period)
        if ('s' in period):
            k_bars = int(period.split('s')[0])
            self.basic_period = k_bars * 1000
        elif ('min' in period):
            k_bars = int(period.split('min')[0]) * 60
        elif ('hour' in period):
            k_bars = int(period.split('hour')[0]) * 60 * 60
        else:
            k_bars = int(period) * 60
        self.k_bars = k_bars
        self.on_x_bar = on_x_bar

        self.get_tick_type_dict()
        self.get_handicap_dict()
        self.last_tick = None
        self.last_bar = None

    def analysis_tick(self, tick_data):
        trade_dict = {}
        if self.last_tick:
            last_vol = self.last_tick['vol']
            vol = tick_data['vol']
            last_inst = self.last_tick['inst']
            inst = tick_data['inst']

            ask_price_delta = self.get_delta(self.last_tick['ask'], tick_data['ask'])
            ask_vol_delta = self.get_delta(self.last_tick['a_v'], tick_data['a_v'])
            bid_price_delta = self.get_delta(self.last_tick['bid'], tick_data['bid'])
            bid_vol_delta = self.get_delta(self.last_tick['b_v'], tick_data['b_v'])
            last_price_delta = self.get_delta(self.last_tick['last'], tick_data['last'])
            volume_delta = self.get_delta(self.last_tick['vol'], tick_data['vol'])
            inst_delta = self.get_delta(self.last_tick['inst'], tick_data['inst'])

            order_forward = self.get_order_forward(
                tick_data['last'], tick_data['ask'],
                tick_data['bid'], self.last_tick['last'],
                self.last_tick['ask'], self.last_tick['bid'])
            open_interest_delta_forward = self.get_open_interest_delta_forward(inst_delta, volume_delta)
            tick_type = self.tick_type_dict[open_interest_delta_forward][order_forward]
            # userful later
            ts = datetime.datetime.fromtimestamp(tick_data['ts']/1000)
            if (open_interest_delta_forward != 'none'):
                # ask_price_delta_str = self.get_delta_str(self.last_tick['ask'], tick_data['ask'])
                # ask_vol_delta_str = self.get_delta_str(self.last_tick['a_v'], tick_data['a_v'])
                # bid_price_delta_str = self.get_delta_str(self.last_tick['bid'], tick_data['bid'])
                # bid_vol_delta_str = self.get_delta_str(self.last_tick['b_v'], tick_data['b_v'])
                # last_price_delta_str = self.get_delta_str(self.last_tick['last'], tick_data['last'])
                # if ask_price_delta != 0:
                #     ask_vol_delta_str = ''
                # if bid_price_delta != 0:
                #     bid_vol_delta_str = ''
                # print('ask {}, {}, {}, {} | bid: {}, {}, {}, {}'.format(
                #     tick_data['ask'], ask_price_delta_str, tick_data['a_v'], ask_vol_delta_str,
                #     tick_data['bid'], bid_price_delta_str, tick_data['b_v'], bid_vol_delta_str))
                #
                # print('ts: {}, last: {}{}, trade: {}, add: {}, {},{}'.format(
                #     ts, tick_data['last'], last_price_delta_str, volume_delta,
                #     inst_delta, tick_type[0], tick_type[1]))

                if ask_price_delta != 0:
                    ask_vol_delta = 0
                if bid_price_delta != 0:
                    bid_vol_delta = 0
                tick_type_type = tick_type[0]
                tick_type_color = tick_type[1]

                trade_dict['ts'] = tick_data['ts']
                trade_dict['ask_price_delta'] = ask_price_delta
                trade_dict['ask_vol_delta'] = ask_vol_delta
                trade_dict['bid_price_delta'] = bid_price_delta
                trade_dict['bid_vol_delta'] = bid_vol_delta
                trade_dict['last_price_delta'] = last_price_delta
                trade_dict['volume_delta'] = volume_delta
                trade_dict['inst_delta'] = inst_delta
                trade_dict['tick_type_type'] = tick_type_type
                trade_dict['tick_type_color'] = tick_type_color
                trade_dict['match_order'] = {}

                if (tick_type_type in self.handicap_dict.keys()):
                    order_opposite, order_similar = self.get_order_combination(inst_delta, volume_delta)
                    opposite_type = self.handicap_dict[tick_type_type]['opposite']
                    similar_type = self.handicap_dict[tick_type_type]['similar']
                    trade_dict['match_order']['opposite_type'] = opposite_type
                    trade_dict['match_order']['opposite_num'] = order_opposite
                    trade_dict['match_order']['similar_type'] = similar_type
                    trade_dict['match_order']['similar_num'] = order_similar
                    # print('match_order: {} {}, {} {}'.format(opposite_type, order_opposite, similar_type, order_similar))
        self.last_tick = tick_data
        return trade_dict

    def update_trade(self, trade_dict):
        new_minute = False

        if not trade_dict['price']:
            return None

        if not self.bar:
            new_minute = True
        elif int(self.bar[0]/self.basic_period) != int(trade_dict['ts']/self.basic_period):
            self.on_bar(self.bar)
            new_minute = True

        side = trade_dict['side']
        size = float(trade_dict['size'])
        if new_minute:
            self.bar = [int(trade_dict['ts']/self.basic_period) * self.basic_period,
                        0,
                        0]
            if (side == 'buy'):
                self.bar[1] = size
            elif (side == 'sell'):
                self.bar[2] = size
            else:
                pass
        else:
            if (side == 'buy'):
                self.bar[1] += size
            elif (side == 'sell'):
                self.bar[2] += size
            else:
                pass

    def update_bar(self, bar_data):
        """
        Update 1 minute bar into generator
        """
        timestamp = bar_data[0] / 1000
        bar_dt = datetime.datetime.fromtimestamp(timestamp)

        if not self.x_bar:
            self.x_bar = bar_data
            self.x_bar.append(bar_dt)
        else:
            self.x_bar[1] += float(bar_data[1])
            self.x_bar[2] += float(bar_data[2])

        finished = False
        if not (bar_dt.minute + 1) % self.k_bars:
            finished = True

        if finished:
            self.x_bar.pop(-1)
            self.on_x_bar(self.x_bar)
            self.x_bar = None

    def float_ge(self, greater, smaller):
        rst = False
        if abs(greater - smaller) < 0.00001:
            rst = True
        elif greater > smaller:
            rst = True
        return rst

    def float_le(self, smaller, greater):
        return self.float_ge(greater, smaller)

    def get_delta(self, pre, num):
        delta = num - pre
        return delta

    def get_delta_str(self, pre, num):
        delta_str = ''
        if num > pre:
            delta_str = '(+' + str(num - pre) + ")"
        elif num < pre:
            delta_str = '(-' + str(pre - num) + ")"
        else:
            pass
        return delta_str

    def get_order_forward(self, last_price, ask_price1, bid_price1, pre_last_price, pre_ask_price1, pre_bid_price1):
        if self.float_ge(last_price, pre_ask_price1):
            local_order_forward = 'up'
        elif not self.float_le(last_price, pre_bid_price1):
            local_order_forward = 'down'
        else:
            if self.float_ge(last_price, ask_price1):
                local_order_forward = 'up'
            elif self.float_le(last_price, bid_price1):
                local_order_forward = 'down'
            else:
                local_order_forward = 'middle'
        return local_order_forward

    def get_open_interest_delta_forward(self, open_interest_delta, volume_delta):
        local_open_interest_delta_forward = 'none'
        if open_interest_delta == 0 and volume_delta == 0:
            local_open_interest_delta_forward = 'none'
        elif open_interest_delta == 0 and volume_delta > 0:
            local_open_interest_delta_forward = 'ex'
        elif open_interest_delta > 0:
            if open_interest_delta - volume_delta == 0:
                local_open_interest_delta_forward = 'open_double'
            else:
                local_open_interest_delta_forward = 'open'
        elif open_interest_delta < 0:
            if open_interest_delta + volume_delta == 0:
                local_open_interest_delta_forward = 'close_double'
            else:
                local_open_interest_delta_forward = 'close'
        return local_open_interest_delta_forward

    def get_order_combination(self, open_interest_delta, volume_delta):
        open_interest_delta = open_interest_delta if open_interest_delta > 0 else -open_interest_delta
        volume_delta_single_side = volume_delta / 2.0
        open_close_delta = open_interest_delta - volume_delta_single_side + 0.0
        order_similar = volume_delta_single_side / 2 + open_close_delta / 2
        order_opposite = volume_delta_single_side / 2 - open_close_delta / 2
        return int(order_opposite), int(order_similar)

    def get_tick_type_dict(self):
        self.tick_type_dict = {}
        self.tick_type_dict['none'] = {
            'up': ('no_change', 'white'),
            'down': ('no_change', 'white'),
            'middle': ('no_change', 'white')
        }
        self.tick_type_dict['ex'] = {
            'up': ('ex_long', 'red'),
            'down': ('ex_short', 'green'),
            'middle': ('ex_none', 'white')
        }
        self.tick_type_dict['open_double'] = {
            'up': ('open_double', 'red'),
            'down': ('open_double', 'green'),
            'middle': ('open_double', 'white')
        }
        self.tick_type_dict['open'] = {
            'up': ('open_long', 'red'),
            'down': ('open_short', 'green'),
            'middle': ('open_none', 'white')
        }
        self.tick_type_dict['close_double'] = {
            'up': ('close_double', 'red'),
            'down': ('close_double', 'green'),
            'middle': ('close_double', 'white')
        }
        self.tick_type_dict['close'] = {
            'up': ('close_short', 'red'),
            'down': ('close_long', 'green'),
            'middle': ('close_none', 'white')
        }
        return None

    def get_handicap_dict(self):
        self.handicap_dict = {}
        self.handicap_dict['open_long'] = {
            'opposite': 'close_long',
            'similar': 'open_short'
        }
        self.handicap_dict['open_short'] = {
            'opposite': 'close_short',
            'similar': 'open_long'
        }
        self.handicap_dict['close_long'] = {
            'opposite': 'open_long',
            'similar': 'close_short'
        }
        self.handicap_dict['close_short'] = {
            'opposite': 'open_short',
            'similar': 'close_long'
        }
        return None
