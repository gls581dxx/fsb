import os
import ast
import sys
import hmac
import json
import uuid
import hashlib
import thriftpy2
import traceback

from thriftpy2.rpc import make_client

from dao_strategy.settings.config import cfg


class DaoStrategy(object):

    def __init__(self):
        self.source = 'dao_web'
        rpc_node = cfg['rpc_node']
        file_path = os.path.split(os.path.realpath(__file__))[0]
        filename = '{}/dao_strategy.thrift'.format(file_path)
        ds_thrift = thriftpy2.load(filename, module_name='ds_thrift')
        self.ds_thrift = make_client(ds_thrift.DaoStrategy, rpc_node['ip'], rpc_node['port'], timeout=10000)
        self.rpc_token = cfg['rpc_token']['dao_web']

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

    def get_strategies(self, strategy_type, page_num, page_limit):
        status = 1
        try:
            sig = self.make_sig('get_strategies', strategy_type, page_num,
                  page_limit)
            resp = self.ds_thrift.get_strategies(sig, strategy_type, page_num,
                   page_limit)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def run_strategy(self, user_id, strategy_instance_id, exchange, account_type, strategy_type, strategy_name, symbol, one_time_buy, sms_send):
        status = 1
        try:
            sig = self.make_sig('run_strategy', user_id,
                  strategy_instance_id, exchange, account_type, strategy_type,
                  strategy_name, symbol, one_time_buy, sms_send)
            resp = self.ds_thrift.run_strategy(sig, user_id,
                   strategy_instance_id, exchange, account_type,
                   strategy_type, strategy_name, symbol, one_time_buy,
                   sms_send)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def control_strategy(self, user_id, strategy_instance_id, order):
        try:
            sig = self.make_sig('control_strategy', user_id,
                  strategy_instance_id, order)
            resp = self.ds_thrift.control_strategy(sig, user_id,
                  strategy_instance_id, order)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_strategy_instance(self, user_id, strategy_type, status, page_num, page_limit):
        try:
            sig = self.make_sig('get_strategy_instance', user_id,
                  strategy_type, status, page_num, page_limit)
            resp = self.ds_thrift.get_strategy_instance(sig, user_id,
                   strategy_type, status, page_num, page_limit)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def submit_arbitrage_strategy(self, user_id, exchange_a, exchange_b, account_type_a, account_type_b, strategy_type, symbol_a, symbol_b, spread_usdt, max_trade_num, min_trade_num):
        try:
            sig = self.make_sig('submit_arbitrage_strategy', user_id,
                  exchange_a, exchange_b, account_type_a, account_type_b,
                  strategy_type, symbol_a, symbol_b, spread_usdt,
                  max_trade_num, min_trade_num)
            resp = self.ds_thrift.submit_arbitrage_strategy(sig, user_id,
                   exchange_a, exchange_b, account_type_a, account_type_b,
                   strategy_type, symbol_a, symbol_b, spread_usdt,
                   max_trade_num, min_trade_num)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_strategy_pnl(self, user_id, strategy_instance_id):
        try:
            sig = self.make_sig('get_strategy_pnl', user_id,
                  strategy_instance_id)
            resp = self.ds_thrift.get_strategy_pnl(sig, user_id,
                  strategy_instance_id)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def submit_conditional_strategy(self, user_id, exchange, account_type, strategy_type, strategy_name, symbol, one_time_buy, sms_send, param):
        try:
            sig = self.make_sig('submit_conditional_strategy', user_id,
                  exchange, account_type, strategy_type, strategy_name,
                  symbol, one_time_buy, sms_send, param)
            resp = self.ds_thrift.submit_conditional_strategy(sig, user_id,
                   exchange, account_type, strategy_type, strategy_name,
                   symbol, one_time_buy, sms_send, param)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_strategy_files(self, user_id, page_num, page_limit):
        try:
            sig = self.make_sig('get_strategy_files', user_id, page_num,
                  page_limit)
            resp = self.ds_thrift.get_strategy_files(sig, user_id,
                   page_num, page_limit)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def manage_strategy_file(self, action, user_id, strategy_file_id, file_nick_name, file_content, file_description):
        try:
            sig = self.make_sig('manage_strategy_file', action, user_id,
                  strategy_file_id, file_nick_name, file_content,
                  file_description)
            resp = self.ds_thrift.manage_strategy_file(sig, action, user_id,
                  strategy_file_id, file_nick_name, file_content,
                  file_description)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def submit_strategy_job(self, strategy_name, user_id, begin_time, end_time, period, exchange, symbol, exchange_2, symbol_2, one_time_buy, direction, log_record, strategy_type, balance_end, balance_front, taker_fee_ratio, maker_fee_ratio, strategy_file_id, param_1_start, param_1_end, param_1_step, param_2_start, param_2_end, param_2_step, indicator_config):
        try:
            sig = self.make_sig('submit_strategy_job', strategy_name, user_id, begin_time, end_time, period, exchange, symbol, exchange_2, symbol_2, one_time_buy, direction, log_record, strategy_type, balance_end, balance_front, taker_fee_ratio, maker_fee_ratio, strategy_file_id, param_1_start, param_1_end, param_1_step, param_2_start, param_2_end, param_2_step, indicator_config)
            resp = self.ds_thrift.submit_strategy_job(sig, strategy_name, user_id, begin_time, end_time, period, exchange, symbol, exchange_2, symbol_2, one_time_buy, direction, log_record, strategy_type, balance_end, balance_front, taker_fee_ratio, maker_fee_ratio, strategy_file_id, param_1_start, param_1_end, param_1_step, param_2_start, param_2_end, param_2_step, indicator_config)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_strategy_jobs(self, user_id, strategy_file_id, page_num, page_limit):
        try:
            sig = self.make_sig('get_strategy_jobs', user_id, strategy_file_id,
                  page_num, page_limit)
            resp = self.ds_thrift.get_strategy_jobs(sig, user_id,
                   strategy_file_id, page_num, page_limit)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def manage_strategy_job(self, action, user_id, strategy_job_id):
        try:
            sig = self.make_sig('manage_strategy_job', action, user_id,
                  strategy_job_id)
            resp = self.ds_thrift.manage_strategy_job(sig, action, user_id,
                   strategy_job_id)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_strategy_tasks(self, user_id, strategy_job_id, page_num, page_limit):
        try:
            sig = self.make_sig('get_strategy_tasks', user_id, strategy_job_id,
                  page_num, page_limit)
            resp = self.ds_thrift.get_strategy_tasks(sig, user_id,
                   strategy_job_id, page_num, page_limit)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def manage_strategy_task(self, action, user_id, strategy_task_id):
        try:
            sig = self.make_sig('manage_strategy_task', action, user_id,
                  strategy_task_id)
            resp = self.ds_thrift.manage_strategy_task(sig, action, user_id,
                   strategy_task_id)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data

    def get_file(self, user_id, file_name):
        try:
            sig = self.make_sig('get_file', user_id, file_name)
            resp = self.ds_thrift.get_file(sig, user_id, file_name)
            status, data = self.load_resp(resp)
        except Exception as e:
            status = 0
            data = 'err: {}'.format(traceback.format_exc())
        return status, data
