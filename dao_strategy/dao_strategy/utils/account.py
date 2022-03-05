import re
import ast

from dao_strategy.db.dt_models import Order
from dao_strategy.settings.config import cfg
from dao_strategy.rpc.dao_quote import DaoQuote


class Account(object):

    def get_future_future_strategy_position(self, strategy_instance):
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        symbol = strategy_instance['symbol']
        symbol_2 = strategy_instance['symbol_2']
        orders = Order.objects.filter(user_id=user_id,
                                      strategy_instance_id=strategy_instance_id,
                                      order_status__in=order_status_list
                                      ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())

        position_dict = {}
        position_dict[symbol] = {'long': 0, 'short': 0}
        position_dict[symbol_2] = {'long': 0, 'short': 0}

        for order_dict in orders:
            symbol_ = order_dict['symbol']
            quantity_treaded = order_dict['quantity_treaded']
            if ('going_long' in order_dict['order_type']):
                position_dict[symbol_]['long'] += quantity_treaded
            elif ('close_long' in order_dict['order_type']):
                position_dict[symbol_]['long'] -= quantity_treaded
            elif ('going_short' in order_dict['order_type']):
                position_dict[symbol_]['short'] += quantity_treaded
            elif ('close_short' in order_dict['order_type']):
                position_dict[symbol_]['short'] -= quantity_treaded
        return position_dict

    def get_future_strategy_position(self, strategy_instance):
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        symbol = strategy_instance['symbol']
        orders = Order.objects.filter(user_id=user_id,
                                      strategy_instance_id=strategy_instance_id,
                                      order_status__in=order_status_list
                                      ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())

        position_dict = {}
        position_dict[symbol] = {'long': 0, 'short': 0}

        for order_dict in orders:
            # symbol_ = order_dict['symbol']
            quantity_treaded = order_dict['quantity_treaded']
            if ('going_long' in order_dict['order_type']):
                position_dict[symbol]['long'] += quantity_treaded
            elif ('close_long' in order_dict['order_type']):
                position_dict[symbol]['long'] -= quantity_treaded
            elif ('going_short' in order_dict['order_type']):
                position_dict[symbol]['short'] += quantity_treaded
            elif ('close_short' in order_dict['order_type']):
                position_dict[symbol]['short'] -= quantity_treaded

        return position_dict

    def get_spot_strategy_position(self, strategy_instance):
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        symbol = strategy_instance['symbol']
        orders = Order.objects.filter(user_id=user_id,
                                      strategy_instance_id=strategy_instance_id,
                                      order_status__in=order_status_list
                                      ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())

        position_dict = {}
        position_dict[symbol] = {'long': 0, 'short': 0}

        for order_dict in orders:
            symbol_ = order_dict['symbol']
            quantity_treaded = order_dict['quantity_treaded']
            if ('buy' in order_dict['order_type']):
                position_dict[symbol_]['long'] += quantity_treaded
            elif ('sell' in order_dict['order_type']):
                position_dict[symbol_]['long'] -= quantity_treaded

        return position_dict

    def get_reg_emu_balance(self, strategy_instance):
        status = 1

        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        symbol = strategy_instance['symbol']
        exchange = strategy_instance['exchange']
        start_usdt = 10000
        coin, basecoin = symbol.split('_')
        exchange_list = ['okexf', 'huobif']
        pre_ex_list = ['okex', 'huobi', 'binance']
        if (exchange not in exchange_list+pre_ex_list):
            status = 0
            data = '暂不支持的交易所!'
            return status, data
        elif (exchange in pre_ex_list):
            free = 100
            balance = 100
            data = {}
            data['coin'] = {'coin': coin, 'free': free, 'balance': balance}
            data['basecoin'] = {'basecoin': basecoin, 'free': free, 'balance': balance}
            return status, data
        coin_balance = 0.0
        coin_freezed = 0.0
        basecoin_balance = 10000
        basecoin_freezed = 0.0
        orders = Order.objects.filter(user_id=user_id,
                 strategy_instance_id=strategy_instance_id,
                 order_status__in=['pending', 'partial_filled', 'filled']
                 ).order_by('order_timestamp')
        for order in orders:
            order_type = order.order_type
            if (order.order_status in ['filled', 'partial_filled']):
                if (order_type in ['buy_market', 'buy_limit']):
                    qty = float(order.quantity)
                    if (order.symbol == symbol):
                        coin_balance += qty
                    else:
                        pass
                    basecoin_balance -= order.avg_price * qty
                elif (order_type in ['sell_market', 'sell_limit']):
                    qty = float(order.quantity)
                    if (order.symbol == symbol):
                        coin_balance -= qty
                    else:
                        pass
                    basecoin_balance += order.avg_price * qty
            elif (order.order_status == 'pending'):
                if (order_type == 'buy_limit'):
                    basecoin_freezed += float(order.price) * float(order.quantity)
                elif (order_type == 'sell_limit'):
                    if (order.symbol == symbol):
                        coin_freezed += float(order.quantity)
        data = {}
        free = coin_balance - coin_freezed
        balance = coin_balance
        data['coin'] = {'coin': coin, 'free': free, 'balance': balance}
        free = basecoin_balance - basecoin_freezed
        balance = basecoin_balance
        data['basecoin'] = {'basecoin': basecoin, 'free': free, 'balance': balance}
        return status, data

    def get_future_future_strategy_balance(self, strategy_instance):
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        account_type = strategy_instance['account_type']
        strategy_name = strategy_instance['id']
        orders = Order.objects.filter(user_id=user_id,
                                      strategy_instance_id=strategy_instance_id,
                                      order_status__in=order_status_list
                                      ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())

        long_open_order_dict_list = []
        long_close_order_dict_list = []
        short_open_order_dict_list = []
        short_close_order_dict_list = []

        for order_dict in orders:
            if ('going_long' in order_dict['order_type']):
                long_open_order_dict_list.append(order_dict)
            elif ('close_long' in order_dict['order_type']):
                long_close_order_dict_list.append(order_dict)
            elif ('going_short' in order_dict['order_type']):
                short_open_order_dict_list.append(order_dict)
            elif ('close_short' in order_dict['order_type']):
                short_close_order_dict_list.append(order_dict)

        length = len(long_open_order_dict_list)
        length_close = len(long_close_order_dict_list)
        if ((length > length_close) and (length > 0)):
            dao_quote = DaoQuote()
            long_open_order_dict = long_open_order_dict_list[-1]
            exchange = long_open_order_dict['exchange']
            symbol = long_open_order_dict['symbol']
            ticker = dao_quote.get_ticker(exchange, symbol)
            long_open_order_dict['avg_price'] = ticker['last']
            long_open_order_dict['order_type'] = 'market_close_long'
            long_close_order_dict_list.append(long_open_order_dict)

            short_open_order_dict = short_open_order_dict_list[-1]
            exchange = short_open_order_dict['exchange']
            symbol = short_open_order_dict['symbol']
            ticker = dao_quote.get_ticker(exchange, symbol)
            short_open_order_dict['avg_price'] = ticker['last']
            short_open_order_dict['order_type'] = 'market_close_long'
            short_close_order_dict_list.append(short_open_order_dict)
            length = length
        else:
            length = length
        capital_dict_list = []
        capital = 0
        capital_dict = {}
        capital_dict['timestamp'] = strategy_instance['strategy_timestamp']
        capital_dict['capital'] = capital
        capital_dict_list.append(capital_dict)
        for i in range(0, length):
            try:
                long_open_order_dict = long_open_order_dict_list.pop(0)
                long_close_order_dict = long_close_order_dict_list.pop(0)
                long_open_price = float(long_open_order_dict['avg_price'])
                long_close_price = float(long_close_order_dict['avg_price'])
                long_qty = float(long_close_order_dict['quantity'])
                long_open_fee = 10 * long_qty / long_open_price * 0.0003
                long_close_fee = 10 * long_qty / long_close_price * 0.0003
                long_earn = (10/long_open_price - 10/long_close_price) * long_qty
                long_real_earn = long_earn - long_open_fee - long_close_fee

                short_open_order_dict = short_open_order_dict_list.pop(0)
                short_close_order_dict = short_close_order_dict_list.pop(0)
                short_open_price = float(short_open_order_dict['avg_price'])
                short_close_price = float(short_close_order_dict['avg_price'])
                short_qty = float(short_close_order_dict['quantity'])
                short_open_fee = 10 * short_qty / short_open_price * 0.0003
                short_close_fee = 10 * short_qty / short_close_price * 0.0003
                short_earn = (10/short_close_price - 10/short_open_price)*short_qty
                short_real_earn = short_earn - short_open_fee - short_close_fee

                total_earn = long_real_earn + short_real_earn

                capital += total_earn
                capital_dict = {}
                capital_dict['timestamp'] = long_close_order_dict[
                                            'order_timestamp']
                capital_dict['capital'] = capital
                capital_dict_list.append(capital_dict)
            except Exception as e:
                print(e)
        return capital_dict_list

    def get_future_strategy_balance(self, strategy_instance):
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        exchange = strategy_instance['exchange']
        orders = Order.objects.filter(user_id=user_id,
                                      strategy_instance_id=strategy_instance_id,
                                      order_status__in=order_status_list
                                      ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())
        capital_dict_list = []
        capital = 0
        capital_dict = {}
        capital_dict['timestamp'] = strategy_instance['strategy_timestamp']
        capital_dict['capital'] = capital
        capital_dict_list.append(capital_dict)
        if (len(orders) > 0):
            if (exchange in ['okexf', 'huobif']):
                capital_dict_list = self.get_coin_future_strategy_balance(orders, capital_dict_list)
            elif (exchange == 'ctp'):
                capital_dict_list = self.get_ctp_strategy_balance(orders, capital_dict_list)
        return capital_dict_list

    def get_coin_future_strategy_balance(self, orders, capital_dict_list):
        symbol = orders[0].get('symbol', '')
        if ('btc' in symbol):
            contract_value = 100
        else:
            contract_value = 10
        capital = 0
        positions_dict = {}
        positions_dict['long_position'] = 0
        positions_dict['long_open_qty'] = 0
        positions_dict['long_avg_price'] = 0
        positions_dict['short_position'] = 0
        positions_dict['short_open_qty'] = 0
        positions_dict['short_avg_price'] = 0
        for order_dict in orders:
            qty = float(order_dict['quantity_treaded'])
            price = float(order_dict['avg_price'])
            if ('going_long' in order_dict['order_type']):
                positions_dict['long_position'] += (contract_value * qty / price)
                positions_dict['long_open_qty'] += qty
                positions_dict['long_avg_price'] = contract_value * positions_dict['long_open_qty'] / positions_dict['long_position']
            elif ('close_long' in order_dict['order_type']):
                if (positions_dict['long_avg_price'] == 0):
                    continue
                open_fee = contract_value * qty / positions_dict['long_avg_price'] * 0.0003
                close_position = contract_value * qty / price
                close_fee = close_position * 0.0003
                earn = (contract_value/positions_dict['long_avg_price'] - contract_value/price) * qty
                real_earn = earn - open_fee - close_fee
                positions_dict['long_position'] = positions_dict['long_position'] - close_position - earn
                positions_dict['long_open_qty'] -= qty
                if (positions_dict['long_open_qty'] == 0):
                    # print(round(positions_dict['long_position'], 5))
                    positions_dict['long_position'] = 0
                capital += real_earn
                capital_dict = {}
                capital_dict['timestamp'] = order_dict['order_timestamp']
                capital_dict['capital'] = capital
                capital_dict_list.append(capital_dict)
            elif ('going_short' in order_dict['order_type']):
                positions_dict['short_position'] += contract_value * qty / price
                positions_dict['short_open_qty'] += qty
                positions_dict['short_avg_price'] = contract_value * positions_dict['short_open_qty'] / positions_dict['short_position']
            elif ('close_short' in order_dict['order_type']):
                if (positions_dict['short_avg_price'] == 0):
                    continue
                open_fee = contract_value * qty / positions_dict['short_avg_price'] * 0.0003
                close_position = contract_value * qty / price
                close_fee = close_position * 0.0003
                earn = (contract_value/price - contract_value/positions_dict['short_avg_price']) * qty
                real_earn = earn - open_fee - close_fee
                positions_dict['short_position'] = positions_dict['short_position'] - close_position - earn
                positions_dict['short_open_qty'] -= qty
                if (positions_dict['short_open_qty'] == 0):
                    # print(round(positions_dict['short_position'], 5))
                    positions_dict['short_position'] = 0
                capital += real_earn
                capital_dict = {}
                capital_dict['timestamp'] = order_dict['order_timestamp']
                capital_dict['capital'] = capital
                capital_dict_list.append(capital_dict)
        return capital_dict_list

    def get_ctp_strategy_balance(self, orders, capital_dict_list):
        symbol = orders[0].get('symbol', '')
        capital = 0
        symbol_fee = re.findall(r'[0-9]+|[a-zA-Z]+', symbol)[0]
        fee_dict = cfg['ctp_fee_dict'][symbol_fee]
        g_fee_type = fee_dict['type']
        g_open_fee = fee_dict['open']
        g_close_fee = fee_dict['close']
        g_close_yest_fee = fee_dict['close_yest']
        long_avg_price = 0
        open_fee = 0
        close_fee = 0
        for order_dict in orders:
            qty = float(order_dict['quantity_treaded'])
            price = float(order_dict['price'])
            if ('going_long' in order_dict['order_type']):
                long_avg_price = price
            elif ('close_long' in order_dict['order_type']):
                if (long_avg_price == 0):
                    continue
                if (g_fee_type == 'num'):
                    open_fee = g_open_fee * qty
                    close_fee = g_close_fee * qty
                elif (g_fee_type == 'ratio'):
                    open_fee = long_avg_price * g_open_fee * qty
                    close_fee = price * close_fee  * qty
                earn = (price - long_avg_price) * qty * 10
                real_earn = earn - open_fee - close_fee
                capital += real_earn
                capital_dict = {}
                capital_dict['timestamp'] = order_dict['order_timestamp']
                capital_dict['capital'] = capital
                capital_dict_list.append(capital_dict)
            elif ('going_short' in order_dict['order_type']):
                short_avg_price = price
            elif ('close_short' in order_dict['order_type']):
                if (short_avg_price == 0):
                    continue
                if (g_fee_type == 'num'):
                    open_fee = g_open_fee * qty
                    close_fee = g_close_fee * qty
                elif (g_fee_type == 'ratio'):
                    open_fee = short_avg_price * g_open_fee * qty
                    close_fee = price * close_fee  * qty
                earn = (short_avg_price - price) * qty * 10
                real_earn = earn - open_fee - close_fee
                capital += real_earn
                capital_dict = {}
                capital_dict['timestamp'] = order_dict['order_timestamp']
                capital_dict['capital'] = capital
                capital_dict_list.append(capital_dict)
        return capital_dict_list

    def get_future_spot_strategy_balance(self, strategy_instance):
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        account_type = strategy_instance['account_type']
        strategy_name = strategy_instance['id']
        orders = Order.objects.filter(user_id=user_id,
                                      strategy_instance_id=strategy_instance_id,
                                      order_status__in=order_status_list
                                      ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())

        future_open_order_dict_list = []
        future_close_order_dict_list = []
        spot_open_order_dict_list = []
        spot_close_order_dict_list = []

        for order_dict in orders:
            if ('going' in order_dict['order_type']):
                future_open_order_dict_list.append(order_dict)
            elif ('close' in order_dict['order_type']):
                future_close_order_dict_list.append(order_dict)
            elif ('sell' in order_dict['order_type']):  # buy does not mean open
                spot_open_order_dict_list.append(order_dict)
            elif ('buy' in order_dict['order_type']):
                spot_close_order_dict_list.append(order_dict)

        length = len(future_open_order_dict_list)
        length_close = len(future_close_order_dict_list)
        if ((length > length_close) and (length > 0)):
            dao_quote = DaoQuote()
            future_open_order_dict = future_open_order_dict_list[-1]
            exchange = future_open_order_dict['exchange']
            symbol = future_open_order_dict['symbol']
            ticker = dao_quote.get_ticker(exchange, symbol)
            future_open_order_dict['avg_price'] = ticker['last']
            future_open_order_dict['order_type'] = 'market_close_long'
            future_close_order_dict_list.append(future_open_order_dict)

            spot_open_order_dict = spot_open_order_dict_list[-1]
            exchange = spot_open_order_dict['exchange']
            symbol = spot_open_order_dict['symbol']
            ticker = dao_quote.get_ticker(exchange, symbol)
            spot_open_order_dict['avg_price'] = ticker['last']
            spot_open_order_dict['order_type'] = 'market_sell'
            spot_close_order_dict_list.append(spot_open_order_dict)
            length = length
        else:
            length = length
        capital_dict_list = []
        capital = 0
        capital_dict = {}
        capital_dict['timestamp'] = strategy_instance['strategy_timestamp']
        capital_dict['capital'] = capital
        capital_dict_list.append(capital_dict)
        for i in range(0, length):
            try:
                future_open_order_dict = future_open_order_dict_list.pop(0)
                future_close_order_dict = future_close_order_dict_list.pop(0)
                future_open_price = float(future_open_order_dict['avg_price'])
                future_close_price = float(future_close_order_dict['avg_price'])
                future_qty = float(future_close_order_dict['quantity_treaded'])
                future_open_fee = 10 * future_qty / future_open_price * 0.0003
                future_close_fee = 10 * future_qty / future_close_price * 0.0003
                if ('long' in future_open_order_dict['order_type']):
                    future_earn = (10/future_open_price - 10/future_close_price) * future_qty
                elif ('short' in future_open_order_dict['order_type']):
                    future_earn = (10/future_close_price - 10/future_open_price)* future_qty
                future_real_earn = future_earn - future_open_fee - future_close_fee

                spot_open_order_dict = spot_open_order_dict_list.pop(0)
                spot_close_order_dict = spot_close_order_dict_list.pop(0)
                spot_open_price = float(spot_open_order_dict['avg_price'])
                spot_close_price = float(spot_close_order_dict['avg_price'])
                spot_open_qty = float(spot_open_order_dict['quantity_treaded'])
                spot_close_qty = float(spot_close_order_dict['quantity_treaded'])
                spot_open_fee = spot_open_qty * 0.0015
                spot_close_fee = spot_close_qty * 0.0015
                if ('buy' in spot_open_order_dict['order_type']):
                    spot_earn = spot_open_qty - spot_close_qty
                elif ('sell' in spot_close_order_dict['order_type']):
                    spot_earn = spot_close_qty - spot_open_qty
                spot_real_earn = spot_earn - spot_open_fee - spot_open_fee
                total_earn = future_real_earn + spot_real_earn

                capital += total_earn
                capital_dict = {}
                capital_dict['timestamp'] = future_close_order_dict[
                                            'order_timestamp']
                capital_dict['capital'] = capital
                capital_dict_list.append(capital_dict)
            except Exception as e:
                print(e)
        return capital_dict_list

    def get_future_spot_strategy_position(self, strategy_instance):
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        account_type = strategy_instance['account_type']
        strategy_name = strategy_instance['id']
        exchange = strategy_instance['exchange']
        exchange_2 = strategy_instance['exchange_2']
        symbol = strategy_instance['symbol']
        symbol_2 = strategy_instance['symbol_2']
        orders = Order.objects.filter(user_id=user_id,
                 strategy_instance_id=strategy_instance_id,
                 order_status__in=order_status_list
                 ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())

        position_dict = {}
        position_dict[symbol] = {'long': 0, 'short': 0}
        position_dict[symbol_2] = {'long': 0, 'short': 0}

        for order_dict in orders:
            symbol_ = order_dict['symbol']
            quantity_treaded = order_dict['quantity_treaded']
            if ('going_long' in order_dict['order_type']):
                position_dict[symbol_]['long'] += quantity_treaded
            elif ('close_long' in order_dict['order_type']):
                position_dict[symbol_]['long'] -= quantity_treaded
            elif ('going_short' in order_dict['order_type']):
                position_dict[symbol_]['short'] += quantity_treaded
            elif ('close_short' in order_dict['order_type']):
                position_dict[symbol_]['short'] -= quantity_treaded
            elif ('buy' in order_dict['order_type']):
                position_dict[symbol_]['long'] += quantity_treaded
            elif ('sell' in order_dict['order_type']):
                position_dict[symbol_]['long'] -= quantity_treaded

        return position_dict

    def get_spot_strategy_balance(self, strategy_instance):
        fee_ratio = 0.0015
        order_status_list = ['partial_filled', 'filled']
        user_id = strategy_instance['user_id']
        strategy_instance_id = strategy_instance['id']
        account_type = strategy_instance['account_type']
        strategy_name = strategy_instance['strategy_name']
        orders = Order.objects.filter(user_id=user_id,
                 strategy_instance_id=strategy_instance_id,
                 order_status__in=order_status_list
                 ).order_by('order_timestamp')
        orders = ast.literal_eval(orders.to_json())

        capital_dict_list = []
        capital = 0
        capital_dict = {}
        capital_dict['timestamp'] = strategy_instance['strategy_timestamp']
        capital_dict['capital'] = capital
        capital_dict_list.append(capital_dict)
        positions_dict = {}
        positions_dict['long_position'] = 0
        positions_dict['long_open_qty'] = 0
        positions_dict['long_avg_price'] = 0
        for order_dict in orders:
            qty = float(order_dict['quantity_treaded'])
            price = float(order_dict['avg_price'])
            if ('buy' in order_dict['order_type']):
                fee = fee_ratio * qty
                positions_dict['long_position'] += (qty - fee)
                positions_dict['long_open_qty'] += qty * price
                positions_dict['long_avg_price'] = positions_dict['long_open_qty'] / positions_dict['long_position']
            elif ('sell' in order_dict['order_type']):
                if (positions_dict['long_avg_price'] == 0):
                    continue
                close_position = qty
                close_fee = fee_ratio * price * qty
                earn = (price - positions_dict['long_avg_price']) * qty
                real_earn = earn - close_fee
                positions_dict['long_position'] = positions_dict['long_position'] - close_position
                positions_dict['long_open_qty'] -= qty * price
                if (positions_dict['long_open_qty'] == 0):
                    # print(round(positions_dict['long_position'], 5))
                    positions_dict['long_position'] = 0
                capital += real_earn
                capital_dict = {}
                capital_dict['timestamp'] = order_dict['order_timestamp']
                capital_dict['capital'] = capital
                capital_dict_list.append(capital_dict)
        return capital_dict_list
