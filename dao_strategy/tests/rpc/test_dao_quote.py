import json

import pathmagic

from dao_strategy.rpc.dao_quote import DaoQuote


class testDaoQuote(object):

    def __init__(self):
        self.dao_quote = DaoQuote()

    def test_get_ticker(self):
        exchange = 'okexf'
        symbol = 'btc_usd-quarter'
        status, data = self.dao_quote.get_ticker(exchange, symbol)
        print(status, data)

    def main(self):
        self.test_get_ticker()
        print('test_pass')


def main():
    tdq = testDaoQuote()
    tdq.main()


if __name__ == '__main__':
    main()
