#!/usr/bin/env python

import h5py


class HDF5_Parser(object):
    """

    Examples
    --------

    >>> import h5py
    >>> indata = h5py.File('test.hdf5')
    >>> dataset = indata.create_dataset("mydataset", (10,), dtype='i')
    >>> indata.close()

    >>> with open('test.hdf5') as f:
    ...     data = HDF5_Parser().read_file(f)
    >>> data['mydataset'][:]
    array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=int32)

    >>> import os
    >>> os.remove('test.hdf5')

    """

    plugin_name = 'hdf5.read'
    plugin_descript = 'read *.hdf5 (in read mode) files using h5py'
    file_regex = '*.hdf5'

    def read_file(self, file_obj, **kwargs):
        return h5py.File(file_obj.name, mode='r')
