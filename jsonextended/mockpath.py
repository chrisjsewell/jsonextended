import contextlib
import os
import sys
import tempfile
from fnmatch import fnmatch
from functools import total_ordering
import collections

# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str

try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

try:
    unicode
except NameError:
    unicode = str


# TODO handling bytes/encoding (py 2 and 3)
class _OpenRead(object):
    def __init__(self, linelist, encoding=None, usebytes=False):
        self._linelist = linelist
        self._current_indx = 0
        self._encoding = encoding
        self._bytes = usebytes

    def read(self, size=None):
        out = '\n'.join(self._linelist)[self._current_indx:]
        if size is not None:
            self._current_indx += size
            out = out[0:self._current_indx]
        if self._encoding is not None:
            out = out.encode(self._encoding)
        return out

    def readline(self):
        if self._current_indx >= len(self._linelist):
            line = ''
        else:
            line = self._linelist[self._current_indx] + '\n'
        self._current_indx += len(line)
        if self._encoding is not None:
            line = line.encode(self._encoding)
        return line

    def readlines(self):
        self._current_indx = len('\n'.join(self._linelist))
        if self._encoding is not None and self:
            return [line.encode(self._encoding) for line in self._linelist]
        else:
            return self._linelist[:]

    def __iter__(self):
        for line in self._linelist:
            if self._encoding is not None:
                line = line.encode(self._encoding)
            yield line


# TODO handling bytes/encoding (py 2 and 3)
class _OpenWrite(object):
    def __init__(self, usebytes=False):
        self._str = ''
        self._bytes = usebytes

    def write(self, instr):
        if hasattr(instr, "decode"):
            instr = instr.decode()
        self._str += instr

    def writelines(self, lines):
        for instr in lines:
            if hasattr(instr, "decode"):
                instr = instr.decode()
            self.write(instr)


