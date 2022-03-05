
from dao_strategy.db.dt_models import DaoLog


def save_log(log_dict):
    log_level = log_dict['log_level']
    log_type = log_dict['log_type']
    user_name = log_dict['user_name']
    user_id = log_dict['user_id']
    phone_num = log_dict['phone_num']
    log_message = log_dict['log_message']


    strategy_name = log_dict.get('strategy_name', '')
    strategy_instance_id = log_dict.get('strategy_instance_id', '')
    strategy_type = log_dict.get('strategy_type', '')
    account_type = log_dict.get('account_type', '')
    exchange = log_dict.get('exchange', '')
    symbol = log_dict.get('symbol', '')

    dao_log = DaoLog(log_level=log_level, log_type=log_type,
                     user_name=user_name, user_id=user_id,
                     phone_num=phone_num, log_message=log_message,
                     strategy_name=strategy_name,
                     strategy_instance_id=strategy_instance_id,
                     strategy_type=strategy_type,
                     account_type=account_type,
                     exchange=exchange, symbol=symbol)
    dao_log.save()


def get_page_rst(total_count, page_num, page_limit):
    total_page_num = total_count / page_limit
    total_page_num = int(total_page_num)
    page_num_list = list(range(1, total_page_num+1))
    if (total_page_num > 5):
        if (page_num <= 3):
            page_num_list_ = list(range(1, 6))
        else:
            page_num_list_ = page_num_list[page_num-3:page_num+2]
            if len(page_num_list_) < 5:
                page_num_list_ = page_num_list[-5:]
        page_num_list = page_num_list_
    return page_num_list


def get_logs(user_id, page_num, page_limit, strategy_instance_id):
    page_limit = int(page_limit)
    page_num = int(page_num)
    offset = (page_num - 1) * page_limit
    total_count = DaoLog.objects.filter(user_id=user_id,
                  strategy_instance_id=strategy_instance_id
                  ).count()
    dao_logs = DaoLog.objects.filter(
               user_id=user_id,
               strategy_instance_id=strategy_instance_id
               ).skip(offset).limit(page_limit).order_by('-log_timestamp')
    page_num_list = get_page_rst(total_count, page_num, page_limit)
    dao_log_dict_list = [dl.to_dict() for dl in dao_logs]
    status = 1
    data = {}
    data['page_num'] = page_num
    data['page_num_list'] = page_num_list
    data['dao_log_dict_list'] = dao_log_dict_list
    return status, data
