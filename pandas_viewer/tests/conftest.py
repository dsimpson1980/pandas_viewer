import pytest

from .. import random

@pytest.fixture(scope='function')
def ts():
    return random.RandomSeries()


@pytest.fixture(scope='function')
def df():
    return random.RandomDataFrame()


@pytest.fixture(scope='function')
def pl():
    return random.RandomPanel()


@pytest.fixture(scope='function')
def random_dict(ts, df, pl):
    return dict(ts=ts, df=df, pl=pl)
