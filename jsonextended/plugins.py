import os, glob, inspect
import imp
import uuid
import warnings

#py 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str

from jsonextended.utils import get_module_path, class_to_str

def _remove_plugins(name_list,cache):
    """ remove plugins list
    
    """
    if isinstance(name_list, basestring):
        name_list=[name_list]
    for name in name_list:
        if name in cache:
            cache.pop(name)


_encoders = {}
def load_encoders(path,overwrite=False):
    """ load encoders from path """
    cache, signature = _encoders, ['objclass']
    if hasattr(path,'glob'):
        pypaths = path.glob('*.py')
    else:
        pypaths = glob.glob(os.path.join(path,'*.py')) 
    
    for pypath in pypaths:
        try:
            module = imp.load_source(str(uuid.uuid4()),str(pypath))
        except Exception as err:
            continue
            
        for name, klass in inspect.getmembers(module, inspect.isclass):
            if all([hasattr(klass,attr) for attr in signature]):
                    name = class_to_str(klass.objclass)
                    # py 2/3 compatibility
                    name = name.replace('__builtin__','builtins')  
                    if name in cache and not overwrite:
                        raise ValueError('{0} already has a function set in {1}'.format(name,cache))
                    cache[name] = klass

def reset_encoders():
    """ reset to default encoders"""
    for key in list(_encoders.keys()):
        _encoders.pop(key)
    from jsonextended import encoders
    load_encoders(get_module_path(encoders))
reset_encoders()

def add_encoders(klass_list, overwrite=False):
    """ encoders must be classes, with attributes: objclass, to_str and to_json
    
    Examples
    --------
    >>> from jsonextended import plugins
    >>> class ListDecoder(object):
    ...     objclass = list
    ...     def to_str(self, obj):
    ...         return str(list)
    ...     def to_json(self, obj):
    ...         return obj
    ...
    >>> plugins.add_encoders([ListDecoder])
    >>> 'builtins.list' in plugins.current_encoders()
    True
    >>> plugins.reset_encoders()
    >>> 'builtins.list' in plugins.current_encoders()
    False
    
    """
    cache, signature = _encoders, ['objclass']

    # check all first
    for klass in klass_list:
        if not all([hasattr(klass,attr) for attr in signature]):
            raise ValueError('{0} must have attributes: {1}'.format(klass,signature))
        name = class_to_str(klass.objclass)
        # py 2/3 compatibility
        name = name.replace('__builtin__','builtins')  
        if name in cache and not overwrite:
            raise ValueError('{0} already has a function set in {1}'.format(name,cache))
    for klass in klass_list:  
        name = class_to_str(klass.objclass)
        # py 2/3 compatibility
        name = name.replace('__builtin__','builtins')  
        cache[name] = klass

def remove_encoders(name_list):
    """ remove encoders in encoder list
    
    Examples
    --------
    >>> from jsonextended import plugins
    >>> plugins.current_encoders()
    ['builtins.set', 'decimal.Decimal', 'numpy.ndarray', 'pint.quantity._Quantity']
    >>> plugins.remove_encoders('decimal.Decimal')
    >>> plugins.current_encoders()
    ['builtins.set', 'numpy.ndarray', 'pint.quantity._Quantity']
    
    """
    _remove_plugins(name_list,_encoders)
    
def current_encoders():
    """ view encoder plugins
    
    Example
    -------
    >>> from jsonextended import plugins
    >>> plugins.current_encoders()
    ['builtins.set', 'decimal.Decimal', 'numpy.ndarray', 'pint.quantity._Quantity']
    
    """
    # py 2 and 3 compatibility
    #return _encoders.viewitems() if hasattr(_encoders,'viewitems') else _encoders.items()
    return sorted(_encoders.keys())
    
def encode(obj, outtype='json'):
    """ encode objects, via encoder plugins, to new type
    
    outtype: str
        use encoder method to_<outtype> to encode
    
    Examples
    --------
    >>> from decimal import Decimal
    >>> encode(Decimal('1.3425345'))
    {'_python_Decimal_': '1.3425345'}
    >>> encode(Decimal('1.3425345'),outtype='str')
    '1.3425345'
    
    >>> encode(set([1,2,3,4,4]))
    {'_python_set_': [1, 2, 3, 4]}
    >>> encode(set([1,2,3,4,4]),outtype='str')
    '{1, 2, 3, 4}'
    
    class A(object):
        def __init__(self):
            self.a = 2
        def b(self):
            return 1


    """            
    for klass_name, encoder in _encoders.items():
        if isinstance(obj, encoder.objclass) and hasattr(encoder, 'to_{}'.format(outtype)):
            return getattr(encoder(),'to_{}'.format(outtype))(obj)
            break  
                
    raise TypeError('No JSON serializer is available for {0} (of type {1})'.format(obj,type(obj)))

