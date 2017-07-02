class Encode_Set(object):
    objclass = set
    def to_str(self, obj):
        return '{'+str(list(obj))[1:-1]+'}'
    def to_json(self, obj):
        return list(obj)