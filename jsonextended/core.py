#!/usr/bin/env python
# -- coding: utf-8 --

## TODO see below
# deal with dictionaries in lists?
# output json with arrays all on one line
#      doesn't seem an easy way
#      could use this: https://stackoverflow.com/a/13252112, but wrap lists with NoIndent first
#      would need to go through first and wrap values that are list instances with NoIndent first

# have a look at:
#    mergers: https://pypi.python.org/pypi/jsonmerge, https://pypi.python.org/pypi/json-merger/0.2.5

# NB: uses lots of recursion, might not be good for very large levels of nesting
# NB: examples use pprint to make sure keys are sorted
# NB: using Decimal parsing my default

# internal packages
import json
import copy
import re
import os, sys
import glob
import textwrap
from fnmatch import fnmatch
from decimal import Decimal
from functools import reduce
import inspect
import uuid

# python 3 to 2 compatibility
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib
try:
    basestring
except NameError:
    basestring = str
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

# external packages
import warnings
warnings.simplefilter('once',ImportWarning)
try:
    import pandas as pd
except ImportError:
    pass
try:
    import ijson
except ImportError:
    pass
    
# local imports
try:
    from jsonextended import _example_json_folder
except:
    import _example_json_folder

from  jsonextended.utils import natural_sort

def get_test_path():
    """ returns test path object

    Examples
    --------
    >>> path = get_test_path()
    >>> path.name
    '_example_json_folder'

    """
    return pathlib.Path(os.path.dirname(os.path.abspath(inspect.getfile(_example_json_folder))))

def _json_get_keys(file_obj,key_path=None):
    key_path = [] if key_path is None else key_path
    data = json.load(file_obj)
    data = dict_multiindex(data,key_path)
    if hasattr(data,'keys'):
        return sorted([str(k) if isinstance(k,basestring) else k for k in data.keys()])
    else:
        return []

def _json_get_keys_ijson(file_obj,key_path=None):

    key_path = [] if key_path is None else key_path
    try:
        path_str = '.'.join(key_path)
        keys = []
        for prefix, etype, value in ijson.parse(file_obj):
            if etype == 'map_key':
                if prefix == path_str:
                    keys.append(value)
        return sorted([str(k) if isinstance(k,basestring) else k for k in keys])
    except NameError:
        warnings.warn('ijson package not found in environment, \
please install for on-disk key indexing',ImportWarning)
        return _json_get_keys(file_obj,key_path)

def _json_get_keys_folder(jdir,key_path=None,in_memory=True,ignore_prefix=('.','_')):
    """ get json keys from directory sturcture

    e.g.

    jdir
        sub_dir1
            data1.json
            data2.json
        sub_dir2
            data.json

    _json_get_keys_folder(jdir)
    => ['sub_dir1', 'sub_dir2']
    _json_get_keys_folder(jdir,['sub_dir1'])
    => ['data1', 'data2']

    NB: json files are identified with .json extension
        files/directories beginning with '.' are ignored

    """
    if not hasattr(jdir,'iterdir'):
        raise ValueError('jdir is not a path object; {}'.format(jdir))

    key_path = [] if key_path is None else key_path

    keys = []

    key_found = False if key_path else True
    search_key = key_path[0] if len(key_path)>0 else None

    for jsub in jdir.iterdir():
        if jsub.is_file() and jsub.name[-5:]=='.json':

            name, ext = os.path.splitext(jsub.name)
            if name == search_key or not key_path:
                key_found = True
                if key_path:
                    return json_keys(jsub,key_path[1:],in_memory,ignore_prefix)
                else:
                    keys.append(name)

        elif jsub.is_dir() and not jsub.name.startswith(ignore_prefix) and (jsub.name == search_key or not key_path):

            key_found = True
            if jsub.name in keys:
                raise IOError('directory has a sub-dir and file with same name: {1} and {1}.json in {0}'.format(jdir,jsub.name))
            if key_path:
                return json_keys(jsub,key_path[1:],in_memory,ignore_prefix)
            else:
                keys.append(jsub.name)

    if not key_found:
        raise KeyError('key not found: {0}'.format(search_key))

    return keys

def json_keys(jfile,key_path=None,in_memory=True,ignore_prefix=('.','_')):
    """ get keys for initial json level, or at level after following key_path

    Parameters
    ----------
    jfile : str, file_like or path_like
        if str, must be existing file or folder,
        if file_like, must have 'read' method
        if path_like, must have 'iterdir' method (see pathlib.Path)
    key_path : list of str
        a list of keys to index into the json before returning keys
    in_memory : bool
        if true reads json into memory before finding keys (this is faster but uses more memory)
    ignore_prefix : list of str
        ignore folders beginning with these prefixes

    Examples
    --------

    >>> json_obj = StringIO(
    ... '''
    ... {
    ...  "a": 1,
    ...  "b": [1.1,2.1],
    ...  "c": {"d":"e","f":"g"}
    ... }
    ... ''')
    ...
    >>> json_keys(json_obj)
    ['a', 'b', 'c']

    >>> i = json_obj.seek(0)
    >>> json_keys(json_obj,["c"])
    ['d', 'f']

    >>> path = get_test_path()
    >>> json_keys(path)
    ['dir1', 'dir2', 'dir3']

    >>> path = get_test_path()
    >>> json_keys(path, ['dir1','file1'], in_memory=True)
    ['initial', 'meta', 'optimised', 'units']

    """
    key_path = [] if key_path is None else key_path

    def eval_file(file_obj):
        if not in_memory:
            return _json_get_keys_ijson(file_obj,key_path)
        else:
            return _json_get_keys(file_obj,key_path)

    if isinstance(jfile,basestring):
        if not os.path.exists(jfile):
            raise IOError('jfile does not exist: {}'.format(jfile))
        if os.path.isdir(jfile):
            jpath = pathlib.Path(jfile)
            return _json_get_keys_folder(jpath, key_path, in_memory, ignore_prefix)
        else:
            with open(jfile, 'r') as file_obj:
                return eval_file(file_obj)
    elif hasattr(jfile,'read'):
        return eval_file(jfile)
    elif hasattr(jfile,'iterdir'):
        if jfile.is_file():
            with jfile.open('r') as file_obj:
                return eval_file(file_obj)
        else:
            return _json_get_keys_folder(jfile, key_path, in_memory, ignore_prefix)
    else:
        raise ValueError('jfile should be a str, file_like or path_like object: {}'.format(jfile))

