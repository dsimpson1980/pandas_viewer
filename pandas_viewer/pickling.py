import cPickle


def dump(obj, filepath):
    with open(filepath, 'wb') as f:
        cPickle.dump(obj, f, cPickle.HIGHEST_PROTOCOL)


def load(filepath):
    with open(filepath, 'rb') as f:
        obj = cPickle.load(f)
    return obj

