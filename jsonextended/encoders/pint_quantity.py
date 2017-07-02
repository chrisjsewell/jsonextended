from pint.quantity import _Quantity

class Encode_Quantity(object):
    objclass = _Quantity
    def to_str(self, obj):
        return ' '.join(u'{:~}'.format(obj).split())
    def to_json(self, obj):
        value = obj.magnitude
        # if numpy array
        if hasattr(value,'tolist'):
            return value.tolist()
        else:
            return value
