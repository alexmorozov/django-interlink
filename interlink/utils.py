#--coding: utf8--

from itertools import cycle, ifilter, islice, repeat


def idiverse(iterables, validate=None):
    """
    Make a diverse flat list from iterables, optionally leaving out non-valid
    items.
    >>> idiverse(['AaBbC', 'DdE', 'F'], validate=lambda x: x.is_lower())
    ['A', 'D', 'F', 'B', 'E', 'C']
    """
    # Original recipe credited to George Sakkis
    if validate is None:
        validate = lambda x: True

    pending = len(iterables)
    nexts = cycle(iter(it).next for it in iterables)
    while pending:
        try:
            for next in nexts:
                valid = ifilter(validate, iter(x() for x in repeat(next)))
                yield valid.next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))


def models_of_same_type(*models):
    """
    Checks whether all the provided `models` are of the same type.
    """
    return len(set(m._meta.concrete_model for m in models)) == 1