@total_ordering
class MockPath(object):
    r"""a mock path, mimicking pathlib.Path,
    supporting context open method for read/write

    Parameters
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
    MockFile("path/to/test.txt")
    >>> file_obj.name
    'test.txt'
    >>> file_obj.parent
    MockFolder("path/to")
    >>> print(str(file_obj))
    path/to/test.txt
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
    ...     with temp.open() as f:
    ...         print(f.readline().strip())
    newline1

    >>> dir_obj = MockPath(
    ...   structure=[{'dir1':[{'subdir':[file_obj.copy_path_obj()]},file_obj.copy_path_obj()]},
    ...              {'dir2':[file_obj.copy_path_obj()]},file_obj.copy_path_obj()]
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
        File("test.txt")
      Folder("dir2")
        File("test.txt")
      File("test.txt")

    >>> "dir1/test.txt" in dir_obj
    True

    >>> dir_obj["dir1/test.txt"]
    MockFile("root/dir1/test.txt")

    >>> list(dir_obj.iterdir())
    [MockFolder("root/dir1"), MockFolder("root/dir2"), MockFile("root/test.txt")]

    >>> list(dir_obj.glob("*"))
    [MockFolder("root/dir1"), MockFolder("root/dir2"), MockFile("root/test.txt")]

    >>> list(dir_obj.glob("dir1/*"))
    [MockFolder("root/dir1/subdir"), MockFile("root/dir1/test.txt")]

    >>> list(dir_obj.glob("**"))
    [MockFolder("root/dir1"), MockFolder("root/dir1/subdir"), MockFolder("root/dir2")]

    >>> list(dir_obj.glob("**/*"))
    [MockFolder("root/dir1"), MockFolder("root/dir1/subdir"), MockFile("root/dir1/subdir/test.txt"), MockFile("root/dir1/test.txt"), MockFolder("root/dir2"), MockFile("root/dir2/test.txt"), MockFile("root/test.txt")]

    #>>> list(dir_obj.glob("**/dir1"))
    #[MockFolder("root/dir1")]

    >>> new = dir_obj.joinpath('dir3')
    >>> new.mkdir()
    >>> list(dir_obj.iterdir())
    [MockFolder("root/dir1"), MockFolder("root/dir2"), MockFolder("root/dir3"), MockFile("root/test.txt")]

    >>> dir_obj.joinpath("test.txt").unlink()
    >>> list(dir_obj.iterdir())
    [MockFolder("root/dir1"), MockFolder("root/dir2"), MockFolder("root/dir3")]

    >>> dir_obj.joinpath("dir3").rmdir()
    >>> list(dir_obj.iterdir())
    [MockFolder("root/dir1"), MockFolder("root/dir2")]

    >>> print(dir_obj.to_string())
    Folder("root")
      Folder("dir1")
        Folder("subdir")
          File("test.txt")
        File("test.txt")
      Folder("dir2")
        File("test.txt")

    >>> dir_obj.joinpath("dir1/subdir")
    MockFolder("root/dir1/subdir")

    >>> dir_obj.joinpath("dir1", "subdir")
    MockFolder("root/dir1/subdir")

    >>> new = dir_obj.joinpath("dir1/subdir/other")
    >>> new
    MockVirtualPath("root/dir1/subdir/other")

    >>> new.touch()
    >>> new
    MockFile("root/dir1/subdir/other")

    >>> new.unlink()
    >>> new
    MockVirtualPath("root/dir1/subdir/other")

    >>> new.mkdir()
    >>> new
    MockFolder("root/dir1/subdir/other")

    >>> newfile = MockPath('newfile.txt', is_file=True)
    >>> new.copy_from(newfile)
    >>> print(new.to_string())
    Folder("other")
      File("newfile.txt")

    >>> file_obj = MockPath("newfile2.txt",is_file=True, content='test')
    >>> file_obj.copy_to(new)
    >>> print(new.to_string())
    Folder("other")
      File("newfile.txt")
      File("newfile2.txt")

    >>> file_obj.name = "newfile3.txt"
    >>> with file_obj.maketemp() as temp:
    ...    new.copy_from(temp)
    >>> print(new.to_string())
    Folder("other")
      File("newfile.txt")
      File("newfile2.txt")
      File("newfile3.txt")

    >>> print(new.copy_path_obj().to_string())
    Folder("other")
      File("newfile.txt")
      File("newfile2.txt")
      File("newfile3.txt")

    >>> with new.maketemp(getoutput=True) as tempdir:
    ...     tempdir.joinpath("new").mkdir()
    ...     tempdir.joinpath("new/file.txt").touch()
    >>> print(new.to_string())
    Folder("other")
      Folder("new")
        File("file.txt")
      File("newfile.txt")
      File("newfile2.txt")
      File("newfile3.txt")

    """

    def __init__(self, path='root',
                 is_file=False, exists=True,
                 structure=(), content='', parent=None):
        self._path = path
        self._name = os.path.basename(path)
        self._exists = exists
        self._is_file = is_file
        self._is_dir = not is_file
        self._content = content.splitlines()
        self._parent = parent
        self._children = []

        paths = self._splitall(path)
        if len(paths) > 1 and parent is None:
            self.parent = MockPath(os.path.join(*paths[:-1]))

        for subobj in structure:
            if hasattr(subobj, 'keys'):
                key = list(subobj.keys())[0]
                self.add_child(MockPath(os.path.join(self._path, key),
                                        structure=subobj[key], parent=self))
            elif isinstance(subobj, MockPath):
                if subobj._parent is not None:
                    raise ValueError("attempting to add a child which already has a parent: {}".format(subobj))
                self.add_child(subobj)
            else:
                raise ValueError('items must be dict_like or MockPath: {}'.format(subobj))

    def _get_path(self):
        return self._path

    path = property(_get_path)

    def _get_parent(self):
        if self._parent is None:
            path = MockPath('subroot')
            path._children = [self]
            return path
        else:
            return self._parent

    def _set_parent(self, parent):
        if parent is None:
            self._parent = None
            parentpath = ''
        else:
            parentpath = parent.path
        self._parent = parent
        self._path = os.path.join(parentpath, self.name)
        for child in self.children:
            child.parent = self

    parent = property(_get_parent, _set_parent)

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name
        if self._parent is not None:
            self._path = os.path.join(self.parent.path, name)

    name = property(_get_name, _set_name)

    def _get_children(self):
        return self._children[:]

    children = property(_get_children)

    def __getitem__(self, name):
        """

        Parameters
        ----------
        name: str or list of strings

        Returns
        -------

        """
        next = []
        if isinstance(name, basestring):
            name = self._splitall(name)
        if isinstance(name, list):
            if len(name) == 1:
                name = name[0]
            else:
                next = name[1:]
                name = name[0]
        if isinstance(name, basestring):
            for child in self.iterdir():
                if child.name == name:
                    if next:
                        return child[next]
                    else:
                        return child
            raise KeyError("no name: {}".format(name))
        else:
            raise ValueError("name not a list or str: {}".format(name))

    def __contains__(self, name):
        """

        Parameters
        ----------
        name: str or list of strings

        Returns
        -------

        """
        try:
            self[name]
            return True
        except KeyError:
            return False

    def add_child(self, child):
        # TODO could allow same name if one is file and one is dir?
        if child.name in [c.name for c in self._children]:
            raise IOError("child with this name already exists: {}".format(child.name))
        child.parent = self
        self._children.append(child)

    # TODO need to implement relative naming and switchin to/from
    def absolute(self):
        return self

    # TODO should return a new mock path rather than a str, need to implement relative naming and switchin to/from
    def relative_to(self, other):
        return os.path.relpath(self._path, other._path)

    def rename(self, target):

        if hasattr(target, "name"):
            name = target.name
        elif isinstance(target, basestring):
            name = target
        else:
            raise ValueError("target must be a string or have a name attribute")

        if not self.exists():
            raise IOError("path doesn't exist: {}".format(self))
        self.name = name
        self._path = os.path.join(os.path.dirname(self._path), name)

    def _recurse_structure(self):
        structure = []
        for child in self.children:
            if not child.exists():
                continue
            if child.is_file():
                structure.append(child.copy_path_obj())
            else:
                structure.append({child.name: [c.copy_path_obj() for c in child.children]})
        return structure

    def copy_path_obj(self):
        """copy mock path (removing path and parent)"""
        if self.is_file():
            return MockPath(path=self.name, is_file=True,
                            exists=self.exists(), structure=[], content="\n".join(self._content), parent=None)
        else:
            structure = self._recurse_structure()
            return MockPath(path=self.name, is_file=False, exists=self.exists(), parent=None,
                            structure=structure)

    def is_file(self):
        return self._is_file

    def is_dir(self):
        return self._is_dir

    def exists(self):
        return self._exists

    def samefile(self, other):
        return self == other

    def _splitall(self, path):

        if isinstance(path, MockPath):
            path = os.path.relpath(str(path), str(self))
        if not isinstance(path, basestring):
            raise ValueError("path is not a string or MockPath: {}".format(path))

        allparts = []
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:  # sentinel for absolute paths
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path:  # sentinel for relative paths
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts

    def _flatten(self, l):
        for el in l:
            if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
                for sub in self._flatten(el):
                    yield sub
            else:
                yield el

    def joinpath(self, *paths):

        parts = list(self._flatten([self._splitall(path) for path in paths]))

        if not parts:
            raise IOError("must be at least one path")
        elif len(parts) == 1:

            if parts[0] == '' or parts[0] == '.':
                return self

            for child in self._children:
                if child.name == parts[0]:
                    return child

            # does not yet exist, must use touch or mkdir to convert to file or folder
            new = MockPath(path=os.path.join(self._path, parts[0]), exists=False, parent=self)
            self.add_child(new)
            return new

        else:
            for child in self._children:
                if child.name == parts[0]:
                    return child.joinpath(*parts[1:])
            new = MockPath(path=os.path.join(self._path, parts[0]), exists=False, parent=self)
            self.add_child(new)
            return new.joinpath(*parts[1:])

    # TODO add mode=0o777, exist_ok=False
    def mkdir(self, parents=False):
        """

        Parameters
        ----------
        mode
        parents: bool
            If parents is true, any missing parents of this path are created as needed
            If parents is false, a missing parent raises FileNotFoundError.

        Returns
        -------

        """
        if self.parent is not None:
            if not self.parent.exists():
                if not parents:
                    raise FileNotFoundError("the parent must exist for {}".format(self))
                else:
                    self.parent.mkdir(parents=parents)  # mode=0o777,

        if not self._exists:
            self._is_file = False
            self._is_dir = True
            self._exists = True

    # TODO store stat attributes and apply them to mktemp
    def stat(self):
        """ Retrieve information about a file

        Parameters
        ----------
        path: str

        Returns
        -------
        attr: object
            see os.stat, includes st_mode, st_size, st_uid, st_gid, st_atime, and st_mtime attributes

        """
        class MockStat(object):
            # at present just returning a typical file result
            def __init__(self):
                self.st_mode = 33188
                self.st_ino = 74204932
                self.st_dev = 16777220
                self.st_nlink = 1
                self.st_uid = 634541
                self.st_gid = 1335817362
                self.st_size = 10410
                self.st_atime = 1504518028
                self.st_mtime = 1504518028
                self.st_ctime = 1504518028

            def __repr__(self):
                return "MockStatResult(st_mode=33188, st_ino=74204932, st_dev=16777220, st_nlink=1, st_uid=634541, " \
                    "st_gid=1335817362, st_size=10410, st_atime=1504518028, st_mtime=1504518028, st_ctime=1504518028)"

        return MockStat()

    def chmod(self, mode):
        """ Change the mode (permissions) of a file

        Parameters
        ----------
        path: str
        mode: int
            new permissions (see os.chmod)

        Examples
        --------
        To make a file executable
        cur_mode = folder.stat("exec.sh").st_mode
        folder.chmod("exec.sh", cur_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH )

        """
        pass

    def touch(self):

        if self.parent is not None:
            if not self.parent.exists():
                raise IOError("the parent must exist")

        if not self._exists:
            self._is_file = True
            self._is_dir = False
            self._exists = True

    def unlink(self):
        if not self._is_file:
            raise IOError("path is not a file")
        self._exists = False

    def rmdir(self):
        if not self._is_dir:
            raise IOError("path is not a directory")
        if list(self.iterdir()):
            raise IOError("path is not empty: {}".format(list(self.iterdir())))
        self._exists = False

    def iterdir(self):
        for subobj in sorted(self.children):
            if subobj.exists():
                yield subobj

    # TODO if glob("**/stop") should stop recursing once found
    def glob(self, regex, recurse=False, toplevel=True):
        """

        Parameters
        ----------
        regex: str
            the path regex, with * to match 0 or more (non-recursive) paths and ** to match zero or more (recursive) directories
        recurse: bool

        Yields
        -------
        path: MockPath

        """
        if not regex and toplevel:
            raise ValueError("Unacceptable pattern: ''")
        parts = self._splitall(regex)
        if parts[0] == "**":
            recurse = True
            parts = [""] if len(parts) == 1 else parts[1:]
        if len(parts) == 1:
            for subobj in sorted(self.iterdir()):
                if subobj.is_dir() and recurse:
                    yield subobj
                    for path in subobj.glob(parts[0], recurse=recurse, toplevel=False):
                        yield path
                elif fnmatch(subobj.name, parts[0]):
                    yield subobj
        else:
            for subobj in sorted(self.iterdir()):
                if subobj.is_dir() and recurse:
                    yield subobj
                    for path in subobj.glob(os.path.join(*parts[1:]), recurse=recurse, toplevel=False):
                        yield path
                elif fnmatch(subobj.name, parts[0]):
                    for path in subobj.glob(os.path.join(*parts[1:]), recurse=recurse, toplevel=False):
                        yield path

    @contextlib.contextmanager
    def maketemp(self, getoutput=False, dir=None):
        """make a named temporary file or folder containing the path contents

        Parameters
        ----------
        getoutput: bool
            if True, (on exit) new paths will be read/added to the path
        dir: None or str
            directory to place temp in (see tempfile.mkstemp)

        Yields
        ------
        temppath: path.Path
            path to temporary

        """
        if self.is_file():
            filetemp = tempfile.NamedTemporaryFile(mode='w+', delete=False, dir=dir)
            try:
                filetemp.write('\n'.join(self._content))
                filetemp.close()
                dirpath = os.path.join(os.path.dirname(filetemp.name), self.name)
                os.rename(filetemp.name, dirpath)
                yield pathlib.Path(dirpath)
            finally:
                try:
                    if getoutput:
                        raise NotImplementedError
                finally:
                    os.remove(dirpath)
        else:
            temppath = pathlib.Path(tempfile.mkdtemp(dir=dir))
            dirpath = os.path.join(os.path.dirname(str(temppath)), self.name)
            os.rename(str(temppath), dirpath)
            temppath = pathlib.Path(dirpath)
            try:
                self.copy_to(temppath.parent)
                yield pathlib.Path(dirpath)
            finally:
                temppath = pathlib.Path(dirpath)
                try:
                    if getoutput:
                        self._iter_temp(self, temppath, overwrite=False)
                finally:
                    for subpath in temppath.glob("**/*"):
                        if subpath.is_file():
                            subpath.unlink()
                    for subpath in reversed(list(temppath.glob("**"))):
                        subpath.rmdir()
                    if temppath.exists():
                        temppath.rmdir()

    def _iter_temp(self, mock, temp, overwrite=False):
        if not mock.name == temp.name:
            raise ValueError("mock name and temp name different: {0}, {1}".format(mock.name, temp.name))
        child_names = {c.name: c for c in mock.children}
        for subpath in temp.iterdir():
            if subpath.is_file():
                if subpath.name in child_names and not overwrite:
                    pass
                else:
                    with subpath.open() as f:
                        newpath = MockPath(subpath.name, is_file=True, content=f.read(), exists=True)
                    mock.add_child(newpath)
            else:
                if subpath.name not in child_names:
                    newpath = MockPath(subpath.name, exists=True)
                    mock.add_child(newpath)
                else:
                    newpath = child_names[subpath.name]
                self._iter_temp(newpath, subpath, overwrite=overwrite)

    def copy_to(self, target):
        """ copy from a mock path to a target

        Parameters
        ----------
        target: str, pathlib.Path or MockPath

        Returns
        -------

        """
        if not self.exists():
            raise IOError("this path does not exist")

        if isinstance(target, basestring):
            target = pathlib.Path(target)
        if isinstance(target, pathlib.Path):
            if not target.is_dir():
                raise IOError("target is not a directory")
            ignore = len(self.path) - len(self.name)
            for path in self.glob("**/*"):
                newpath = target.joinpath(str(path)[ignore:])
                if path.is_dir():
                    if not newpath.exists():
                        newpath.mkdir()
                else:
                    if newpath.exists():
                        raise IOError("file already exists: {}".format(newpath))
                    else:
                        newpath.touch()
                    with newpath.open('w') as f:
                        if sys.version_info.major > 2:
                            f.write("\n".join(path._content))
                        else:
                            f.write(unicode('\n'.join(path._content)))

        elif isinstance(target, MockPath):
            if not target.is_dir():
                raise IOError("target is not a directory")
            newpath = self.copy_path_obj()
            return target.add_child(newpath)
        else:
            raise ValueError("target is not str, pathlib.Path or MockPath: {}".format(target))

    def copy_from(self, source):
        """ copy from a source to a mock directory

        Parameters
        ----------
        source: str, file_obj, pathlib.Path or MockPath

        Returns
        -------

        """
        if not self.is_dir() or not self.exists():
            raise IOError("this path is not an existing directory")

        if isinstance(source, basestring):
            source = pathlib.Path(source)
            if not source.exists():
                raise IOError("source does not exist: {}".format(source))
        if isinstance(source, MockPath):
            if not source.exists():
                raise IOError("source does not exist: {}".format(source))
            else:
                newpath = source.copy_path_obj()
                self.add_child(newpath)
        elif isinstance(source, pathlib.Path):
            if not source.exists():
                raise IOError("source does not exist: {}".format(source))
            elif source.is_file():
                with source.open() as f:
                    content = f.read()
                newfile = MockPath(source.name, is_file=True, parent=self, content=content)
                self.add_child(newfile)
            else:
                raise NotImplementedError
        else:
            raise ValueError("source is not str, pathlib.Path or MockPath: {}".format(source))

    @contextlib.contextmanager
    def open(self, mode='r', encoding=None):
        """ context manager for opening a file

        Parameters
        ----------
        mode: str
        encoding: None or str

        Returns
        -------

        """
        if self.is_dir():
            raise IOError('[Errno 21] Is a directory: {}'.format(self.path))

        if 'r' in mode:
            obj = _OpenRead(self._content, encoding, "b" in mode)
            yield obj
        elif 'w' in mode:
            obj = _OpenWrite("b" in mode)
            yield obj
            self._content = obj._str.splitlines()
        else:
            raise ValueError('readwrite should contain r or w')

    def __gt__(self, other):
        if not hasattr(other, 'name'):
            return NotImplemented
        return self.path > other.path

    def __eq__(self, other):
        if not hasattr(other, 'name'):
            return NotImplemented
        return self.path == other.path

    def _recurse_print(self, obj, text='', indent=0, indentlvl=2, file_content=False):
        indent += indentlvl
        for subobj in sorted(obj):
            if not subobj.exists():
                continue
            if subobj.is_dir():
                text += ' ' * indent + '{0}("{1}")\n'.format(self._folderstr, subobj.name)
                text += self._recurse_print(subobj.iterdir(),
                                            indent=indent, file_content=file_content)
            else:
                if file_content:
                    sep = '\n' + ' ' * (indent + 1)
                    text += ' ' * indent + sep.join(
                        ['{0}("{1}") Contents:'.format(self._filestr, subobj.name)] + subobj._content) + '\n'
                else:
                    text += ' ' * indent + '{0}("{1}")\n'.format(self._filestr, subobj.name)

        return text

    def to_string(self, indentlvl=2, file_content=False, color=False):
        """convert to string """
        if color:
            self._folderstr = colortxt('Folder', 'green')
            self._filestr = colortxt('File', 'blue')
        else:
            self._folderstr = 'Folder'
            self._filestr = 'File'

        if self.is_file():
            return '\n'.join(['{0}("{1}") Contents:'.format(self._filestr, self.name)] + self._content)
        elif self.is_dir():
            text = '{0}("{1}")\n'.format(self._folderstr, self.name)
            text += self._recurse_print(self.iterdir(), indentlvl=indentlvl,
                                        file_content=file_content)

            text = text[0:-1] if text.endswith('\n') else text
            return text
        else:
            return 'MockPath({})'.format(self.name)

    def __str__(self):
        return self._path  # self.__repr__()

    def __repr__(self):
        if not self.exists():
            return 'MockVirtualPath("{}")'.format(self._path)
        elif self.is_dir():
            return 'MockFolder("{}")'.format(self._path)
        elif self.is_file():
            return 'MockFile("{}")'.format(self._path)
        else:
            return 'MockPath("{}")'.format(self._path)

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
