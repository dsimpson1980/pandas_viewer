from ..random import *


def test_RandomSeries():
    ts = RandomSeries()
    assert isinstance(ts, pd.Series)


def test_RandomDataFrame():
    df = RandomDataFrame()
    assert isinstance(df, pd.DataFrame)


def test_RandomPanel():
    df = RandomPanel()
    assert isinstance(df, pd.Panel)
