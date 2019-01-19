#!/usr/bin/env python
# -- coding: utf-8 --

## TODO see below
# output json with arrays all on one line
#      doesn't seem an easy way
#      could use this: https://stackoverflow.com/a/13252112, but wrap lists with NoIndent first
#      would need to go through first and wrap values that are list instances with NoIndent first


# internal packages
import json
import os
from decimal import Decimal

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
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

# external packages
import warnings

warnings.simplefilter('once', ImportWarning)
try:
    import ijson
except ImportError:
    pass

# local imports
from jsonextended.edict import indexes, pprint, convert_type
from jsonextended.plugins import decode


def _get_keys(file_obj, key_path=None):
    key_path = [] if key_path is None else key_path
    data = json.load(file_obj, object_hook=decode)
    data = indexes(data, key_path)
    if hasattr(data, 'keys'):
        return sorted([str(k) if isinstance(k, basestring) else k for k in data.keys()])
    else:
        return []


def _get_keys_ijson(file_obj, key_path=None):
    key_path = [] if key_path is None else key_path
    try:
        path_str = '.'.join(key_path)
        keys = []
        for prefix, etype, value in ijson.parse(file_obj):
            if etype == 'map_key':
                if prefix == path_str:
                    keys.append(value)
        return sorted([str(k) if isinstance(k, basestring) else k for k in keys])
    except NameError:
        warnings.warn('ijson package not found in environment, \
please install for on-disk key indexing', ImportWarning)
        return _get_keys(file_obj, key_path)


def _get_keys_folder(jdir, key_path=None, in_memory=True, ignore_prefix=('.', '_')):
    """ get json keys from directory structure

    e.g.

    jdir
        sub_dir1
            data1.json
            data2.json
        sub_dir2
            data.json

    _get_keys_folder(jdir)
    => ['sub_dir1', 'sub_dir2']
    _get_keys_folder(jdir,['sub_dir1'])
    => ['data1', 'data2']

    NB: json files are identified with .json extension
        files/directories beginning with '.' are ignored

    """
    if not hasattr(jdir, 'iterdir'):
        raise ValueError('jdir is not a path object; {}'.format(jdir))

    key_path = [] if key_path is None else key_path

    keys = []

    key_found = False if key_path else True
    search_key = key_path[0] if len(key_path) > 0 else None

    for jsub in jdir.iterdir():
        if jsub.is_file() and jsub.name[-5:] == '.json':

            name, ext = os.path.splitext(jsub.name)
            if name == search_key or not key_path:
                key_found = True
                if key_path:
                    return jkeys(jsub, key_path[1:], in_memory, ignore_prefix)
                else:
                    keys.append(name)

        elif jsub.is_dir() and not jsub.name.startswith(ignore_prefix) and (jsub.name == search_key or not key_path):

            key_found = True
            if jsub.name in keys:
                raise IOError(
                    'directory has a sub-dir and file with same name: {1} and {1}.json in {0}'.format(jdir, jsub.name))
            if key_path:
                return jkeys(jsub, key_path[1:], in_memory, ignore_prefix)
            else:
                keys.append(jsub.name)

    if not key_found:
        raise KeyError('key not found: {0}'.format(search_key))

    return sorted(keys)


