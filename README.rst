=============
JSON Extended
=============

**Project**: https://github.com/chrisjsewell/jsonextended

.. image:: https://travis-ci.org/chrisjsewell/jsonextended.svg?branch=master
    :target: https://travis-ci.org/chrisjsewell/jsonextended


A module to extend the python json package functionality: 

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

Installation
------------

.. parsed-literal::

    pip install jsonextended

jsonextended has no import dependancies, on Python 3.x and only `pathlib2` on 2.7 but,
for full functionallity, it is advised to install the following packages:

.. parsed-literal::

    conda install -c conda-forge ijson numpy pandas pint 

Examples
---------

For more information, all functions contain docstrings with tested examples.


Data Folders JSONisation
~~~~~~~~~~~~~~~~~~~~~~~~

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

.. code:: python

     ejson.dict_to_html(jdict1,depth=3)


To try the rendered JSON tree, output in the Jupyter Notebook, go to : https://chrisjsewell.github.io/


Nested Dictionary Manipulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    jdict2 = ejson.json_to_dict(path,['dir1','file1'])
    ejson.dict_pprint(jdict2,depth=1)


.. parsed-literal::

    initial: {...}
    meta: {...}
    optimised: {...}
    units: {...}


.. code:: python

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


.. code:: python

    ejson.dict_pprint(ejson.dict_flatten(filtered))


.. parsed-literal::

    ('initial', 'crystallographic', 'volume'):   924.62752781
    ('initial', 'primitive', 'volume'):          462.313764
    ('optimised', 'crystallographic', 'volume'): 1063.98960509
    ('optimised', 'primitive', 'volume'):        531.994803


Units Schema
~~~~~~~~~~~~

Unit schema builds on the concept of standard jsonschema, whereby one JSON can be used to validate another.

In this case one JSON, containing physical units for a given key path, is applied to a data JSON.

.. code:: python

    from jsonextended.units import apply_unitschema, split_quantities
    withunits = apply_unitschema(filtered,{'volume':'angstrom^3'})
    ejson.dict_pprint(withunits)


.. parsed-literal::

    initial: 
      crystallographic: 
        volume: 924.62752781 Å ** 3
      primitive: 
        volume: 462.313764 Å ** 3
    optimised: 
      crystallographic: 
        volume: 1063.98960509 Å ** 3
      primitive: 
        volume: 531.994803 Å ** 3


.. code:: python

    newunits = apply_unitschema(withunits,{'volume':'nm^3'})
    ejson.dict_pprint(newunits)


.. parsed-literal::

    initial: 
      crystallographic: 
        volume: 0.92462752781 nm ** 3
      primitive: 
        volume: 0.462313764 nm ** 3
    optimised: 
      crystallographic: 
        volume: 1.06398960509 nm ** 3
      primitive: 
        volume: 0.531994803 nm ** 3


.. code:: python

    ejson.dict_pprint(split_quantities(newunits),depth=4)


.. parsed-literal::

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




