import os

from pandas_viewer import random, pickling


def main():
    output_dir = os.path.expanduser('~/random')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ts = random.RandomSeries()
    pickling.dump(ts, os.path.join(output_dir, 'ts.pickle'))
    ts.to_csv(os.path.join(output_dir, 'ts.csv'))
    df = random.RandomDataFrame()
    pickling.dump(df, os.path.join(output_dir, 'df.pickle'))
    df.to_csv(os.path.join(output_dir, 'df.csv'))
    pl = random.RandomPanel()
    pickling.dump(pl, os.path.join(output_dir, 'pl.pickle'))
    pickling.dump(dict(ts=ts, df=df, pl=pl),
                  os.path.join(output_dir, 'dict.pickle'))

if __name__ == '__main__':
    main()
