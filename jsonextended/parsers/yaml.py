#!/usr/bin/env python

from ruamel.yaml import YAML


class YAML_Parser(object):
    r"""

    Examples
    --------

    >>> from pprint import pprint
    >>> from jsonextended.utils import MockPath
    >>> fileobj = MockPath(is_file=True,
    ... content='key1:\n  subkey1: a\n  subkey2: [1,2,3]'
    ... )
    >>> with fileobj.open() as f:
    ...     data = YAML_Parser().read_file(f)
    >>> pprint(dict(data["key1"]))
    {'subkey1': 'a', 'subkey2': [1, 2, 3]}

    """

    plugin_name = 'yaml.ruamel'
    plugin_descript = 'read *.yaml files using ruamel.yaml'
    file_regex = '*.yaml'

    def read_file(self, file_obj, **kwargs):
        return YAML().load(file_obj)
