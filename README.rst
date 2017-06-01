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

