#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" a module to manipulate python dictionary like objects

"""
# internal packages
import os, sys
import copy
import uuid
import json
import re
from fnmatch import fnmatch
import textwrap
from functools import reduce, total_ordering

# python 3 to 2 compatibility
try:
    basestring
except NameError:
    basestring = str
try:
    unicode
except NameError:
    unicode = str
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

# external packages
import warnings
warnings.simplefilter('once',ImportWarning)

# local imports
from jsonextended.utils import natural_sort, colortxt
from jsonextended.plugins import encode, decode, parse, parser_available

def is_dict_like(obj,attr=('keys','items')):
    """test if object is dict like"""
    for a in attr:
        if not hasattr(obj, a):
           return False
    return True 

def is_path_like(obj,attr=('name','is_file', 'is_dir', 'iterdir')):
    """test if object is pathlib.Path like"""
    for a in attr:
        if not hasattr(obj, a):
           return False
    return True 

def convert_type(d, intype, outtype, convert_list=True, in_place=True):
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
    >>> pprint(convert_type(d,str,float))
    {'a': 1.0, 'b': 2.0}
    
    >>> d = {'a':['1','2']}
    >>> pprint(convert_type(d,str,float))
    {'a': [1.0, 2.0]}

    >>> d = {'a':[('1','2'),[3,4]]}
    >>> pprint(convert_type(d,str,float))
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
            if is_dict_like(dic[key]):
                _traverse_dict(dic[key])
            else:
                dic[key] = _convert(dic[key])

    def _traverse_iter(iter):
        new_iter = []
        for key in iter:
            if is_dict_like(key):
                _traverse_dict(key)
                new_iter.append(key)
            else:
                new_iter.append(_convert(key))
                
        return new_iter

    if is_dict_like(out_dict):
        _traverse_dict(out_dict)
    else:
        data = _convert(out_dict)
    
    return out_dict

def _default_print_func(s):
    print(s)

def _strip_ansi(source):
    """
    Remove ANSI escape codes from text.
    Parameters
    ----------
    source : str
        Source to remove the ANSI from
    """
    ansi_re = re.compile('\x1b\\[(.*?)([@-~])')
    return ansi_re.sub('', source)

def pprint(d, lvlindent=2, initindent=0, delim=':',
           max_width=80, depth=3, no_values=False,
           align_vals=True, print_func=None,
           keycolor=None, compress_lists=None,
           round_floats=None, _dlist=False):
    """ print a nested dict in readable format
        (- denotes an element in a list of dictionaries)

    Parameters
    ----------
    d : obj
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
    print_func : func or None
        function to print strings (print if None)
    keycolor : None or str
         if str, color keys by this color, 
         allowed: red, green, yellow, blue, magenta, cyan, white
    compress_lists : int
         compress lists/tuples longer than this,
          e.g. [1,1,1,1,1,1] -> [1, 1,..., 1]
    round_floats : int
         significant figures for floats  

    Examples
    --------

    >>> d = {'a':{'b':{'c':'Å','de':[4,5,[7,'x'],9]}}}
    >>> pprint(d,depth=None)
    a: 
      b: 
        c:  Å
        de: [4, 5, [7, x], 9]
    >>> pprint(d,max_width=17,depth=None)
    a: 
      b: 
        c:  Å
        de: [4, 5, 
            [7, x], 
            9]
    >>> pprint(d,no_values=True,depth=None)
    a: 
      b: 
        c:  
        de: 
    >>> pprint(d,depth=2)
    a: 
      b: {...}
    >>> pprint({'a':[1,1,1,1,1,1,1,1]},
    ...        compress_lists=3)
    a: [1, 1, 1, ...(x5)]

    """
    if print_func is None:
        print_func = _default_print_func

    if not is_dict_like(d):
        d = {'':d}
        #print_func('{}'.format(d))
        #return
        
    extra = lvlindent if _dlist else 0

    def decode_to_str(obj):
        val_string = obj
        if isinstance(obj, list):
            if compress_lists is not None:
                if len(obj) > compress_lists:
                    diff = str(len(obj) - compress_lists)
                    obj = obj[:compress_lists] + ['...(x{})'.format(diff)]
            val_string = '['+', '.join([decode_to_str(o) for o in obj])+']'
        elif isinstance(obj, tuple):
            if compress_lists is not None:
                if len(obj) > compress_lists:
                    diff = str(len(obj) - compress_lists)
                    obj = list(obj[:compress_lists]) + ['...(x{})'.format(diff)]
            val_string = '('+', '.join([decode_to_str(o) for o in obj])+')'
        elif isinstance(obj, float) and round_floats is not None:
            round_str = '{0:.' + str(round_floats-1) + 'E}'
            val_string = str(float(round_str.format(obj)))
        else:
            try:
                val_string = encode(obj, outtype='str')
            except (TypeError, UnicodeError):
               pass
        # convert unicode to str (so no u'' prefix in python 2)         
        try:
            return str(val_string)
        except:
            return unicode(val_string)

    if align_vals:
        key_width = 0
        for key, val in d.items():
            if not is_dict_like(val):
                key_str = decode_to_str(key)
                key_width = max(key_width, len(key_str))

    max_depth = depth
    for i, key in enumerate(natural_sort(d.keys())):
        value = d[key]
        if _dlist and i==0:
            key_str = '- ' + decode_to_str(key)
        elif _dlist:
            key_str = '  ' + decode_to_str(key)
        else:
            key_str = decode_to_str(key)
        
        if keycolor is not None:
            key_str = colortxt(key_str,keycolor)

        if align_vals:
            key_str = '{0: <{1}} '.format(key_str+delim,key_width+len(delim))
        else:
            key_str = '{0}{1} '.format(key_str,delim)

        depth = max_depth if not max_depth is None else 2
        if keycolor is not None:
            key_length = len(_strip_ansi(key_str))
        else:
            key_length = len(key_str)
        key_line = ' ' * initindent + key_str
        new_line = ' ' * initindent + ' '*key_length

        if depth <= 0:
            continue
        if is_dict_like(value):
            if depth <= 1:
                print_func(' ' * initindent + key_str + '{...}')
            else:
                print_func(' ' * initindent + key_str)
                pprint(value, lvlindent, initindent+lvlindent+extra,delim,
                            max_width,depth=max_depth-1 if not max_depth is None else None,
                            no_values=no_values,align_vals=align_vals,
                            print_func=print_func,keycolor=keycolor,
                            compress_lists=compress_lists,round_floats=round_floats)
            continue
            
        if isinstance(value,list):
            if all([is_dict_like(o) for o in value]) and value:
                if depth <= 1:
                    print_func(key_line + '[...]')  
                    continue     
                print_func(key_line)            
                for obj in value:
                    pprint(obj, lvlindent, initindent+lvlindent+extra,delim,
                        max_width,depth=max_depth-1 if not max_depth is None else None,
                        no_values=no_values,align_vals=align_vals,
                        print_func=print_func,keycolor=keycolor,
                        compress_lists=compress_lists,
                        round_floats=round_floats,_dlist=True)
                continue
        
        val_string_all = decode_to_str(value) if not no_values else ''        
        for i, val_string in enumerate(val_string_all.split('\n')):            
            if not max_width is None:
                if len(key_line)+1 > max_width:
                    raise Exception('cannot fit keys and data within set max_width')
                # divide into chuncks and join by same indentation
                val_indent = ' ' * (initindent + key_length)
                n = max_width - len(val_indent)
                val_string = val_indent.join([s + ' \n' for s in textwrap.wrap(val_string,n)])[:-2]

            if i==0:
                print_func(key_line + val_string)
            else:
                print_func(new_line + val_string)

def extract(d,path=None):
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
    >>> pprint(extract(d,[2,'b']))
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

def indexes(dic, keys=None):
    """ index dictionary by multiple keys

    Parameters
    ----------
    dic : dict
    keys : list

    Examples
    --------

    >>> d = {1:{"a":"A"},2:{"b":"B"}}
    >>> indexes(d,[1,'a'])
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