def dict_convert_type(d, intype, outtype, convert_list=True, in_place=True):
    """ convert all values of one type to another 
    
    Parameters
    ----------
    d : dict
    intype : type_class
    outtype : type_class
    convert_list : bool
        whether to convert instances inside lists and tuples
    in_place : bool
        if True, applies conversions to original dict, else returns copy
    
    Examples
    --------
    
    >>> from pprint import pprint
    
    >>> d = {'a':'1','b':'2'}
    >>> pprint(dict_convert_type(d,str,float))
    {'a': 1.0, 'b': 2.0}
    
    >>> d = {'a':['1','2']}
    >>> pprint(dict_convert_type(d,str,float))
    {'a': [1.0, 2.0]}

    >>> d = {'a':[('1','2'),[3,4]]}
    >>> pprint(dict_convert_type(d,str,float))
    {'a': [(1.0, 2.0), [3, 4]]}

    """
    if not in_place:
        out_dict = copy.deepcopy(d)
    else: 
        out_dict = d
    
    def _convert(obj):
        if isinstance(obj,intype):
            try:
                obj = outtype(obj)
            except:
                pass 
        elif isinstance(obj, list) and convert_list:
            obj = _traverse_iter(obj)
        elif isinstance(obj, tuple) and convert_list:
            obj = tuple(_traverse_iter(obj))
        
        return obj

    def _traverse_dict(dic):
        for key in dic.keys():
            if isinstance(dic[key], dict):
                _traverse_dict(dic[key])
            else:
                dic[key] = _convert(dic[key])

    def _traverse_iter(iter):
        new_iter = []
        for key in iter:
            if isinstance(key, dict):
                _traverse_dict(key)
                new_iter.append(key)
            else:
                new_iter.append(_convert(key))
                
        return new_iter

    if isinstance(out_dict,dict):
        _traverse_dict(out_dict)
    else:
        data = _convert(out_dict)
    
    return out_dict

def _json_file_with_keys(file_obj,key_path=None,parse_decimal=False):
    """read json with keys

    Parameters
    ----------
    file_obj : object
        object with read method
    key_path : list of str
        key to index befor parsing
    parse_decimal : bool
        whether to parse numbers as Decimal instances (retains exact precision)

    Notes
    -----
    ijson outputs decimals as Decimal class (for arbitrary precision)

    """
    key_path = [] if key_path is None else key_path

    try:
        objs = ijson.items(file_obj,'.'.join(key_path))
    except NameError:
        warnings.warn('ijson package not found in environment, \
        please install for on-disk key indexing',ImportWarning)
        data = json.load(file_obj, parse_float=Decimal if parse_decimal else float)
        return dict_multiindex(data,key_path)
    try:
        data = objs.next()
    except StopIteration:
        raise KeyError('key path not available in json: {}'.format(key_path))

    # by default ijson parses Decimal values
    if not parse_decimal:
        dict_convert_type(data, Decimal, float, in_place=True)

    return data

# TODO this is a hack to get _folder_to_json to work if last key_path is at a leaf node, should improve
class _Terminus(object):
    def __hash__(self):
        return 1
    def __eq__(self, other):
        return True

def _folder_to_json(jdir, key_path=None, in_memory=True,
                    ignore_prefix=('.','_'), dic={}, parse_decimal=False):
    """ read in folder structure as json

    e.g.

    jdir
        sub_dir1
            data.json
        sub_dir2
            data.json

    _folder_to_json(jdir)
    => {'sub_dir1':{'data':{...}},
        'sub_dir2':{'data':{...}}}

    NB: json files are identified with .json extension

    """
    key_path = [] if key_path is None else key_path

    if not hasattr(jdir,'iterdir'):
        raise ValueError('jdir is not a path object; {}'.format(jdir))

    key_found = False if key_path else True
    search_key = key_path[0] if len(key_path)>0 else None


    for jsub in jdir.iterdir():
        if jsub.is_file() and jsub.name.endswith('.json'):

            name, ext = os.path.splitext(jsub.name)
            if name == search_key or not key_path:
                key_found = True
                if key_path:
                    data = json_to_dict(jsub,key_path[1:],in_memory,ignore_prefix,parse_decimal)
                    if isinstance(data,dict):
                        dic.update(data)
                    else:
                        dic.update({_Terminus():data})
                else:
                    dic[name] = json_to_dict(jsub,key_path[1:],in_memory,ignore_prefix,parse_decimal)

        elif jsub.is_dir() and not jsub.name.startswith(ignore_prefix) and (jsub.name == search_key or not key_path):

            key_found = True
            if jsub.name in dic.keys():
                raise IOError('directory has a sub-dir and file with same name: {1} and {1}.json in {0}'.format(jdir,jsub.name))
            if key_path:
                sub_d = dic
            else:
                dic[jsub.name] = {}
                sub_d = dic[jsub.name]
            _folder_to_json(jsub,key_path[1:],in_memory,ignore_prefix,sub_d,parse_decimal)

    if not key_found:
        raise KeyError('key not found: {0}'.format(search_key))

