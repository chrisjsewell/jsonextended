"""
https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
"""
from decimal import Decimal

class Encode_Decimal(object):
    
    objclass = Decimal
    dict_signature = ['_python_Decimal_']
    
    def to_str(self, obj):
        return obj.to_eng_string()
        
    def to_json(self, obj):
        return {'_python_Decimal_':obj.to_eng_string()}
        
    def from_json(self, obj):
        return Decimal(obj['_python_Decimal_'])
        
        
        
    