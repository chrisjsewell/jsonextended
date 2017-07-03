from pint import UnitRegistry
ureg = UnitRegistry()
from pint.quantity import _Quantity

class Encode_Quantity(object):
    
    plugin_name = 'pint.Quantity'
    objclass = _Quantity
    dict_signature = ['_pint_Quantity_']
    
    def to_str(self, obj):
        return ' '.join(u'{:~}'.format(obj).split())
        
    def to_json(self, obj):
        value = obj.magnitude
        units = obj.units
        return {'_pint_Quantity_':{'Magnitude':value,'Units':str(units)}}
            
    def from_json(self, obj):
        return ureg.Quantity(obj['_pint_Quantity_']['Magnitude'],
                             obj['_pint_Quantity_']['Units'])