def json_to_dict(jfile, key_path=None, in_memory=True ,
                ignore_prefix=('.','_'), parse_decimal=False):
    """ input json to dict

    Parameters
    ----------
    jfile : str, file_like or path_like
        if str, must be existing file or folder,
        if file_like, must have 'read' method
        if path_like, must have 'iterdir' method (see pathlib.Path)
    key_path : list of str
        a list of keys to index into the json before parsing it
    in_memory : bool
        if true reads full json into memory before filtering keys (this is faster but uses more memory)
    ignore_prefix : list of str
        ignore folders beginning with these prefixes
    parse_decimal : bool
        whether to parse numbers as Decimal instances (retains exact precision)

    Examples
    --------

    >>> from pprint import pformat

    >>> json_obj = StringIO(
    ... '''
    ... {
    ...  "a": 1,
    ...  "b": [1.1,2.1],
    ...  "c": {"d":"e"}
    ... }
    ... ''')
    ...

    >>> dstr = pformat(json_to_dict(json_obj))
    >>> print(dstr.replace("u'","'"))
    {'a': 1, 'b': [1.1, 2.1], 'c': {'d': 'e'}}

    >>> i = json_obj.seek(0)
    >>> dstr = pformat(json_to_dict(json_obj,parse_decimal=True))
    >>> print(dstr.replace("u'","'"))
    {'a': 1, 'b': [Decimal('1.1'), Decimal('2.1')], 'c': {'d': 'e'}}

    >>> i = json_obj.seek(0)
    >>> str(json_to_dict(json_obj,["c","d"]))
    'e'

    >>> path = get_test_path()
    >>> jdict1 = json_to_dict(path)
    >>> dict_pprint(jdict1,depth=2)
    dir1: 
      dir1_1: {...}
      file1: {...}
      file2: {...}
    dir2: 
      file1: {...}
    dir3: 

    >>> jdict2 = json_to_dict(path,['dir1','file1'],in_memory=False)
    >>> dict_pprint(jdict2,depth=1)
    initial: {...}
    meta: {...}
    optimised: {...}
    units: {...}

    """        
    key_path = [] if key_path is None else key_path

    if isinstance(jfile,basestring):
        if not os.path.exists(jfile):
            raise IOError('jfile does not exist: {}'.format(jfile))
        if os.path.isdir(jfile):
            data = {}
            jpath = pathlib.Path(jfile)
            _folder_to_json(jpath,key_path[:],in_memory,ignore_prefix,data,parse_decimal)
            if isinstance(list(data.keys())[0], _Terminus):
                data = data.values()[0]
        else:
            with open(jfile, 'r') as file_obj:
                if key_path and not in_memory:
                    data = _json_file_with_keys(file_obj,key_path,parse_decimal)
                elif key_path:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float)
                    data = dict_multiindex(data,key_path)
                else:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float)
    elif hasattr(jfile,'read'):
        if key_path and not in_memory:
            data = _json_file_with_keys(jfile,key_path,parse_decimal)
        elif key_path:
            data = json.load(jfile, parse_float=Decimal if parse_decimal else float)
            data = dict_multiindex(data,key_path)
        else:
            data = json.load(jfile, parse_float=Decimal if parse_decimal else float)
    elif hasattr(jfile,'iterdir'):
        if jfile.is_file():
            with jfile.open() as file_obj:
                if key_path and not in_memory:
                    data = _json_file_with_keys(file_obj,key_path,parse_decimal)
                elif key_path:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float)
                    data = dict_multiindex(data,key_path)
                else:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float)
        else:
            data = {}
            _folder_to_json(jfile,key_path[:],in_memory,ignore_prefix,data,parse_decimal)
            if isinstance(list(data.keys())[0], _Terminus):
                data = data.values()[0]
    else:
        raise ValueError('jfile should be a str, file_like or path_like object: {}'.format(jfile))

    return data

def json_extended_encoder(obj, as_str=False):
    """Support for data types that JSON default encoder
    does not do.

    This includes:

        * Set
        * Bytes (Python 3)
        * Decimals
        * Numpy array or number (if installed)
        * pint.Quantity (if installed)

    Notes
    -----
    See:
    http://astropy.readthedocs.io/en/latest/_modules/astropy/utils/misc.html#JsonCustomEncoder
    https://stackoverflow.com/questions/27909658/json-encoder-and-decoder-for-complex-numpy-arrays
    https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object

    """
    if isinstance(obj, set):
        if as_str:
            return str(obj)
        else:
            return list(obj)
    elif isinstance(obj, bytes):  # pragma: py3
        return obj.decode()
    elif isinstance(obj, Decimal):
        if as_str:
            return obj.to_eng_string()
        else:
            return float(obj)
    elif as_str:
        if isinstance(obj, list):
            return '['+', '.join([json_extended_encoder(o,True) for o in obj])+']'
        elif isinstance(obj, tuple):
            return '('+', '.join([json_extended_encoder(o,True) for o in obj])+')'

    # only load external packages if available
    try:
        import numpy as np
        if isinstance(obj, (np.ndarray, np.number)):
            if as_str:
                return ' '.join(str(obj).split())
            else:
                return obj.tolist()
    except ImportError:
        pass
    try:
        from pint.quantity import _Quantity
        if isinstance(obj, _Quantity):
            if as_str:
                return ' '.join(u'{:~}'.format(obj).split())
            value = obj.magnitude
            # if numpy array
            if hasattr(value,'tolist'):
                return value.tolist()
            else:
                return value
    except ImportError:
        pass

    raise TypeError('No JSON serializer is available for {0} (of type {1})'.format(obj,type(obj)))