def flatten(d,key_as_tuple=True,sep='.'):
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
    >>> pprint(flatten(d))
    {(1, 'a'): 'A', (2, 'b'): 'B'}

    >>> d = {1:{"a":"A"},2:{"b":"B"}}
    >>> pprint(flatten(d,key_as_tuple=False))
    {'1.a': 'A', '2.b': 'B'}

    """
    def expand(key, value):
        if is_dict_like(value):
            if key_as_tuple:
                return [ (key + k, v) for k, v in flatten(value,key_as_tuple).items() ]
            else:
                return [ (str(key) + sep + k, v) for k, v in flatten(value,key_as_tuple).items() ]
        else:
            return [ (key, value) ]

    if key_as_tuple:
        items = [ item for k, v in d.items() for item in expand((k,), v) ]
    else:
        items = [ item for k, v in d.items() for item in expand(k, v) ]

    return dict(items)

def unflatten(d, key_as_tuple=True,delim='.'):
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
    >>> pprint(unflatten(d))
    {'a': {'b': 1, 'c': 2}}

    >>> d2 = {'a.b':1,'a.c':2}
    >>> pprint(unflatten(d2,key_as_tuple=False))
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

def merge(dicts,overwrite=False,append=False):
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
    >>> pprint(merge([d1,d2]))
    {1: {'a': 'A'}, 2: {'b': 'B', 'c': 'C'}}

    >>> d1 = {1:{"a":["A"]}}
    >>> d2 = {1:{"a":["D"]}}
    >>> pprint(merge([d1,d2],append=True))
    {1: {'a': ['A', 'D']}}

    >>> d1 = {1:{"a":"A"},2:{"b":"B"}}
    >>> d2 = {1:{"a":"X"},2:{"c":"C"}}
    >>> merge([d1,d2],overwrite=False)
    Traceback (most recent call last):
    ...
    ValueError: different data already exists at 1.a: old: A, new: X

    >>> merge([{},{}],overwrite=False)
    {}
    >>> merge([{},{'a':1}],overwrite=False)
    {'a': 1}
    >>> pprint(merge([{},{'a':1},{'a':1},{'b':2}]))
    {'a': 1, 'b': 2}

    """
    outdict = copy.deepcopy(dicts[0])

    def single_merge(a, b, overwrite=overwrite, error_path=None):
        """merges b into a
        """
        if error_path is None: error_path = []
        for key in b:
            if key in a:
                if is_dict_like(a[key]) and is_dict_like(b[key]):
                    single_merge(a[key], b[key], overwrite, error_path + [str(key)])
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

    reduce(single_merge, [outdict]+dicts[1:])

    return outdict

