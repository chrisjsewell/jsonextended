import pickle

class Encode_Set(object):

    plugin_name = 'python.set'
    objclass = set
    dict_signature = ['_python_set_']

    def to_str(self, obj):
        return '{'+str(list(obj))[1:-1]+'}'

    def to_json(self, obj):
        return {'_python_set_': list(obj)}

    def from_json(self, obj):
        return set(obj['_python_set_'])
        