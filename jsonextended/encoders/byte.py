class Encode_Bytes(object):
    objclass = bytes
    def to_str(self, obj):
        return obj.decode()
    def to_json(self, obj):
        return obj.decode()