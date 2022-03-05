import time
import datetime

from bson.objectid import ObjectId
from mongoengine import fields
from mongoengine import connect
from mongoengine import Document, EmbeddedDocument

from dao_strategy.settings.config import cfg


def get_connect():
    db_name = 'dao_trade'
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


alias_db = 'dt'
get_connect()


class User(Document):
    meta = {'db_alias': alias_db}
    created_time = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    user_name = fields.StringField(max_length=250)
    phone_num = fields.StringField(max_length=250)
    phone_zone_code = fields.StringField(max_length=250)
    password = fields.StringField(max_length=64)
    sms_vcode = fields.StringField(default='')
    img_vcode = fields.StringField(default='')
    ex_aes_key = fields.StringField(default='', max_length=64)
    invitor = fields.StringField(max_length=250)
    feishu_api = fields.StringField(default='', max_length=250)
    agree = fields.StringField(max_length=250)
    google_auth_secret = fields.StringField(default='', max_length=250)
    exchange = fields.DictField()

    def __unicode__(self):
        return self.user_name


class ExAccount(Document):
    meta = {'db_alias': alias_db}
    created_time = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    user_id = fields.ObjectIdField(unique_with=['ex_account_name', 'exchange'])
    user_name = fields.StringField(max_length=250)
    phone_num = fields.StringField(max_length=250)
    ex_account_name = fields.StringField(default='', max_length=250)
    exchange = fields.StringField(default='', max_length=250)
    maker = fields.StringField(default='0', max_length=250)
    taker = fields.StringField(default='0', max_length=250)
    api_key = fields.StringField(default='', max_length=250)
    secret_key = fields.StringField(default='', max_length=250)
    broker_id = fields.StringField(default='', max_length=250)
    md_address = fields.StringField(default='', max_length=250)
    td_address = fields.StringField(default='', max_length=250)
    ctp_taker = fields.StringField(default='0', max_length=250)
    ctp_app_id = fields.StringField(default='', max_length=250)
    ctp_auth_code = fields.StringField(default='', max_length=250)

    def __unicode__(self):
        return self.user_name


class Order(Document):
    meta = {'db_alias': alias_db}
    order_datetime = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    order_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    user_name = fields.StringField(max_length=250)
    user_id = fields.ObjectIdField()
    phone_num = fields.StringField(max_length=250)
    exchange = fields.StringField(max_length=250)
    account_type = fields.StringField(max_length=250)  # default='api_bind',
    strategy_instance_id = fields.ObjectIdField(default=ObjectId)
    strategy_name = fields.StringField(max_length=250)  # default='manual',
    symbol = fields.StringField(max_length=250)
    order_type = fields.StringField(max_length=250)
    order_id = fields.StringField(max_length=250)
    price = fields.StringField(max_length=250)
    avg_price = fields.FloatField()
    quantity = fields.StringField(max_length=250)
    quantity_treaded = fields.FloatField()
    quantity_frozen = fields.FloatField()
    quantity_canceled = fields.FloatField()
    order_cancel_timestamp = fields.FloatField()
    order_deal_timestamp = fields.FloatField()
    order_status = fields.StringField(max_length=250)
    trading_day = fields.StringField(default='')

    def __unicode__(self):
        return self.order_id

    def to_dict(self):
        order_dict = {}
        order_dict['id'] =str(self.id)
        order_dict['order_datetime'] = str(self.order_datetime)
        order_dict['order_timestamp'] = self.order_timestamp
        order_dict['user_name'] = self.user_name
        order_dict['user_id'] = str(self.user_id)
        order_dict['phone_num'] = self.phone_num
        order_dict['exchange'] = self.exchange
        order_dict['account_type'] = self.account_type
        order_dict['strategy_instance_id'] = str(self.strategy_instance_id)
        order_dict['strategy_name'] = self.strategy_name
        order_dict['symbol'] = self.symbol
        order_dict['order_type'] = self.order_type
        order_dict['order_id'] = self.order_id
        order_dict['price'] = self.price
        order_dict['avg_price'] = self.avg_price
        order_dict['quantity'] = self.quantity
        order_dict['quantity_treaded'] = self.quantity_treaded
        order_dict['quantity_frozen'] = self.quantity_frozen
        order_dict['quantity_canceled'] = self.quantity_canceled
        order_dict['order_cancel_timestamp'] = self.order_cancel_timestamp
        order_dict['order_deal_timestamp'] = self.order_deal_timestamp
        order_dict['order_status'] = self.order_status
        return order_dict


