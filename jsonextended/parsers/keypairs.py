#!/usr/bin/env python

class KeyPair_Parser(object):
    """
    Examples
    --------

    >>> from pprint import pprint
    >>> from jsonextended.utils import MockPath
    >>> fileobj = MockPath(is_file=True,
    ... content='''# comment line
    ... key1 val1
    ... key2 val2
    ... key3 val3'''
    ... )
    >>> with fileobj.open() as f:
    ...     data = KeyPair_Parser().read_file(f)
    >>> pprint(data)
    {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'}

    """

    plugin_name = 'keypair'
    plugin_descript = "read *.keypair, where each line should be; '<key> <pair>'"
    file_regex = '*.keypair'

    def read_file(self, file_obj, **kwargs):

        comments = kwargs.get('comments', '#')
        delim = kwargs.get('keypair_delim', None)
        keypair = {}
        for line in file_obj:
            if line.strip().startswith(comments):
                continue
            key, pair = line.strip().split(delim)
            keypair[key] = pair
        return keypair
