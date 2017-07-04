#!/usr/bin/env python

import json

class JSON_Parser(object):
    """

    Examples
    --------
    
    >>> from jsonextended.utils import MockPath
    >>> fileobj = MockPath(is_file=True,
    ... content='{"key1":[1,2,3]}'
    ... )
    >>> with fileobj.open() as f:
    ...     data = JSON_Parser().read_file(f)
    >>> list(data.values())
    [[1, 2, 3]]
    
    """
    
    plugin_name = 'json.basic'
    plugin_decript = 'read a basic json file'
    file_regex = '*.json'
    
    def read_file(self, file_obj, **kwargs):
        
        return json.load(file_obj, object_hook=kwargs.get('object_hook',None), 
                                   parse_float=kwargs.get('parse_float',None))