def flattennd(d,levels=0,key_as_tuple=True,delim='.'):
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
    >>> pprint(flattennd(d,0))
    {(1, 2, 3, 'b'): 'B', (1, 2, 3, 'c'): 'C', (1, 2, 4): 'D'}

    >>> pprint(flattennd(d,1))
    {(1, 2): {4: 'D'}, (1, 2, 3): {'b': 'B', 'c': 'C'}}

    >>> pprint(flattennd(d,2))
    {(1,): {2: {4: 'D'}}, (1, 2): {3: {'b': 'B', 'c': 'C'}}}

    >>> pprint(flattennd(d,3))
    {(): {1: {2: {4: 'D'}}}, (1,): {2: {3: {'b': 'B', 'c': 'C'}}}}
    
    >>> pprint(flattennd(d,4))
    {(): {1: {2: {3: {'b': 'B', 'c': 'C'}, 4: 'D'}}}}

    >>> pprint(flattennd(d,5))
    {(): {1: {2: {3: {'b': 'B', 'c': 'C'}, 4: 'D'}}}}

    >>> pprint(flattennd(d,1,key_as_tuple=False,delim='.'))
    {'1.2': {4: 'D'}, '1.2.3': {'b': 'B', 'c': 'C'}}

    """
    if levels < 0:
        raise ValueError('unflattened levels must be greater than 0')

    new_d = {}
    flattened = flatten(d,True,delim)
    if levels == 0:
        return flattened
    
    for key, value in flattened.items():
        new_key = key[:-(levels)] if key_as_tuple else delim.join([str(k) for k in key[:-(levels)]])
        new_levels = key[-(levels):]

        val_dict = {new_levels:value}
        val_dict = unflatten(val_dict,True,delim)

        if not new_key in new_d:
            new_d[new_key] = val_dict
        else:
            new_d[new_key] = merge([new_d[new_key],val_dict])

    return new_d

def flatten2d(d,key_as_tuple=True,delim='.'):
    """ get nested dict as {key:dict,...},
    where key is tuple/string of all-1 nested keys
    
    NB: is same as flattennd(d,1,key_as_tuple,delim)

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
    >>> pprint(flatten2d(d))
    {(1, 2): {4: 'D'}, (1, 2, 3): {'b': 'B', 'c': 'C'}}

    >>> pprint(flatten2d(d,key_as_tuple=False,delim=','))
    {'1,2': {4: 'D'}, '1,2,3': {'b': 'B', 'c': 'C'}}

    """
    return flattennd(d,1,key_as_tuple,delim)

def remove_keys(d, keys=None):
    """ remove certain keys from nested dict, retaining preceeding paths

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {1:{"a":"A"},"a":{"b":"B"}}
    >>> pprint(remove_keys(d,['a']))
    {1: 'A', 'b': 'B'}

    """
    keys = [] if keys is None else keys

    if not hasattr(d, 'items'):
        return d
    else:
        dic = flatten(d)
        new_dic = {}
        for key,value in dic.items():
            new_key = tuple([i for i in key if i not in keys])
            new_dic[new_key] = value
        return unflatten(new_dic)

def remove_keyvals(d, keyvals=None):
    """ remove paths with at least one branch leading to certain (key,value) pairs from dict

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {1:{"b":"A"},"a":{"b":"B","c":"D"},"b":{"a":"B"}}
    >>> pprint(remove_keyvals(d,[("b","B")]))
    {1: {'b': 'A'}, 'b': {'a': 'B'}}

    """
    keyvals = [] if keyvals is None else keyvals

    if not hasattr(d, 'items'):
        return d
    
    flatd = flatten(d)
    def is_in(a,b):
        try:
            return a in b
        except:
            return False

    
    prune = [k[0] for k,v in flatd.items() if is_in((k[-1],v),keyvals)]
    flatd = {k:v for k,v in flatd.items() if not is_in(k[0],prune)}
    
    return unflatten(flatd)


def remove_paths(d, keys=None):
    """ remove paths containing certain keys from dict

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {1:{"a":"A"},2:{"b":"B"},4:{5:{6:'a',7:'b'}}}
    >>> pprint(remove_paths(d,[6,'a']))
    {1: {}, 2: {'b': 'B'}, 4: {5: {7: 'b'}}}

    """
    keys = [] if keys is None else keys
    if not hasattr(d, 'items'):
        return d
    else:
        return {key: remove_paths(value,keys) for key, value in d.items() if key not in keys}

def filter_values(d,vals=None):
    """ filters leaf nodes of nested dictionary

    Parameters
    ----------
    d : dict
    vals : list
        values to filter by

    Examples
    --------

    >>> d = {1:{"a":"A"},2:{"b":"B"},4:{5:{6:'a'}}}
    >>> filter_values(d,['a'])
    {4: {5: {6: 'a'}}}

    """
    vals = [] if vals is None else vals
    
    flatd = flatten(d)
    def is_in(a,b):
        try:
            return a in b
        except:
            return False

    flatd = {k:v for k,v in flatd.items() if is_in(v,vals)}
    return unflatten(flatd)
    
    # vals = [] if vals is None else vals
    #
    # def fltr(dic):
    #     for key in list(dic.keys()):
    #         if is_dict_like(dic[key]):
    #             fltr(dic[key])
    #             if not dic[key]:
    #                 del dic[key]
    #         elif dic[key] not in vals:
    #             del dic[key]
    #
    # d = copy.deepcopy(d)
    # fltr(d)
    # return d

def filter_keyvals(d,vals=None):
    """ filters leaf nodes key:value pairs of nested dictionary

    Parameters
    ----------
    d : dict
    vals : list of tuples
        (key,value) to filter by

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {1:{6:'a'},3:{7:'a'},2:{6:"b"},4:{5:{6:'a'}}}
    >>> pprint(filter_keyvals(d,[(6,'a')]))
    {1: {6: 'a'}, 4: {5: {6: 'a'}}}

    """
    vals = [] if vals is None else vals
    
    flatd = flatten(d)
    def is_in(a,b):
        try:
            return a in b
        except:
            return False

    flatd = {k:v for k,v in flatd.items() if is_in((k[-1],v),vals)}
    return unflatten(flatd)
    

    # def fltr(dic):
    #     for key in list(dic.keys()):
    #         if is_dict_like(dic[key]):
    #             fltr(dic[key])
    #             if not dic[key]:
    #                 del dic[key]
    #         elif (key,dic[key]) not in vals:
    #             del dic[key]
    #
    # d = copy.deepcopy(d)
    # fltr(d)
    # return d

# def _filter_key_recurse(d, keys, use_wildcards):
#     if is_dict_like(d):
#         retVal = {}
#         for key in d:
#             if use_wildcards and isinstance(key, basestring):
#                 if any([fnmatch(key,k) for k in keys]):
#                     retVal[key] = d[key]
#                 elif isinstance(d[key], list) or is_dict_like(d[key]):
#                     child = _filter_key_recurse(d[key], keys, use_wildcards)
#                     if child:
#                         retVal[key] = child
#             elif key in keys:
#                 retVal[key] = d[key]
#             elif isinstance(d[key], list) or is_dict_like(d[key]):
#                 child = _filter_key_recurse(d[key], keys, use_wildcards)
#                 if child:
#                     retVal[key] = child
#         if retVal:
#              return retVal
#         else:
#              return {}
#     elif isinstance(d, list):
#         retVal = []
#         for entry in d:
#             child = _filter_key_recurse(entry, keys, use_wildcards)
#             if child:
#                 retVal.append(child)
#         if retVal:
#             return retVal
#         else:
#             return []

def filter_keys(d, keys, use_wildcards=False):
    """ filter dict by certain keys

    Parameters
    ----------
    dic : dict
    keys: list
    use_wildcards : bool
        if true, can use * (matches everything) and ? (matches any single character)

    Examples
    --------

    >>> from pprint import pprint

    >>> d = {1:{"a":"A"},2:{"b":"B"},4:{5:{6:'a',7:'b'}}}
    >>> pprint(filter_keys(d,['a',6]))
    {1: {'a': 'A'}, 4: {5: {6: 'a'}}}

    >>> d = {1:{"axxxx":"A"},2:{"b":"B"}}
    >>> pprint(filter_keys(d,['a*'],use_wildcards=True))
    {1: {'axxxx': 'A'}}

    """
    flatd = flatten(d)
    def is_in(a,bs):
        if use_wildcards:
            for b in bs:
                try:
                    if a==b:
                        return True
                    if fnmatch(b,a):
                        return True  
                except:
                    pass
            return False
        else:
            try:
                return a in bs
            except:
                return False

    flatd = {paths:v for paths,v in flatd.items() if any([is_in(k,paths) for k in keys])}
    return unflatten(flatd)
    
    
    # new_dic = _filter_key_recurse(d, keys, use_wildcards)
    # if deepcopy:
    #     return copy.deepcopy(new_dic)
    # else:
        # return copy.copy(new_dic)
    

def filter_paths(d, paths):
    """ filter dict by certain paths containing key sets

    Parameters
    ----------
    d : dict
    paths : list

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {'a':{'b':1,'c':{'d':2}},'e':{'c':3}}
    >>> filter_paths(d,[('c','d')])
    {'a': {'c': {'d': 2}}}

    """
    all_keys = [x for y in paths if isinstance(y,tuple) for x in y]
    all_keys += [x for x in paths if not isinstance(x,tuple)]
    # faster to filter first I think
    new_d = filter_keys(d,all_keys)
    new_d = flatten(d)
    for key in list(new_d.keys()):
        if not any([set(key).issuperset(path if isinstance(path,tuple) else [path]) for path in paths]):
            new_d.pop(key)
    return unflatten(new_d)

def rename_keys(d,keymap=None):
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
    >>> pprint(rename_keys(d,{'old_name':'new_name'}))
    {'a': {'new_name': 1}}

    """
    keymap = {} if keymap is None else keymap
    if not hasattr(d, 'items'):
        return d
    else:
        return {keymap[key] if key in keymap else key: rename_keys(value,keymap) for key, value in d.items()}