def dict_to_json(d, jfile, overwrite=False, dirlevel=1,
                 sort_keys=True, indent=2, encoder=json_extended_encoder, **kwargs):
    """ output dict to json

    Parameters
    ----------
    d : dict
    jfile : str or file_like
        if file_like, must have write method
    overwrite : bool
        whether to overwrite existing files
    dirlevel : int
        if jfile is path to folder, defines how many key levels to set as sub-folders
    sort_keys : bool
        if true then the output of dictionaries will be sorted by key
    indent : int
        if non-negative integer, then JSON array elements and
        object members will be pretty-printed on new lines with that indent level spacing.
    encoder : func
        encoder function to extend type of objects encoded by JSON
    kwargs : dict
        keywords for json.dump

    Examples
    --------


    >>> json_obj = StringIO()
    >>> d = {'a':{'b':1}}
    >>> dict_to_json(d, json_obj)
    >>> print(json_obj.getvalue())
    {
      "a": {
        "b": 1
      }
    }

    """
    if isinstance(jfile,basestring):
        if os.path.exists(jfile):
            if os.path.isfile(jfile) and not overwrite:
                raise IOError('jfile already exists and overwrite is set to false: {}'.format(jfile))
            if os.path.isdir(jfile):
                raise NotImplemented
        with open(jfile, 'w') as outfile:
            json.dump(d, outfile,
                      sort_keys=sort_keys,indent=indent, default=encoder)
    elif not hasattr(jfile,'write'):
        raise ValueError('jfile should be a str or file_like object: {}'.format(jfile))
    else:
        json.dump(d, jfile,
                  sort_keys=sort_keys,indent=indent, default=encoder)

def _default_print_func(s):
    print(s)

def dict_pprint(d, lvlindent=2, initindent=0, delim=':',
                max_width=80, depth=3, no_values=False,
                align_vals=True,
                encoder=json_extended_encoder, print_func=None):
    """ print a nested dict in readable format

    Parameters
    ----------
    d : dict
    lvlindent : int
        additional indentation spaces for each level
    initindent : int
        initial indentation spaces
    delim : str
        delimiter between key and value nodes
    max_width : int
        max character width of each line
    depth : int or None
        maximum levels to display
    no_values : bool
        whether to print values
    align_vals : bool
        whether to align values for each level
    encoder : func
        class to extend objects encoded by JSON
    print_func : func or None
        function to print strings (print if None)

    Examples
    --------

    >>> d = {'a':{'b':{'c':[1,2],'de':[4,5,6,7,8,9]}}}
    >>> dict_pprint(d,depth=None)
    a: 
      b: 
        c:  [1, 2]
        de: [4, 5, 6, 7, 8, 9]
    >>> dict_pprint(d,max_width=17,depth=None)
    a: 
      b: 
        c:  [1, 2]
        de: [4, 5, 6, 
            7, 8, 9]
    >>> dict_pprint(d,no_values=True,depth=None)
    a: 
      b: 
        c:  
        de: 
    >>> dict_pprint(d,depth=2)
    a: 
      b: {...}

    """
    if print_func is None:
        print_func = _default_print_func

    if not isinstance(d, dict):
        print_func('{}'.format(d))
        return

    def convert_str(obj):
        """ convert unicode to str (so no u'' prefix in python 2) """
        if isinstance(obj, list):
            return str([str(v) if isinstance(v,basestring) else v for v in obj])
        if isinstance(obj, tuple):
            return str(tuple([str(v) if isinstance(v,basestring) else v for v in obj]))
        else:
            try:
                return str(obj)
            except:
                return unicode(obj)

    if align_vals:
        key_width = 0
        for key, val in d.items():
            if not isinstance(val,dict):
                key_str = convert_str(key)
                key_width = max(key_width, len(key_str))

    max_depth = depth
    for key in natural_sort(d.keys()):
        value = d[key]
        key_str = convert_str(key)

        if align_vals:
            key_str = '{0: <{1}} '.format(key_str+delim,key_width+len(delim))
        else:
            key_str = '{0}{1} '.format(key_str,delim)

        depth = max_depth if not max_depth is None else 2
        if depth <= 0:
            pass
        elif isinstance(value, dict):
            if depth <= 1:
                print_func(' ' * initindent + key_str + '{...}')
            else:
                print_func(' ' * initindent + key_str)
                dict_pprint(value, lvlindent, initindent+lvlindent,delim,
                            max_width,depth=max_depth-1 if not max_depth is None else None,
                            no_values=no_values,align_vals=align_vals,
                            encoder=encoder,print_func=print_func)
        else:
            val_string = value
            if not encoder is None:
                try:
                    val_string = encoder(value, as_str=True)
                except TypeError:
                   pass
            val_string = convert_str(val_string) if not no_values else ''
            if not max_width is None:
                if len(' ' * initindent + key_str)+1 > max_width:
                    raise Exception('cannot fit keys and data within set max_width')
                # divide into chuncks and join by same indentation
                val_indent = ' ' * (initindent + len(key_str))
                n = max_width - len(val_indent)
                val_string = val_indent.join([s + ' \n' for s in textwrap.wrap(val_string,n)])[:-2]

            print_func(' ' * initindent + key_str + val_string)