_decoders = {}
def load_decoders(path,overwrite=False):
    """ load decoders from path """
    cache, signature = _decoders, ['dict_signature']
    if hasattr(path,'glob'):
        pypaths = path.glob('*.py')
    else:
        pypaths = glob.glob(os.path.join(path,'*.py')) 
    
    for pypath in pypaths:
        try:
            module = imp.load_source(str(uuid.uuid4()),str(pypath))
        except Exception as err:
            continue
            
        for name, klass in inspect.getmembers(module, inspect.isclass):
            if all([hasattr(klass,attr) for attr in signature]):
                    name = tuple(sorted(klass.dict_signature))
                    if name in cache and not overwrite:
                        raise ValueError('{0} already has a function set in {1}'.format(klass.dict_signature,cache))
                    cache[name] = klass

def reset_decoders():
    """ reset to default decoders"""
    for key in list(_decoders.keys()):
        _decoders.pop(key)
    from jsonextended import encoders
    load_decoders(get_module_path(encoders))
reset_decoders()

def add_decoders(klass_list, overwrite=False):
    """ decoders must be classes, with attributes: dict_signature
    
    Examples
    --------
    >>> from jsonextended import plugins
    >>> class ListDecoder(object):
    ...     dict_signature = ['_python_list_']
    ...     def from_json(self, obj):
    ...         return obj
    ...
    >>> plugins.add_decoders([ListDecoder])
    >>> ('_python_list_',) in plugins.current_decoders()
    True
    >>> plugins.reset_decoders()
    >>> ('_python_list_',) in plugins.current_decoders()
    False
    
    """
    cache, signature = _decoders, ['dict_signature']

    # check all first
    for klass in klass_list:
        if not all([hasattr(klass,attr) for attr in signature]):
            raise ValueError('{0} must have attributes: {1}'.format(klass,signature))
        name = tuple(sorted(klass.dict_signature)) 
        if name in cache and not overwrite:
            raise ValueError('{0} already has a function set in {1}'.format(name,cache))
    for klass in klass_list:  
        name = tuple(sorted(klass.dict_signature))  
        cache[name] = klass

def remove_decoders(name_list):
    """ remove decoders in decoder list
    
    Examples
    --------
    >>> from jsonextended import plugins
    >>> plugins.current_decoders()
    [('_numpy_ndarray',), ('_pint_Quantity_',), ('_python_Decimal_',), ('_python_set_',)]
    >>> plugins.remove_decoders([('_python_Decimal_',)])
    >>> plugins.current_decoders()
    [('_numpy_ndarray',), ('_pint_Quantity_',), ('_python_set_',)]
    
    """
    for name in name_list:
        if name in _decoders:
            _decoders.pop(name)
    
def current_decoders():
    """ view encoder plugins
    
    Example
    -------
    >>> from jsonextended import plugins
    >>> plugins.current_decoders()
    [('_numpy_ndarray',), ('_pint_Quantity_',), ('_python_Decimal_',), ('_python_set_',)]
    
    """
    # py 2 and 3 compatibility
    #return _encoders.viewitems() if hasattr(_encoders,'viewitems') else _encoders.items()
    return sorted(_decoders.keys())
    
def decode(dct, outtype='json'):
    """ decode objects, via decoder plugins, to new type
    
    outtype: str
        use decoder method from_<outtype> to encode
    
    Examples
    --------
    >>> from decimal import Decimal
    >>> decode({'_python_Decimal_':'1.3425345'})
    Decimal('1.3425345')

    """            
    for klass_name, decoder in _decoders.items():
        if set(decoder.dict_signature).issubset(dct.keys()) and hasattr(decoder, 'to_{}'.format(outtype)):
            return getattr(decoder(),'from_{}'.format(outtype))(dct)
            break  
                
    return dct#raise TypeError('No JSON deserializer is available for {0} (of type {1})'.format(dct,type(dct)))

