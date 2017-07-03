"""
https://stackoverflow.com/questions/27909658/json-encoder-and-decoder-for-complex-numpy-arrays
"""

import numpy as np

class Encode_NDArray(object):

    objclass = np.ndarray
    dict_signature = ['_numpy_ndarray']

    def to_str(self, obj):
        return ' '.join(str(obj).split())

    def to_json(self, obj):
        return {'_numpy_ndarray':{'value':obj.tolist(),'dtype':str(obj.dtype)}}
        
    def from_json(self, obj):
        return np.array(obj['_numpy_ndarray']['value'],
                        dtype=obj['_numpy_ndarray']['dtype'])
        