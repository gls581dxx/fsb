# from dao_strategy.utils import drawing
from dao_strategy.utils.convert import to_timestamp


def generate_trade_open(order_records, filename):
    trade_records = []
    for i in range(0, len(order_records)-1):
        if order_records[i][2] == 'buy':
            fee = ''
            open_usdt = order_records[i][3] + order_records[i][4]
            earn = ''
            total = ''
            one_log = [order_records[i][0], order_records[i][1], 'long',
                       '', '', fee, open_usdt, earn, total, '',
                       order_records[i][-1]]
            trade_records.append(one_log)

    with open(filename+'_rsi.txt', 'w') as f:
        f.write(str(trade_records))


def generate_trade_log(order_records):
    trade_records = []
    for i in range(0, len(order_records)-1):
        if order_records[i][2] == 'open':
            fee = order_records[i][3] + order_records[i+1][3]
            open_usdt = order_records[i][3] + order_records[i][4]
            earn = order_records[i+1][4] - open_usdt
            total = order_records[i+1][4]
            try:
                one_log = [order_records[i][0], order_records[i][1], 'long',
                           order_records[i+1][0], order_records[i+1][1],
                           fee, open_usdt, earn, total, order_records[i+1][5],
                           order_records[i][6], order_records[i][7],
                           order_records[i][8]]
            except:
                one_log = [order_records[i][0], order_records[i][1], 'long',
                           order_records[i+1][0], order_records[i+1][1],
                           fee, open_usdt, earn, total, order_records[i+1][5],
                           order_records[i][6], order_records[i][7]]
            trade_records.append(one_log)

    case_1 = 0
    case_2 = 0
    init_fund = 0
    total_earn = 0
    fee_sum = 0
    pure_earn = 0
    earn_num = 0
    loss_num = 0
    win_ratio = 0
    avg_earn = 0
    avg_loss = 0
    earn_loss_ratio = 0
    earn_max = 0
    loss_max = 0
    max_back_ratio = 0
    avg_hodl_time = 0
    avg_earn_hodl_time = 0
    avg_loss_hodl_time = 0
    only_earn_sum = 0
    only_loss_sum = 0
    # earn_max = trade_records[0][7]
    # loss_max = trade_records[0][7]
    earn_max = 0
    loss_max = 0
    earn_hodl_time = 0
    loss_hodl_time = 0
    balance_dict_list = []

    avg_earn_hodl_time = 0

    for each_trade in trade_records:
        fee_sum += each_trade[5]
        balance_dict = {}
        balance_dict['timestamp'] = int(to_timestamp(each_trade[3]))
        balance_dict['balance_num'] = each_trade[8]
        balance_dict_list.append(balance_dict)
        earn = each_trade[7]
        case = each_trade[9]
        if earn >= 0:
            earn_num += 1
            only_earn_sum += earn
            earn_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))
        else:
            loss_num += 1
            only_loss_sum += earn
            loss_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))

        each_trade[5] = round(each_trade[5], 3)
        each_trade[6] = round(each_trade[6], 3)
        each_trade[7] = round(each_trade[7], 3)
        each_trade[8] = round(each_trade[8], 3)

        earn_max = max(earn_max, earn)
        loss_max = min(loss_max, earn)

        if (case == 'case_one'):
            case_1 += 1
        elif (case == 'case_two'):
            case_2 += 1

    cost_function_dict = {}
    cost_function_dict['case_1'] = case_1
    cost_function_dict['case_2'] = case_2

    init_fund = order_records[0][3] + order_records[0][4]
    cost_function_dict['init_fund'] = round(init_fund, 3)

    total_earn = order_records[-1][4] - init_fund
    total_earn = total_earn + fee_sum
    cost_function_dict['total_earn'] = round(total_earn, 3)

    cost_function_dict['fee_sum'] = round(fee_sum, 3)

    pure_earn = order_records[-1][4] - init_fund
    cost_function_dict['pure_earn'] = round(pure_earn, 3)

    cost_function_dict['earn_num'] = earn_num

    cost_function_dict['loss_num'] = loss_num

    if ((earn_num != 0) and (loss_num != 0)):
        win_ratio = float(earn_num) / (earn_num + loss_num)
        win_ratio = round(win_ratio, 3)
    cost_function_dict['win_ratio'] = win_ratio

    if ((earn_num != 0) and (only_earn_sum != 0)):
        avg_earn = float(only_earn_sum) / earn_num
    cost_function_dict['avg_earn'] = round(avg_earn, 3)

    if ((loss_num != 0) and (only_loss_sum != 0)):
        avg_loss = float(only_loss_sum) / loss_num
    cost_function_dict['avg_loss'] = round(avg_loss, 3)

    if ((earn_num != 0) and (avg_earn != 0) and (avg_loss != 0)):
        earn_loss_ratio = float(avg_earn) / avg_loss
        if ((avg_earn > avg_loss) and (earn_loss_ratio < 0)):
            earn_loss_ratio = -earn_loss_ratio
    cost_function_dict['earn_loss_ratio'] = round(earn_loss_ratio, 3)

    cost_function_dict['earn_max'] = round(earn_max, 3)

    cost_function_dict['loss_max'] = round(loss_max, 3)

    back_ratio = []
    for balance_dict in balance_dict_list:
        try:
            back_ratio.append(((balance_dict['balance_num'] - balance_dict['balance_num']) /
                               float(balance_dict['balance_num'])))
        except Exception as e:
            pass
    back_ratio.sort()
    # back_ratio.reverse()
    back_ratio = back_ratio[:3]
    sum = 0
    for i in back_ratio:
        sum += i

    if (sum != 0):
        max_back_ratio = sum / 3.0
    cost_function_dict['max_back_ratio'] = round(max_back_ratio, 3)

    if (((earn_hodl_time > 0) or (loss_hodl_time > 0)) and
       ((earn_num > 0) or (loss_num > 0))):
        avg_hodl_time = ((earn_hodl_time + loss_hodl_time) /
                         float(earn_num + loss_num))
        avg_hodl_time = avg_hodl_time / 3600
    cost_function_dict['avg_hodl_time'] = round(avg_hodl_time, 3)

    if ((earn_num != 0) and (earn_hodl_time > 0)):
        avg_earn_hodl_time = earn_hodl_time/float(earn_num)
        avg_earn_hodl_time = avg_earn_hodl_time/3600
    cost_function_dict['avg_earn_hodl_time'] = round(avg_earn_hodl_time, 3)

    if ((loss_num != 0) and (loss_hodl_time > 0)):
        avg_loss_hodl_time = loss_hodl_time / float(loss_num)
        avg_loss_hodl_time = avg_loss_hodl_time / 3600
    cost_function_dict['avg_loss_hodl_time'] = round(avg_loss_hodl_time, 3)

    return cost_function_dict, balance_dict_list, trade_records


