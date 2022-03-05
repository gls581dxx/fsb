import datetime as dt
import matplotlib.dates as md
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from dao_strategy.utils import convert


def save_all_in_test_pdf(filename, in_dict):
    with PdfPages(filename) as pdf:
        for indicator_name in in_dict:
            indicator_param_list = []
            indicator_score_list = []
            indicator_dict = in_dict[indicator_name]
            for i in sorted(indicator_dict.keys()):
                indicator_param_list.append(i)
                indicator_score_list.append(indicator_dict[i])

            title = ('indicator: {}').format(indicator_name)
            plt.xticks(rotation=25)
            plt.title(title)
            plt.plot(indicator_param_list, indicator_score_list,
                     linestyle='-', color='b', label='score')
            plt.axhline(99, color='g', label='strandard')
            plt.xlabel('param')
            plt.ylabel('score')
            plt.legend(loc='best')
            pdf.savefig()
            plt.close()
    return True


def save_params_fig(filename, strategy_tasks):
    with PdfPages(filename) as pdf:
        fig_row = 0
        for st in strategy_tasks:
            if len(st.trade_records) == 0:
                continue
            trade_records = st.trade_records
            param_1 = st.param_1
            param_2 = st.param_2
            trade_num = st.earn_num + st.loss_num
            win_ratio = st.win_ratio
            earn_loss_ratio = st.earn_loss_ratio
            balance = round(st.balance, 3)
            dates = []
            balance_list = []
            price_list = []
            for trade_record in trade_records:
                date = trade_record[3]
                timestamp = convert.to_timestamp(date)
                date = dt.datetime.fromtimestamp(int(timestamp))
                dates.append(date)
                balance_list.append(trade_record[8])
                price_list.append(trade_record[4])
            title = ('e: {}, s: {}, p1: {}, p2: {}, balance: {}, nums: {}, '
                    'wr: {}, elr: {}').format(st.exchange, st.symbol, param_1,
                    param_2, balance, trade_num, win_ratio, earn_loss_ratio)
            f, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 7), sharex=True)
            plt.xticks(rotation=25)
            xfmt = md.DateFormatter('%Y/%m/%d %H:%M:%S')
            ax1.xaxis.set_major_formatter(xfmt)
            ax2.xaxis.set_major_formatter(xfmt)
            f.suptitle(title)
            ax1.plot(dates, price_list, linestyle='-', color='g', label='Price')
            ax2.plot(dates, balance_list, linestyle='-', color='purple', label='PnL')
            ax1.legend(loc='best')
            ax2.legend(loc='best')
            ax1.set_ylabel('Price')
            ax2.set_ylabel('PnL')
            pdf.savefig()
            plt.close()
    return True
