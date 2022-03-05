from dao_strategy.utils import global_var as g


def compute_earn_long(contract_value, open_price, close_price, quantity):
    if (g.g_exchange == 'ctp'):
        earn = (close_price - open_price) * quantity * g.g_tick_earn
    else:
        earn = (contract_value/open_price - contract_value/close_price) * quantity
    return earn


def compute_earn_short(contract_value, open_price, close_price, quantity):
    if (g.g_exchange == 'ctp'):
        earn = (open_price - close_price) * quantity * g.g_tick_earn
    else:
        earn = (contract_value/close_price - contract_value/open_price) * quantity
    return earn


def compute_fee(contract_value, fee_ratio, deal_price, quantity):
    if (g.g_exchange == 'ctp'):
        if (g.g_direct == 'open'):
            if (g.g_fee_type == 'num'):
                fee = g.g_open_fee
            elif (g.g_fee_type == 'ratio'):
                fee = deal_price * g.g_open_fee
        if (g.g_direct == 'close'):
            if (g.g_fee_type == 'num'):
                fee = g.g_close_fee
            elif (g.g_fee_type == 'ratio'):
                fee = deal_price * g.g_close_fee
    else:
        fee = contract_value * quantity / deal_price * fee_ratio
    return fee


def compute_qty_long(contract_value, open_price, close_price, fee_ratio, earn):
    quantity = (earn / (contract_value *
                        (((1-fee_ratio) / open_price) -
                         ((1+fee_ratio) / close_price))))
    return quantity


def compute_qty_short(contract_value, open_price, close_price, fee_ratio, earn):
    quantity = (earn / (contract_value *
                        (((1-fee_ratio) / close_price) -
                         ((1+fee_ratio) / open_price))))
    return quantity


def compute_spot_fee(direct, fee_ratio, deal_price, quantity):
    if ((direct == 'buy') or (direct == 'open')):
        fee = fee_ratio * quantity
    elif (direct == 'sell' or (direct == 'close')):
        fee = fee_ratio * deal_price * quantity
    return fee
