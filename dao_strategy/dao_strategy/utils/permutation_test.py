import random
import bisect

import numpy as np
import scipy.stats as stats


def compute_corr(return_list, indicator_list):
    n = 10000
    m = len(indicator_list)

    v = indicator_list

    np.random.seed(0)
    spears = []
    for i in range(0, n):
        noise = np.random.normal(0, 1, m)
        corr = stats.stats.spearmanr(noise, v)[0]
        spears.append(corr)

    spears.sort()
    cut95right = spears[int(n * 0.95)]
    cut95left = spears[int(n * 0.05)]

    real = stats.stats.spearmanr(return_list, v)[0]

    axvline_list = [cut95right, cut95left, real]

    i = bisect.bisect_right(spears, real)
    score = i / n
    if (score < 0.5):
        score = 1 - score
    return score


def compute_one_indicator(indicator_name, trade_records, indicator_score_dict):
    return_list = []
    indicator_list = []
    for i in trade_records:
        return_list.append(i[7])
        indicator_num = normalize_indicator(i[10][indicator_name])
        if (str(indicator_num) == 'nan'):
            indicator_num = 0.1
        indicator_list.append(indicator_num)

    score = compute_corr(return_list, indicator_list)
    indicator_score_dict[indicator_name] = score*100
    return indicator_score_dict


def normalize_indicator(num):
    # num = (num - 50) / 100
    return num


def p_test_indicator(trade_records):
    indicator_name_list = []

    indicator_dict = trade_records[0][10]
    indicator_score_dict = {}
    jobs = []
    for indicator_name in indicator_dict:
        indicator_score_dict_ = compute_one_indicator(indicator_name, trade_records, {})
        indicator_score_dict.update(indicator_score_dict_)

    in_dict = {}
    for indicator_name in indicator_score_dict:
        name_list = indicator_name.split('_')
        name = '_'.join(name_list[:-1])
        param = float(name_list[-1])
        score = indicator_score_dict[indicator_name]
        if (name not in in_dict.keys()):
            in_dict[name] = {}
        in_dict[name][param] = round(score, 3)
    return in_dict