def dict_extract(d,path=None):
    """ extract section of dictionary

    Parameters
    ----------
    d : dict
    path : list of str
        keys to section

    Returns
    -------
    new_dict : dict
        original, without extracted section
    extract_dict : dict
        extracted section

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {1:{"a":"A"},2:{"b":"B",'c':'C'}}
    >>> pprint(dict_extract(d,[2,'b']))
    ({1: {'a': 'A'}, 2: {'c': 'C'}}, {'b': 'B'})

    """
    path = [] if path is None else path

    d_new = copy.deepcopy(d)
    d_sub = d_new
    for key in path[:-1]:
        d_sub = d_sub[key]

    key = path[-1]
    d_extract = {key:d_sub[key]}
    d_sub.pop(key)

    return d_new, d_extract

def dict_multiindex(dic, keys=None):
    """ index dictionary by multiple keys

    Parameters
    ----------
    dic : dict
    keys : list

    Examples
    --------

    >>> d = {1:{"a":"A"},2:{"b":"B"}}
    >>> dict_multiindex(d,[1,'a'])
    'A'

    """
    keys = [] if keys is None else keys

    assert hasattr(dic,'keys')
    new = dic.copy()
    for key in keys:
        if not hasattr(new,'keys'):
            raise KeyError('No indexes after: {}'.format(old_key))
        old_key = key
        new = new[key]
    return new

def dict_flatten(d,key_as_tuple=True,sep='.'):
    """ get nested dict as {key:val,...}, where key is tuple/string of all nested keys

    Parameters
    ----------
    d : dict
    key_as_tuple : bool
        whether keys are list of nested keys or delimited string of nested keys
    sep : str
        if key_as_tuple=False, delimiter for keys

    Examples
    --------

    >>> from pprint import pprint

    >>> d = {1:{"a":"A"},2:{"b":"B"}}
    >>> pprint(dict_flatten(d))
    {(1, 'a'): 'A', (2, 'b'): 'B'}

    >>> d = {1:{"a":"A"},2:{"b":"B"}}
    >>> pprint(dict_flatten(d,key_as_tuple=False))
    {'1.a': 'A', '2.b': 'B'}

    """
    def expand(key, value):
        if isinstance(value, dict):
            if key_as_tuple:
                return [ (key + k, v) for k, v in dict_flatten(value,key_as_tuple).items() ]
            else:
                return [ (str(key) + sep + k, v) for k, v in dict_flatten(value,key_as_tuple).items() ]
        else:
            return [ (key, value) ]

    if key_as_tuple:
        items = [ item for k, v in d.items() for item in expand((k,), v) ]
    else:
        items = [ item for k, v in d.items() for item in expand(k, v) ]

    return dict(items)

def dict_unflatten(d, key_as_tuple=True,delim='.'):
    """ unlatten dictionary
    with keys as tuples or delimited strings

    Parameters
    ----------
    d : dict
    key_as_tuple : bool
        if true, keys are tuples, else, keys are delimited strings
    delim : str
        if keys are strings, then split by delim

    Examples
    --------

    >>> from pprint import pprint

    >>> d = {('a','b'):1,('a','c'):2}
    >>> pprint(dict_unflatten(d))
    {'a': {'b': 1, 'c': 2}}

    >>> d2 = {'a.b':1,'a.c':2}
    >>> pprint(dict_unflatten(d2,key_as_tuple=False))
    {'a': {'b': 1, 'c': 2}}

    """
    d = copy.deepcopy(d)
    
    if key_as_tuple:
        result = d.pop(()) if () in d else {}
    else:
        result = d.pop('') if '' in d else {}
        
    for key, value in d.items():

        if not isinstance(key,tuple) and key_as_tuple:
            raise ValueError('key not tuple and key_as_tuple set to True: {}'.format(key))
        elif not isinstance(key,basestring) and not key_as_tuple:
            raise ValueError('key not string and key_as_tuple set to False: {}'.format(key))
        elif isinstance(key,basestring) and not key_as_tuple:
            parts = key.split(delim)
        else:
            parts = key
            
        d = result
        for part in parts[:-1]:
            if part not in d:
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value

    return result

def dicts_merge(dicts,overwrite=False,append=False):
    """ merge dicts,
    starting with dicts[1] into dicts[0]

    Parameters
    ----------
    dicts : list
        list of dictionaries
    overwrite : bool
        if true allow overwriting of current data
    append : bool
        if true and items are both lists, then add them

    Examples
    --------

    >>> from pprint import pprint

    >>> d1 = {1:{"a":"A"},2:{"b":"B"}}
    >>> d2 = {1:{"a":"A"},2:{"c":"C"}}
    >>> pprint(dicts_merge([d1,d2]))
    {1: {'a': 'A'}, 2: {'b': 'B', 'c': 'C'}}

    >>> d1 = {1:{"a":["A"]}}
    >>> d2 = {1:{"a":["D"]}}
    >>> pprint(dicts_merge([d1,d2],append=True))
    {1: {'a': ['A', 'D']}}

    >>> d1 = {1:{"a":"A"},2:{"b":"B"}}
    >>> d2 = {1:{"a":"X"},2:{"c":"C"}}
    >>> dicts_merge([d1,d2],overwrite=False)
    Traceback (most recent call last):
    ...
    ValueError: different data already exists at 1.a: old: A, new: X

    >>> dicts_merge([{},{}],overwrite=False)
    {}
    >>> dicts_merge([{},{'a':1}],overwrite=False)
    {'a': 1}
    >>> pprint(dicts_merge([{},{'a':1},{'a':1},{'b':2}]))
    {'a': 1, 'b': 2}

    """
    outdict = copy.deepcopy(dicts[0])

    def merge(a, b, overwrite=overwrite, error_path=None):
        """merges b into a
        """
        if error_path is None: error_path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    merge(a[key], b[key], overwrite, error_path + [str(key)])
                elif isinstance(a[key], list) and isinstance(b[key], list) and append:
                    a[key] += b[key]
                elif a[key] == b[key]:
                    pass # same leaf value
                elif overwrite:
                    a[key] = b[key]
                else:
                    raise ValueError('different data already exists at {0}: old: {1}, new: {2}'.format(
                        '.'.join(error_path + [str(key)]),a[key],b[key]))
            else:
                a[key] = b[key]
        return a

    reduce(merge, [outdict]+dicts[1:])

    return outdict

