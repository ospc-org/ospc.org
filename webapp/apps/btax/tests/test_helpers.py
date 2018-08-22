from ..helpers import expand_1D, expand_2D, expand_list


class TestTaxInputs():

    def test_expand1d(self):
        x = [1, 2, 3]
        assert expand_1D(x, 5) == [1, 2, 3, None, None]

    def test_expand2d(self):
        x = [[1, 2, 3], [4, 5, 6]]
        exp = [[1, 2, 3], [4, 5, 6], [None, None, None]]
        assert expand_2D(x, 3) == exp

    def test_expand_list_1(self):
        x = [1, 2, 3]
        assert expand_list(x, 5) == [1, 2, 3, None, None]
