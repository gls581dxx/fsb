import time
import datetime

from bson.objectid import ObjectId
from mongoengine import fields
from mongoengine import connect
from mongoengine import Document, EmbeddedDocument

from dao_strategy.settings.config import cfg


def get_connect():
    db_name = 'dao_strategy'
    mongo_cfg = cfg['mongo'][db_name]
    mode = mongo_cfg['mode']
    connstr = mongo_cfg['connstr']
    db_name = mongo_cfg['db_name']
    db_user = mongo_cfg['db_user']
    db_pwd = mongo_cfg['db_pwd']
    if mode == 'ReplicaSet':
        repl_name = mongo_cfg['repl_name']
        connect(repl_name, host=connstr.format(db_user, db_pwd, db_name),
                alias=alias_db)
    elif mode == 'single':
        host, port = connstr.split(':')
        connect(db_name, host=host, port=int(port), username=db_user,
                password=db_pwd, alias=alias_db)
    else:
        print('[*] no db config, exit')
        sys.exit(0)


alias_db = 'ds'
get_connect()


class StrategyFile(Document):
    meta = {'db_alias': alias_db}
    strategy_file_datetime = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    create_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    last_timestamp = fields.FloatField(
        default=time.time
    )
    user_name = fields.StringField(default='')
    user_id = fields.ObjectIdField()
    phone_num = fields.StringField(default='')
    file_nick_name = fields.StringField(default='')
    file_content = fields.StringField(default='')
    file_description = fields.StringField(default='')
    delete_status = fields.IntField(default=0)

    def __unicode__(self):
        return self.user_name

    def to_dict(self):
        file_dict = {}
        file_dict['strategy_file_id'] = str(self.id)
        file_dict['strategy_file_datetime'] = str(self.strategy_file_datetime)
        file_dict['create_timestamp'] = self.create_timestamp
        file_dict['last_timestamp'] = self.last_timestamp
        file_dict['user_name'] = self.user_name
        file_dict['user_id'] = str(self.user_id)
        file_dict['phone_num'] = self.phone_num
        file_dict['file_nick_name'] = self.file_nick_name
        file_dict['file_content'] = self.file_content
        file_dict['file_description'] = self.file_description
        file_dict['delete_status'] = self.delete_status
        return file_dict


