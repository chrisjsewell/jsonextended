import os, inspect
import re
import contextlib 
from functools import total_ordering 
from fnmatch import fnmatch 
import tempfile

# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str
# python 3 to 2 compatibility
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib


def class_to_str(obj):
    """ get class string from object 
    
    Examples
    --------
    
    >>> class_to_str(list).split('.')[1]
    'list'
       
    """
    mod_str = obj.__module__
    name_str = obj.__name__
    if mod_str=='__main__':
        return name_str 
    else :
        return '.'.join([mod_str,name_str])

def get_module_path(module):
    """return a directory path to a module"""
    return pathlib.Path(os.path.dirname(os.path.abspath(inspect.getfile(module))))

from jsonextended import _example_data_folder
def get_test_path():
    """ returns test path object

    Examples
    --------
    >>> path = get_test_path()
    >>> path.name
    '_example_data_folder'

    """
    return get_module_path(_example_data_folder)

def get_data_path(data, module, check_exists=True):
    """return a directory path to data within a module

    data : str or list of str
        file name or list of sub-directories and file name (e.g. ['lammps','data.txt'])   
    """
    basepath = os.path.dirname(os.path.abspath(inspect.getfile(module)))
    
    if isinstance(data, basestring): data = [data]
    
    dirpath = os.path.join(basepath, *data)
    
    if check_exists:
        assert os.path.exists(dirpath), '{0} does not exist'.format(dirpath)
    
    return pathlib.Path(dirpath)

def _atoi(text):
    return int(text) if text.isdigit() else text
def _natural_keys(text):
    """human order sorting

    alist.sort(key=_natural_keys)
    """
    return [_atoi(c) for c in re.split('(\d+)',str(text))]

def natural_sort(iterable):
    """human order sorting of number strings 

    Examples
    --------
    
    >>> sorted(['011','1', '21'])
    ['011', '1', '21']
    
    >>> natural_sort(['011','1', '21'])
    ['1', '011', '21']
    
    """
    return sorted(iterable, key=_natural_keys)


class _OpenRead(object):
    def __init__(self, linelist):
        self._linelist = linelist
        self._current_indx = 0
    def read(self):
        return '\n'.join(self._linelist)
    def readline(self):
        if self._current_indx >= len(self._linelist):
            line = ''
        else:
            line = self._linelist[self._current_indx] + '\n'
        self._current_indx += 1
        return line
    def __iter__(self):
        for line in self._linelist:
            yield line

class _OpenWrite(object):
    def __init__(self):
        self._str = ''
    def write(self,instr):
        self._str += instr
    def writelines(self, lines):
        for instr in lines:
            self.write(instr)

