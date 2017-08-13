class Encode_Set(object):
    """

    Examples
    --------

    >>> Encode_Set().to_str(set([1,2,3]))
    '{1, 2, 3}'

    >>> Encode_Set().to_json(set([1,2,3]))
    {'_python_set_': [1, 2, 3]}

    >>> list(Encode_Set().from_json({'_python_set_': [1, 2, 3]}))
    [1, 2, 3]

    """

    plugin_name = 'python.set'
    plugin_descript = 'decode/encode python set'
    objclass = set
    dict_signature = ['_python_set_']

    def to_str(self, obj):
        return '{' + str(list(obj))[1:-1] + '}'

    def to_json(self, obj):
        return {'_python_set_': list(obj)}

    def from_json(self, obj):
        return set(obj['_python_set_'])