def generate_long_trade_log_filter(order_records, filter_dict):
    indicator = filter_dict['indicator']
    start = filter_dict['start']
    end = filter_dict['end']
    balance_range_dict_list = []
    balance_range_dict = {}
    balance_range_dict['timestamp'] = int(to_timestamp(order_records[1][0]))
    balance_range_dict['balance_num'] = order_records[0][3] + order_records[0][4]
    balance_range_dict_list.append(balance_range_dict)
    for i in range(0, len(order_records)-1):
        if ((order_records[i][2] == 'open') and
           (start <= order_records[i][6][indicator] <= end)):
            fee = order_records[i][3] + order_records[i+1][3]
            open_usdt = order_records[i][3] + order_records[i][4]
            earn = order_records[i+1][4] - open_usdt
            last_balance = balance_range_dict_list[-1]['balance_num']
            new_balance = last_balance + earn
            balance_range_dict = {}
            balance_range_dict['timestamp'] = int(to_timestamp(order_records[i+1][0]))
            balance_range_dict['balance_num'] = new_balance
            balance_range_dict_list.append(balance_range_dict)
        else:
            pass

    return balance_range_dict_list


def save_file(filename, cost_function_dict, trade_records):

    # with open(filename[:-4]+'_indicator.txt', 'w') as f:
    #     f.write(str(trade_records))

    record = ''
    record += '条件一: {}\n\r'.format(cost_function_dict['case_1'])
    record += '条件二: {}\n\r'.format(cost_function_dict['case_2'])
    record += '资金初始额: {}\n\r'.format(cost_function_dict['init_fund'])
    record += '总盈利: {}\n\r'.format(cost_function_dict['total_earn'])
    record += '手续费总额: {}\n\r'.format(cost_function_dict['fee_sum'])
    record += '绝对盈利: {}\n\r'.format(cost_function_dict['pure_earn'])
    record += '盈利次数: {}\n\r'.format(cost_function_dict['earn_num'])
    record += '亏损次数: {}\n\r'.format(cost_function_dict['loss_num'])
    record += '胜率: {}\n\r'.format(cost_function_dict['win_ratio'])
    record += '平均盈利大小: {}\n\r'.format(cost_function_dict.get('avg_earn', 0.0))
    record += '平均亏损大小: {}\n\r'.format(cost_function_dict['avg_loss'])
    record += '盈亏比: {}\n\r'.format(cost_function_dict.get('earn_loss_ratio', 0.0))
    record += '单笔最大盈利: {}\n\r'.format(cost_function_dict.get('earn_max', 0.0))
    record += '单笔最大亏损: {}\n\r'.format(cost_function_dict['loss_max'])
    record += '最大回撤比率: {}\n\r'.format(cost_function_dict.get('max_back_ratio', 0.0))
    record += '平均持仓时长: {} hours\n\r'.format(
              cost_function_dict.get('avg_hodl_time', 0.0))
    record += '盈利平均持仓时长: {} hours\n\r'.format(
              cost_function_dict.get('avg_earn_hodl_time', 0.0))
    record += '亏损平均持仓时长: {} hours\n\r'.format(
              cost_function_dict.get('avg_loss_hodl_time', 0.0))

    trade_records_txt = ''
    for i in trade_records:
        trade_records_txt += str(i) + '\n'

    with open(filename, 'w') as f:
        f.write(str(record)+'\n\n'+trade_records_txt)


