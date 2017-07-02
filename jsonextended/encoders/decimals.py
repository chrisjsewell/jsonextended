"""
https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
"""
from decimal import Decimal

class Encode_Decimal(object):
    objclass = Decimal
    def to_str(self, obj):
        return obj.to_eng_string()
    def to_json(self, obj):
        return float(obj)