def apply(d, leaf_key, func, new_name=None, **kwargs):
    """ apply a function to all values with a certain leaf (terminal) key
    
    Parameters
    ----------
    d : dict
    leaf_key : any
        name of leaf key
    func : func
        function to apply
    new_name : any
        if not None, rename leaf_key
    kwargs : dict
        additional keywords to parse to function

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {'a':1,'b':1}
    >>> func = lambda x: x+1
    >>> pprint(apply(d,'a',func))
    {'a': 2, 'b': 1}
    >>> pprint(apply(d,'a',func,new_name='c'))
    {'b': 1, 'c': 2}
    
    """
    flatd = flatten(d)
    flatd = {k:(func(v, **kwargs) if k[-1]==leaf_key else v) for k,v in flatd.items()}
    if new_name is not None:
        flatd = {(tuple(list(k[:-1])+[new_name]) if k[-1]==leaf_key else k):v for k,v in flatd.items()}
    
    return unflatten(flatd)

def combine_apply(d, leaf_keys, func, new_name, 
                  flatten_dict=True,
                  remove_lkeys=True,overwrite=False, 
                  **kwargs):
    """ combine values with certain leaf (terminal) keys by a function
    
    Parameters
    ----------
    d : dict
    leaf_keys : list
        names of leaf keys
    func : func
        function to apply, 
        must take at least len(leaf_keys) arguments
    new_name : any
        new key name
    flatten_dict : bool
        flatten the dict for combining
    remove_lkeys: bool
        whether to remove leaf_keys
    overwrite: bool
        whether to overwrite any existing new_name key
    kwargs : dict
        additional keywords to parse to function

    Examples
    --------

    >>> from pprint import pprint
    >>> d = {'a':1,'b':2}
    >>> func = lambda x,y: x+y
    >>> pprint(combine_apply(d,['a','b'],func,'c'))
    {'c': 3}
    >>> pprint(combine_apply(d,['a','b'],func,'c',remove_lkeys=False))
    {'a': 1, 'b': 2, 'c': 3}

    >>> d = {1:{'a':1,'b':2},2:{'a':4,'b':5},3:{'a':1}}
    >>> pprint(combine_apply(d,['a','b'],func,'c'))
    {1: {'c': 3}, 2: {'c': 9}, 3: {'a': 1}}
    
    
    """
    if flatten_dict:
        flatd = flatten2d(d)
    else:
        flatd = unflatten(d,key_as_tuple=False,delim='*@#$')
        
    for dic in flatd.values():
        if not is_dict_like(dic):
            continue
        if all([k in list(dic.keys()) for k in leaf_keys]):
            if remove_lkeys:
                vals = [dic.pop(k) for k in leaf_keys]
            else:
                vals = [dic[k] for k in leaf_keys]
            if new_name in dic and not overwrite:
                raise ValueError('{} already in sub-dict'.format(new_name))
            dic[new_name] = func(*vals,**kwargs)
    
    if flatten_dict:
        return unflatten(flatd)
    else:
        return flatd
    
    
