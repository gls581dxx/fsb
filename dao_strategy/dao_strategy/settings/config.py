
import os
import yaml


HFT_TICKER = 't'
HFT_DEPTH = 'd'
HFT_DEPTHALL = 'a'
HFT_TRADE = 'e'
HFT_BAR = 'b'


def get_yaml():
    file_path = os.path.split(os.path.realpath(__file__))[0]
    file_name = '/dev_config.yaml'
    full_name = file_path + file_name
    f = open(full_name)
    y = yaml.load(f, Loader=yaml.SafeLoader)
    f.close()

    contract_name = '/contract_config.yaml'
    contract_name = file_path + contract_name
    f3 = open(contract_name)
    c = yaml.load(f3, Loader=yaml.SafeLoader)
    f3.close()

    y.update(c)
    return y


cfg = get_yaml()