def collect_trade_log(order_dict_list, balance_dict_list, filename):
    order_dict_list = order_dict_list[1:]
    trade_records = []
    for i in range(0, len(order_dict_list)-1):
        if order_dict_list[i]['direct'] == 'open':
            fee = order_dict_list[i]['fee'] + order_dict_list[i+1]['fee']
            open_usdt = balance_dict_list[i]['balance']
            earn = balance_dict_list[i+2]['balance'] - open_usdt
            total = balance_dict_list[i+2]['balance']

            one_log = [order_dict_list[i]['time'], order_dict_list[i]['price'],
                       'long', order_dict_list[i+1]['time'],
                       order_dict_list[i+1]['price'],
                       fee, open_usdt, earn, total]
            trade_records.append(one_log)

    trade_records_txt = ''
    for i in trade_records:
        trade_records_txt += str(i) + '\n'

    # with open(filename, 'w') as f:
    #     f.write(trade_records_txt)
    #
    # print 'trade_records generated~'

    fee_sum = 0
    earn_num = 0
    loss_num = 0
    only_earn_sum = 0
    only_loss_sum = 0
    earn_max = trade_records[0][7]
    loss_max = trade_records[0][7]
    earn_hodl_time = 0
    loss_hodl_time = 0
    balance_range = []
    case_1 = 0
    case_2 = 0
    for each_trade in trade_records:
        fee_sum += each_trade[5]
        balance_range.append(each_trade[8])
        earn = each_trade[7]
        # case = each_trade[9]
        if (earn >= 0):
            earn_num += 1
            only_earn_sum += earn
            earn_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))
        else:
            loss_num += 1
            only_loss_sum += earn
            loss_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))

        if earn_max < earn:
            earn_max = earn
        elif loss_max > earn:
            loss_max = earn
        # if  case == 'case_one':
        #     case_1 += 1
        # elif case == 'case_two':
        #     case_2 += 1

    record = ''
    cost_function_dict = {}
    # record += '条件一: ' + str(case_1) + '\n\r'
    # record += '条件二: ' + str(case_2) + '\n\r'
    init_fund = balance_dict_list[0]['balance']
    init_fund = round(init_fund, 3)
    cost_function_dict['init_fund'] = init_fund
    record += '资金初始额: ' + str(init_fund) + '\n\r'

    total_earn = balance_dict_list[-1]['balance'] - init_fund
    total_earn = total_earn + fee_sum
    total_earn = round(total_earn, 3)
    cost_function_dict['total_earn'] = total_earn
    record += '总盈利: ' + str(total_earn) + '\n\r'

    fee_sum = fee_sum
    fee_sum = round(fee_sum, 3)
    cost_function_dict['fee_sum'] = fee_sum
    record += '手续费总额: ' + str(fee_sum) + '\n\r'

    pure_earn = balance_dict_list[-1]['balance'] - init_fund
    pure_earn = round(pure_earn, 3)
    cost_function_dict['pure_earn'] = pure_earn
    record += '绝对盈利: ' + str(pure_earn) + '\n\r'

    earn_num = earn_num
    cost_function_dict['earn_num'] = earn_num
    record += '盈利次数: ' + str(earn_num) + '\n\r'

    loss_num = loss_num
    cost_function_dict['loss_num'] = loss_num
    record += '亏损次数: ' + str(loss_num) + '\n\r'

    win_ratio = float(earn_num)/(earn_num+loss_num)
    win_ratio = round(win_ratio, 3)
    cost_function_dict['win_ratio'] = win_ratio
    record += '胜率: ' + str(win_ratio) + '\n\r'

    if (earn_num != 0):
        avg_earn = float(only_earn_sum)/earn_num
        avg_earn = round(avg_earn, 3)
        cost_function_dict['avg_earn'] = avg_earn
        record += '平均盈利大小: ' + str(avg_earn) + '\n\r'

    if (loss_num != 0):
        avg_loss = float(only_loss_sum)/loss_num
        avg_loss = round(avg_loss, 3)
        cost_function_dict['avg_loss'] = avg_loss
        record += '平均亏损大小: ' + str(avg_loss) + '\n\r'

        if (earn_num != 0):

            earn_loss_ratio = float(avg_earn)/avg_loss
            if avg_earn > avg_loss and earn_loss_ratio < 0:
                earn_loss_ratio = -earn_loss_ratio
            earn_loss_ratio = round(earn_loss_ratio, 3)
            cost_function_dict['earn_loss_ratio'] = earn_loss_ratio
            record += '盈亏比: ' + str(earn_loss_ratio) + '\n\r'

    earn_max = earn_max
    earn_max = round(earn_max, 3)
    cost_function_dict['earn_max'] = earn_max
    record += '单笔最大盈利: ' + str(earn_max) + '\n\r'

    loss_max = loss_max
    loss_max = round(loss_max, 3)
    cost_function_dict['loss_max'] = loss_max
    record += '单笔最大亏损: ' + str(loss_max) + '\n\r'

    back_ratio = []
    for i in range(0, len(balance_range)-1):
        back_ratio.append(((balance_range[i] - balance_range[i+1]) /
                           float(balance_range[i])))
    back_ratio.sort()
    # back_ratio.reverse()
    back_ratio = back_ratio[:3]
    sum = 0
    for i in back_ratio:
        sum += i

    max_back_ratio = sum/3.0
    max_back_ratio = round(max_back_ratio, 3)
    cost_function_dict['max_back_ratio'] = max_back_ratio
    record += '最大回撤比率: ' + str(max_back_ratio) + '\n\r'

    avg_hodl_time = ((earn_hodl_time + loss_hodl_time) /
                     float(earn_num + loss_num))
    avg_hodl_time = avg_hodl_time/3600
    avg_hodl_time = round(avg_hodl_time, 3)
    cost_function_dict['avg_hodl_time'] = avg_hodl_time
    record += '平均持仓时长: ' + str(avg_hodl_time)+' hours' + '\n\r'

    if earn_num != 0:
        avg_earn_hodl_time = earn_hodl_time/float(earn_num)
        avg_earn_hodl_time = avg_earn_hodl_time/3600
        avg_earn_hodl_time = round(avg_earn_hodl_time, 3)
        cost_function_dict['avg_earn_hodl_time'] = avg_earn_hodl_time
        record += '盈利平均持仓时长: ' + str(avg_earn_hodl_time)+' hours' + '\n\r'

    if loss_num != 0:
        avg_loss_hodl_time = loss_hodl_time/float(loss_num)
        avg_loss_hodl_time = avg_loss_hodl_time/3600
        avg_loss_hodl_time = round(avg_loss_hodl_time, 3)
        cost_function_dict['avg_loss_hodl_time'] = avg_loss_hodl_time
        record += '亏损平均持仓时长: ' + str(avg_loss_hodl_time)+' hours' + '\n\r'

    with open(filename, 'w') as f:
        f.write(str(record)+'\n\n'+trade_records_txt)

    balance_range = balance_range
    drawing.save_balance_fig(balance_range, filename[:-4]+'_balance.jpg')


