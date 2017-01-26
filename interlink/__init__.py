#--coding: utf8--


class QuerySets(object):
    def available_objects(self):
        raise NotImplementedError

    def relevant_objects(self, model):
        raise NotImplementedError
