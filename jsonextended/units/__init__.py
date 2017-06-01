#!/usr/bin/env python
# -- coding: utf-8 --
""" a package to manipulate the physical units of JSON data,
via unitschema

jsonextended utilises the pint package to manage physical units.
This was chosen due to its large user-base and support for numpy:
https://socialcompare.com/en/comparison/python-units-quantities-packages-383avix4

"""

from jsonextended.units.core import (apply_unitschema,
                            split_quantities, combine_quantities)