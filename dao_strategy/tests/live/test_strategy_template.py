import datetime

import pathmagic

from dao_strategy.live.strategy_template import StrategyTemplate


class testStrategyTemplate(StrategyTemplate):
    """docstring for testStrategyTemplate."""

    def __init__(self):
        pass

    def test_ctp_time_filter(self):
        dt = datetime.datetime.now()
        rst = self.ctp_time_filter(dt)
        print(dt, rst)
        print('[*] 非交易的小时')
        for i in [8, 9, 10, 11, 12, 13, 15, 16, 20, 21, 23]:
            dt = datetime.datetime(2022,2,22,i,0,0)
            rst = self.ctp_time_filter(dt)
            print(dt, rst)
        print('[*] 上午10点休息')
        for i in [14, 15, 29, 30]:
            dt = datetime.datetime(2022,2,22,10,i,0)
            rst = self.ctp_time_filter(dt)
            print(dt, rst)
        print('[*] 上午10点15前')
        for i in range(53, 60):
            dt = datetime.datetime(2022,2,22,10,14,i)
            rst = self.ctp_time_filter(dt)
            print(dt, rst)
        print('[*] 上午11点30前')
        for i in range(53, 60):
            dt = datetime.datetime(2022,2,22,11,29,i)
            rst = self.ctp_time_filter(dt)
            print(dt, rst)
        print('[*] 下午13点30前')
        for i in [29, 30]:
            dt = datetime.datetime(2022,2,22,13,i,0)
            rst = self.ctp_time_filter(dt)
            print(dt, rst)
        print('[*] 下午15点前')
        for i in range(53, 60):
            dt = datetime.datetime(2022,2,22,14,59,i)
            rst = self.ctp_time_filter(dt)
            print(dt, rst)
        print('[*] 晚上23点前')
        for i in range(53, 60):
            dt = datetime.datetime(2022,2,22,22,59,i)
            rst = self.ctp_time_filter(dt)
            print(dt, rst)
        print('[*] test pass')

    def main(self):
        self.test_ctp_time_filter()


def main():
    tst = testStrategyTemplate()
    tst.main()


if __name__ == '__main__':
    main()
