from dao_strategy.utils import earn
from dao_strategy.utils import global_var as g


def market_going_long(coin):
    g.g_direct = 'open'

    fee = earn.compute_fee(g.g_contract_value, g.g_fee_ratio,
                           g.g_open_price, g.g_quantity)
    g.g_balance = g.g_balance - fee
    g.g_balance_range.append(g.g_balance)
    g.g_trade_records.append([g.g_time_now, g.g_open_price,
                             g.g_direct, fee, g.g_balance, '',
                             g.g_param_1, g.g_param_2, g.g_param_3])
    going_short_id = 111
    return going_short_id


def market_close_long(coin):
    g.g_direct = 'close'

    fee = earn.compute_fee(g.g_contract_value, g.g_fee_ratio,
                           g.g_close_price, g.g_quantity)
    earn_coin = earn.compute_earn_long(g.g_contract_value, g.g_open_price,
                                       g.g_close_price, g.g_quantity)
    g.g_balance = g.g_balance + earn_coin - fee
    g.g_balance_range.append(g.g_balance)
    g.g_trade_records.append([g.g_time_now, g.g_close_price,
                             g.g_direct, fee, g.g_balance, g.g_type, '', '', ''])
    close_short_id = 333
    return close_short_id


def market_going_short(coin):
    g.g_direct = 'open'

    fee = earn.compute_fee(g.g_contract_value, g.g_fee_ratio,
                           g.g_open_price, g.g_quantity)
    g.g_balance = g.g_balance - fee
    g.g_balance_range.append(round(g.g_balance, 5))
    g.g_trade_records.append([g.g_time_now, g.g_open_price,
                             g.g_direct, round(fee, 5), round(g.g_balance, 5), '',
                             g.g_param_1, g.g_param_2, g.g_param_3])
    going_short_id = 222
    return going_short_id


def market_close_short(coin):
    g.g_direct = 'close'

    fee = earn.compute_fee(g.g_contract_value, g.g_fee_ratio,
                           g.g_close_price, g.g_quantity)
    earn_coin = earn.compute_earn_short(g.g_contract_value, g.g_open_price,
                                        g.g_close_price, g.g_quantity)
    g.g_balance = g.g_balance + earn_coin - fee
    g.g_balance_range.append(round(g.g_balance, 5))
    g.g_trade_records.append([g.g_time_now, g.g_close_price,
                             g.g_direct, round(fee, 5), round(g.g_balance, 5),
                             g.g_type, '', '', ''])
    close_short_id = 444
    return close_short_id


def market_buy(symbol):
    g.g_direct = 'open'

    fee = earn.compute_spot_fee(g.g_direct, g.g_fee_ratio, g.g_buy_price, g.g_quantity)
    g.g_balance_front = g.g_balance_front + g.g_quantity - fee
    g.g_balance_end = g.g_balance_end - g.g_buy_price * g.g_quantity
    fee_end = fee * g.g_buy_price
    g.g_balance -= fee_end
    g.g_balance_range.append(g.g_balance)
    g.g_trade_records.append([g.g_time_now, g.g_buy_price,
                             g.g_direct, fee_end, g.g_balance, '',
                             g.g_param_1, g.g_param_2, g.g_param_3])
    buy_id = 111
    return buy_id


def market_sell(symbol):
    g.g_direct = 'close'

    fee_end = earn.compute_spot_fee(g.g_direct, g.g_fee_ratio, g.g_sell_price, g.g_quantity)
    g.g_balance_front = g.g_balance_front - g.g_quantity
    g.g_balance_end = g.g_balance_end + g.g_sell_price * g.g_quantity - fee_end
    g.g_balance = g.g_balance_front * g.g_sell_price + g.g_balance_end
    g.g_balance_range.append(g.g_balance)
    g.g_trade_records.append([g.g_time_now, g.g_sell_price,
                             g.g_direct, fee_end, g.g_balance, '',
                             g.g_param_1, g.g_param_2, g.g_param_3])
    sell_id = 333
    return sell_id
