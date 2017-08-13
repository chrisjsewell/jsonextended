#!/usr/bin/env python
# -- coding: utf-8 --

from fnmatch import fnmatch

# make units optional when importing jsonextended
try:
    import numpy as np
except ImportError:
    pass

try:
    from pint import UnitRegistry

    ureg = UnitRegistry()
    from pint.quantity import _Quantity
except ImportError:
    pass

from jsonextended.edict import flatten, flatten2d, unflatten, merge


def get_in_units(value, units):
    """get a value in the required units """
    try:
        return ureg.Quantity(value, units)
    except NameError:
        raise ImportError('please install pint to use this module')


def apply_unitschema(data, uschema, as_quantity=True,
                     raise_outerr=False, convert_base=False,
                     use_wildcards=False, list_of_dicts=False):
    """ apply the unit schema to the data

    Parameters
    ----------
    data : dict
    uschema : dict
        units schema to apply
    as_quantity : bool
        if true, return values as pint.Quantity objects
    raise_outerr : bool
        raise error if a unit cannot be found in the outschema
    convert_to_base : bool
        rescale units to base units
    use_wildcards : bool
        if true, can use * (matches everything) and ? (matches any single character)
    list_of_dicts: bool
        treat list of dicts as additional branches

    Examples
    --------
    >>> from pprint import pprint

    >>> data = {'energy':1,'x':[1,2],'other':{'y':[4,5]},'y':[4,5],'meta':None}
    >>> uschema =   {'energy':'eV','x':'nm','other':{'y':'m'},'y':'cm'}
    >>> data_units = apply_unitschema(data,uschema)
    >>> pprint(data_units)
    {'energy': <Quantity(1, 'electron_volt')>,
     'meta': None,
     'other': {'y': <Quantity([4 5], 'meter')>},
     'x': <Quantity([1 2], 'nanometer')>,
     'y': <Quantity([4 5], 'centimeter')>}

    >>> newschema = {'energy':'kJ','other':{'y':'nm'},'y':'m'}
    >>> new_data = apply_unitschema(data_units,newschema)
    >>> pprint(new_data)
    {'energy': <Quantity(1.60217653e-22, 'kilojoule')>,
     'meta': None,
     'other': {'y': <Quantity([  4.00000000e+09   5.00000000e+09], 'nanometer')>},
     'x': <Quantity([1 2], 'nanometer')>,
     'y': <Quantity([ 0.04  0.05], 'meter')>}

    >>> old_data = apply_unitschema(new_data,uschema,as_quantity=False)
    >>> pprint(old_data)
    {'energy': 1.0,
     'meta': None,
     'other': {'y': array([ 4.,  5.])},
     'x': array([1, 2]),
     'y': array([ 4.,  5.])}

    """
    try:
        _Quantity
    except NameError:
        raise ImportError('please install pint to use this module')
    list_of_dicts = '__list__' if list_of_dicts else None

    # flatten edict
    uschema_flat = flatten(uschema, key_as_tuple=True)
    # sorted by longest key size, to get best match first
    uschema_keys = sorted(uschema_flat, key=len, reverse=True)
    data_flat = flatten(data, key_as_tuple=True, list_of_dicts=list_of_dicts)

    for dkey, dvalue in data_flat.items():
        converted = False
        for ukey in uschema_keys:

            if not len(ukey) == len(dkey[-len(ukey):]):
                continue

            if use_wildcards:
                match = all([fnmatch(d, u) for u, d in zip(ukey, dkey[-len(ukey):])])
            else:
                match = ukey == dkey[-len(ukey):]

            if match:
                # handle the fact that it return an numpy object type if list of floats
                if isinstance(dvalue, (list, tuple)):
                    dvalue = np.array(dvalue)
                    if dvalue.dtype == np.object:
                        dvalue = dvalue.astype(float)

                if isinstance(dvalue, _Quantity):
                    quantity = dvalue.to(uschema_flat[ukey])
                else:
                    quantity = ureg.Quantity(dvalue, uschema_flat[ukey])

                if convert_base:
                    quantity = quantity.to_base_units()

                if as_quantity:
                    data_flat[dkey] = quantity
                else:
                    data_flat[dkey] = quantity.magnitude
                break

        if not converted and raise_outerr:
            raise KeyError('could not find units for {}'.format(dkey))

    return unflatten(data_flat, list_of_dicts=list_of_dicts)


