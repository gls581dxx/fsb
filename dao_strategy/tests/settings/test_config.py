# coding=utf-8

import pathmagic

from dao_strategy.settings.config import cfg


def test_cfg():
    print(cfg)
    print(cfg.keys())


def main():
    test_cfg()


if __name__ == '__main__':
    main()
