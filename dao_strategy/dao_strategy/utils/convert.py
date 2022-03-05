import time
import datetime


def combine_lines(klines, period):
    if ('min' in period):
        k_bars = int(period.split('min')[0])
    elif ('hour' in period):
        k_bars = int(period.split('hour')[0]) * 60
    else:
        k_bars = 1
    bars = k_bars
    new_klines = []
    if (len(klines) % bars == 0):
        length = int(len(klines)/bars)
    elif (len(klines) % bars > 0):
        length = int(len(klines)/bars) + 1
    for i in range(0, length):
        klines_part = klines[i*bars:(i+1)*bars]
        timestamp = klines_part[0][0]
        open = klines_part[0][1]
        high = klines_part[0][2]
        low = klines_part[0][3]
        close = klines_part[-1][4]
        for kline in klines_part:
            if high < kline[2]:
                high = kline[2]
            if low > kline[3]:
                low = kline[3]
        new_klines.append([timestamp, open, high, low, close])
    return new_klines


def combine_lines_2(klines, bars):
    new_klines = []
    if (len(klines) % bars == 0):
        length = int(len(klines)/bars)
    elif (len(klines) % bars > 0):
        length = int(len(klines)/bars) + 1
    for i in range(0, length):
        klines_part = klines[i*bars:(i+1)*bars]
        timestamp = klines_part[0][0]
        open = klines_part[0][1]
        high = klines_part[0][2]
        low = klines_part[0][3]
        close = klines_part[-1][4]
        for kline in klines_part:
            if high < kline[2]:
                high = kline[2]
            if low > kline[3]:
                low = kline[3]
        new_klines.append([timestamp, open, high, low, close])
    return new_klines


def combine_lines_3(klines, bars):
    new_klines = []
    if (len(klines) % bars == 0):
        length = int(len(klines)/bars)
    elif (len(klines) % bars > 0):
        length = int(len(klines)/bars) + 1
    for i in range(0, length):
        klines_part = klines[i*bars:(i+1)*bars]
        timestamp = klines_part[0][0]
        open = klines_part[0][1]
        high = klines_part[0][2]
        low = klines_part[0][3]
        close = klines_part[-1][4]
        volume = 0
        for kline in klines_part:
            if high < kline[2]:
                high = kline[2]
            if low > kline[3]:
                low = kline[3]
            volume += kline[5]
        new_klines.append([timestamp, open, high, low, close, volume])
        volume = 0
    return new_klines


def spread_lines(bars_a, bars_b):
    bars = []
    for i in range(0, len(bars_a)):
        bar_a = bars_a[i]
        bar_b = bars_b[i]
        bar = [bar_a[0], bar_a[1]-bar_b[1], bar_a[2]-bar_b[2], bar_a[3]-bar_b[3], bar_a[4]-bar_b[4], bar_a[5]+bar_b[5]]
        bars.append(bar)
    return bars


def combine_lines_5(klines, bars, offset=0):
    new_klines = []
    if (len(klines) % bars == 0):
        length = int(len(klines)/bars)
    elif (len(klines) % bars > 0):
        length = int(len(klines)/bars) + 1
    for i in range(0, length):
        if (i == 0):
            continue
        klines_part = klines[i*bars-offset:(i+1)*bars-offset]
        timestamp = klines_part[0][0]
        open = klines_part[0][1]
        high = klines_part[0][2]
        low = klines_part[0][3]
        close = klines_part[-1][4]
        for kline in klines_part:
            if high < kline[2]:
                high = kline[2]
            if low > kline[3]:
                low = kline[3]
        new_klines.append([timestamp, open, high, low, close])
    return new_klines


def shift_time(timestamp):
    if (timestamp/(10**10)>10):
        timestamp = timestamp / 1000
    format = '%Y-%m-%d %H:%M:%S'
    value = time.localtime(timestamp)
    return time.strftime(format, value)


def to_timestr(timestamp):
    format = '%Y/%m/%d-%H:%M:%S'
    value = time.localtime(timestamp)
    return time.strftime(format, value)


def to_timestamp(time_date):
    format = '%Y-%m-%d %H:%M:%S'
    timearray = time.strptime(time_date, format)
    timestamp = str(int(time.mktime(timearray)))
    return timestamp


def to_timestamp_v3(iso_time):
    format = '%Y-%m-%dT%H:%M:%S.%fZ'
    dt = datetime.datetime.strptime(iso_time, format)
    timestamp = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
    return timestamp
