import os, inspect
# python 2/3 compatibility
try:
    basestring
except NameError:
    basestring = str

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
    
    return dirpath

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

