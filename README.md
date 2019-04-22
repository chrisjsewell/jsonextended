# JSON Extended

[![Build Status](https://travis-ci.org/chrisjsewell/jsonextended.svg?branch=master)](
  https://travis-ci.org/chrisjsewell/jsonextended)
[![Coverage Status](https://coveralls.io/repos/github/chrisjsewell/jsonextended/badge.svg?branch=master)](https://coveralls.io/github/chrisjsewell/jsonextended?branch=master)
[![Documentation Status](https://readthedocs.org/projects/jsonextended/badge/?version=latest)](http://jsonextended.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/jsonextended.svg)](https://pypi.python.org/pypi/jsonextended/)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/jsonextended/badges/version.svg)](https://anaconda.org/conda-forge/jsonextended)
<!-- [![Codacy
Badge](https://api.codacy.com/project/badge/Grade/60ce582812a6431fa20c4074c517288c)](https://www.codacy.com/app/chrisj_sewell/jsonextended?utm_source=github.com&utm_medium=referral&utm_content=chrisjsewell/jsonextended&utm_campaign=Badge_Grade) -->

A module to extend the python json package functionality:

- Treat a directory structure like a nested dictionary:
  - **lightweight plugin system**: define bespoke classes for
    **parsing** different file extensions (in-the-box: .json, .csv, .hdf5)
    and **encoding/decoding** objects
  - **lazy loading**: read files only when they are indexed into
  - **tab completion**: index as tabs for quick exploration of data
- Manipulation of nested dictionaries:
  - enhanced pretty printer
  - Javascript rendered, expandable tree in the Jupyter Notebook
  - functions including; filter, merge, flatten, unflatten, diff
  - output to directory structure (of *n* folder levels)
- On-disk indexing option for large json files (using the ijson package)
- Units schema concept to apply and convert physical units (using the pint package)

**Documentation**: https://jsonextended.readthedocs.io

## Contents

- [JSON Extended](#json-extended)
  - [Contents](#contents)
  - [Installation](#installation)
  - [Basic Example](#basic-example)
  - [Creating and Loading Plugins](#creating-and-loading-plugins)
    - [Interface specifications](#interface-specifications)
  - [Extended Examples](#extended-examples)
    - [Data Folders JSONisation](#data-folders-jsonisation)
    - [Nested Dictionary Manipulation](#nested-dictionary-manipulation)
    - [Units Schema](#units-schema)

## Installation

From Conda (recommended):

    conda install -c conda-forge jsonextended

From PyPi:

    pip install jsonextended

jsonextended has no import dependancies, on Python 3.x and only
`pathlib2` on 2.7 but, for full functionallity, it is advised to install
the following packages:

    conda install -c conda-forge ijson numpy pint h5py pandas

## Basic Example

``` {.python}
from jsonextended import edict, plugins, example_mockpaths
```

Take a directory structure, potentially containing multiple file types:

``` {.python}
datadir = example_mockpaths.directory1
print(datadir.to_string(indentlvl=3,file_content=True))
```

    Folder("dir1")
       File("file1.json") Contents:
        {"key2": {"key3": 4, "key4": 5}, "key1": [1, 2, 3]}
       Folder("subdir1")
         File("file1.csv") Contents:
           # a csv file
          header1,header2,header3
          val1,val2,val3
          val4,val5,val6
          val7,val8,val9
         File("file1.literal.csv") Contents:
           # a csv file with numbers
          header1,header2,header3
          1,1.1,string1
          2,2.2,string2
          3,3.3,string3
       Folder("subdir2")
         Folder("subsubdir21")
           File("file1.keypair") Contents:
             # a key-pair file
            key1 val1
            key2 val2
            key3 val3
            key4 val4

Plugins can be defined for parsing each file type (see [Creating
Plugins](#creating-and-loading-plugins) section):

``` {.python}
plugins.load_builtin_plugins('parsers')
plugins.view_plugins('parsers')
```

    {'csv.basic': 'read *.csv delimited file with headers to {header:[column_values]}',
     'csv.literal': 'read *.literal.csv delimited files with headers to {header:column_values}, with number strings converted to int/float',
     'hdf5.read': 'read *.hdf5 (in read mode) files using h5py',
     'json.basic': 'read *.json files using json.load',
     'keypair': "read *.keypair, where each line should be; '<key> <pair>'"}

LazyLoad then takes a path name, path-like object or dict-like object,
which will lazily load each file with a compatible plugin.

``` {.python}
lazy = edict.LazyLoad(datadir)
lazy
```

    {file1.json:..,subdir1:..,subdir2:..}

Lazyload can then be treated like a dictionary, or indexed by tab
completion:

``` {.python}
list(lazy.keys())
```

    ['subdir1', 'subdir2', 'file1.json']

``` {.python}
lazy[['file1.json','key1']]
```

    [1, 2, 3]

``` {.python}
lazy.subdir1.file1_literal_csv.header2
```

    [1.1, 2.2, 3.3]

For pretty printing of the dictionary:

``` {.python}
edict.pprint(lazy,depth=2)
```

    file1.json:
      key1: [1, 2, 3]
      key2: {...}
    subdir1:
      file1.csv: {...}
      file1.literal.csv: {...}
    subdir2:
      subsubdir21: {...}

Numerous functions exist to manipulate the nested dictionary:

``` {.python}
edict.flatten(lazy.subdir1)
```

    {('file1.csv', 'header1'): ['val1', 'val4', 'val7'],
     ('file1.csv', 'header2'): ['val2', 'val5', 'val8'],
     ('file1.csv', 'header3'): ['val3', 'val6', 'val9'],
     ('file1.literal.csv', 'header1'): [1, 2, 3],
     ('file1.literal.csv', 'header2'): [1.1, 2.2, 3.3],
     ('file1.literal.csv', 'header3'): ['string1', 'string2', 'string3']}

LazyLoad parses the `plugins.decode` function to parser plugin's
`read_file` method (keyword 'object\_hook'). Therefore, bespoke decoder
plugins can be set up for specific dictionary key signatures:

``` {.python}
print(example_mockpaths.jsonfile2.to_string())
```

    File("file2.json") Contents:
    {"key1":{"_python_set_": [1, 2, 3]},"key2":{"_numpy_ndarray_": {"dtype": "int64", "value": [1, 2, 3]}}}

``` {.python}
edict.LazyLoad(example_mockpaths.jsonfile2).to_dict()
```

    {u'key1': {u'_python_set_': [1, 2, 3]},
     u'key2': {u'_numpy_ndarray_': {u'dtype': u'int64', u'value': [1, 2, 3]}}}

``` {.python}
plugins.load_builtin_plugins('decoders')
plugins.view_plugins('decoders')
```

    {'decimal.Decimal': 'encode/decode Decimal type',
     'numpy.ndarray': 'encode/decode numpy.ndarray',
     'pint.Quantity': 'encode/decode pint.Quantity object',
     'python.set': 'decode/encode python set'}

``` {.python}
dct = edict.LazyLoad(example_mockpaths.jsonfile2).to_dict()
dct
```

    {u'key1': {1, 2, 3}, u'key2': array([1, 2, 3])}

This process can be reversed, using encoder plugins:

``` {.python}
plugins.load_builtin_plugins('encoders')
plugins.view_plugins('encoders')
```

    {'decimal.Decimal': 'encode/decode Decimal type',
     'numpy.ndarray': 'encode/decode numpy.ndarray',
     'pint.Quantity': 'encode/decode pint.Quantity object',
     'python.set': 'decode/encode python set'}

``` {.python}
import json
json.dumps(dct,default=plugins.encode)
```

    '{"key2": {"_numpy_ndarray_": {"dtype": "int64", "value": [1, 2, 3]}}, "key1": {"_python_set_": [1, 2, 3]}}'

## Creating and Loading Plugins

``` {.python}
from jsonextended import plugins, utils
```

Plugins are recognised as classes with a minimal set of attributes
matching the plugin category interface:

``` {.python}
plugins.view_interfaces()
```

    {'decoders': ['plugin_name', 'plugin_descript', 'dict_signature'],
     'encoders': ['plugin_name', 'plugin_descript', 'objclass'],
     'parsers': ['plugin_name', 'plugin_descript', 'file_regex', 'read_file']}

``` {.python}
plugins.unload_all_plugins()
plugins.view_plugins()
```

    {'decoders': {}, 'encoders': {}, 'parsers': {}}

For example, a simple parser plugin would be:

``` {.python}
class ParserPlugin(object):
    plugin_name = 'example'
    plugin_descript = 'a parser for *.example files, that outputs (line_number:line)'
    file_regex = '*.example'
    def read_file(self, file_obj, **kwargs):
        out_dict = {}
        for i, line in enumerate(file_obj):
            out_dict[i] = line.strip()
        return out_dict
```

Plugins can be loaded as a class:

``` {.python}
plugins.load_plugin_classes([ParserPlugin],'parsers')
plugins.view_plugins()
```

    {'decoders': {},
     'encoders': {},
     'parsers': {'example': 'a parser for *.example files, that outputs (line_number:line)'}}

Or by directory (loading all .py files):

``` {.python}
fobj = utils.MockPath('example.py',is_file=True,content="""
class ParserPlugin(object):
    plugin_name = 'example.other'
    plugin_descript = 'a parser for *.example.other files, that outputs (line_number:line)'
    file_regex = '*.example.other'
    def read_file(self, file_obj, **kwargs):
        out_dict = {}
        for i, line in enumerate(file_obj):
            out_dict[i] = line.strip()
        return out_dict
""")
dobj = utils.MockPath(structure=[fobj])
plugins.load_plugins_dir(dobj,'parsers')
plugins.view_plugins()
```

    {'decoders': {},
     'encoders': {},
     'parsers': {'example': 'a parser for *.example files, that outputs (line_number:line)',
      'example.other': 'a parser for *.example.other files, that outputs (line_number:line)'}}

For a more complex example of a parser, see
`jsonextended.complex_parsers`

### Interface specifications

- Parsers:
  - *file\_regex* attribute, a str denoting what files to apply it
    to. A file will be parsed by the longest regex it matches.
  - *read\_file* method, which takes an (open) file object and
    kwargs as parameters
- Decoders:
  - *dict\_signature* attribute, a tuple denoting the keys which the
    dictionary must have, e.g. dict\_signature=('a','b') decodes `{'a':1,'b':2}`
  - *from\_...* method(s), which takes a dict object as parameter.
    The `plugins.decode` function will use the method denoted by the
    intype parameter, e.g. if intype='json', then `from_json` will
    be called.
- Encoders:
  - *objclass* attribute, the object class to apply the encoding to,
    e.g. objclass=decimal.Decimal encodes objects of that type
  - *to\_...* method(s), which takes a dict object as parameter. The
    `plugins.encode` function will use the method denoted by the
    outtype parameter, e.g. if outtype='json', then `to_json` will be called.

## Extended Examples

For more information, all functions contain doc-strings with tested
examples.

### Data Folders JSONisation

``` {.python}
from jsonextended import ejson, edict, utils
```

``` {.python}
path = utils.get_test_path()
ejson.jkeys(path)
```

    ['dir1', 'dir2', 'dir3']

``` {.python}
jdict1 = ejson.to_dict(path)
edict.pprint(jdict1,depth=2)
```

    dir1:
      dir1_1: {...}
      file1: {...}
      file2: {...}
    dir2:
      file1: {...}
    dir3:

``` {.python}
edict.to_html(jdict1,depth=2)
```

To try the rendered JSON tree, output in the Jupyter Notebook, go to :
<https://chrisjsewell.github.io/>

### Nested Dictionary Manipulation

``` {.python}
jdict2 = ejson.to_dict(path,['dir1','file1'])
edict.pprint(jdict2,depth=1)
```

    initial: {...}
    meta: {...}
    optimised: {...}
    units: {...}

``` {.python}
filtered = edict.filter_keys(jdict2,['vol*'],use_wildcards=True)
edict.pprint(filtered)
```

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

``` {.python}
edict.pprint(edict.flatten(filtered))
```

    (initial, crystallographic, volume):   924.62752781
    (initial, primitive, volume):          462.313764
    (optimised, crystallographic, volume): 1063.98960509
    (optimised, primitive, volume):        531.994803

### Units Schema

``` {.python}
from jsonextended.units import apply_unitschema, split_quantities
withunits = apply_unitschema(filtered,{'volume':'angstrom^3'})
edict.pprint(withunits)
```

    initial:
      crystallographic:
        volume: 924.62752781 angstrom ** 3
      primitive:
        volume: 462.313764 angstrom ** 3
    optimised:
      crystallographic:
        volume: 1063.98960509 angstrom ** 3
      primitive:
        volume: 531.994803 angstrom ** 3

``` {.python}
newunits = apply_unitschema(withunits,{'volume':'nm^3'})
edict.pprint(newunits)
```

    initial:
      crystallographic:
        volume: 0.92462752781 nanometer ** 3
      primitive:
        volume: 0.462313764 nanometer ** 3
    optimised:
      crystallographic:
        volume: 1.06398960509 nanometer ** 3
      primitive:
        volume: 0.531994803 nanometer ** 3

``` {.python}
edict.pprint(split_quantities(newunits),depth=4)
```

    initial:
      crystallographic:
        volume:
          magnitude: 0.92462752781
          units:     nanometer ** 3
      primitive:
        volume:
          magnitude: 0.462313764
          units:     nanometer ** 3
    optimised:
      crystallographic:
        volume:
          magnitude: 1.06398960509
          units:     nanometer ** 3
      primitive:
        volume:
          magnitude: 0.531994803
          units:     nanometer ** 3
