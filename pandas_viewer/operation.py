def dict_operation(d1, d2, func):
    try:
        result = func(d1, d2)
    except:
        if isinstance(d1, dict) and isinstance(d2, dict):
            result = {}
            for k, v1 in d1.iteritems():
                v2 = d2.get(k, None)
                result[k] = dict_operation(v1, v2, func)
        else:
            result = None
    return result


def dict_plus(d1, d2):
    return dict_operation(d1, d2, _add)


def dict_minus(d1, d2):
    return dict_operation(d1, d2, _minus)


def _op(lhs, rhs, attr):
    try:
        return getattr(lhs, attr)(rhs, axis=0)
    except ValueError:
        return None


def _add(lhs, rhs):
    return _op(lhs, rhs, 'add')


def _minus(lhs, rhs):
    return _op(lhs, rhs, 'minus')
