import pandas as pd
from numpy import testing

from ..operation import *
from .. import random


def test_ts(ts):
    ts2 = random.RandomSeries()
    ts3 = dict_plus(ts, ts2)
    assert isinstance(ts3, pd.Series)
    test_ts3 = ts + ts2
    testing.assert_array_equal(ts3.values, test_ts3.values)
    testing.assert_array_equal(ts3.index, test_ts3.index)


def test_df(df):
    df2 = random.RandomDataFrame()
    df3 = dict_plus(df, df2)
    assert isinstance(df3, pd.DataFrame)
    test_df3 = df + df2
    testing.assert_array_equal(df3.values, test_df3.values)
    testing.assert_array_equal(df3.index, test_df3.index)


def test_df_ts(df, ts):
    result = dict_plus(df, ts)
    assert isinstance(result, pd.DataFrame)
    test_df = df.add(ts, axis=0)
    testing.assert_array_equal(result.values, test_df.values)
    testing.assert_array_equal(result.index, test_df.index)


def test_random_dict(random_dict):
    random_dict2 = dict(ts=random.RandomSeries(), df=random.RandomDataFrame(),
                        pl=random.RandomPanel())
    result = dict_plus(random_dict, random_dict2)
    assert isinstance(result, dict)
    for k, v in result.iteritems():
        test_obj = random_dict[k].add(random_dict2[k])
        testing.assert_array_equal(v.values, test_obj.values)
        attr = 'items' if isinstance(v, pd.Panel) else 'index'
        testing.assert_array_equal(getattr(v, attr), getattr(test_obj, attr))
