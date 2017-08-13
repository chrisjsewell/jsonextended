#!/usr/bin/env python
import json


class NBParser(object):
    """
    Examples
    --------
    >>> from jsonextended.utils import MockPath
    >>> from jsonextended.edict import pprint
    >>> fileobj = MockPath(is_file=True,
    ... content='''{
    ... "cells":[],
    ... "metadata":{}
    ... }'''
    ... )
    >>> with fileobj.open() as f:
    ...     data = NBParser().read_file(f)
    >>> pprint(data)
    cells: []
    metadata:

    """

    plugin_name = 'ipynb'
    plugin_descript = 'read Jupyter Notebooks'
    file_regex = '*.ipynb'

    def read_file(self, file_obj, **kwargs):
        return json.load(file_obj)
