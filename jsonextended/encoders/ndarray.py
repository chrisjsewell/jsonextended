"""
https://stackoverflow.com/questions/27909658/json-encoder-and-decoder-for-complex-numpy-arrays
"""

import numpy as np

try:
    from functools import reduce
except ImportError:
    pass
import operator


class Encode_NDArray(object):
    """

    Examples
    --------
    >>> from pprint import pprint
    >>> import numpy as np

    >>> Encode_NDArray().to_str(np.asarray([1,2,3]))
    '[1 2 3]'

    >>> pprint(Encode_NDArray().to_json(np.asarray([1,2,3])))
    {'_numpy_ndarray_': {'dtype': 'int64', 'value': [1, 2, 3]}}

    >>> Encode_NDArray().from_json({'_numpy_ndarray_': {'dtype': 'int64', 'value': [1, 2, 3]}})
    array([1, 2, 3])

    """

    plugin_name = 'numpy.ndarray'
    plugin_descript = 'encode/decode numpy.ndarray'
    objclass = np.ndarray
    dict_signature = ['_numpy_ndarray_']

    def to_str(self, obj):
        elements = reduce(operator.mul, obj.shape, 1)
        if elements > 10:
            return 'np.array({0}, min={1:.2E}, max={2:.2E})'.format(
                obj.shape, np.nanmin(obj), np.nanmax(obj))
        else:
            return ' '.join(str(obj).split())

    def to_json(self, obj):
        return {'_numpy_ndarray_': {'value': obj.tolist(), 'dtype': str(obj.dtype)}}

    def from_json(self, obj):
        return np.array(obj['_numpy_ndarray_']['value'],
                        dtype=obj['_numpy_ndarray_']['dtype'])
