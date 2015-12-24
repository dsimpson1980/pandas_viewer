import pandas as pd
import numpy as np
import os

import pickling


output_dir = r'/archive/random'

def random_ts(dates=None, freq='30T'):
    if dates is None:
        dates = gen_dates(freq)
    return pd.Series(np.random.rand(len(dates)), dates)


def random_df(dates=None, freq='30T', cols=3):
    if dates is None:
        dates = gen_dates(freq)
    return pd.DataFrame(np.random.rand(len(dates), cols), dates)

def random_pl(dates=None, freq='30T', mj=3, mi=4):
    if dates is None:
        dates = gen_dates(freq)
    return pd.Panel(np.random.rand(len(dates), mj, mi), items=dates)

def gen_dates(freq='30T'):
    return pd.date_range('01-Sep-15', '30-Nov-15', freq=freq)


for name, func in dict(random_timeseries=random_ts, random_dataframe=random_df,
                       random_panel=random_pl).iteritems():
    pickling.dump(func(), os.path.join(output_dir, '{}.pickle'.format(name)))