class StrategyJob(Document):
    meta = {'db_alias': alias_db}
    strategy_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    strategy_name = fields.StringField()
    strategy_file_id = fields.ObjectIdField()
    user_name = fields.StringField()
    user_id = fields.ObjectIdField()
    begin_time = fields.StringField()
    end_time = fields.StringField()
    period = fields.IntField(default=1)
    period_list = fields.ListField(default=[], blank=True)
    exchange = fields.StringField()
    symbol = fields.StringField()
    exchange_2 = fields.StringField(default='')
    symbol_2 = fields.StringField(default='')
    one_time_buy = fields.FloatField(default=0.0)
    direction = fields.StringField()
    log_record = fields.StringField(default='no')
    strategy_type = fields.StringField()
    balance_end = fields.FloatField(default=0.0)
    balance_front = fields.FloatField(default=0.0)
    taker_fee_ratio = fields.FloatField(default=0.0)
    maker_fee_ratio = fields.FloatField(default=0.0)
    param_1_start = fields.StringField()
    param_1_end = fields.StringField(default='')
    param_1_step = fields.StringField(default='')
    param_2_start = fields.StringField()
    param_2_end = fields.StringField(default='')
    param_2_step = fields.StringField(default='')
    indicator_config = fields.DictField(default={}, blank=True)
    file_nick_name = fields.StringField(default='')
    file_content = fields.StringField(default='')
    file_description = fields.StringField(default='')
    exception = fields.IntField(default=0)
    exception_msg = fields.StringField(default='None')
    status = fields.StringField()

    def __unicode__(self):
        return self.user_name

    def to_dict(self):
        sj_dict = {}
        sj_dict['id'] = str(self.id)
        sj_dict['strategy_job_id'] = str(self.id)
        sj_dict['strategy_timestamp'] = self.strategy_timestamp
        sj_dict['strategy_name'] = self.strategy_name
        sj_dict['strategy_file_id'] = str(self.strategy_name)
        sj_dict['user_name'] = self.user_name
        sj_dict['user_id'] = str(self.user_id)
        sj_dict['begin_time'] = self.begin_time
        sj_dict['end_time'] = self.end_time
        sj_dict['period'] = self.period
        sj_dict['period_list'] = self.period_list
        sj_dict['exchange'] = self.exchange
        sj_dict['symbol'] = self.symbol
        sj_dict['exchange_2'] = self.exchange_2
        sj_dict['symbol_2'] = self.symbol_2
        sj_dict['one_time_buy'] = self.one_time_buy
        sj_dict['direction'] = self.direction
        sj_dict['log_record'] = self.log_record
        sj_dict['strategy_type'] = self.strategy_type
        sj_dict['balance_end'] = self.balance_end
        sj_dict['balance_front'] = self.balance_front
        sj_dict['taker_fee_ratio'] = self.taker_fee_ratio
        sj_dict['maker_fee_ratio'] = self.maker_fee_ratio
        sj_dict['param_1_start'] = self.param_1_start
        sj_dict['param_1_end'] = self.param_1_end
        sj_dict['param_1_step'] = self.param_1_step
        sj_dict['param_2_start'] = self.param_2_start
        sj_dict['param_2_end'] = self.param_2_end
        sj_dict['param_2_step'] = self.param_2_step
        sj_dict['indicator_config'] = self.indicator_config
        sj_dict['file_nick_name'] = self.file_nick_name
        sj_dict['file_content'] = self.file_content
        sj_dict['file_description'] = self.file_description
        sj_dict['exception'] = self.exception
        sj_dict['exception_msg'] = self.exception_msg
        sj_dict['status'] = self.status
        return sj_dict


