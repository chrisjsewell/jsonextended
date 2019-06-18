Releases
---------

v0.7.0 - Improved edict.filter_keyvals and added edict.filter_keyfuncs 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- added "OR"/"AND" `logic` parameter 
- removed `errors` parameter from edict.filter_keyvals (instead use edict.filter_keyfuncs) 

v0.7.1 - added deep_copy option to edict functions 
++++++++++++++++++++++++++++++++++++++++++++++++++++
 

v0.7.2 - corrected filter_keyvals for dict_like siblings 
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
- added additional tests 

v0.7.3 -  added plugin class contextmanager 
+++++++++++++++++++++++++++++++++++++++++++++
 

v0.7.4 - added fraction.Fraction encoder plugin 
+++++++++++++++++++++++++++++++++++++++++++++++++
 

v0.7.6 - bug fix for mock path read context 
+++++++++++++++++++++++++++++++++++++++++++++
 

v0.7.7 - added allow_other_keys for plugin.decoders 
+++++++++++++++++++++++++++++++++++++++++++++++++++++
 

0.7.8 -  add sdist to pypi (required for conda-forge)  
++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 

v0.7.9 - add files required by setup.py to manifest (for sdist) 
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 

v0.6.0 - Improvements to LazyLoad 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- in `edict.LazyLoad` 
    - changed `ignore_prefixes` -> `ignore_regexes` for greater flexibility 
    - added logging (at debug level) for each file parsed (helpful for longer loading times) 
    - added better exception handling for file parsing (to help with debugging) 
- added `edict.dump` in order to better mirror standard `json` module (its exactly the same as `edict.to_json`) 
 
 
 

v0.6.1 - added remove_lkey to edict.apply and parse_errors to LazyLoad 
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 

v0.6.2 - added .yaml parser plugin 
++++++++++++++++++++++++++++++++++++
 

v0.6.3 - edict.remove_paths; allow list of path keys 
++++++++++++++++++++++++++++++++++++++++++++++++++++++
 

v0.6.4 - edict.merge added list_of_dicts option 
+++++++++++++++++++++++++++++++++++++++++++++++++
 

v0.5.0 - Major Improvements to MockPath 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
split off into separate package 
paths relative to base 
index 
handle maketemp of folder 

v0.5.1 - API Documentation update 
+++++++++++++++++++++++++++++++++++
 

v0.5.2 - Minor improvement 
++++++++++++++++++++++++++++
 

v0.5.3 - Minor Bug Fix 
++++++++++++++++++++++++
 

v0.5.4 - Minor improvement 
++++++++++++++++++++++++++++
- added byte decoding to mock path write class 

v0.5.5 - Minor improvements of MockPath 
+++++++++++++++++++++++++++++++++++++++++
added stat and chmod (dummy) methods 

v0.5.6 - Minor improvements of MockPath 
+++++++++++++++++++++++++++++++++++++++++
 

v0.5.7 - Reorder Documentation of Versions 
++++++++++++++++++++++++++++++++++++++++++++
 

v0.4.0 - Apply functions 
~~~~~~~~~~~~~~~~~~~~~~~~~~
- added apply and combine_apply functions 
- refactored edict to avoid deepcopy recursion (flatten, unflatten) 
 
 
 

v0.4.1 - General functionality improvement 
++++++++++++++++++++++++++++++++++++++++++++
-  added more support for list of dict structures 
- option to keep siblings when filtering by keyval 
- added wildcard option to remove_keys and value plus/minus error to filter_keyvals 
 
 
 
 
 
 
 
 
 
 

v0.4.2 - Added ReadTheDoc Site 
++++++++++++++++++++++++++++++++
 

v0.4.3 - minor bug fixes and improvements 
+++++++++++++++++++++++++++++++++++++++++++
 

v0.4.4 - Addition of Diff Evaluator 
+++++++++++++++++++++++++++++++++++++
`edict.diff`, which can optionally use numpy.allclose to assess arrays of floating point numbers 

v0.4.5 - Minor improvements 
+++++++++++++++++++++++++++++
 

v0.4.6 - Minor improvements of MockPath 
+++++++++++++++++++++++++++++++++++++++++
 

v0.3.7 - pprint improvements 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 improved pprint 
- treat items in list of dicts as heirarchical 
- compress_lists option 
- round_floats option 
 
Also added ipynb parser 