def jkeys(jfile, key_path=None, in_memory=True, ignore_prefix=('.', '_')):
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

    >>> from jsonextended.utils import MockPath
    >>> file_obj = MockPath('test.json',is_file=True,
    ... content='''
    ... {
    ...  "a": 1,
    ...  "b": [1.1,2.1],
    ...  "c": {"d":"e","f":"g"}
    ... }
    ... ''')
    ...
    >>> jkeys(file_obj)
    ['a', 'b', 'c']

    >>> jkeys(file_obj,["c"])
    ['d', 'f']

    >>> from jsonextended.utils import get_test_path
    >>> path = get_test_path()
    >>> jkeys(path)
    ['dir1', 'dir2', 'dir3']

    >>> path = get_test_path()
    >>> jkeys(path, ['dir1','file1'], in_memory=True)
    ['initial', 'meta', 'optimised', 'units']

    """
    key_path = [] if key_path is None else key_path

    def eval_file(file_obj):
        if not in_memory:
            return _get_keys_ijson(file_obj, key_path)
        else:
            return _get_keys(file_obj, key_path)

    if isinstance(jfile, basestring):
        if not os.path.exists(jfile):
            raise IOError('jfile does not exist: {}'.format(jfile))
        if os.path.isdir(jfile):
            jpath = pathlib.Path(jfile)
            return _get_keys_folder(jpath, key_path, in_memory, ignore_prefix)
        else:
            with open(jfile, 'r') as file_obj:
                return eval_file(file_obj)
    elif hasattr(jfile, 'read'):
        return eval_file(jfile)
    elif hasattr(jfile, 'iterdir'):
        if jfile.is_file():
            with jfile.open('r') as file_obj:
                return eval_file(file_obj)
        else:
            return _get_keys_folder(jfile, key_path, in_memory, ignore_prefix)
    else:
        raise ValueError('jfile should be a str, file_like or path_like object: {}'.format(jfile))


def _file_with_keys(file_obj, key_path=None, parse_decimal=False):
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
        objs = ijson.items(file_obj, '.'.join(key_path))
    except NameError:
        warnings.warn('ijson package not found in environment, \
        please install for on-disk key indexing', ImportWarning)
        data = json.load(file_obj, parse_float=Decimal if parse_decimal else float, object_hook=decode)
        return indexes(data, key_path)
    try:
        data = next(objs)  # .next()
    except StopIteration:
        raise KeyError('key path not available in json: {}'.format(key_path))

    # by default ijson parses Decimal values
    if not parse_decimal:
        convert_type(data, Decimal, float, in_place=True)

    datastr = json.dumps(data)
    data = json.loads(datastr, object_hook=decode)

    return data


# TODO this is a hack to get _folder_to_json to work if last key_path is at a leaf node, should improve
class _Terminus(object):
    def __hash__(self):
        return 1

    def __eq__(self, other):
        return True


def _folder_to_json(jdir, key_path=None, in_memory=True,
                    ignore_prefix=('.', '_'), dic={}, parse_decimal=False):
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

    if not hasattr(jdir, 'iterdir'):
        raise ValueError('jdir is not a path object; {}'.format(jdir))

    key_found = False if key_path else True
    search_key = key_path[0] if len(key_path) > 0 else None

    for jsub in jdir.iterdir():
        if jsub.is_file() and jsub.name.endswith('.json'):

            name, ext = os.path.splitext(jsub.name)
            if name == search_key or not key_path:
                key_found = True
                if key_path:
                    data = to_dict(jsub, key_path[1:], in_memory, ignore_prefix, parse_decimal)
                    if isinstance(data, dict):
                        dic.update(data)
                    else:
                        dic.update({_Terminus(): data})
                else:
                    dic[name] = to_dict(jsub, key_path[1:], in_memory, ignore_prefix, parse_decimal)

        elif jsub.is_dir() and not jsub.name.startswith(ignore_prefix) and (jsub.name == search_key or not key_path):

            key_found = True
            if jsub.name in dic.keys():
                raise IOError(
                    'directory has a sub-dir and file with same name: {1} and {1}.json in {0}'.format(jdir, jsub.name))
            if key_path:
                sub_d = dic
            else:
                dic[jsub.name] = {}
                sub_d = dic[jsub.name]
            _folder_to_json(jsub, key_path[1:], in_memory, ignore_prefix, sub_d, parse_decimal)

    if not key_found:
        raise KeyError('key not found: {0}'.format(search_key))


def to_dict(jfile, key_path=None, in_memory=True,
            ignore_prefix=('.', '_'), parse_decimal=False):
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

    >>> from jsonextended.utils import MockPath
    >>> file_obj = MockPath('test.json',is_file=True,
    ... content='''
    ... {
    ...  "a": 1,
    ...  "b": [1.1,2.1],
    ...  "c": {"d":"e"}
    ... }
    ... ''')
    ...

    >>> dstr = pformat(to_dict(file_obj))
    >>> print(dstr.replace("u'","'"))
    {'a': 1, 'b': [1.1, 2.1], 'c': {'d': 'e'}}

    >>> dstr = pformat(to_dict(file_obj,parse_decimal=True))
    >>> print(dstr.replace("u'","'"))
    {'a': 1, 'b': [Decimal('1.1'), Decimal('2.1')], 'c': {'d': 'e'}}

    >>> str(to_dict(file_obj,["c","d"]))
    'e'

    >>> from jsonextended.utils import get_test_path
    >>> path = get_test_path()
    >>> jdict1 = to_dict(path)
    >>> pprint(jdict1,depth=2)
    dir1:
      dir1_1: {...}
      file1: {...}
      file2: {...}
    dir2:
      file1: {...}
    dir3:

    >>> jdict2 = to_dict(path,['dir1','file1','initial'],in_memory=False)
    >>> pprint(jdict2,depth=1)
    crystallographic: {...}
    primitive: {...}

    """
    key_path = [] if key_path is None else key_path

    if isinstance(jfile, basestring):
        if not os.path.exists(jfile):
            raise IOError('jfile does not exist: {}'.format(jfile))
        if os.path.isdir(jfile):
            data = {}
            jpath = pathlib.Path(jfile)
            _folder_to_json(jpath, key_path[:], in_memory, ignore_prefix, data, parse_decimal)
            if isinstance(list(data.keys())[0], _Terminus):
                data = data.values()[0]
        else:
            with open(jfile, 'r') as file_obj:
                if key_path and not in_memory:
                    data = _file_with_keys(file_obj, key_path, parse_decimal)
                elif key_path:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float, object_hook=decode)
                    data = indexes(data, key_path)
                else:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float, object_hook=decode)
    elif hasattr(jfile, 'read'):
        if key_path and not in_memory:
            data = _file_with_keys(jfile, key_path, parse_decimal)
        elif key_path:
            data = json.load(jfile, parse_float=Decimal if parse_decimal else float, object_hook=decode)
            data = indexes(data, key_path)
        else:
            data = json.load(jfile, parse_float=Decimal if parse_decimal else float, object_hook=decode)
    elif hasattr(jfile, 'iterdir'):
        if jfile.is_file():
            with jfile.open() as file_obj:
                if key_path and not in_memory:
                    data = _file_with_keys(file_obj, key_path, parse_decimal)
                elif key_path:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float, object_hook=decode)
                    data = indexes(data, key_path)
                else:
                    data = json.load(file_obj, parse_float=Decimal if parse_decimal else float, object_hook=decode)
        else:
            data = {}
            _folder_to_json(jfile, key_path[:], in_memory, ignore_prefix, data, parse_decimal)
            if isinstance(list(data.keys())[0], _Terminus):
                data = data.values()[0]
    else:
        raise ValueError('jfile should be a str, file_like or path_like object: {}'.format(jfile))

    return data