def manage_trade_dict_list(trade_dict_list):
    money = 10000.0
    qty = 0
    fee_ratio = 0.003
    earn_sum = 0
    trade_log = []
    trade_dict_list_2 = []
    for trade_dict in trade_dict_list:
        try:
            if (trade_dict['status'] == 'drop'):
                continue
            open_price = trade_dict['open_price']
            close_price = trade_dict['close_price']
            fee_1 = money * fee_ratio
            qty = (money - fee_1) / open_price
            close_money = qty * close_price
            fee_2 = close_money * fee_ratio
            earn = close_money - money - fee_2
            trade_dict['earn'] = earn
            trade_log.append({'earn': earn, 'rsi': trade_dict['rsi']})
            trade_dict_list_2.append(trade_dict)
            earn_sum += earn
        except:
            print(trade_dict)
    return earn_sum, trade_log, trade_dict_list_2


def generate_short_trade_log(order_records):
    trade_records = []
    for i in range(0, len(order_records)-1):
        if order_records[i][2] == 'open':
            fee = order_records[i][3] + order_records[i+1][3]
            open_usdt = order_records[i][3] + order_records[i][4]
            earn = order_records[i+1][4] - open_usdt
            total = order_records[i+1][4]
            try:
                one_log = [order_records[i][0], order_records[i][1], 'short',
                           order_records[i+1][0], order_records[i+1][1],
                           fee, open_usdt, earn, total, order_records[i+1][5],
                           order_records[i][6], order_records[i][7]]
            except:
                one_log = [order_records[i][0], order_records[i][1], 'short',
                           order_records[i+1][0], order_records[i+1][1],
                           fee, open_usdt, earn, total, order_records[i+1][5],
                           order_records[i][6]]
            trade_records.append(one_log)

    trade_records_txt = ''
    for i in trade_records:
        trade_records_txt += str(i) + '\n'

    fee_sum = 0
    earn_num = 0
    loss_num = 0
    only_earn_sum = 0
    only_loss_sum = 0
    earn_max = trade_records[0][7]
    loss_max = trade_records[0][7]
    earn_hodl_time = 0
    loss_hodl_time = 0
    balance_dict_list = []
    case_1 = 0
    case_2 = 0
    for each_trade in trade_records:
        fee_sum += each_trade[5]
        balance_dict = {}
        balance_dict['timestamp'] = int(to_timestamp(each_trade[3]))
        balance_dict['balance_num'] = each_trade[8]
        balance_dict_list.append(balance_dict)
        earn = each_trade[7]
        case = each_trade[9]
        if earn >= 0:
            earn_num += 1
            only_earn_sum += earn
            earn_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))
        else:
            loss_num += 1
            only_loss_sum += earn
            loss_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))

        if (earn_max < earn):
            earn_max = earn
        elif (loss_max > earn):
            loss_max = earn
        if (case == 'case_one'):
            case_1 += 1
        elif (case == 'case_two'):
            case_2 += 1

    cost_function_dict = {}
    cost_function_dict['case_1'] = case_1
    cost_function_dict['case_2'] = case_2

    init_fund = order_records[0][3] + order_records[0][4]
    cost_function_dict['init_fund'] = round(init_fund, 3)

    total_earn = order_records[-1][4] - init_fund
    total_earn = total_earn + fee_sum
    cost_function_dict['total_earn'] = round(total_earn, 3)

    cost_function_dict['fee_sum'] = round(fee_sum, 3)

    pure_earn = order_records[-1][4] - init_fund
    cost_function_dict['pure_earn'] = round(pure_earn, 3)

    cost_function_dict['earn_num'] = earn_num

    cost_function_dict['loss_num'] = loss_num

    win_ratio = float(earn_num)/(earn_num+loss_num)
    cost_function_dict['win_ratio'] = round(win_ratio, 3)

    if (earn_num != 0):
        avg_earn = float(only_earn_sum)/earn_num
        cost_function_dict['avg_earn'] = round(avg_earn, 3)

    if (loss_num != 0):
        avg_loss = float(only_loss_sum)/loss_num
        cost_function_dict['avg_loss'] = round(avg_loss, 3)

        if (earn_num != 0):

            earn_loss_ratio = float(avg_earn)/avg_loss
            if ((avg_earn > avg_loss) and (earn_loss_ratio < 0)):
                earn_loss_ratio = -earn_loss_ratio
            cost_function_dict['earn_loss_ratio'] = round(earn_loss_ratio, 3)

    cost_function_dict['earn_max'] = round(earn_max, 3)

    cost_function_dict['loss_max'] = round(loss_max, 3)

    back_ratio = []
    for i in range(0, len(balance_dict_list)):
        try:
            back_ratio.append(((balance_dict[i]['balance_num'] - balance_dict[i+1]['balance_num']) /
                               float(balance_dict[i]['balance_num'])))
        except Exception as e:
            pass
    back_ratio.sort()
    # back_ratio.reverse()
    back_ratio = back_ratio[:3]
    sum = 0
    for i in back_ratio:
        sum += i

    max_back_ratio = sum/3.0
    cost_function_dict['max_back_ratio'] = round(max_back_ratio, 3)

    avg_hodl_time = ((earn_hodl_time + loss_hodl_time) /
                     float(earn_num + loss_num))
    avg_hodl_time = avg_hodl_time/3600
    cost_function_dict['avg_hodl_time'] = round(avg_hodl_time, 3)

    if earn_num != 0:
        avg_earn_hodl_time = earn_hodl_time/float(earn_num)
        avg_earn_hodl_time = avg_earn_hodl_time/3600
        cost_function_dict['avg_earn_hodl_time'] = round(avg_earn_hodl_time, 3)

    if loss_num != 0:
        avg_loss_hodl_time = loss_hodl_time/float(loss_num)
        avg_loss_hodl_time = avg_loss_hodl_time/3600
        cost_function_dict['avg_loss_hodl_time'] = round(avg_loss_hodl_time, 3)

    return cost_function_dict, balance_dict_list, trade_records


