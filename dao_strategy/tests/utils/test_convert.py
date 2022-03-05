
import time
import datetime

import pathmagic

from dao_strategy.utils import convert


def test_shift_time():
    timestamp = time.time()
    time_str = convert.shift_time(timestamp)
    print(timestamp, time_str)


def test_to_timestamp():
    time_date = str(datetime.datetime.now()).split('.')[0]
    ts = convert.to_timestamp(time_date)
    print(time_date, ts)


def main():
    test_shift_time()
    test_to_timestamp()


if __name__ == '__main__':
    main()
