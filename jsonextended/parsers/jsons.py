#!/usr/bin/env python

import json

class JSON_Parser(object):
    file_regex = '*.json'
    def read_file(self, file_obj, **kwargs):
        
        return json.load(file_obj, object_hook=kwargs.get('object_hook',None), 
                                   parse_float=kwargs.get('parse_float',None))