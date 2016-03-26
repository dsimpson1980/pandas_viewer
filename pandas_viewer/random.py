import pandas as pd
import numpy as np


class RandomSeries(pd.Series):

    def __init__(self, start='1-Sep-15', end='30-Sep-15', freq='D'):
        dates = pd.date_range(start, end, freq=freq)
        values = np.random.rand(len(dates))
        super(RandomSeries, self).__init__(values, dates)


class RandomDataFrame(pd.DataFrame):

    def __init__(self, start='1-Sep-15', end='30-Sep-15', freq='D', cols=2):
        dates = pd.date_range(start, end, freq=freq)
        values = np.random.rand(len(dates), cols)
        super(RandomDataFrame, self).__init__(values, dates)


class RandomPanel(pd.Panel):

    def __init__(self, start='1-Sep-15', end='30-Sep-15', freq='D', mjr=3,
                 mnr=2):
        dates = pd.date_range(start, end, freq=freq)
        values = np.random.rand(len(dates), mjr, mnr)
        super(RandomPanel, self).__init__(values, items=dates)
