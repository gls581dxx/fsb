#!/usr/bin/env python

import os
import sys
import optparse


def run_rpc():
    from dao_strategy.rpc import rpc_server
    rpc_server.run()


def send_task():
    from dao_strategy.backtest import backtest
    backtest.send_task()


def push_task():
    from dao_strategy.backtest import backtest
    backtest.push_task()


def backtest_d(num):
    if num is None:
        from dao_strategy.backtest import backtest
        backtest.backtest_d()
    else:
        filename = os.path.basename(__file__)
        if num == '-1':
            cmd = "ps auxww | grep 'manage.py -t backd' | awk '{print $2}' | xargs kill -9"
            os.system(cmd)
            print(cmd)
            return True
        for i in range(0, int(num)):
            cmd_str = 'python {} -t backd &'.format(filename)
            os.system(cmd_str)
            print(i, cmd_str)


def monitor():
    from dao_strategy.backtest import backtest
    backtest.monitor()


def fresh_primary():
    from dao_strategy.db import dt_mongo
    dt_mongo.fresh_primary()


def print_info():
    filename = os.path.basename(__file__)
    print('need set param, such as:')
    print('python {} -t rpc'.format(filename))
    print('python {} -t send'.format(filename))
    print('python {} -t push'.format(filename))
    print('python {} -t backd'.format(filename))
    print('python {} -t backd -n 9'.format(filename))
    print('python {} -t backd -n -1'.format(filename))
    print('python {} -t monitor'.format(filename))
    print('python {} -t fresh_primary'.format(filename))


def main():
    parser = optparse.OptionParser()
    parser.add_option("-t", "--type", dest="run_type",
                      help="run func")
    parser.add_option("-n", "--num", dest="numbers",
                      help="run instance num")
    (options, args) = parser.parse_args()
    if options.run_type != None:
        param = options.run_type
        if (param == 'rpc'):
            run_rpc()
        elif (param == 'send'):
            send_task()
        elif (param == 'push'):
            push_task()
        elif (param == 'backd'):
            num = options.numbers
            backtest_d(num)
        elif (param == 'monitor'):
            monitor()
        elif (param == 'fresh_primary'):
            fresh_primary()
        else:
            print_info()
            sys.exit(0)
    else:
        print_info()
        sys.exit(0)


if __name__ == '__main__':
    main()
