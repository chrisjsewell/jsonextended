from pint import UnitRegistry

ureg = UnitRegistry()
from pint.quantity import _Quantity


class Encode_Quantity(object):
    """

    Examples
    --------
    >>> from pprint import pprint
    >>> from pint import UnitRegistry
    >>> ureg = UnitRegistry()

    >>> print(Encode_Quantity().to_str(ureg.Quantity(1,'nanometre')))
    1 nm

    >>> pprint(Encode_Quantity().to_json(ureg.Quantity(1,'nanometre')))
    {'_pint_Quantity_': {'Magnitude': 1, 'Units': 'nanometer'}}

    >>> Encode_Quantity().from_json({'_pint_Quantity_': {'Magnitude': 1, 'Units': 'nanometer'}})
    <Quantity(1, 'nanometer')>

    """

    plugin_name = 'pint.Quantity'
    plugin_descript = 'encode/decode pint.Quantity object'
    objclass = _Quantity
    dict_signature = ['_pint_Quantity_']

    def to_str(self, obj):
        return ' '.join(u'{:~}'.format(obj).split())

    def to_json(self, obj):
        value = obj.magnitude
        units = obj.units
        return {'_pint_Quantity_': {'Magnitude': value, 'Units': str(units)}}

    def from_json(self, obj):
        return ureg.Quantity(obj['_pint_Quantity_']['Magnitude'],
                             obj['_pint_Quantity_']['Units'])