class StrategyTask(Document):
    meta = {'db_alias': alias_db}
    strategy_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    strategy_name = fields.StringField()
    strategy_job_id = fields.ObjectIdField()
    user_name = fields.StringField()
    user_id = fields.ObjectIdField()
    begin_time = fields.StringField()
    end_time = fields.StringField()
    period = fields.IntField(default=1)
    period_list = fields.ListField(default=[], blank=True)
    exchange = fields.StringField()
    symbol = fields.StringField()
    exchange_2 = fields.StringField(default='')
    symbol_2 = fields.StringField(default='')
    one_time_buy = fields.FloatField(default=0.0)
    direction = fields.StringField()
    log_record = fields.StringField(default='no')
    strategy_type = fields.StringField()
    file_path = fields.StringField(default='')
    filename = fields.StringField(default='')
    balance_end = fields.FloatField(default=0.0)
    balance_front = fields.FloatField(default=0.0)
    taker_fee_ratio = fields.FloatField(default=0.0)
    maker_fee_ratio = fields.FloatField(default=0.0)
    param_1 = fields.FloatField()
    param_2 = fields.FloatField()
    indicator_config = fields.DictField(default={}, blank=True)
    exception = fields.IntField(default=0)
    exception_msg = fields.StringField(default='None')
    status = fields.StringField()
    processor_id = fields.StringField(default='1')
    processor_ip = fields.StringField(default='127.0.0.1')
    processor_pid = fields.StringField(default='-1')

    balance = fields.FloatField(default=0.0)
    case_1 = fields.IntField(default=0)
    case_2 = fields.IntField(default=0)
    init_fund = fields.FloatField(default=0.0)
    total_earn = fields.FloatField(default=0.0)
    fee_sum = fields.FloatField(default=0.0)
    pure_earn = fields.FloatField(default=0.0)
    earn_num = fields.IntField(default=0)
    loss_num = fields.IntField(default=0)
    win_ratio = fields.FloatField(default=0.0)
    avg_earn = fields.FloatField(default=0.0)
    avg_loss = fields.FloatField(default=0.0)
    earn_loss_ratio = fields.FloatField(default=0.0)
    earn_max = fields.FloatField(default=0.0)
    loss_max = fields.FloatField(default=0.0)
    max_back_ratio = fields.FloatField(default=0.0)
    avg_hodl_time = fields.FloatField(default=0.0)
    avg_earn_hodl_time = fields.FloatField(default=0.0)
    avg_loss_hodl_time = fields.FloatField(default=0.0)
    n_order_records = fields.ListField(default=[], blank=True)
    order_records = fields.ListField(default=[], blank=True)
    trade_records = fields.ListField(default=[], blank=True)
    balance_range = fields.ListField(default=[], blank=True)

    def __unicode__(self):
        return self.user_name

    def to_dict(self):
        st_dict = {}
        st_dict['id'] = str(self.id)
        st_dict['strategy_task_id'] = str(self.id)
        st_dict['strategy_timestamp'] = self.strategy_timestamp
        st_dict['strategy_name'] = self.strategy_name
        st_dict['strategy_job_id'] = str(self.strategy_job_id)
        st_dict['user_name'] = self.user_name
        st_dict['user_id'] = str(self.user_id)
        st_dict['begin_time'] = self.begin_time
        st_dict['end_time'] = self.end_time
        st_dict['period'] = self.period
        st_dict['period_list'] = self.period_list
        st_dict['exchange'] = self.exchange
        st_dict['symbol'] = self.symbol
        st_dict['exchange_2'] = self.exchange_2
        st_dict['symbol_2'] = self.symbol_2
        st_dict['one_time_buy'] = self.one_time_buy
        st_dict['direction'] = self.direction
        st_dict['log_record'] = self.log_record
        st_dict['strategy_type'] = self.strategy_type
        st_dict['file_path'] = self.file_path
        st_dict['filename'] = self.filename
        st_dict['balance_end'] = self.balance_end
        st_dict['balance_front'] = self.balance_front
        st_dict['taker_fee_ratio'] = self.taker_fee_ratio
        st_dict['maker_fee_ratio'] = self.maker_fee_ratio
        st_dict['param_1'] = self.param_1
        st_dict['param_2'] = self.param_2
        st_dict['indicator_config'] = self.indicator_config
        st_dict['exception'] = self.exception
        st_dict['exception_msg'] = self.exception_msg
        st_dict['status'] = self.status
        st_dict['balance'] = self.balance
        st_dict['case_1'] = self.case_1
        st_dict['case_2'] = self.case_2
        st_dict['init_fund'] = self.init_fund
        st_dict['total_earn'] = self.total_earn
        st_dict['fee_sum'] = self.fee_sum
        st_dict['pure_earn'] = self.pure_earn
        st_dict['earn_num'] = self.earn_num
        st_dict['loss_num'] = self.loss_num
        st_dict['win_ratio'] = self.win_ratio
        st_dict['avg_earn'] = self.avg_earn
        st_dict['avg_loss'] = self.avg_loss
        st_dict['earn_loss_ratio'] = self.earn_loss_ratio
        st_dict['earn_max'] = self.earn_max
        st_dict['loss_max'] = self.loss_max
        st_dict['max_back_ratio'] = self.max_back_ratio
        st_dict['avg_hodl_time'] = self.avg_hodl_time
        st_dict['avg_earn_hodl_time'] = self.avg_earn_hodl_time
        st_dict['avg_loss_hodl_time'] = self.avg_loss_hodl_time
        st_dict['n_order_records'] = self.n_order_records
        st_dict['order_records'] = self.order_records
        st_dict['trade_records'] = self.trade_records
        st_dict['balance_range'] = self.balance_range
        return st_dict


