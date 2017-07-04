#!/usr/bin/env python
# -- coding: utf-8 --
""" a module for parsing simulation data to json format

"""
# python 3 to 2 compatibility
try:
    basestring
except NameError:
    basestring = str

class BasicParser(object):
    """ a base class for parsing simulation data to json

    subclasses should add methods beggining '_eval_',
    which read particular data from lines,
    using the helper methods provided (all start with single _ )

    Examples
    --------

    >>> class TestParser(BasicParser):
    ...
    ...     def _eval_init(self):
    ...         if self._has_sig('sim_name ='):
    ...             self.add_data('name', self._get_fields_after(2,join=True),['meta'])
    ...
    ...     def _eval_data(self):
    ...
    ...         if self._has_sig('a table of x,y,z data'):
    ...             self._skip_lines(2)
    ...             cdict = self._table_todict(
    ...                         ['x','y','z'],
    ...                         [float,float,float])
    ...             self.add_data('geometry',cdict,['config'])
    ...
    >>> from jsonextended.utils import MockPath
    >>> file_obj = MockPath('test.txt',is_file=True,
    ... content='''
    ...     sim_name = test simulation
    ...
    ...     a table of x,y,z data
    ...     x y z
    ...     1 2 3
    ...     4 5 6
    ... ''')
    ...
    >>> from pprint import pprint
    >>> parser = TestParser()
    >>> data = parser.read_file(file_obj)
    >>> pprint(data)
    {'config': {'geometry': {'x': [1.0, 4.0], 'y': [2.0, 5.0], 'z': [3.0, 6.0]}},
     'meta': {'name': 'test simulation'}}

    >>> out_file_obj = MockPath('test.json',is_file=True,exists=False)
    >>> parser.output_json(out_file_obj,indent=None)
    >>> print(out_file_obj.to_string())
    File("test.json") Contents:
    {"config": {"geometry": {"x": [1.0, 4.0], "y": [2.0, 5.0], "z": [3.0, 6.0]}}, "meta": {"name": "test simulation"}}

    """  
      
    _always_exit_section = True
    
    def __init__(self):
        """ a class for parsing data to json format """
        self.reset()

    def reset(self):
        """ remove all data
        """
        self.__file = None
        self.__delim = None
        self.__file_line = ''
        self.__file_line_number = 0
        self.__in_file_section = []
        self.__init_file_keys = []
        self.__data = {}

    def __get_data(self):
        return self.__data.copy()
    data = property(__get_data)

    def add_dict(self, d, overwrite=False):
        """ input nested dictionary object

        d : dict
        overwrite : bool
            if true allow overwriting of current data

        """
        from jsonextended.edict import merge
        self.__data = merge([self.__data,d],overwrite=overwrite)

    def add_json(self, jfile, overwrite=False,
                 key_path=[], in_memory=True, ignore_prefix=('.', '_')):
        """ input json file data

        jfile : str, file_like or path_like
            if str, must be existing file or folder,
            if file_like, must have 'read' method
            if path_like, must have 'iterdir' method (see pathlib.Path)
        overwrite : bool
            if true allow overwriting of current data
        key_path : list of str
            a list of keys to index into the json before parsing it
        in_memory : bool
            if true reads full json into memory before filtering keys (this is faster but uses more memory)
        ignore_prefix : list of str
            ignore folders beginning with these prefixes

        """
        from jsonextended.edict import merge
        from jsonextended.ejson import to_dict
        new_data = to_dict(jfile, key_path, in_memory, ignore_prefix)
        self.__data = merge([self.__data,new_data],overwrite=overwrite)

    def output_json(self, jfile, overwrite=False, dirlevel=0, sort_keys=True, indent=2, **kwargs):
        """ output parsed data to json

        jfile : str or file_like
            if file_like, must have write method
        overwrite : bool
            whether to overwrite existing files
        dirlevel : int
            if jfile is path to folder, defines how many key levels to set as sub-folders
        sort_keys : bool
            if true then the output of dictionaries will be sorted by key
        indent : int
            if non-negative integer, then JSON array elements and
            object members will be pretty-printed on new lines with that indent level spacing.
        kwargs : dict
            keywords for json.dump

        """
        from jsonextended.edict import to_json
        to_json(self.__data, jfile, overwrite=overwrite, dirlevel=dirlevel,
                           sort_keys=sort_keys, indent=indent, **kwargs)

    def add_data(self,keys,values,init_keys=None,
                dtype=None,merge=False):
        """ add data item

        keys : str or list of strings
            key for data
        values : various
        init_keys : list of strings
        dtype : type
            data type
        merge : bool
            if True and key already exists, then attempt to merge values (list addition or dict update)

        """
        init_keys = [] if init_keys is None else init_keys
        if not isinstance(init_keys,list):
            raise ValueError('init_keys must be a list: {0}'.format(init_keys))

        init_keys = self.__init_file_keys + init_keys

        mdict = self.__data
        for k in init_keys:
            if not k in mdict:
                mdict[k] = {}
            mdict = mdict[k]
            if not isinstance(mdict,dict):
                raise ValueError('{0} already set as leaf'.format(k))

        if not isinstance(keys,list):
            keys = [keys]
            values = [values]

        for k,v in zip(keys,values):
            if (k in mdict and merge and
                isinstance(mdict[k],dict) and isinstance(v,dict)):
                mdict[k].update(v)
            elif (k in mdict and merge and
                isinstance(mdict[k],list) and isinstance(v,list)):
                mdict[k] += v
            elif k in mdict:
                raise IOError('data already contains keys; {0}'.format(
                    init_keys+[k]))
            else:
                mdict[k] = dtype(v) if dtype is not None else v

    def read_file(self, rfile, delim=None,
                  init_section=[], init_keys=None, **kwargs):
        """ read file to json format

        Properties
        ----------
        rfile : str or file_like
            file to read
        delim : str or None
            delimiter by which to split file lines. If None, splits by whitespace
        init_section: list of strings
            section of file to start in

        """
        init_keys = [] if init_keys is None else init_keys
        
        if isinstance(rfile,basestring):
            with open(rfile,'r') as f:
                return self._with_open_file(f,delim,init_section,init_keys,**kwargs)
        elif hasattr(rfile, 'open'):
            with rfile.open('r') as f:
                return self._with_open_file(f,delim,init_section,init_keys,**kwargs)
        elif not hasattr(rfile,'readline'):
            raise ValueError('rfile should be a str or file_like object: {}'.format(rfile))
        else:
            return self._with_open_file(rfile,delim,init_section,init_keys,**kwargs)

    def _with_open_file(self, f, delim=None,
                  init_section=[], init_keys=None, **kwargs):
        self.__file = f
        self.__file_line_number = 1
        self.__delim = delim
        self.__in_file_section = init_section
        self.__init_file_keys = init_keys[:]

        try:
            self.__file_line = f.readline()
            while self.__file_line:
                self.__file_line =self.__file_line.strip()
                for func_name, func in self.__class__.__dict__.items():
                    if func_name[0:6]=='_eval_':
                        # if returns True then line has been evaluated
                        if func(self)==True:
                            break
                self.__file_line = f.readline()
                self.__file_line_number += 1
        finally:
            self.__in_file_section = []
            self.__init_file_keys = []
            self.__file = None
            self.__file_line_number = 0
            self.__delim = None
        
        return self.data

    def __get_line(self):
        return self.__file_line
    def __set_line(self,line):
        assert isinstance(line,basestring), 'line must be a string: {}'.format(line)
        self.__file_line = line
    _line = property(__get_line,__set_line)

    def _get_section(self,level=None):
        if not self.__in_file_section:
            raise IOError('no file section available')
        if level is not None:
            if len(self.__in_file_section) < level - 1:
                raise IOError('no file section available for level: {}'.format(level))
            else:
                return self.__in_file_section[level-1]
        return self.__in_file_section[:]

    def _exit_file_section(self,level=1):
        """ exit file section
        
        level : int
        """
        assert level > 0, 'level must be 1 or greater'
        self.__in_file_section = self.__in_file_section[:level-1]        
        
    def _enter_file_section(self,section,level=1):
        """ enter file section
        
        section : str
        level : int
        """
        if not self._always_exit_section and level>len(self.__in_file_section):
            raise IOError("attempting to enter '{0}' as level {1} but already in file section: {2} (line number: {3})".format(
                section,level, self.__in_file_section,self.__file_line_number))                
        elif level <= len(self.__in_file_section) + 1:
            self.__in_file_section = self.__in_file_section[0:level-1] + [section]
        else:
            raise IOError("attempting to set '{0}' as level {1} for current file section: {2} (line number: {3})".format(
                section,level, self.__in_file_section,self.__file_line_number))

    def _in_section(self, section, *sections):
        """ test if in section(s) """
        if len(self.__in_file_section) < 1 + len(sections):
            return False
        for i,s in enumerate([section]+list(sections)):
            if self.__in_file_section[i] != s:
                return False
        return True
            
        
    def _skip_lines(self, i=1):
        """skip i lines of file """
        if self.__file is None:
            return ''
        if hasattr(self.__file,'closed'):
            if self.__file.closed:
                return ''
        for _ in range(i):
            self.__file_line = self.__file.readline()
            self.__file_line_number += 1

        self.__file_line = self.__file_line.strip()

    def _has_sig(self, sig_dict):
        """ check if line matches field signature

        line : str
        sig_dict: str or dict
            {field_num:value,...}, field_num start at 1

        """
        if isinstance(sig_dict,basestring):
            f = sig_dict.split(self.__delim)
            sig_dict = dict(zip(range(1,len(f)+1),f))
        line_list =self.__file_line.split(self.__delim)
        if len(line_list) < max(sig_dict.keys()):
            return False
        for field, value in sig_dict.items():
            if line_list[field-1] != value:
                return False
        return True

    def _get_fields(self, field_nums):
        """ get field from line, field_num start at 1

        """
        if isinstance(field_nums,int):
            field_nums = [field_nums]
        line_list =self.__file_line.split(self.__delim)
        if len(line_list) < max(field_nums):
            raise IOError('line does not have {0} fields; {1}'.format(max(field_nums),self.__file_line))
        vals = [line_list[n-1] for n in field_nums]
        if len(vals) == 1:
            return vals[0]
        else:
            return vals

    def _get_fields_after(self,field_num, join=False):
        """ get all fields after field_num, field_num start at 1

        join : bool
            join fields together into single sting (by delimiter)
        """
        line_list =self.__file_line.split(self.__delim)
        if len(line_list) < field_num:
            raise IOError('line does not have {0} fields; {1}'.format(field_num,self.__file_line))

        if join:
            delim = ' ' if self.__delim is None else self.__delim
            return delim.join(line_list[field_num:])
        else:
            return line_list[field_num:]

    def _str_map(self,sdict):
        """ return function to convert strings to another value

        sdict : dict
            mapping of string value to new value

        """
        def func(val):
            if val in sdict:
                return sdict[val]
            else:
                raise ValueError('value not in {0}, as expected: {1}'.format(
                                sdict.keys(),val))
        return func

    def _table_todict(self,columns,dtypes,length=None):
        row = 1
        cdict = dict([(c,[]) for c in columns])
        line_split =self.__file_line.split(self.__delim)
        while len(line_split) >= len(columns):
            for v,k,dtype in zip(line_split,columns,dtypes):
                cdict[k].append(dtype(v))
            row += 1
            if length is not None:
                if row > length:
                    break
            self._skip_lines()
            line_split =self.__file_line.split(self.__delim)
        return cdict

if __name__ == '__main__':
    import doctest
    print(doctest.testmod())