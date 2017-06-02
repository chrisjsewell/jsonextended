def memory_usage():
    """return memory usage of python process in MB 
    
    >>> type(memory_usage())
    float
    
    """
    import resource, sys
    rusage_denom = 1024.
    if sys.platform == 'darwin':
        # ... it seems that in OSX the output is different units ...
        rusage_denom = rusage_denom * rusage_denom
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rusage_denom
    return mem
