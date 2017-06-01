
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
ejson.dict_to_html(jdict2,depth=2)
```

    <head>
        <meta charset="UTF-8">
<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
		<title>Example JSON JavaScript Representation</title>

    </head>
    
    <body>
		
	<div id="content"></div>	
		
<style type="text/css">
    .renderjson a              { text-decoration: none; }
    .renderjson .disclosure    { color: red;
                                 font-size: 125%; }
    .renderjson .syntax        { color: darkgrey; }
    .renderjson .string        { color: black; }
    .renderjson .number        { color: black; }
    .renderjson .boolean       { color: purple; }
    .renderjson .key           { color: royalblue; }
    .renderjson .keyword       { color: orange; }
    .renderjson .object.syntax { color: lightseagreen; }
    .renderjson .array.syntax  { color: lightseagreen; }
    </style><div id="37e54692-0cc1-469a-bd9f-911c498fb526" style="max-height: 600px; width:100%%;"></div>
                <script >
            require(["https://rawgit.com/caldwell/renderjson/master/renderjson.js"], function() {
                document.getElementById("37e54692-0cc1-469a-bd9f-911c498fb526").appendChild(
                    renderjson.set_max_string_length(20)
                              //.set_icons(circled plus, circled minus)
                              .set_icons(String.fromCharCode(8853), String.fromCharCode(8854))
                              .set_sort_objects(true)
					.set_show_to_level(2)(


						{'a':1,'b':2}
					
					
					))
            });</script>

		
    </body>

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

