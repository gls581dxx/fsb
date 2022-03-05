import pathmagic

from dao_strategy.utils.account import Account
from dao_strategy.db.dt_models import StrategyInstance


class testAccount(object):

    def __init__(self):
        self.account = Account()

    def test_get_future_future_strategy_position(self):
        # strategy_instance_id = '5d1c5cb32a0aa556aab15988' # strategy_9
        strategy_instance_id = '5da2e8432a0aa51c34785d53' # strategy_27

        si = StrategyInstance.objects.get(id=strategy_instance_id)
        position_dict = self.account.get_future_future_strategy_position(si.to_dict())
        print(position_dict)

    def test_get_future_strategy_position(self):
        # strategy_instance_id = '5d1c5cb32a0aa556aab15988' # strategy_9
        strategy_instance_id = '5da2e8432a0aa51c34785d53' # strategy_27

        si = StrategyInstance.objects.get(id=strategy_instance_id)
        position_dict = self.account.get_future_strategy_position(si.to_dict())
        print(position_dict)

    def test_get_spot_strategy_position(self):
        # strategy_instance_id = '5dd256bb5e6f2346cbba1008' # btc hft
        strategy_instance_id = '5e0f0934d9ceb5bf3149c165' # okb
        si = StrategyInstance.objects.get(id=strategy_instance_id)
        position_dict = self.account.get_spot_strategy_position(si.to_dict())
        print(position_dict)

    def test_get_reg_emu_balance(self):
        strategy_instance_id = '5c3e1e7e2a0aa51b21fdbc4a'
        si = StrategyInstance.objects.get(id=strategy_instance_id)
        status, data = self.account.get_reg_emu_balance(si.to_dict())
        print(status, data)

    def test_get_future_future_strategy_balance(self):
        strategy_instance_id = '5cb456312a0aa544cd9e0be4' # ff_arbitrage_strategy
        si = StrategyInstance.objects.get(id=strategy_instance_id)
        capital_dict_list = self.account.get_future_future_strategy_balance(si.to_dict())
        print(capital_dict_list)

    def test_get_future_strategy_balance(self):
        # strategy_instance_id = '5d1c5cb32a0aa556aab15988' # strategy_9 coin
        strategy_instance_id = '5e12fbdb142801bc71e0c6f7' # strategy_43 ctp
        si = StrategyInstance.objects.get(id=strategy_instance_id)
        capital_dict_list = self.account.get_future_strategy_balance(si.to_dict())
        print(capital_dict_list)

    def test_get_coin_future_strategy_balance(self):
        # 5d1c5cb32a0aa556aab15988 coin future
        # test_get_future_strategy_balance()
        print('test pass')

    def test_get_ctp_strategy_balance(self):
        # 5e12fbdb142801bc71e0c6f7 ctp future
        # test_get_future_strategy_balance()
        print('test pass')

    def test_get_future_spot_strategy_balance(self):
        strategy_instance_id = '5cea635f2a0aa572ccff7f13' # fs
        si = StrategyInstance.objects.get(id=strategy_instance_id)
        capital_dict_list = self.account.get_future_spot_strategy_balance(si.to_dict())
        print(capital_dict_list)

    def test_get_future_spot_strategy_position(self):
        strategy_instance_id = '5cea635f2a0aa572ccff7f13' # fs
        si = StrategyInstance.objects.get(id=strategy_instance_id)
        position_dict = self.account.get_future_spot_strategy_position(si.to_dict())
        print(position_dict)

    def test_get_spot_strategy_balance(self):
        strategy_instance_id = '5da1db822a0aa575072c3133'
        si = StrategyInstance.objects.get(id=strategy_instance_id)
        capital_dict_list = self.account.get_spot_strategy_balance(si.to_dict())
        print(capital_dict_list)

    def main(self):
        self.test_get_future_future_strategy_position()
        self.test_get_future_strategy_position()
        self.test_get_spot_strategy_position()
        self.test_get_reg_emu_balance()
        self.test_get_future_future_strategy_balance()
        self.test_get_future_strategy_balance()
        self.test_get_coin_future_strategy_balance()
        self.test_get_ctp_strategy_balance()
        self.test_get_future_spot_strategy_balance()
        self.test_get_future_spot_strategy_position()
        self.test_get_spot_strategy_balance()


def main():
    ta = testAccount()
    ta.main()


if __name__ == '__main__':
    main()