def split_quantities(data, units='units', magnitude='magnitude',
                     list_of_dicts=False):
    """ split pint.Quantity objects into <unit,magnitude> pairs

    Parameters
    ----------
    data : dict
    units : str
        name for units key
    magnitude : str
        name for magnitude key
    list_of_dicts: bool
        treat list of dicts as additional branches

    Examples
    --------
    >>> from pprint import pprint

    >>> from pint import UnitRegistry
    >>> ureg = UnitRegistry()
    >>> Q = ureg.Quantity

    >>> qdata = {'energy': Q(1.602e-22, 'kilojoule'),
    ...          'meta': None,
    ...          'other': {'y': Q([4,5,6], 'nanometer')},
    ...          'x': Q([1,2,3], 'nanometer'),
    ...          'y': Q([8,9,10], 'meter')}
    ...
    >>> split_data = split_quantities(qdata)
    >>> pprint(split_data)
    {'energy': {'magnitude': 1.602e-22, 'units': 'kilojoule'},
     'meta': None,
     'other': {'y': {'magnitude': array([4, 5, 6]), 'units': 'nanometer'}},
     'x': {'magnitude': array([1, 2, 3]), 'units': 'nanometer'},
     'y': {'magnitude': array([ 8,  9, 10]), 'units': 'meter'}}

    """
    try:
        _Quantity
    except NameError:
        raise ImportError('please install pint to use this module')
    list_of_dicts = '__list__' if list_of_dicts else None
    data_flatten = flatten(data, list_of_dicts=list_of_dicts)
    for key, val in data_flatten.items():
        if isinstance(val, _Quantity):
            data_flatten[key] = {units: str(val.units),
                                 magnitude: val.magnitude}
    return unflatten(data_flatten, list_of_dicts=list_of_dicts)


def combine_quantities(data, units='units', magnitude='magnitude',
                       list_of_dicts=False):
    """ combine <unit,magnitude> pairs into pint.Quantity objects

    Parameters
    ----------
    data : dict
    units : str
        name of units key
    magnitude : str
        name of magnitude key
    list_of_dicts: bool
        treat list of dicts as additional branches

    Examples
    --------
    >>> from pprint import pprint

    >>> sdata = {'energy': {'magnitude': 1.602e-22, 'units': 'kilojoule'},
    ...          'meta': None,
    ...          'other': {'y': {'magnitude': [4, 5, 6], 'units': 'nanometer'}},
    ...          'x': {'magnitude': [1, 2, 3], 'units': 'nanometer'},
    ...          'y': {'magnitude': [8,9,10], 'units': 'meter'}}
    ...
    >>> combined_data = combine_quantities(sdata)
    >>> pprint(combined_data)
    {'energy': <Quantity(1.602e-22, 'kilojoule')>,
     'meta': None,
     'other': {'y': <Quantity([4 5 6], 'nanometer')>},
     'x': <Quantity([1 2 3], 'nanometer')>,
     'y': <Quantity([ 8  9 10], 'meter')>}

    """
    try:
        _Quantity
    except NameError:
        raise ImportError('please install pint to use this module')
    list_of_dicts = '__list__' if list_of_dicts else None

    data_flatten2d = flatten2d(data, list_of_dicts=list_of_dicts)
    new_dict = {}
    for key, val in list(data_flatten2d.items()):
        if units in val and magnitude in val:
            quantity = ureg.Quantity(val.pop(magnitude), val.pop(units))
            if not val:
                data_flatten2d.pop(key)
            new_dict[key] = quantity
    final_dict = merge([data_flatten2d, new_dict])
    # olddict = unflatten(data_flatten2d,list_of_dicts=list_of_dicts)
    # new_dict = unflatten(new_dict,list_of_dicts=list_of_dicts)
    return unflatten(final_dict, list_of_dicts=list_of_dicts)  # merge([olddict,new_dict])


if __name__ == '__main__':
    import doctest

    print(doctest.testmod())
