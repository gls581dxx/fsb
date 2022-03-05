import pathmagic

from dao_strategy.rpc.rpc_server import Dispatcher


class testDispatcher(object):

    def __init__(self):
        self.dp = Dispatcher()

    def test_get_page_rst(self):
        total_count = 7
        page_limit = 5
        for page_num in range(1, 11):
            page_num_list = self.dp.get_page_rst(total_count, page_num, page_limit)
            print(page_num, page_num_list)

    def main(self):
        self.test_get_page_rst()


def main():
    td = testDispatcher()
    td.main()


if __name__ == '__main__':
    main()