def generate_short_trade_log_filter(order_records, filter_dict):
    # copy long
    indicator = filter_dict['indicator']
    start = filter_dict['start']
    end = filter_dict['end']
    balance_range = []
    balance_range.append(order_records[0][3] + order_records[0][4])
    for i in range(0, len(order_records)-1):
        if ((order_records[i][2] == 'open') and
           (start <= order_records[i][6][indicator] <= end)):
            fee = order_records[i][3] + order_records[i+1][3]
            open_usdt = order_records[i][3] + order_records[i][4]
            earn = order_records[i+1][4] - open_usdt
            last_balance = balance_range[-1]
            new_balance = last_balance + earn
            balance_range.append(new_balance)
        else:
            pass

    return balance_range


# def generate_short_trade_log_filter(order_records, filter_dict):
#     indicator = filter_dict['indicator']
#     start = filter_dict['start']
#     end = filter_dict['end']
#     balance_range = []
#     for i in range(0, len(order_records)-1):
#         if ((order_records[i][2] == 'open') and
#            (start < order_records[i][6] < end)):
#             total = order_records[i+1][4]
#             balance_range.append(total)
#         else:
#             pass
#
#     return balance_range


def generate_arbitrage_trade_log(order_records):
    trade_records = []
    init_spread = 0
    for i in range(0, len(order_records)-1):
        if order_records[i][2] == 'open':
            open_spread = order_records[i][1]
            close_spread = order_records[i+1][1]
            fee = 0
            open_usdt = init_spread
            earn = close_spread - open_spread
            total = init_spread + earn
            init_spread = total
            try:
                one_log = [order_records[i][0], order_records[i][1], 'long',
                           order_records[i+1][0], order_records[i+1][1],
                           fee, open_usdt, earn, total, order_records[i+1][5],
                           order_records[i][6], order_records[i][7],
                           order_records[i][8]]
            except:
                one_log = [order_records[i][0], order_records[i][1], 'long',
                           order_records[i+1][0], order_records[i+1][1],
                           fee, open_usdt, earn, total, order_records[i+1][5],
                           order_records[i][6], order_records[i][7]]
            trade_records.append(one_log)

    case_1 = 0
    case_2 = 0
    init_fund = 0
    total_earn = 0
    fee_sum = 0
    pure_earn = 0
    earn_num = 0
    loss_num = 0
    win_ratio = 0
    avg_earn = 0
    avg_loss = 0
    earn_loss_ratio = 0
    earn_max = 0
    loss_max = 0
    max_back_ratio = 0
    avg_hodl_time = 0
    avg_earn_hodl_time = 0
    avg_loss_hodl_time = 0
    only_earn_sum = 0
    only_loss_sum = 0
    earn_max = trade_records[0][7]
    loss_max = trade_records[0][7]
    earn_hodl_time = 0
    loss_hodl_time = 0
    balance_dict_list = []

    avg_earn_hodl_time = 0

    for each_trade in trade_records:
        fee_sum += each_trade[5]
        balance_dict = {}
        balance_dict['timestamp'] = int(to_timestamp(each_trade[3]))
        balance_dict['balance_num'] = each_trade[8]
        balance_dict_list.append(balance_dict)
        earn = each_trade[7]
        case = each_trade[9]
        if earn >= 0:
            earn_num += 1
            only_earn_sum += earn
            earn_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))
        else:
            loss_num += 1
            only_loss_sum += earn
            loss_hodl_time += (int(to_timestamp(each_trade[3])) -
                               int(to_timestamp(each_trade[0])))

        each_trade[5] = round(each_trade[5], 3)
        each_trade[6] = round(each_trade[6], 3)
        each_trade[7] = round(each_trade[7], 3)
        each_trade[8] = round(each_trade[8], 3)

        if (earn_max < earn):
            earn_max = earn
        elif (loss_max > earn):
            loss_max = earn
        if (case == 'case_one'):
            case_1 += 1
        elif (case == 'case_two'):
            case_2 += 1

    cost_function_dict = {}
    cost_function_dict['case_1'] = case_1
    cost_function_dict['case_2'] = case_2

    init_fund = order_records[0][3] + order_records[0][4]
    cost_function_dict['init_fund'] = round(init_fund, 3)

    # total_earn = order_records[-1][4] - init_fund
    # total_earn = total_earn + fee_sum
    cost_function_dict['total_earn'] = round(init_spread, 3)

    cost_function_dict['fee_sum'] = round(fee_sum, 3)

    # pure_earn = order_records[-1][4] - init_fund
    cost_function_dict['pure_earn'] = round(init_spread, 3)

    cost_function_dict['earn_num'] = earn_num

    cost_function_dict['loss_num'] = loss_num

    if ((earn_num != 0) and (loss_num != 0)):
        win_ratio = float(earn_num) / (earn_num + loss_num)
        win_ratio = round(win_ratio, 3)
    cost_function_dict['win_ratio'] = win_ratio

    if ((earn_num != 0) and (only_earn_sum != 0)):
        avg_earn = float(only_earn_sum) / earn_num
    cost_function_dict['avg_earn'] = round(avg_earn, 3)

    if ((loss_num != 0) and (only_loss_sum != 0)):
        avg_loss = float(only_loss_sum) / loss_num
    cost_function_dict['avg_loss'] = round(avg_loss, 3)

    if ((earn_num != 0) and (avg_earn != 0) and (avg_loss != 0)):
        earn_loss_ratio = float(avg_earn) / avg_loss
        if ((avg_earn > avg_loss) and (earn_loss_ratio < 0)):
            earn_loss_ratio = -earn_loss_ratio
    cost_function_dict['earn_loss_ratio'] = round(earn_loss_ratio, 3)

    earn_max = earn_max
    cost_function_dict['earn_max'] = round(earn_max, 3)

    loss_max = loss_max
    cost_function_dict['loss_max'] = round(loss_max, 3)

    back_ratio = []
    for balance_dict in balance_dict_list:
        try:
            back_ratio.append(((balance_dict['balance_num'] - balance_dict['balance_num']) /
                               float(balance_dict['balance_num'])))
        except Exception as e:
            pass
    back_ratio.sort()
    # back_ratio.reverse()
    back_ratio = back_ratio[:3]
    sum = 0
    for i in back_ratio:
        sum += i

    if (sum != 0):
        max_back_ratio = sum / 3.0
    cost_function_dict['max_back_ratio'] = round(max_back_ratio, 3)

    if (((earn_hodl_time > 0) or (loss_hodl_time > 0)) and
       ((earn_num > 0) or (loss_num > 0))):
        avg_hodl_time = ((earn_hodl_time + loss_hodl_time) /
                         float(earn_num + loss_num))
        avg_hodl_time = avg_hodl_time / 3600
    cost_function_dict['avg_hodl_time'] = round(avg_hodl_time, 3)

    if ((earn_num != 0) and (earn_hodl_time > 0)):
        avg_earn_hodl_time = earn_hodl_time/float(earn_num)
        avg_earn_hodl_time = avg_earn_hodl_time/3600
    cost_function_dict['avg_earn_hodl_time'] = round(avg_earn_hodl_time, 3)

    if ((loss_num != 0) and (loss_hodl_time > 0)):
        avg_loss_hodl_time = loss_hodl_time / float(loss_num)
        avg_loss_hodl_time = avg_loss_hodl_time / 3600
    cost_function_dict['avg_loss_hodl_time'] = round(avg_loss_hodl_time, 3)

    return cost_function_dict, balance_dict_list, trade_records