def dict_flattennd(d,levels=0,key_as_tuple=True,delim='.'):
    """ get nested dict as {key:dict,...},
    where key is tuple/string of all-nlevels of nested keys

    Parameters
    ----------
    d : dict
    levels : int
        the number of levels to leave unflattened
    key_as_tuple : bool
        whether keys are list of nested keys or delimited string of nested keys
    delim : str
        if key_as_tuple=False, delimiter for keys

    Examples
    --------

    >>> from pprint import pprint

    >>> d = {1:{2:{3:{'b':'B','c':'C'},4:'D'}}}
    >>> pprint(dict_flattennd(d,0))
    {(1, 2, 3, 'b'): 'B', (1, 2, 3, 'c'): 'C', (1, 2, 4): 'D'}

    >>> pprint(dict_flattennd(d,1))
    {(1, 2): {4: 'D'}, (1, 2, 3): {'b': 'B', 'c': 'C'}}

    >>> pprint(dict_flattennd(d,2))
    {(1,): {2: {4: 'D'}}, (1, 2): {3: {'b': 'B', 'c': 'C'}}}

    >>> pprint(dict_flattennd(d,3))
    {(): {1: {2: {4: 'D'}}}, (1,): {2: {3: {'b': 'B', 'c': 'C'}}}}
    
    >>> pprint(dict_flattennd(d,4))
    {(): {1: {2: {3: {'b': 'B', 'c': 'C'}, 4: 'D'}}}}

    >>> pprint(dict_flattennd(d,5))
    {(): {1: {2: {3: {'b': 'B', 'c': 'C'}, 4: 'D'}}}}

    >>> pprint(dict_flattennd(d,1,key_as_tuple=False,delim='.'))
    {'1.2': {4: 'D'}, '1.2.3': {'b': 'B', 'c': 'C'}}

    """
    if levels < 0:
        raise ValueError('unflattened levels must be greater than 0')

    new_d = {}
    flattened = dict_flatten(d,True,delim)
    if levels == 0:
        return flattened
    
    for key, value in flattened.items():
        new_key = key[:-(levels)] if key_as_tuple else delim.join([str(k) for k in key[:-(levels)]])
        new_levels = key[-(levels):]

        val_dict = {new_levels:value}
        val_dict = dict_unflatten(val_dict,True,delim)

        if not new_key in new_d:
            new_d[new_key] = val_dict
        else:
            new_d[new_key] = dicts_merge([new_d[new_key],val_dict])

    return new_d

def dict_flatten2d(d,key_as_tuple=True,delim='.'):
    """ get nested dict as {key:dict,...},
    where key is tuple/string of all-1 nested keys
    
    NB: is same as dict_flattennd(d,1,key_as_tuple,delim)

    Parameters
    ----------
    d : dict
    key_as_tuple : bool
        whether keys are list of nested keys or delimited string of nested keys
    delim : str
        if key_as_tuple=False, delimiter for keys

    Examples
    --------

    >>> from pprint import pprint

    >>> d = {1:{2:{3:{'b':'B','c':'C'},4:'D'}}}
    >>> pprint(dict_flatten2d(d))
    {(1, 2): {4: 'D'}, (1, 2, 3): {'b': 'B', 'c': 'C'}}

    >>> pprint(dict_flatten2d(d,key_as_tuple=False,delim=','))
    {'1,2': {4: 'D'}, '1,2,3': {'b': 'B', 'c': 'C'}}

    """
    return dict_flattennd(d,1,key_as_tuple,delim)

def dict_remove_keys(d, keys=None):
    """ remove certain keys from nested dict, retaining preceeding paths

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {1:{"a":"A"},"a":{"b":"B"}}
    >>> pprint(dict_remove_keys(d,['a']))
    {1: 'A', 'b': 'B'}

    """
    keys = [] if keys is None else keys

    if not hasattr(d, 'items'):
        return d
    else:
        dic = dict_flatten(d)
        new_dic = {}
        for key,value in dic.items():
            new_key = tuple([i for i in key if i not in keys])
            new_dic[new_key] = value
        return dict_unflatten(new_dic)

def dict_remove_paths(d, keys=None):
    """ remove paths containing certain keys from dict

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {1:{"a":"A"},2:{"b":"B"},4:{5:{6:'a',7:'b'}}}
    >>> pprint(dict_remove_paths(d,[6,'a']))
    {1: {}, 2: {'b': 'B'}, 4: {5: {7: 'b'}}}

    """
    keys = [] if keys is None else keys
    if not hasattr(d, 'items'):
        return d
    else:
        return {key: dict_remove_paths(value,keys) for key, value in d.items() if key not in keys}

def dict_filter_values(d,vals=None):
    """ filters leaf nodes of nested dictionary

    Parameters
    ----------
    d : dict
    vals : list
        values to filter by

    Examples
    --------

    >>> d = {1:{"a":"A"},2:{"b":"B"},4:{5:{6:'a'}}}
    >>> dict_filter_values(d,['a'])
    {4: {5: {6: 'a'}}}

    """
    vals = [] if vals is None else vals

    def fltr(dic):
        for key in list(dic.keys()):
            if isinstance(dic[key], dict):
                fltr(dic[key])
                if not dic[key]:
                    del dic[key]
            elif dic[key] not in vals:
                del dic[key]

    d = copy.deepcopy(d)
    fltr(d)
    return d

