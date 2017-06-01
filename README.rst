=============
JSON Extended
=============

**Project**: https://github.com/chrisjsewell/jsonextended

.. image:: https://travis-ci.org/chrisjsewell/jsonextended.svg?branch=master
    :target: https://travis-ci.org/chrisjsewell/jsonextended
	.. image:: https://coveralls.io/repos/github/chrisjsewell/jsonextended/badge.svg?branch=master
:target: https://coveralls.io/github/chrisjsewell/jsonextended?branch=master



A python module to extend the json package; treating path structures,
with nested directories and multiple .json files, as a single json.

It provides:

-  Functions for decoding/encoding between the on-disk JSON structure
   and in-memory nested dictionary structure, including

   -  on-disk indexing of the json structure (using the ijson package)

   -  extended data type serialisation (numpy.ndarray, Decimals,
      pint.Quantities)

-  Functions for viewing and manipulating the nested dictionaries

   -  including Javascript rendered, expandable tree in the Jupyter Notebook

-  Units schema concept to apply and convert physical units (using the
   pint package)

-  Parser abstract class for dealing with converting other file formats
   to JSON

Examples
********

Data Folders JSONisation
------------------------

.. code:: python

    import jsonextended as ejson
    
    path = ejson.get_test_path()
    ejson.json_keys(path)


.. parsed-literal::

    ['dir1', 'dir2', 'dir3']


.. code:: python

    jdict1 = ejson.json_to_dict(path)
    ejson.dict_pprint(jdict1,depth=2)

.. parsed-literal::

    dir1: 
      dir1_1: {...}
      file1: {...}
      file2: {...}
    dir2: 
      file1: {...}
    dir3: 