def split_lists(d, split_keys, 
                 new_name='split',check_length=True):
    """split_lists key:list pairs into dicts for each item in the lists
    
    Parameters
    ----------
    d : dict
    split_keys : list
        keys to split
    new_name : str
        top level key for split items
    check_length : bool
        if true, raise error if any lists are of a different length
        
    Examples
    --------

    >>> from pprint import pprint

    >>> d = {'path_key':{'x':[1,2],'y':[3,4],'a':1}}
    >>> new_d = split_lists(d,['x','y'])
    >>> pprint(new_d)
    {'path_key': {'a': 1, 'split': [{'x': 1, 'y': 3}, {'x': 2, 'y': 4}]}}
    
    >>> split_lists(d,['x','a'])
    Traceback (most recent call last):
    ...
    ValueError: "a" data at the following path is not a list ('path_key',)

    >>> d2 = {'path_key':{'x':[1,7],'y':[3,4,5]}}
    >>> split_lists(d2,['x','y'])
    Traceback (most recent call last):
    ...
    ValueError: lists at the following path do not have the same size ('path_key',)


    """    
    flattened = flatten2d(d)

    new_d = {}
    for key, value in flattened.items():
        if set(split_keys).issubset(value.keys()):
            #combine_d = {}
            combine_d = []
            sub_d = {}
            length = None
            for subkey, subvalue in value.items(): 
                if subkey in split_keys:
                    if not isinstance(subvalue,list):
                        raise ValueError('"{0}" data at the following path is not a list {1}'.format(subkey,key))

                    if check_length and length is not None:
                        if len(subvalue)!=length:
                            raise ValueError('lists at the following path '
                                             'do not have the same size {0}'.format(key))
                    if length is None:
                        combine_d = [{subkey:v} for v in subvalue]
                    else:
                        for item, val in zip(combine_d,subvalue):
                            item[subkey] = val
                         
                    length = len(subvalue)
                    #new_combine = {k:{subkey:v} for k,v in enumerate(subvalue)}
                    #combine_d = merge([combine_d,new_combine])
                else:
                    sub_d[subkey] = subvalue                
                try:
                    new_d[key] = merge([sub_d,{new_name:combine_d}])
                except ValueError as err:
                    raise ValueError('split data key: '
                                     '{0}, already exists at this level for {1}'.format(new_name,key))            
        else:
            new_d[key] = value
    
    return unflatten(new_d)

