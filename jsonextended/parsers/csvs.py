#!/usr/bin/env python

class CSV_Parser(object):
    """
    Examples
    --------
    >>> from pprint import pprint

    >>> from jsonextended.utils import MockPath
    >>> fileobj = MockPath(is_file=True,
    ... content='''# comment line
    ... head1,head2
    ... val1,val2
    ... val3,val4'''
    ... )
    >>> with fileobj.open() as f:
    ...     data = CSV_Parser().read_file(f)
    >>> pprint(data)
    {'head1': ['val1', 'val3'], 'head2': ['val2', 'val4']}

    """

    plugin_name = 'csv.basic'
    plugin_descript = 'read *.csv delimited file with headers to {header:[column_values]}'
    file_regex = '*.csv'

    def read_file(self, file_obj, **kwargs):

        delim = kwargs.get('csv_delim', ',')
        comments = kwargs.get('comments', '#')
        keypairs = None
        for line in file_obj:
            if line.strip().startswith(comments):
                continue
            values = line.strip().split(delim)
            if keypairs is None:
                keypairs = [(v, []) for v in values]
                continue
            assert len(keypairs) == len(values), 'row different length to headers'
            for keypair, value in zip(keypairs, values):
                keypair[1].append(value)

        return {} if keypairs is None else dict(keypairs)