def dict_filter_keys(d, keys, use_wildcards=False):
    """ filter dict by certain keys

    Parameters
    ----------
    d : dict
    keys: list
    use_wildcards : bool
        if true, can use * (matches everything) and ? (matches any single character)

    Examples
    --------

    >>> from pprint import pprint

    >>> d = {1:{"a":"A"},2:{"b":"B"},4:{5:{6:'a',7:'b'}}}
    >>> pprint(dict_filter_keys(d,['a',6]))
    {1: {'a': 'A'}, 4: {5: {6: 'a'}}}

    >>> d = {1:{"axxxx":"A"},2:{"b":"B"}}
    >>> pprint(dict_filter_keys(d,['a*'],use_wildcards=True))
    {1: {'axxxx': 'A'}}

    """
    if isinstance(d, dict):
        retVal = {}
        for key in d:
            if use_wildcards and isinstance(key, basestring):
                if any([fnmatch(key,k) for k in keys]):
                    retVal[key] = copy.deepcopy(d[key])
                elif isinstance(d[key], list) or isinstance(d[key], dict):
                    child = dict_filter_keys(d[key], keys, use_wildcards)
                    if child:
                        retVal[key] = child
            elif key in keys:
                retVal[key] = copy.deepcopy(d[key])
            elif isinstance(d[key], list) or isinstance(d[key], dict):
                child = dict_filter_keys(d[key], keys, use_wildcards)
                if child:
                    retVal[key] = child
        if retVal:
             return retVal
        else:
             return {}
    elif isinstance(d, list):
        retVal = []
        for entry in d:
            child = dict_filter_keys(entry, keys, use_wildcards)
            if child:
                retVal.append(child)
        if retVal:
            return retVal
        else:
            return []

def dict_filter_paths(d, paths):
    """ filter dict by certain paths containing key sets

    Parameters
    ----------
    d : dict
    paths : list

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {'a':{'b':1,'c':{'d':2}},'e':{'c':3}}
    >>> dict_filter_paths(d,[('c','d')])
    {'a': {'c': {'d': 2}}}

    """
    all_keys = [x for y in paths if isinstance(y,tuple) for x in y]
    all_keys += [x for x in paths if not isinstance(x,tuple)]
    # faster to filter first I think
    new_d = dict_filter_keys(d,all_keys)
    new_d = dict_flatten(d)
    for key in list(new_d.keys()):
        if not any([set(key).issuperset(path if isinstance(path,tuple) else [path]) for path in paths]):
            new_d.pop(key)
    return dict_unflatten(new_d)

def dict_rename_keys(d,keymap=None):
    """ rename keys in dict

    Parameters
    ----------
    d : dict
    keymap : dict
        dictionary of key name mappings

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {'a':{'old_name':1}}
    >>> pprint(dict_rename_keys(d,{'old_name':'new_name'}))
    {'a': {'new_name': 1}}

    """
    keymap = {} if keymap is None else keymap
    if not hasattr(d, 'items'):
        return d
    else:
        return {keymap[key] if key in keymap else key: dict_rename_keys(value,keymap) for key, value in d.items()}

def dict_combine_lists(d, combine, 
                 combine_key='combined',check_length=True):
    """combine key:list pairs into dicts for each item in the lists
    
    Parameters
    ----------
    d : dict
    combine : list
        keys to combine
    combine_key : str
        top level key for combined items
    check_length : bool
        if true, raise error if any lists are of a different length
        
    Examples
    --------

    >>> from pprint import pprint

    >>> d = {'path_key':{'x':[1,2],'y':[3,4],'a':1}}
    >>> new_d = dict_combine_lists(d,['x','y'])
    >>> pprint(new_d)
    {'path_key': {'a': 1,
                  'combined': {'1': {'x': 1, 'y': 3}, '2': {'x': 2, 'y': 4}}}}
    
    >>> dict_combine_lists(d,['x','a'])
    Traceback (most recent call last):
    ...
    ValueError: "a" data at the following path is not a list ('path_key',)

    >>> d2 = {'path_key':{'x':[1,7],'y':[3,4,5]}}
    >>> dict_combine_lists(d2,['x','y'])
    Traceback (most recent call last):
    ...
    ValueError: lists at the following path do not have the same size ('path_key',)


    """    
    flattened = dict_flatten2d(d)

    new_d = {}
    for key, value in flattened.items():
        if set(combine).issubset(value.keys()):
            combine_d = {}
            sub_d = {}
            length = None
            for subkey, subvalue in value.items(): 
                if subkey in combine:
                    if not isinstance(subvalue,list):
                        raise ValueError('"{0}" data at the following path is not a list {1}'.format(subkey,key))

                    if check_length and length is not None:
                        if len(subvalue)!=length:
                            raise ValueError('lists at the following path '
                                             'do not have the same size {0}'.format(key))

                    length = len(subvalue)
                    new_combine = {str(k+1):{subkey:v} for k,v in enumerate(subvalue)}
                    combine_d = dicts_merge([combine_d,new_combine])
                else:
                    sub_d[subkey] = subvalue
                try:
                    new_d[key] = dicts_merge([sub_d,{combine_key:combine_d}])
                except ValueError as err:
                    raise ValueError('combined data key: '
                                     '{0}, already exists at this level for {1}'.format(combine_key,key))
        else:
            new_d[key] = value
    
    return dict_unflatten(new_d)

