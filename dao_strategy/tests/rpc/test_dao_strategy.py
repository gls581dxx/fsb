import json
import time
import base64
import pprint

import pathmagic

from dao_strategy.rpc.dao_strategy import DaoStrategy


class testDaoStrategy(object):

    def __init__(self):
        self.dao_strategy = DaoStrategy()

    def test_get_strategies(self):
        strategy_type = 'future_strategy'
        page_num = '1'
        page_limit = '3'
        status, data = self.dao_strategy.get_strategies(strategy_type, page_num, page_limit)
        # print(status, data)
        strategy_dict_list = data['strategy_dict_list']
        for strategy_dict in strategy_dict_list:
            pprint.pprint(strategy_dict)

    def test_run_strategy(self):
        user_id = '5cb452702a0aa544cd9e0bca'
        strategy_instance_id = '5d1c5cb32a0aa556aab15988'
        exchange = 'okexf'
        account_type = 'api_bind'
        strategy_type = 'future_strategy'
        strategy_name = 'strategy_9'
        symbol = 'btc_usd-quarter'
        one_time_buy = '30'
        sms_send = 'shu'
        status, data = self.dao_strategy.run_strategy(user_id, strategy_instance_id, exchange, account_type, strategy_type, strategy_name, symbol, one_time_buy, sms_send)
        print(status, data)

    def test_control_strategy(self):
        user_id = '5cb452702a0aa544cd9e0bca'
        strategy_instance_id = '5d1c5cb32a0aa556aab15988'
        order = 'start'
        # order = 'stop'
        # order = 'cover'
        status, data = self.dao_strategy.control_strategy(user_id, strategy_instance_id, order)
        print(status, data)

    def test_get_strategy_instance(self):
        user_id = '5cb452702a0aa544cd9e0bca'
        strategy_type = 'future_strategy'
        status = 'running'
        page_num = '1'
        page_limit = '3'
        status, data = self.dao_strategy.get_strategy_instance(user_id, strategy_type, status, page_num, page_limit)
        print(status, data)

    def test_submit_arbitrage_strategy(self):
        user_id = '5cb452702a0aa544cd9e0bca'
        exchange_a = 'okexf'
        exchange_b = 'okex'
        account_type_a = 'api_bind'
        account_type_b = 'api_bind'
        strategy_type = 'strategy_9'
        symbol_a = 'btc_usd-quarter'
        symbol_b = 'ltc_usd-quarter'
        spread_usdt = '50000'
        max_trade_num = '3'
        min_trade_num = '1'
        status, data = self.dao_strategy.submit_arbitrage_strategy(user_id, exchange_a, exchange_b, account_type_a, account_type_b, strategy_type, symbol_a, symbol_b, spread_usdt, max_trade_num, min_trade_num)
        print(status, data)

    def test_get_strategy_pnl(self):
        user_id = '5cb452702a0aa544cd9e0bca'
        strategy_instance_id = '5d1c5cb32a0aa556aab15988'
        status, data = self.dao_strategy.get_strategy_pnl(user_id, strategy_instance_id)
        print(status, data)

    def test_submit_conditional_strategy(self):
        user_id = '5cb452702a0aa544cd9e0bca'
        exchange = 'okexf'
        account_type = 'api_bind'
        strategy_type = 'future_strategy'
        strategy_name = 'ma_strategy'
        symbol = 'btc_usd-quarter'
        one_time_buy = '10'
        sms_send = 'shu'
        param = 'ma_strategy_type=ma_gold&ma_strategy_short=5&ma_strategy_long=10&ma_strategy_price_type=market&ma_strategy_order=buy&ma_strategy_amount_type=quantity&ma_strategy_sms_send=yes&ma_strategy_end_time=2021-08-09 00:00:00'
        status, data = self.dao_strategy.submit_conditional_strategy(user_id,
               exchange, account_type, strategy_type, strategy_name,
               symbol, one_time_buy, sms_send, param)
        print(status, data)

    def test_get_file(self):
        user_id = '5cb452702a0aa544cd9e0bca'
        file_name = 'params_fig_6139bac0b8a1aefe780e2ba9.pdf'
        status, data = self.dao_strategy.get_file(user_id, file_name)
        file_content = data['file_content']
        with open(file_name, 'wb') as f:
            f.write(base64.b64decode(file_content))

    def main(self):
        self.test_get_strategies()
        self.test_run_strategy()
        self.test_control_strategy()
        self.test_get_strategy_instance()
        self.test_submit_arbitrage_strategy()
        self.test_get_strategy_pnl()
        self.test_submit_conditional_strategy()
        self.test_get_file()
        print('test_pass')


def main():
    tdu = testDaoStrategy()
    tdu.main()


if __name__ == '__main__':
    main()
