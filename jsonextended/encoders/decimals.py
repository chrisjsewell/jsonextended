"""
https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
"""
from decimal import Decimal


class Encode_Decimal(object):
    """

    Examples
    --------
    >>> from decimal import Decimal
    >>> Encode_Decimal().to_str(Decimal('1.2345'))
    '1.2345'
    >>> Encode_Decimal().to_json(Decimal('1.2345'))
    {'_python_Decimal_': '1.2345'}
    >>> Encode_Decimal().from_json({'_python_Decimal_': '1.2345'})
    Decimal('1.2345')

    """

    plugin_name = 'decimal.Decimal'
    plugin_descript = 'encode/decode Decimal type'
    objclass = Decimal
    dict_signature = ['_python_Decimal_']

    def to_str(self, obj):
        return obj.to_eng_string()

    def to_json(self, obj):
        return {'_python_Decimal_': obj.to_eng_string()}

    def from_json(self, obj):
        return Decimal(obj['_python_Decimal_'])