@total_ordering 
class MockPath(object):
    r"""a mock path, mimicking pathlib.Path, 
    supporting context open method for read/write
    
    Properties
    ----------
    path : str
        the path string
    is_file : bool
        if True is file, else folder
    content : str
        content of the file
    structure:
        structure of the directory

    Examples
    --------
    >>> file_obj = MockPath("path/to/test.txt",is_file=True,
    ...                     content="line1\nline2\nline3")
    ...
    >>> file_obj
    MockFile("test.txt")
    >>> file_obj.name
    'test.txt'
    >>> print(file_obj.to_string())
    File("test.txt") Contents:
    line1
    line2
    line3
    >>> file_obj.is_file()
    True
    >>> file_obj.is_dir()
    False
    >>> with file_obj.open('r') as f:
    ...     print(f.readline().strip())
    line1
    >>> with file_obj.open('w') as f:
    ...     f.write('newline1\nnewline2')
    >>> print(file_obj.to_string())
    File("test.txt") Contents:
    newline1
    newline2
    
    >>> with file_obj.maketemp() as temp:
    ...     with open(temp.name) as f:
    ...         print(f.readline().strip())
    newline1
    
    >>> dir_obj = MockPath(
    ...   structure=[{'dir1':[{'subdir':[]},file_obj]},{'dir2':[file_obj]},file_obj]
    ... )
    >>> dir_obj
    MockFolder("root")
    >>> dir_obj.name
    'root'
    >>> dir_obj.is_file()
    False
    >>> dir_obj.is_dir()
    True
    >>> print(dir_obj.to_string())
    Folder("root") 
      Folder("dir1") 
        Folder("subdir") 
        File("test.txt") 
      Folder("dir2") 
        File("test.txt") 
      File("test.txt") 

    >>> list(dir_obj.iterdir())
    [MockFolder("dir1"), MockFolder("dir2"), MockFile("test.txt")]
    
    >>> new = dir_obj.joinpath('dir3')
    >>> list(dir_obj.iterdir())
    [MockFolder("dir1"), MockFolder("dir2"), MockFile("test.txt")]

    >>> new.mkdir()
    >>> list(dir_obj.iterdir())
    [MockFolder("dir1"), MockFolder("dir2"), MockFolder("dir3"), MockFile("test.txt")]
        
    """
    def __init__(self, path='root', 
                 is_file=False,exists=True,
                 structure=[],content=''):
        self._path = path
        self.name = os.path.basename(path)
        self._exists = exists
        self._is_file = is_file
        self._is_dir = not is_file        
        self._content = content.splitlines()
        
        self.children = []
        for subobj in structure:
            if hasattr(subobj,'keys'):            
                key = list(subobj.keys())[0]
                self.children.append(MockPath(os.path.join(self._path,key),
                                              structure=subobj[key]))
            elif isinstance(subobj,MockPath):
                self.children.append(subobj)
            else:
                raise ValueError('items must be dict_like or MockPath: {}'.format(subobj))        
        
    def is_file(self):
        return self._is_file
    def is_dir(self):
        return self._is_dir
    def exists(self):
        return self._exists
                        
    def joinpath(self, path):
        if len(os.path.split(path)[0]):
            raise NotImplementedError
        for child in self.children:
            if child.name == path:
                return child
                
        # does not yet exist, must use touch or mkdir to convert to file or folder
        new = MockPath(path=os.path.join(self._path,path),exists=False)
        self.children.append(new)
        return new
        
    def mkdir(self):
        if not self._exists:
            self._is_file = False
            self._is_dir = True
            self._exists = True
    def touch(self):
        if not self._exists:
            self._is_file = True
            self._is_dir = False
            self._exists = True

    def iterdir(self):
        for subobj in sorted(self.children):
            if subobj.exists():
                yield subobj
    
    def glob(self, regex):
        for subobj in sorted(self.children):
            if fnmatch(subobj.name,regex):
                yield subobj     
    
    @contextlib.contextmanager    
    def maketemp(self):
        """make a named temporary file containing the file contents """
        if self.is_dir():
            raise IOError('[Errno 21] Is a directory: {}'.format(self.path))
        fileTemp = tempfile.NamedTemporaryFile(mode='w+',delete = False)
        try:
            fileTemp.write('\n'.join(self._content))
            fileTemp.close()
            yield fileTemp
        finally:
            os.remove(fileTemp.name)        
        
    @contextlib.contextmanager    
    def open(self, readwrite='r'):
        if self.is_dir():
            raise IOError('[Errno 21] Is a directory: {}'.format(self.path))
            
        if 'r' in readwrite:
            obj = _OpenRead(self._content)
            yield obj
        elif 'w' in readwrite:
            obj = _OpenWrite()
            yield obj
            self._content = obj._str.splitlines()
        else:
            raise ValueError('readwrite should contain r or w')

    def __gt__(self,other):
        if not hasattr(other, 'name'):
            return NotImplemented
        return self.name > other.name
    def __eq__(self,other):
        if not hasattr(other, 'name'):
            return NotImplemented
        return self.name == other.name
        
    def _recurse_print(self, obj, text='',indent=0,indentlvl=2,file_content=False):
        indent += indentlvl
        for subobj in sorted(obj):
            if not subobj.exists():
                continue
            if subobj.is_dir():            
                text += ' '*indent + '{0}("{1}") \n'.format(self._folderstr, subobj.name)
                text += self._recurse_print(subobj.children,
                                indent=indent,file_content=file_content)
            else:
                if file_content:
                    sep = '\n'+' '*(indent+1)
                    text += ' '*indent + sep.join(['{0}("{1}") Contents:'.format(self._filestr,subobj.name)]+subobj._content) + '\n'
                else:
                    text += ' '*indent + '{0}("{1}") \n'.format(self._filestr,subobj.name)
            
        return text
        
    def to_string(self,indentlvl=2,file_content=False,color=False):
        """convert to string """
        if color:
            self._folderstr = colortxt('Folder','green')
            self._filestr = colortxt('File','blue')
        else:
            self._folderstr = 'Folder'
            self._filestr = 'File'
        
        if self.is_file():
            return '\n'.join(['{0}("{1}") Contents:'.format(self._filestr,self.name)]+self._content)
        elif self.is_dir():
            text = '{0}("{1}") \n'.format(self._folderstr,self.name)
            text += self._recurse_print(self.children,indentlvl=indentlvl,
                                        file_content=file_content)
            
            text = text[0:-1] if text.endswith('\n') else text
            return text
        else:
            return 'MockPath({})'.format(self.name)
        
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        if not self.exists():
            return 'MockVirtualPath("{}")'.format(self.name)
        elif self.is_dir():
            return 'MockFolder("{}")'.format(self.name)
        elif self.is_file():
            return 'MockFile("{}")'.format(self.name)
        else:
            return 'MockPath("{}")'.format(self.name)            

