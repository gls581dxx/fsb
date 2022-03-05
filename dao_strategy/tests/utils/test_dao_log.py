import pathmagic

from dao_strategy.utils import dao_log


def test_save_log():
    log_dict = {}
    log_dict['log_level'] = 'info'
    log_dict['log_type'] = 'hh'
    log_dict['user_name'] = '15530290099'
    log_dict['user_id'] = '5cb452702a0aa544cd9e0bca'
    log_dict['phone_num'] = '15530290099'
    log_dict['log_message'] = ''
    dao_log.save_log(log_dict)


def test_get_logs():
    user_id = '5cb452702a0aa544cd9e0bca'
    page_num = '1'
    page_limit = '10'
    strategy_instance_id = ''
    status, data = dao_log.get_logs(user_id, page_num, page_limit, strategy_instance_id)
    print(status)
    print(data)


def main():
    test_save_log()
    test_get_logs()


if __name__ == '__main__':
    main()
