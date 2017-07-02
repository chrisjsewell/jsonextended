#!/usr/bin/env python
""" a module to manipulate python dictionary like objects

"""
# internal packages
import sys
import copy
import uuid
import json
from fnmatch import fnmatch
import textwrap
from functools import reduce

# python 3 to 2 compatibility
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
try:
    basestring
except NameError:
    basestring = str

# local imports
from jsonextended.utils import natural_sort
from jsonextended.plugins import encode

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

def _default_print_func(s):
    print(s)

def pprint(d, lvlindent=2, initindent=0, delim=':',
                max_width=80, depth=3, no_values=False,
                align_vals=True, print_func=None):
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
    print_func : func or None
        function to print strings (print if None)

    Examples
    --------

    >>> d = {'a':{'b':{'c':[1,2],'de':[4,5,6,7,8,9]}}}
    >>> pprint(d,depth=None)
    a: 
      b: 
        c:  [1, 2]
        de: [4, 5, 6, 7, 8, 9]
    >>> pprint(d,max_width=17,depth=None)
    a: 
      b: 
        c:  [1, 2]
        de: [4, 5, 6, 
            7, 8, 9]
    >>> pprint(d,no_values=True,depth=None)
    a: 
      b: 
        c:  
        de: 
    >>> pprint(d,depth=2)
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
                pprint(value, lvlindent, initindent+lvlindent,delim,
                            max_width,depth=max_depth-1 if not max_depth is None else None,
                            no_values=no_values,align_vals=align_vals,print_func=print_func)
        else:
            val_string = value
            try:
                val_string = encode(value, as_str=True)
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
        if isinstance(value, dict):
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

def filter_keys(d, keys, use_wildcards=False):
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
    >>> pprint(filter_keys(d,['a',6]))
    {1: {'a': 'A'}, 4: {5: {6: 'a'}}}

    >>> d = {1:{"axxxx":"A"},2:{"b":"B"}}
    >>> pprint(filter_keys(d,['a*'],use_wildcards=True))
    {1: {'axxxx': 'A'}}

    """
    if isinstance(d, dict):
        retVal = {}
        for key in d:
            if use_wildcards and isinstance(key, basestring):
                if any([fnmatch(key,k) for k in keys]):
                    retVal[key] = copy.deepcopy(d[key])
                elif isinstance(d[key], list) or isinstance(d[key], dict):
                    child = filter_keys(d[key], keys, use_wildcards)
                    if child:
                        retVal[key] = child
            elif key in keys:
                retVal[key] = copy.deepcopy(d[key])
            elif isinstance(d[key], list) or isinstance(d[key], dict):
                child = filter_keys(d[key], keys, use_wildcards)
                if child:
                    retVal[key] = child
        if retVal:
             return retVal
        else:
             return {}
    elif isinstance(d, list):
        retVal = []
        for entry in d:
            child = filter_keys(entry, keys, use_wildcards)
            if child:
                retVal.append(child)
        if retVal:
            return retVal
        else:
            return []

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

def combine_lists(d, combine, 
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
    >>> new_d = combine_lists(d,['x','y'])
    >>> pprint(new_d)
    {'path_key': {'a': 1,
                  'combined': {'1': {'x': 1, 'y': 3}, '2': {'x': 2, 'y': 4}}}}
    
    >>> combine_lists(d,['x','a'])
    Traceback (most recent call last):
    ...
    ValueError: "a" data at the following path is not a list ('path_key',)

    >>> d2 = {'path_key':{'x':[1,7],'y':[3,4,5]}}
    >>> combine_lists(d2,['x','y'])
    Traceback (most recent call last):
    ...
    ValueError: lists at the following path do not have the same size ('path_key',)


    """    
    flattened = flatten2d(d)

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
                    combine_d = merge([combine_d,new_combine])
                else:
                    sub_d[subkey] = subvalue
                try:
                    new_d[key] = merge([sub_d,{combine_key:combine_d}])
                except ValueError as err:
                    raise ValueError('combined data key: '
                                     '{0}, already exists at this level for {1}'.format(combine_key,key))
        else:
            new_d[key] = value
    
    return unflatten(new_d)

def to_json(d, jfile, overwrite=False, dirlevel=1,
                 sort_keys=True, indent=2, **kwargs):
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


    >>> obj = StringIO()
    >>> d = {'a':{'b':1}}
    >>> to_json(d, obj)
    >>> print(obj.getvalue())
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
                      sort_keys=sort_keys,indent=indent, default=encode)
    elif not hasattr(jfile,'write'):
        raise ValueError('jfile should be a str or file_like object: {}'.format(jfile))
    else:
        json.dump(d, jfile,
                  sort_keys=sort_keys,indent=indent, default=encode)

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

        if isinstance(obj, dict):
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
