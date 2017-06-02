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
    mem = process.get_memory_info()[0] / float(2 ** 20)
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
