import pathmagic

from dao_strategy.backtest import backtest


def test_backtest_main():
    strategy_config_dict = {}
    strategy_config_dict['_id'] = {'$oid': '123456'}
    strategy_config_dict['strategy_datetime'] = ''
    strategy_config_dict['strategy_file_id'] = {'$oid': '111333555'}
    strategy_config_dict['user_name'] = 'jesse'
    strategy_config_dict['user_id'] = {'$oid': '5cb452702a0aa544cd9e0bca'}
    strategy_config_dict['phone_zone_code'] = '86'
    strategy_config_dict['phone_num'] = '155'
    strategy_config_dict['run_type'] = 'real'
    strategy_config_dict['sms_send'] = 'no'
    strategy_config_dict['param_1_start'] = '100'
    strategy_config_dict['param_1_end'] = ''
    strategy_config_dict['param_1_step'] = ''
    strategy_config_dict['param_2_start'] = '100'
    strategy_config_dict['param_2_end'] = ''
    strategy_config_dict['param_2_step'] = ''
    strategy_config_dict['log_record'] = 'no'
    strategy_config_dict['account_type'] = 'reg_backtest'
    strategy_config_dict['strategy_name'] = ''
    strategy_config_dict['min_trade_num'] = 0.0
    strategy_config_dict['status_dict'] = {}
    strategy_config_dict['balance_end'] = 10000.0
    strategy_config_dict['balance_front'] = 10000.0
    strategy_config_dict['taker_fee_ratio'] = 0.0003
    strategy_config_dict['maker_fee_ratio'] = 0.0003
    strategy_config_dict['strategy_type'] = 'future_strategy'
    strategy_config_dict['file_path'] = 'dao_strategy/backtest/strategy_files/'
    strategy_config_dict['filename'] = 'strategy_9.py'
    strategy_config_dict['exchange'] = 'okexf'
    strategy_config_dict['symbol'] = 'btc_usd-quarter'
    strategy_config_dict['one_time_buy'] = 1000.0
    strategy_config_dict['begin_time'] = '2021-05-01 00:00:00'
    strategy_config_dict['period'] = 30
    strategy_config_dict['period_list'] = []
    strategy_config_dict['end_time'] = '2021-09-01 00:00:00'

    backtest.backtest_main(strategy_config_dict)


def test_get_exchange_symbol_dict():
    # case_1
    exchange = 'okexf'
    symbol = 'btc_usd-quarter'
    exchange_symbol_dict = backtest.get_exchange_symbol_dict(exchange, symbol)
    print(exchange_symbol_dict)

    # case_2
    exchange = 'okexf,ctp'
    symbol = 'btc_usd-quarter,CF205,FG205,rb2201'
    exchange_symbol_dict = backtest.get_exchange_symbol_dict(exchange, symbol)
    print(exchange_symbol_dict)

    for exchange in exchange_symbol_dict.keys():
        for symbol in exchange_symbol_dict[exchange]:
            print(exchange, symbol)


def main():
    # test_backtest_main()
    test_get_exchange_symbol_dict()


if __name__ == '__main__':
    main()
