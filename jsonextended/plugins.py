import os, glob, inspect
import imp
import uuid
import warnings

#py 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str


from jsonextended.utils import get_module_path

_encoders = {}

def load_encoders(path, overwrite=False):
    """ encoders must be classes, with attributes: objclass, to_str and to_json
    
    """
    if hasattr(path,'glob'):
        pypaths = path.glob('*.py')
    else:
        pypaths = glob.glob(os.path.join(path,'*.py')) 
    
    for pypath in pypaths:
        try:
            module = imp.load_source(str(uuid.uuid4()),str(pypath))
        except Exception as err:
            continue
            
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if all([hasattr(cls,attr) for attr in ['objclass','to_str','to_json']]):
                    if cls.objclass in _encoders and not overwrite:
                        raise ValueError('{} already has an encoder set'.format(cls.objclass))
                    _encoders[cls.objclass] = cls

def add_encoder(cls, overwrite=False):
    """ encoders must be classes, with attributes: objclass, to_str and to_json
    
    """
    if not all([hasattr(cls,attr) for attr in ['objclass','to_str','to_json']]):
        raise ValueError('must have attributes: objclass, to_str and to_json')
    if cls.objclass in _encoders and not overwrite:
        raise ValueError('{} already has an encoder set'.format(cls.objclass))
    _encoders[cls.objclass] = cls
    
def get_encoders_view():
    # py 2 and 3 compatibility
    return _encoders.viewitems() if hasattr(_encoders,'viewitems') else _encoders.items()

from jsonextended import encoders
load_encoders(get_module_path(encoders))
    
def encode(obj, as_str=False):
    """ encode objects, via encoder plugins, to json friendly
    
    as_str: bool
        if True, convert to string only
    
    Examples
    --------
    >>> from decimal import Decimal
    >>> encode(Decimal('1.3425345'))
    1.3425345
    >>> encode(Decimal('1.3425345'),as_str=True)
    '1.3425345'

    >>> encode(set([1,2,3,4,4]))
    [1, 2, 3, 4]
    >>> encode(set([1,2,3,4,4]),as_str=True)
    '{1, 2, 3, 4}'

    """
    if as_str:
        if isinstance(obj, list):
            return '['+', '.join([encode(o,True) for o in obj])+']'
        elif isinstance(obj, tuple):
            return '('+', '.join([encode(o,True) for o in obj])+')'
            
    for cls, encoder in _encoders.items():
        if isinstance(obj, cls):
            if as_str:
                return encoder().to_str(obj)
            else:
                return encoder().to_json(obj)
            break     
    
    raise TypeError('No JSON serializer is available for {0} (of type {1})'.format(obj,type(obj)))