def combine_lists(d,keys=None):
    """ combine lists of dicts 
    
    d : dict
    keys : list
        keys to combine (all if None)
    
    Example
    -------
    >>> from pprint import pprint
    >>> d = {'path_key': {'a': 1, 'split': [{'x': 1, 'y': 3}, {'x': 2, 'y': 4}]}}
    >>> pprint(combine_lists(d,['split']))
    {'path_key': {'a': 1, 'split': {'x': [1, 2], 'y': [3, 4]}}}
    
    """
    flattened = flatten(d)
    for key, value in list(flattened.items()): 
        if not keys is None:
            try:
                if not key[-1] in keys:
                    continue
            except:
                continue
        if not isinstance(value,list):
            continue
        if not all([is_dict_like(d) for d in value]):
            continue
        newd = {}
        for subdic in value:
            for subk,subv in subdic.items():
                if subk not in newd:
                    newd[subk] = []
                newd[subk].append(subv)
        flattened[key] = newd
    
    return unflatten(flattened)

def to_json(dct, jfile, overwrite=False, dirlevel=0,
                 sort_keys=True, indent=2, 
                 default_name='root.json',**kwargs):
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
    kwargs : dict
        keywords for json.dump

    Examples
    --------

    >>> from jsonextended.utils import MockPath
    >>> file_obj = MockPath('test.json',is_file=True,exists=False)
    >>> dct = {'a':{'b':1}}
    >>> to_json(dct, file_obj)
    >>> print(file_obj.to_string())
    File("test.json") Contents:
    {
      "a": {
        "b": 1
      }
    }
                 
    >>> from jsonextended.utils import MockPath
    >>> folder_obj = MockPath()
    >>> dct = {'x':{'a':{'b':1},'c':{'d':3}}}
    >>> to_json(dct, folder_obj, dirlevel=0,indent=None)
    >>> print(folder_obj.to_string(file_content=True))
    Folder("root") 
      File("x.json") Contents:
       {"a": {"b": 1}, "c": {"d": 3}}

    >>> folder_obj = MockPath()
    >>> to_json(dct, folder_obj, dirlevel=1,indent=None)
    >>> print(folder_obj.to_string(file_content=True))
    Folder("root") 
      Folder("x") 
        File("a.json") Contents:
         {"b": 1}
        File("c.json") Contents:
         {"d": 3}

                 
    """
    if hasattr(jfile,'write'):
        json.dump(dct, jfile, sort_keys=sort_keys,indent=indent, default=encode)
        return
    
    if isinstance(jfile,basestring):
        path = pathlib.Path(jfile)
    else:
        path = jfile
        
    if not all([hasattr(path,attr) for attr in ['exists','is_dir','is_file','touch','open']]):
        raise ValueError('jfile should be a str or file_like object: {}'.format(jfile))
        
    if path.is_file() and path.exists() and not overwrite:
         raise IOError('jfile already exists and overwrite is set to false: {}'.format(jfile))
    
    if not path.is_dir() and dirlevel <= 0:
        path.touch() # try to create file if doesn't already exist
        with path.open('w') as outfile:
            outfile.write(unicode(json.dumps(
            dct,sort_keys=sort_keys,indent=indent, default=encode, **kwargs)))
            return

    if not path.is_dir():
        path.mkdir()
        dirlevel -= 1
            
    # if one or more values if not a nested dict
    if not all([hasattr(v,'items') for v in dct.values()]):
        newpath = path.joinpath(default_name)
        newpath.touch()
        with newpath.open('w') as outfile:
            outfile.write(unicode(json.dumps(
            dct,sort_keys=sort_keys,indent=indent, default=encode, **kwargs)))
            return     
    
    for key, val in dct.items():
        if dirlevel <= 0:
            newpath = path.joinpath('{}.json'.format(key))
            newpath.touch()
            with newpath.open('w') as outfile:
                outfile.write(unicode(json.dumps(
                val,ensure_ascii=False,sort_keys=sort_keys,indent=indent, default=encode, **kwargs)))   
        else:            
            newpath = path.joinpath('{}'.format(key))
            if not newpath.exists():
                newpath.mkdir()
            to_json(val, newpath, overwrite=overwrite, dirlevel=dirlevel-1,
                             sort_keys=sort_keys, indent=indent, 
                             default_name='{}.json'.format(key),**kwargs)  
    

class to_html(object):
    """
    Pretty display dictionary in collapsible format with indents

    Parameters
    ----------
    obj : str or dict
        dict or json
    depth: int
        Depth of the json tree structure displayed, the rest is collapsed.
    max_length: int
        Maximum number of characters of a string displayed as preview, longer string appear collapsed.
    max_height: int
        Maxium height in pixels of containing box.
    sort: bool
        Whether the json keys are sorted alphabetically.
    local : bool
        use local version of javascript file
    uniqueid : str
        unique identifier (if None, auto-created)

    Examples
    ---------

    >>> dic = {'sape': {'value': 22}, 'jack': 4098, 'guido': 4127}
    >>> obj = to_html(dic, depth=1, max_length=10, sort=False, local=True, uniqueid='123')
    >>> print(obj._repr_html_())
    <style>
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
        </style><div id="123" style="max-height: 600px; width:100%%;"></div>
                    <script>
                require(["jsonextended/renderjson.js"], function() {
                    document.getElementById("123").appendChild(
                        renderjson.set_max_string_length(10)
                                  //.set_icons(circled plus, circled minus)
                                  .set_icons(String.fromCharCode(8853), String.fromCharCode(8854))
                                  .set_sort_objects(false)
                                  .set_show_to_level(1)({"guido": 4127, "jack": 4098, "sape": {"value": 22}}))
                });</script>



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
                 sort=True, local=True, uniqueid=None):
        """
        obj : str or dict
            dict or json
        depth: int
            Depth of the json tree structure displayed, the rest is collapsed.
        max_length: int
            Maximum number of characters of a string displayed as preview, longer string appear collapsed.
        max_height: int
            Maxium height in pixels of containing box.
        sort: bool
            Whether the json keys are sorted alphabetically.

        """

        def is_json(myjson):
            try:
                object = json.loads(myjson)
            except ValueError:
                return False
            return True

        if is_dict_like(obj):
            self.str = json.dumps(obj,default=encode,sort_keys=True)
        elif is_json(obj):
            self.str = obj
        else:
            raise ValueError('Wrong Input, dict or json expected')

        self.uuid = uniqueid if uniqueid is not None else str(uuid.uuid4())
        self.depth = int(depth)
        self.max_length = int(max_length)
        self.max_height = int(max_height)
        self.sort = json.dumps(sort)
        self.local = local


    def _get_html(self):
        return """<div id="{0}" style="max-height: {1}px; width:100%%;"></div>
                """.format(self.uuid, self.max_height)

    def _get_renderpath(self):
        #return os.path.join(os.path.dirname(os.path.dirname(os.path.relpath(inspect.getfile(_example_json_folder)))),
        #                              'renderjson.js')
        renderjson = 'jsonextended/renderjson.js'
        if sys.version_info < (3,0) or self.local:
            return renderjson
        # try online, python 2 doesn't seem to like it
        try:
            renderjson = 'https://rawgit.com/caldwell/renderjson/master/renderjson.js'
            urlopen(renderjson)
        except:
            pass
        return renderjson

    def _get_javascript(self):
        renderjson = self._get_renderpath()
        return """<script>
            require(["{0}"], function() {{
                document.getElementById("{1}").appendChild(
                    renderjson.set_max_string_length({2})
                              //.set_icons(circled plus, circled minus)
                              .set_icons(String.fromCharCode(8853), String.fromCharCode(8854))
                              .set_sort_objects({3})
                              .set_show_to_level({4})({5}))
            }});</script>""".format(renderjson, self.uuid, self.max_length,
                                   self.sort, self.depth, self.str)


    def _repr_html_(self):

        return self._CSS+self._get_html()+self._get_javascript()

    def __ipython_display_(self):

        from IPython.display import display_html, display_javascript
        display_html(self._CSS+self._get_html())
        display_javascript(self._get_javascript())

