#!/usr/bin/env python
# -- coding: utf-8 --
""" a module to extend the python json package functionality;

-  decoding/encoding between the on-disk JSON structure
   and in-memory nested dictionary structure, including:

   -  treating path structures, with nested directories and multiple .json files, as a single json.

   -  on-disk indexing of the json structure (using the ijson package)

   -  extended data type serialisation (numpy.ndarray, Decimals,
      pint.Quantities,...)

-  viewing and manipulating the nested dictionaries:

   -  enhanced pretty printer
   
   -  Javascript rendered, expandable tree in the Jupyter Notebook
   
   -  filter, merge, flatten, unflatten functions

-  Units schema concept to apply and convert physical units (using the
   pint package)

-  Parser abstract class for dealing with converting other file formats
   to JSON

Notes
-----

On-disk indexing of the json structure, before reading into memory,
to reduce memory overhead when dealing with large json structures/files (using the ijson package).
e.g.
    path = get_test_path()
    %memit jdict1 = json_to_dict(path,['dir1','file2','meta'],in_memory=True)
    maximum of 3: 12.242188 MB per loop

    %memit jdict1 = json_to_dict(path,['dir1','file2','meta'],in_memory=False)
    maximum of 3: 6.996094 MB per loop


Examples
--------

>>> import jsonextended as ejson

>>> path = ejson.get_test_path()
>>> path.is_dir()
True

>>> json_keys(path)
['dir1', 'dir2', 'dir3']

>>> jdict1 = ejson.json_to_dict(path)
>>> ejson.dict_pprint(jdict1,depth=2)
dir1: 
  dir1_1: {...}
  file1: {...}
  file2: {...}
dir2: 
  file1: {...}
dir3: 


>>> jdict2 = ejson.json_to_dict(path,['dir1','file1'])
>>> ejson.dict_pprint(jdict2,depth=1)
initial: {...}
meta: {...}
optimised: {...}
units: {...}

>>> filtered = ejson.dict_filter_keys(jdict2,['vol*'],use_wildcards=True)
>>> ejson.dict_pprint(filtered)
initial: 
  crystallographic: 
    volume: 924.62752781
  primitive: 
    volume: 462.313764
optimised: 
  crystallographic: 
    volume: 1063.98960509
  primitive: 
    volume: 531.994803

>>> ejson.dict_pprint(ejson.dict_flatten(filtered))
('initial', 'crystallographic', 'volume'):   924.62752781
('initial', 'primitive', 'volume'):          462.313764
('optimised', 'crystallographic', 'volume'): 1063.98960509
('optimised', 'primitive', 'volume'):        531.994803

"""

__version__ = '0.1.3.4'

from jsonextended.core import (get_test_path,json_keys,json_to_dict, dict_to_json,
                            dict_pprint,dict_extract,dict_multiindex, dict_rename_keys,
                            dict_flatten,dict_unflatten,dict_flatten2d,dict_flattennd,
                            dicts_merge, dict_remove_keys,dict_remove_paths,
                            dict_filter_values,dict_filter_keys,dict_filter_paths,
                            DictTree,dict_to_html)

from jsonextended import parsers, units, utils

def _run_nose_tests(doctests=True, verbose=True):
    """ 
    mimics nosetests --with-doctest -v --exe jsonextended 
    also use:
    pylint --output-format html jsonextended > jsonextended_pylint.html
    """
    import os, sys, jsonextended, nose
    nose_argv = sys.argv
    nose_argv += ['--detailed-errors', '--exe']
    if verbose:
        nose_argv.append('-v')
    if doctests:
        nose_argv.append('--with-doctest')
    nose_argv.append('jsonextended')
    initial_dir = os.getcwd()
    my_package_file = os.path.abspath(jsonextended.__file__)
    print(my_package_file)
    my_package_dir = os.path.dirname(os.path.dirname(my_package_file))
    print(my_package_dir)
    os.chdir(my_package_dir)
    try:
        nose.run(argv=nose_argv)
    finally:
        os.chdir(initial_dir)

