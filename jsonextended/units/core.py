#!/usr/bin/env python
# -- coding: utf-8 --

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

from jsonextended import dict_flatten, dict_flatten2d, dict_unflatten, dicts_merge

def apply_unitschema(data, uschema, as_quantity=True,
                    raise_outerr=False, convert_base=False):
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
    # flatten dicts
    uschema_flat = dict_flatten(uschema,key_as_tuple=True)
    # sorted by longest key size, to get best match first
    uschema_keys = sorted(uschema_flat, key=len, reverse=True)
    data_flat = dict_flatten(data,key_as_tuple=True)

    for dkey, dvalue in data_flat.items():
        converted = False
        for ukey in uschema_keys:
            if ukey == dkey[-len(ukey):]:
                # handle the fact that it return an numpy object type if list of floats
                if isinstance(dvalue,(list,tuple)):
                    dvalue = np.array(dvalue)
                    if dvalue.dtype == np.object:
                        dvalue = dvalue.astype(float)
                        
                if isinstance(dvalue,_Quantity):
                    quantity = dvalue.to(uschema_flat[ukey])
                else:
                    quantity = ureg.Quantity(dvalue,uschema_flat[ukey])
                
                if convert_base:
                    quantity = quantity.to_base_units()
                                    
                if as_quantity:
                    data_flat[dkey] = quantity
                else:
                    data_flat[dkey] = quantity.magnitude
                break
        
        if not converted and raise_outerr:
            raise KeyError('could not find units for {}'.format(dkey))

    return dict_unflatten(data_flat)

def split_quantities(data,units='units',magnitude='magnitude'):
    """ split pint.Quantity objects into <unit,magnitude> pairs
    
    Parameters
    ----------
    data : dict
    units : str
        name for units key
    magnitude : str
        name for magnitude key
        
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
    data_flatten = dict_flatten(data)
    for key, val in data_flatten.items():
        if isinstance(val, _Quantity):
            data_flatten[key] = {units:str(val.units),
                                 magnitude:val.magnitude}
    return dict_unflatten(data_flatten)

def combine_quantities(data,units='units',magnitude='magnitude'):
    """ combine <unit,magnitude> pairs into pint.Quantity objects 

    Parameters
    ----------
    data : dict
    units : str
        name of units key
    magnitude : str
        name of magnitude key
        
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
    data_flatten2d = dict_flatten2d(data)
    new_dict = {}
    for key, val in list(data_flatten2d.items()):
        if units in val and magnitude in val:
            quantity = ureg.Quantity(val.pop(magnitude),val.pop(units))
            if not val:
                data_flatten2d.pop(key)
            new_dict[key] = quantity
    olddict = dict_unflatten(data_flatten2d)
    new_dict = dict_unflatten(new_dict)
    return dicts_merge([olddict,new_dict])

if __name__ == '__main__':
    import doctest
    print(doctest.testmod())
