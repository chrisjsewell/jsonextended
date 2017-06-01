JSON Extended
=============

**Project**: https://github.com/chrisjsewell/jsonextended

.. image:: https://travis-ci.org/chrisjsewell/jsonextended.svg?branch=master
    :target: https://travis-ci.org/chrisjsewell/jsonextended


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
---------

Data Folders JSONisation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    import jsonextended as ejson
    
    path = ejson.get_test_path()
    ejson.json_keys(path)




.. parsed-literal::

    ['dir1', 'dir2', 'dir3']



.. code:: ipython2

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


Nested Dict Manipulation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: ipython2

    jdict2 = ejson.json_to_dict(path,['dir1','file1'])
    ejson.dict_pprint(jdict2,depth=1)


.. parsed-literal::

    initial: {...}
    meta: {...}
    optimised: {...}
    units: {...}


.. code:: ipython2

    filtered = ejson.dict_filter_keys(jdict2,['vol*'],use_wildcards=True)
    ejson.dict_pprint(filtered)


.. parsed-literal::

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


.. code:: ipython2

    ejson.dict_pprint(ejson.dict_flatten(filtered))


.. parsed-literal::

    ('initial', 'crystallographic', 'volume'):   924.62752781
    ('initial', 'primitive', 'volume'):          462.313764
    ('optimised', 'crystallographic', 'volume'): 1063.98960509
    ('optimised', 'primitive', 'volume'):        531.994803