class DictTree(object):
    """ a class to explore nested dictionaries by attributes

        Examples
        --------

        >>> from pprint import pprint

        >>> d = {'a':{'b':{'c':[1,2,3],'d':[4,5,6]}}}
        >>> tree = DictTree(d)
        >>> pprint(tree.a.b.attr_Dict)
        {'c': [1, 2, 3], 'd': [4, 5, 6]}
        >>> tree.a.b.c
        [1, 2, 3]
        >>> tree[['a','b','d']]
        [4, 5, 6]
        >>> tree.a.b.attr_DF
           c  d
        0  1  4
        1  2  5
        2  3  6

    """
    def __init__(self, ndict):
        """ explore nested dictionaries by attributes

        ndict : dict
            nested dictionary

        """
        self._val = ndict

        for name in ndict:
            val = ndict[name]
            if isinstance(val, dict):
                val = DictTree(val)
            setattr(self,self._convert(name),val)

        if isinstance(ndict, dict):
            setattr(self,'attr_Dict',ndict)
            try:
                setattr(self,'attr_DF',pd.DataFrame(ndict))
            except NameError:
                warnings.warn('pandas package not found in environment, \
please install to view leaf dicts as DataFrames',ImportWarning)
            except:
                pass

    def __repr__(self):
        return 'dicttree({})'.format(str(self._val.__repr__()))

    def __getitem__(self, keys):
        if isinstance(keys,basestring):
            keys = [keys]
        if not isinstance(self._val, dict):
            return None
        else:
            d = self._val
            for k in keys:
                d = d[k]
            if isinstance(d, dict):
                return DictTree(d)
            else:
                return d

    def _convert(self,val):
        """attributes aren't allowed to start with a number
        and replace non alphanumeric characters with _
        """
        try:
            int(str(val)[0])
            val = 'i'+str(val)
        except:
            pass
        return re.sub('[^0-9a-zA-Z]+', '_', str(val))

class dict_to_html(object):
    """
    Pretty display dictionary in collapsible format with indents

    Parameters
    ----------
    depth: int
        Depth of the json tree structure displayed, the rest is collapsed.
    max_length: int
        Maximum number of characters of a string displayed as preview, longer string appear collapsed.
    max_height: int
        Maxium height in pixels of containing box.
    sort: bool
        Whether the json keys are sorted alphabetically.

    Examples
    ---------

    dic = {'sape': {'value': 22}, 'jack': 4098, 'guido': 4127}
    dict_to_html(dic, depth=1, max_length=10, sort=False)

    """

    _CSS = '<style>' + """
    .renderjson a              { text-decoration: none; }
    .renderjson .disclosure    { color: red;
                                 font-size: 125%; }
    .renderjson .syntax        { color: darkgrey; }
    .renderjson .string        { color: black; }
    .renderjson .number        { color: black; }
    .renderjson .boolean       { color: purple; }
    .renderjson .key           { color: royalblue; }
    .renderjson .keyword       { color: orange; }
    .renderjson .object.syntax { color: lightseagreen; }
    .renderjson .array.syntax  { color: lightseagreen; }
    """ + '</style>'

    def __init__(self, obj, depth=2, max_length=20, max_height=600,
                 sort=True,encoder=json_extended_encoder):
        """
        depth: int
            Depth of the json tree structure displayed, the rest is collapsed.
        max_length: int
            Maximum number of characters of a string displayed as preview, longer string appear collapsed.
        max_height: int
            Maxium height in pixels of containing box.
        sort: bool
            Whether the json keys are sorted alphabetically.
        encoder : func
            extend objects that can be json encoded

        """

        def is_json(myjson):
            try:
                json_object = json.loads(myjson)
            except ValueError:
                return False
            return True

        if isinstance(obj, dict):
            self.json_str = json.dumps(obj,default=encoder)
        elif is_json(obj):
            self.json_str = obj
        else:
            raise ValueError('Wrong Input, dict or json expected')

        self.uuid = str(uuid.uuid4())
        self.depth = int(depth)
        self.max_length = int(max_length)
        self.max_height = int(max_height)
        self.sort = json.dumps(sort)


    def _get_html(self):
        return """<div id="{0}" style="max-height: {1}px; width:100%%;"></div>
                """.format(self.uuid, self.max_height)

    def _get_renderjson_path(self):
        #return os.path.join(os.path.dirname(os.path.dirname(os.path.relpath(inspect.getfile(_example_json_folder)))),
        #                              'renderjson.js')
        renderjson = 'jsonextended/renderjson.js'
        if sys.version_info < (3,0):
            return renderjson
        # try online, python 2 doesn't seem to like it
        try:
            renderjson = 'https://rawgit.com/caldwell/renderjson/master/renderjson.js'
            urlopen(renderjson)
        except:
            pass
        return renderjson

    def _get_javascript(self):
        renderjson = self._get_renderjson_path()
        return """<script>
            require(["{0}"], function() {{
                document.getElementById("{1}").appendChild(
                    renderjson.set_max_string_length({2})
                              //.set_icons(circled plus, circled minus)
                              .set_icons(String.fromCharCode(8853), String.fromCharCode(8854))
                              .set_sort_objects({3})
                              .set_show_to_level({4})({5}))
            }});</script>""".format(renderjson, self.uuid, self.max_length,
                                   self.sort, self.depth, self.json_str)


    def _repr_html_(self):

        return self._CSS+self._get_html()+self._get_javascript()

    def __ipython_display_(self):

        from IPython.display import display_html, display_javascript
        display_html(self._CSS+self._get_html())
        display_javascript(self._get_javascript())

if __name__ == '__main__':
    import doctest
    print(doctest.testmod())