def memory_usage():
    """return memory usage of python process in MB 
    
    from http://fa.bianp.net/blog/2013/different-ways-to-get-memory-consumption-or-lessons-learned-from-memory_profiler/
    psutil is quicker
    
    >>> isinstance(memory_usage(),float)
    True
    
    """
    try:
        import psutil, os
    except ImportError:
        return _memory_usage_ps()
        
    process = psutil.Process(os.getpid())
    mem = process.memory_info()[0] / float(2 ** 20)
    return mem

def _memory_usage_ps():
    """return memory usage of python process in MB 
    
    >>> isinstance(_memory_usage_ps(),float)
    True
    
    """
    import subprocess, os
    out = subprocess.Popen(['ps', 'v', '-p', str(os.getpid())],
    stdout=subprocess.PIPE).communicate()[0].split(b'\n')
    vsz_index = out[0].split().index(b'RSS')
    mem = float(out[1].split()[vsz_index]) / 1024
    return mem
    
def load_memit():
    """load memory usage ipython magic, 
    require memory_profiler package to be installed
    
    to get usage: %memit?
    
    Author: Vlad Niculae <vlad@vene.ro>
    Makes use of memory_profiler from Fabian Pedregosa
    available at https://github.com/fabianp/memory_profiler
    """
    from IPython.core.magic import Magics, line_magic, magics_class
    from memory_profiler import memory_usage as _mu

    try:
        ip = get_ipython()
    except NameError as err:
        raise Exception('not in ipython/jupyter kernel:\n {}'.format(err))
    
    @magics_class
    class MemMagics(Magics):
        @line_magic
        def memit(self, line='', setup='pass'):
            """Measure memory usage of a Python statement

            Usage, in line mode:
              %memit [-ir<R>t<T>] statement

            Options:
            -r<R>: repeat the loop iteration <R> times and take the best result.
            Default: 3

            -i: run the code in the current environment, without forking a new
            process. This is required on some MacOS versions of Accelerate if your
            line contains a call to `np.dot`.

            -t<T>: timeout after <T> seconds. Unused if `-i` is active.
            Default: None

            Examples
            --------
            ::

              In [1]: import numpy as np

              In [2]: %memit np.zeros(1e7)
              maximum of 3: 76.402344 MB per loop

              In [3]: %memit np.ones(1e6)
              maximum of 3: 7.820312 MB per loop

              In [4]: %memit -r 10 np.empty(1e8)
              maximum of 10: 0.101562 MB per loop

              In [5]: memit -t 3 while True: pass;
              Subprocess timed out.
              Subprocess timed out.
              Subprocess timed out.
              ERROR: all subprocesses exited unsuccessfully. Try again with the
              `-i` option.
              maximum of 3: -inf MB per loop

            """
            opts, stmt = self.parse_options(line, 'r:t:i', posix=False,
                                            strict=False)
            repeat = int(getattr(opts, 'r', 3))
            if repeat < 1:
                repeat == 1
            timeout = int(getattr(opts, 't', 0))
            if timeout <= 0:
                timeout = None
            run_in_place = hasattr(opts, 'i')

            # Don't depend on multiprocessing:
            try:
                import multiprocessing as pr
                from multiprocessing.queues import SimpleQueue
                q = SimpleQueue()
            except ImportError:
                class ListWithPut(list):
                    "Just a list where the `append` method is aliased to `put`."
                    def put(self, x):
                        self.append(x)
                q = ListWithPut()
                print ('WARNING: cannot import module `multiprocessing`. Forcing '
                       'the `-i` option.')
                run_in_place = True

            ns = self.shell.user_ns

            def _get_usage(q, stmt, setup='pass', ns={}):
                try:
                    exec(setup) in ns
                    _mu0 = _mu()[0]
                    exec(stmt) in ns
                    _mu1 = _mu()[0]
                    q.put(_mu1 - _mu0)
                except Exception as e:
                    q.put(float('-inf'))
                    raise e

            if run_in_place:
                for _ in xrange(repeat):
                    _get_usage(q, stmt, ns=ns)
            else:
                # run in consecutive subprocesses
                at_least_one_worked = False
                for _ in xrange(repeat):
                    p = pr.Process(target=_get_usage, args=(q, stmt, 'pass', ns))
                    p.start()
                    p.join(timeout=timeout)
                    if p.exitcode == 0:
                        at_least_one_worked = True
                    else:
                        p.terminate()
                        if p.exitcode == None:
                            print('Subprocess timed out.')
                        else:
                            print('Subprocess exited with code %d.' % p.exitcode)
                        q.put(float('-inf'))

                if not at_least_one_worked:
                    print('ERROR: all subprocesses exited unsuccessfully. Try '
                           'again with the `-i` option.')

            usages = [q.get() for _ in xrange(repeat)]
            usage = max(usages)
            print("maximum of %d: %f MB per loop" % (repeat, usage))

    ip.register_magics(MemMagics)

