import os
import ast
import hmac
import json
import hashlib
import thriftpy2
import traceback

from thriftpy2.rpc import make_client

from dao_strategy.settings.config import cfg


class DaoQuote(object):

    def __init__(self):
        self.source = 'dao_strategy'
        rpc_cfg = cfg['rpc']['dao_quote']
        file_path = os.path.split(os.path.realpath(__file__))[0]
        filename = '{}/dao_quote.thrift'.format(file_path)
        dq_thrift = thriftpy2.load(filename, module_name='dq_thrift')
        self.dq_thrift = make_client(dq_thrift.DaoQuote, rpc_cfg['host'], rpc_cfg['port'], timeout=10000)
        self.rpc_token = rpc_cfg['token']

    def make_sig(self, *args):
        content = ','.join(args)
        sig = hmac.new(self.rpc_token.encode("utf8"),
                       msg=content.encode("utf8"),
                       digestmod=hashlib.sha256).hexdigest()
        sig = '{}.{}'.format(self.source, sig)
        return sig

    def load_resp(self, resp):
        resp = json.loads(resp)
        status = resp['status']
        data = resp['data']
        return status, data

    def get_ticker(self, exchange, symbol):
        status = 1
        try:
            sig = self.make_sig('get_ticker', exchange, symbol)
            resp = self.dq_thrift.get_ticker(sig, exchange, symbol)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_kline(self, exchange, symbol):
        status = 1
        try:
            sig = self.make_sig('get_kline', exchange, symbol)
            resp = self.dq_thrift.get_kline(sig, exchange, symbol)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_depth(self, exchange, symbol):
        status = 1
        try:
            sig = self.make_sig('get_depth', exchange, symbol)
            resp = self.dq_thrift.get_depth(sig, exchange, symbol)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_spread_line(self, exchange_a, symbol_a, exchange_b, symbol_b, period):
        try:
            sig = self.make_sig('get_spread_line', exchange_a, symbol_a, exchange_b, symbol_b, period)
            resp = self.dq_thrift.get_spread_line(sig, exchange_a, symbol_a, exchange_b, symbol_b, period)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_backtest_kline_db(self, exchange, symbol, period, begin_timestamp, end_timestamp):
        try:
            sig = self.make_sig('get_backtest_kline_db', exchange, symbol, period, begin_timestamp, end_timestamp)
            resp = self.dq_thrift.get_backtest_kline_db(sig, exchange, symbol, period, begin_timestamp, end_timestamp)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_kline_db(self, exchange, symbol, period, num, end_timestamp):
        try:
            sig = self.make_sig('get_kline_db', exchange, symbol, period, num, end_timestamp)
            resp = self.dq_thrift.get_kline_db(sig, exchange, symbol, period, num, end_timestamp)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_sqlite_klines_df(self, exchange, symbol, begin_timestamp, end_timestamp):
        try:
            sig = self.make_sig('get_sqlite_klines_df', exchange, symbol, begin_timestamp, end_timestamp)
            resp = self.dq_thrift.get_sqlite_klines_df(sig, exchange, symbol, begin_timestamp, end_timestamp)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_hfd(self, exchange, symbol, type_list, begin_timestamp, end_timestamp):
        try:
            sig = self.make_sig('get_hfd', exchange, symbol, type_list, begin_timestamp, end_timestamp)
            resp = self.dq_thrift.get_hfd(sig, exchange, symbol, type_list, begin_timestamp, end_timestamp)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_trade_dict_list(self, exchange, symbol, begin_timestamp, end_timestamp):
        try:
            sig = self.make_sig('get_trade_dict_list', exchange, symbol, begin_timestamp, end_timestamp)
            resp = self.dq_thrift.get_trade_dict_list(sig, exchange, symbol, begin_timestamp, end_timestamp)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def download_dao_quote(self, begin_time, end_time):
        try:
            sig = self.make_sig('download_dao_quote', begin_time, end_time)
            resp = self.dq_thrift.download_dao_quote(sig, begin_time, end_time)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data
