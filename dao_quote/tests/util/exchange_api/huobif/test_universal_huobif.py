# coding=utf-8

import asyncio
import pathmagic

from dao_quote.util.exchange_api.huobif import universal_huobif


async def test_async_ticker():
    symbol = 'btc_usd-quarter'
    rst = await universal_huobif.async_ticker(symbol)
    print(rst)
    # print(rst['ticker']['last'])


async def test_async_bar():
    symbol = 'btc_usd-quarter'
    rst = await universal_huobif.async_bar(symbol)
    print(rst)


async def test_async_depth():
    symbol = 'btc_usd-quarter'
    rst = await universal_huobif.async_depth(symbol)
    # print(rst['asks'][0])
    # print(rst['asks'][-1])
    # print(rst['bids'][0])
    # print(rst['bids'][-1])
    print(rst)


def test_ticker():
    symbol = 'btc_usd-quarter'
    rst = universal_huobif.ticker(symbol)
    print(rst)
    # print(rst['ticker']['last'])


def test_bar():
    symbol = 'btc_usd-quarter'
    rst = universal_huobif.bar(symbol)
    print(rst)
    print(len(rst))


def test_bars():
    symbol = 'btc_usd-quarter'
    period = '5min'  # '15min'
    rst = universal_huobif.bars(symbol, period)
    print(rst)
    print(len(rst))


def test_depth():
    symbol = 'btc_usd-quarter'
    rst = universal_huobif.depth(symbol)
    # print(rst['asks'][0])
    # print(rst['asks'][-1])
    # print(rst['bids'][0])
    # print(rst['bids'][-1])
    print(rst)


def main():
    # tasks = []
    # tasks.append(test_async_ticker())
    # tasks.append(test_async_bar())
    # tasks.append(test_async_depth())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(asyncio.gather(*tasks))
    # test_ticker()
    # test_bar()
    # test_bars()
    # test_depth()
    print('test pass')


if __name__ == '__main__':
    main()
