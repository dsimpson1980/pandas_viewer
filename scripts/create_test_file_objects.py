import os

from pandas_viewer import random, pickling


def main():
    output_dir = os.path.expanduser('~/random')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for name, cls in dict(ts=random.RandomSeries, df=random.RandomDataFrame,
                          pl=random.RandomPanel).iteritems():
        obj = cls()
        pickling.dump(obj, os.path.join(output_dir, '{}.pickle'.format(name)))
        if not isinstance(obj, random.RandomPanel):
            obj.to_csv(os.path.join(output_dir, '{}.csv'.format(name)))

if __name__ == '__main__':
    main()
