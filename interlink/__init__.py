#--coding: utf8--

__version__ = '0.0.5'


class QuerySets(object):
    def available_objects(self):
        raise NotImplementedError

    def relevant_objects(self, model):
        raise NotImplementedError