@total_ordering 
class LazyLoad(object):
    """ lazy load a dict_like object or file structure as a pseudo dictionary
    (works with all edict functions)
    supplies tab completion of keys
    
    Properties
    ----------
    obj : dict, string, file_like
        object 
    ignore_prefix : list of str
        ignore files and folders beginning with these prefixes 
    recursive : bool
        if True, load subdirectories
    parent : obj
         the parent object of this instance
    key_paths : bool
        indicates if the keys of the object can be resolved as file/folder paths
        (to ensure strings do not get unintentionally treated as paths)
    parser_kwargs : keywords or dict 
        additional keywords for parser plugins read_file method
        
    
    Examples
    --------
    
    >>> from jsonextended import plugins
    >>> plugins.load_builtin_plugins()
    []
    
    >>> l = LazyLoad({'a':{'b':2},3:4})
    >>> print(l)
    {3:..,a:..}
    >>> l['a']
    {b:..}
    >>> l[['a','b']]
    2
    >>> l.a.b
    2
    >>> l.i3
    4
    
    >>> from jsonextended.utils import get_test_path
    >>> from jsonextended.edict import pprint
    
    >>> lazydict = LazyLoad(get_test_path())
    >>> pprint(lazydict,depth=2)
    dir1: 
      dir1_1: {...}
      file1.json: {...}
      file2.json: {...}
    dir2: 
      file1.csv: {...}
      file1.json: {...}
    dir3: 
    file1.keypair: 
      key1: val1
      key2: val2
      key3: val3
    
    >>> 'dir1' in lazydict
    True
    
    >>> sorted(lazydict.keys())
    ['dir1', 'dir2', 'dir3', 'file1.keypair']
    
    >>> sorted(lazydict.values())
    [{}, {key1:..,key2:..,key3:..}, {file1.csv:..,file1.json:..}, {dir1_1:..,file1.json:..,file2.json:..}]
    
    >>> lazydict.dir1.file1_json
    {initial:..,meta:..,optimised:..,units:..}
        
    >>> ldict = lazydict.dir1.file1_json.to_dict()
    >>> isinstance(ldict,dict)
    True
    >>> pprint(ldict,depth=1)
    initial: {...}
    meta: {...}
    optimised: {...}
    units: {...}
    
    >>> lazydict = LazyLoad(get_test_path(),recursive=False)
    >>> lazydict
    {file1.keypair:..}
    
    >>> LazyLoad([1,2,3])
    Traceback (most recent call last):
     ...
    ValueError: not an expandable object: [1, 2, 3]

    >>> plugins.unload_all_plugins()    
    
    """
    def __init__(self, obj, 
                 ignore_prefixes=('.','_'), recursive=True,
                 parent=None, key_paths=True,
                 **parser_kwargs): 
        """ initialise
        """
        self._obj = obj
        self._ignore_prefixes = ignore_prefixes
        self._key_paths = key_paths
        self._parser_kwargs = parser_kwargs
        if 'object_hook' not in parser_kwargs:
            self._parser_kwargs['object_hook']=decode
        self._recurse = recursive
        self._itemmap = None
        self._tabmap = None
    
    def _next_level(self, obj):
        """get object for next level of tab """
        if is_dict_like(obj):
            child = LazyLoad(obj, self._ignore_prefixes,parent=self, 
                                  key_paths=False)
            return child
        if is_path_like(obj):
            if not obj.name.startswith(self._ignore_prefixes):
                if parser_available(obj):
                    child = LazyLoad(obj, self._ignore_prefixes,parent=self,
                                          key_paths=False)
                    return child
                elif obj.is_dir():
                    child = LazyLoad(obj, self._ignore_prefixes,parent=self,
                                          key_paths=self._key_paths)
                    return child
                                
        return obj
    
    def _expand(self):
        """ create item map for 
        """
        if self._itemmap is not None:
            return
        
        obj = self._obj
        if is_dict_like(obj):
            self._itemmap = {key:self._next_level(val) for key,val in obj.items()}
        
        elif isinstance(obj, basestring) and self._key_paths:
            obj = pathlib.Path(obj)

        if is_path_like(obj):
            if obj.is_file():
                new_obj = parse(obj,**self._parser_kwargs)
                self._itemmap = {key:self._next_level(val) for key,val in new_obj.items()}
            if obj.is_dir():
                new_obj = {}
                for subpath in obj.iterdir():
                    if not subpath.name.startswith(self._ignore_prefixes):
                        if parser_available(subpath):                            
                            new_obj[subpath.name] = self._next_level(subpath)
                        elif subpath.is_dir() and self._recurse:
                            new_obj[subpath.name] = self._next_level(subpath)
                self._itemmap = new_obj
        
        if self._itemmap is None:
            raise ValueError('not an expandable object: {}'.format(obj))
        self._tabmap = {self._sanitise(key):val for key,val in self._itemmap.items()}
     
    def __dir__(self):
        self._expand()
        return ['keys','items','values','to_dict','to_df','to_obj'] + [name for name in self._tabmap]
    
    def __getattr__(self,attr):
        self._expand()
        if attr in self._tabmap:
            return self._tabmap[attr]
        #return super(LazyLoad,self).__getattr__(attr)
        raise AttributeError(attr)
        
    def __getitem__(self, items):
        if not isinstance(items,list):
            items = [items]
        obj = self
        for item in items:
            if not isinstance(obj, self.__class__):
                raise KeyError('{} (reached leaf node)'.format(item))
            obj._expand()
            obj  = obj._itemmap[item]   
        return obj     
    
    def __contains__(self, item):
        self._expand()
        return item in self._itemmap
                
    def __iter__(self):
        self._expand()
        for key in self._itemmap:
            yield key        
            
    def __repr__(self):
        self._expand()
        end=':..' if len(self._itemmap)>0 else ''
        return '{'+':..,'.join(sorted([str(_) for _ in self._itemmap]))+end+'}'
    def __str__(self):
        return self.__repr__()
    
    def __gt__(self,other):
        if not hasattr(other, '__str__'):
            return NotImplemented
        return len(self.__str__()) > len(other.__str__())
    def __eq__(self,other):
        if not hasattr(other, '__str__'):
            return NotImplemented
        return len(self.__str__()) == len(other.__str__())

    def _sanitise(self,val):
        """sanitise tab names
        attributes aren't allowed to start with a number
        and replace non alphanumeric characters with _
        """
        try:
            int(str(val)[0])
            val = 'i'+str(val)
        except:
            pass
        val = re.sub('[^0-9a-zA-Z]+', '_', str(val))
        val = 'u'+val if val.startswith('_') else val
        val = val+'_key' if val in ['keys','items','values','to_dict','to_df','to_obj'] else val
        return val

    def keys(self):
        """ D.keys() -> iter of D's keys        
        """
        return self.__iter__()
    def values(self):
        """ D.values() -> list of D's values
        """
        self._expand()
        for val in self._itemmap.values():
            yield val        
    def items(self):
        """ D.items() -> list of D's (key, value) pairs, as 2-tuples
        """
        self._expand()
        for key, val in self._itemmap.items():
            yield key, val
    
    def _recurse_children(self, obj, root=None):
        root = {} if root is None else root
        if not hasattr(obj, 'items'):
            return obj
        else:
            return {root[key] if key in root else key: self._recurse_children(value,root) for key, value in obj.items()}
    
    def to_obj(self):
        """ D.to_obj -> the internal object of D """
        return self._obj
    def to_dict(self):
        """ D.to_dict -> D (fully loaded) as nested dict """
        return self._recurse_children(self)
    def to_df(self, **kwargs):
        """ D.to_df -> D as pandas.DataFrame """
        import pandas as pd
        return pd.DataFrame(self._recurse_children(self), **kwargs)
