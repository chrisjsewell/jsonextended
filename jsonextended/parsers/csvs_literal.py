#!/usr/bin/env python
import ast


class CSVLiteral_Parser(object):
    """
    Examples
    --------
    >>> from pprint import pprint

    >>> from jsonextended.utils import MockPath
    >>> fileobj = MockPath(is_file=True,
    ... content='''# comment line
    ... head1,head2
    ... 1.1,3
    ... 2.2,"3.3"'''
    ... )
    >>> with fileobj.open() as f:
    ...     data = CSVLiteral_Parser().read_file(f)
    >>> pprint(data)
    {'head1': [1.1, 2.2], 'head2': [3, '3.3']}

    """

    plugin_name = 'csv.literal'
    plugin_descript = "read *.literal.csv delimited files with headers to {header:column_values}, with number strings converted to int/float"
    ", s.t. values are converted to their python type"
    file_regex = '*.literal.csv'

    @staticmethod
    def tryeval(val):
        try:
            val = ast.literal_eval(val)
        except ValueError:
            pass
        return val

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

        return {} if keypairs is None else {k: [self.tryeval(v) for v in vs] for k, vs in keypairs}