class IndicatorConfig(Document):
    meta = {'db_alias': alias_db}
    indicator_datetime = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    indicator_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    indicator_name = fields.StringField(max_length=250)
    user_name = fields.StringField(max_length=250)
    user_id = fields.ObjectIdField()
    phone_zone_code = fields.StringField(max_length=250)
    phone_num = fields.StringField(max_length=250)
    begin_time = fields.StringField(max_length=250)
    end_time = fields.StringField(max_length=250)
    period_list = fields.ListField(default=[], blank=True)
    exchange = fields.StringField(max_length=250)
    symbol = fields.StringField(max_length=250)
    one_time_buy = fields.FloatField(default=0.0)
    direction = fields.StringField(max_length=250)
    indicator_type = fields.StringField(max_length=250)
    file_path = fields.StringField(default='', max_length=250)
    filename = fields.StringField(default='', max_length=250)
    func_name = fields.StringField(default='', max_length=250)
    indicator_file_id = fields.ObjectIdField()
    param_1_start = fields.StringField(max_length=250)
    param_1_end = fields.StringField(default='', max_length=250)
    param_1_step = fields.StringField(default='', max_length=250)
    param_2_start = fields.StringField(max_length=250)
    param_2_end = fields.StringField(default='', max_length=250)
    param_2_step = fields.StringField(default='', max_length=250)
    param_1 = fields.StringField(default='', max_length=250)
    param_2 = fields.StringField(default='', max_length=250)
    exception = fields.IntField(default=0)
    exception_msg = fields.StringField(default='None', max_length=25000)
    status = fields.StringField(max_length=250)

    def __unicode__(self):
        return self.user_name


class IndicatorBacktestRecord(Document):
    meta = {'db_alias': alias_db}
    create_time = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    create_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    user_name = fields.StringField(max_length=250)
    phone_num = fields.StringField(max_length=250)
    phone_zone_code = fields.StringField(max_length=250)
    indicator_config_id = fields.ObjectIdField()
    indicator_name = fields.StringField(default='', max_length=250)
    param_1 = fields.FloatField(default=0.0)
    param_2 = fields.FloatField(default=0.0)
    corr_5 = fields.FloatField(default=0.0)
    mean_5 = fields.FloatField(default=0.0)
    corr_10 = fields.FloatField(default=0.0)
    mean_10 = fields.FloatField(default=0.0)
    corr_30 = fields.FloatField(default=0.0)
    mean_30 = fields.FloatField(default=0.0)
    indicator_mean = fields.FloatField(default=0.0)
    indicator_std = fields.FloatField(default=0.0)
    balance = fields.FloatField(default=0.0)
    case_1 = fields.IntField(default=0)
    case_2 = fields.IntField(default=0)
    init_fund = fields.FloatField(default=0.0)
    total_earn = fields.FloatField(default=0.0)
    fee_sum = fields.FloatField(default=0.0)
    pure_earn = fields.FloatField(default=0.0)
    earn_num = fields.FloatField(default=0.0)
    loss_num = fields.FloatField(default=0.0)
    win_ratio = fields.FloatField(default=0.0)
    avg_earn = fields.FloatField(default=0.0)
    avg_loss = fields.FloatField(default=0.0)
    earn_loss_ratio = fields.FloatField(default=0.0)
    earn_max = fields.FloatField(default=0.0)
    loss_max = fields.FloatField(default=0.0)
    max_back_ratio = fields.FloatField(default=0.0)
    avg_hodl_time = fields.FloatField(default=0.0)
    avg_earn_hodl_time = fields.FloatField(default=0.0)
    avg_loss_hodl_time = fields.FloatField(default=0.0)
    order_records = fields.ListField(default=[], blank=True)
    trade_records = fields.ListField(default=[], blank=True)
    balance_range = fields.ListField(default=[], blank=True)
    exception = fields.IntField(default=0)
    exception_msg = fields.StringField(default='None', max_length=25000)

    def __unicode__(self):
        return self.user_name