import os

_ATTRIBUTES = dict(
    list(zip([
        'bold',
        'dark',
        '',
        'underline',
        'blink',
        '',
        'reverse',
        'concealed'
    ],
        list(range(1, 9))
    ))
)
del _ATTRIBUTES['']

_HIGHLIGHTS = dict(
    list(zip([
        'on_grey',
        'on_red',
        'on_green',
        'on_yellow',
        'on_blue',
        'on_magenta',
        'on_cyan',
        'on_white'
    ],
        list(range(40, 48))
    ))
)

_COLORS = dict(
    list(zip([
        'grey',
        'red',
        'green',
        'yellow',
        'blue',
        'magenta',
        'cyan',
        'white',
    ],
        list(range(30, 38))
    ))
)


def colortxt(text, color=None, on_color=None, attrs=None):
    """Colorize text.

    Available text colors:
        red, green, yellow, blue, magenta, cyan, white.

    Available text highlights:
        on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white.

    Available attributes:
        bold, dark, underline, blink, reverse, concealed.

    Examples
    --------
    >>> txt = colortxt('Hello, World!', 'red', 'on_grey', ['bold'])
    >>> print(txt)
    \x1b[1m\x1b[40m\x1b[31mHello, World!\x1b[0m

    """
    _RESET = '\033[0m'
    __ISON = True
    if __ISON and os.getenv('ANSI_COLORS_DISABLED') is None:
        fmt_str = '\033[%dm%s'
        if color is not None:
            text = fmt_str % (_COLORS[color], text)

        if on_color is not None:
            text = fmt_str % (_HIGHLIGHTS[on_color], text)

        if attrs is not None:
            for attr in attrs:
                text = fmt_str % (_ATTRIBUTES[attr], text)

        text += _RESET
    return text


