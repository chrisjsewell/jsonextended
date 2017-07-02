"""
https://stackoverflow.com/questions/27909658/json-encoder-and-decoder-for-complex-numpy-arrays
"""

import numpy

class Encode_NDArray(object):
    objclass = numpy.ndarray
    def to_str(self, obj):
        return ' '.join(str(obj).split())
    def to_json(self, obj):
        return obj.tolist()
        
class Encode_NPNumber(object):
    objclass = numpy.number
    def to_str(self, obj):
        return ' '.join(str(obj).split())
    def to_json(self, obj):
        return obj.tolist()