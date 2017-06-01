
[![Build Status](https://travis-ci.org/chrisjsewell/jsonextended.svg?branch=master)](https://travis-ci.org/chrisjsewell/jsonextended)


# JSON Extended

A python module to extend the json package; treating path structures, with nested directories and multiple .json files, as a single json.

It provides:

- Functions for decoding/encoding between the on-disk JSON structure and in-memory nested dictionary structure, including

    - on-disk indexing of the json structure (using the ijson package)
    - extended data type serialisation (numpy.ndarray, Decimals, pint.Quantities) 

- Functions for viewing and manipulating the nested dictionaries

    - including Javascript rendered, expandable tree in the Jupyter Notebook

- Units schema concept to apply and convert physical units (using the pint package)

- Parser abstract class for dealing with converting other file formats to JSON


## Example

### Data Folders JSONisation


```python
import jsonextended as ejson

path = ejson.get_test_path()
ejson.json_keys(path)
```




    ['dir1', 'dir2', 'dir3']




```python
jdict1 = ejson.json_to_dict(path)
ejson.dict_pprint(jdict1,depth=2)
```

    dir1: 
      dir1_1: {...}
      file1: {...}
      file2: {...}
    dir2: 
      file1: {...}
    dir3: 



```python
ejson.dict_to_html(jdict1,depth=3)
```

To See Rendered JSON Output: https://chrisjsewell.github.io/

### Nested Dict Manipulation


```python
jdict2 = ejson.json_to_dict(path,['dir1','file1'])
ejson.dict_pprint(jdict2,depth=1)
```

    initial: {...}
    meta: {...}
    optimised: {...}
    units: {...}



```python
filtered = ejson.dict_filter_keys(jdict2,['vol*'],use_wildcards=True)
ejson.dict_pprint(filtered)
```

    initial: 
      crystallographic: 
        volume: 924.62752781
      primitive: 
        volume: 462.313764
    optimised: 
      crystallographic: 
        volume: 1063.98960509
      primitive: 
        volume: 531.994803



```python
ejson.dict_pprint(ejson.dict_flatten(filtered))
```

    ('initial', 'crystallographic', 'volume'):   924.62752781
    ('initial', 'primitive', 'volume'):          462.313764
    ('optimised', 'crystallographic', 'volume'): 1063.98960509
    ('optimised', 'primitive', 'volume'):        531.994803


### Units Schema


```python
from jsonextended.units import apply_unitschema, split_quantities
withunits = apply_unitschema(filtered,{'volume':'angstrom^3'})
ejson.dict_pprint(withunits)
```

    initial: 
      crystallographic: 
        volume: 924.62752781 Å ** 3
      primitive: 
        volume: 462.313764 Å ** 3
    optimised: 
      crystallographic: 
        volume: 1063.98960509 Å ** 3
      primitive: 
        volume: 531.994803 Å ** 3



```python
newunits = apply_unitschema(withunits,{'volume':'nm^3'})
ejson.dict_pprint(newunits)
```

    initial: 
      crystallographic: 
        volume: 0.92462752781 nm ** 3
      primitive: 
        volume: 0.462313764 nm ** 3
    optimised: 
      crystallographic: 
        volume: 1.06398960509 nm ** 3
      primitive: 
        volume: 0.531994803 nm ** 3



```python
ejson.dict_pprint(split_quantities(newunits),depth=4)
```

    initial: 
      crystallographic: 
        volume: 
          magnitude: 0.92462752781
          units:     nanometer ** 3
      primitive: 
        volume: 
          magnitude: 0.462313764
          units:     nanometer ** 3
    optimised: 
      crystallographic: 
        volume: 
          magnitude: 1.06398960509
          units:     nanometer ** 3
      primitive: 
        volume: 
          magnitude: 0.531994803
          units:     nanometer ** 3