class StrategyClass(Document):
    meta = {'db_alias': alias_db}
    strategy_datetime = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    strategy_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    strategy_type = fields.StringField(default='', max_length=250)
    strategy_name = fields.StringField(default='', max_length=250)
    strategy_exchange = fields.StringField(max_length=250)
    strategy_symbol = fields.StringField(max_length=250)
    strategy_description = fields.StringField(max_length=250)
    strategy_dir = fields.StringField(default='', max_length=250)
    strategy_file = fields.StringField(default='', max_length=250)
    strategy_class_name = fields.StringField(default='', max_length=250)
    strategy_param_dict = fields.DictField(default={}, blank=True)

    def __unicode__(self):
        return self.strategy_name

    def to_dict(self):
        sc_dict = {}
        sc_dict['id'] =str(self.id)
        sc_dict['strategy_datetime'] = str(self.strategy_datetime)
        sc_dict['strategy_timestamp'] = self.strategy_timestamp
        sc_dict['strategy_type'] = self.strategy_type
        sc_dict['strategy_name'] = self.strategy_name
        sc_dict['strategy_exchange'] = self.strategy_exchange
        sc_dict['strategy_symbol'] = self.strategy_symbol
        sc_dict['strategy_description'] = self.strategy_description
        sc_dict['strategy_dir'] = self.strategy_dir
        sc_dict['strategy_file'] = self.strategy_file
        sc_dict['strategy_class_name'] = self.strategy_class_name
        sc_dict['strategy_param_dict'] = self.strategy_param_dict
        return sc_dict


class StrategyInstance(Document):
    meta = {'db_alias': alias_db}
    strategy_datetime = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    strategy_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    user_name = fields.StringField(max_length=250)
    user_id = fields.ObjectIdField()
    phone_num = fields.StringField(max_length=250)
    exchange = fields.StringField(max_length=250)
    exchange_2 = fields.StringField(default='', max_length=250)
    account_type = fields.StringField(max_length=250)
    account_type_2 = fields.StringField(default='', max_length=250)
    strategy_name = fields.StringField(default='', max_length=250)
    strategy_type = fields.StringField(max_length=250)
    symbol = fields.StringField(max_length=250)
    symbol_2 = fields.StringField(default='', max_length=250)
    one_time_buy = fields.FloatField(default=0.0)
    sms_send = fields.StringField(default='yes', max_length=250)
    spread_usdt = fields.FloatField(default=0.0)
    max_trade_num = fields.FloatField(default=0.0)
    min_trade_num = fields.FloatField(default=0.0)
    param_dict = fields.DictField(default={}, blank=True)
    status = fields.StringField(max_length=250)
    status_dict = fields.DictField(default={}, blank=True)
    pid = fields.IntField(default=-1)

    def __unicode__(self):
        return self.user_name

    def to_dict(self):
        si_dict = {}
        si_dict['id'] =str(self.id)
        si_dict['strategy_datetime'] = str(self.strategy_datetime)
        si_dict['strategy_timestamp'] = self.strategy_timestamp
        si_dict['user_name'] = self.user_name
        si_dict['user_id'] = str(self.user_id)
        si_dict['phone_num'] = self.phone_num
        si_dict['exchange'] = self.exchange
        si_dict['exchange_2'] = self.exchange_2
        si_dict['account_type'] = self.account_type
        si_dict['account_type_2'] = self.account_type_2
        si_dict['strategy_name'] = self.strategy_name
        si_dict['strategy_type'] = self.strategy_type
        si_dict['symbol'] = self.symbol
        si_dict['symbol_2'] = self.symbol_2
        si_dict['one_time_buy'] = self.one_time_buy
        si_dict['sms_send'] = self.sms_send
        si_dict['spread_usdt'] = self.spread_usdt
        si_dict['max_trade_num'] = self.max_trade_num
        si_dict['min_trade_num'] = self.min_trade_num
        si_dict['param_dict'] = self.param_dict
        si_dict['status'] = self.status
        si_dict['status_dict'] = self.status_dict
        si_dict['pid'] = self.pid
        return si_dict


class DaoLog(Document):
    meta = {'db_alias': alias_db}
    log_datetime = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    log_timestamp = fields.FloatField(
        default=time.time, editable=False,
    )
    log_level = fields.StringField(max_length=250)
    log_type = fields.StringField(max_length=250)
    user_name = fields.StringField(max_length=250)
    user_id = fields.ObjectIdField()
    phone_num = fields.StringField(max_length=250)
    log_message = fields.StringField()
    strategy_name = fields.StringField(max_length=250)
    strategy_instance_id = fields.StringField(max_length=250)
    strategy_type = fields.StringField(max_length=250)
    account_type = fields.StringField(max_length=250)
    exchange = fields.StringField(max_length=250)
    symbol = fields.StringField(max_length=250)

    def __unicode__(self):
        return self.log_level

    def to_dict(self):
        dl_dict = {}
        dl_dict['id'] =str(self.id)
        dl_dict['log_datetime'] = str(self.log_datetime)
        dl_dict['log_timestamp'] = self.log_timestamp
        dl_dict['log_level'] = self.log_level
        dl_dict['log_type'] = self.log_type
        dl_dict['user_name'] = self.user_name
        dl_dict['user_id'] = str(self.user_id)
        dl_dict['phone_num'] = self.phone_num
        dl_dict['log_message'] = self.log_message
        dl_dict['strategy_name'] = self.strategy_name
        dl_dict['strategy_instance_id'] = self.strategy_instance_id
        dl_dict['strategy_type'] = self.strategy_type
        dl_dict['account_type'] = self.account_type
        dl_dict['exchange'] = self.exchange
        dl_dict['symbol'] = self.symbol
        return dl_dict
