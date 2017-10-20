"""
https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
"""
from fractions import Fraction


class Encode_Fraction(object):
    """

    Examples
    --------
    >>> from decimal import Decimal
    >>> Encode_Fraction().to_str(Fraction(1, 3))
    '1/3'
    >>> Encode_Fraction().to_json(Fraction('1/3'))
    {'_python_Fraction_': '1/3'}
    >>> Encode_Fraction().from_json({'_python_Fraction_': '1/3'})
    Fraction(1, 3)

    """

    plugin_name = 'fractions.Fraction'
    plugin_descript = 'encode/decode Fraction type'
    objclass = Fraction
    dict_signature = ['_python_Fraction_']

    def to_str(self, obj):
        return str(obj)

    def to_json(self, obj):
        return {'_python_Fraction_': str(obj)}

    def from_json(self, obj):
        return Fraction(obj['_python_Fraction_'])
