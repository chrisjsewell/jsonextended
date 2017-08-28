#!/usr/bin/env python
"""mock files and folder structure for testing

Examples
--------
>>> jsonfile1
MockFile("dir1/file1.json")
>>> jsonfile2
MockFile("file2.json")
>>> csvfile1
MockFile("dir1/subdir1/file1.csv")
>>> csvfile2
MockFile("dir1/subdir1/file1.literal.csv")
>>> kpfile1
MockFile("dir1/subdir2/subsubdir21/file1.keypair")

>>> print(directory1.to_string(indentlvl=3,file_content=False))
Folder("dir1")
   File("file1.json")
   Folder("subdir1")
     File("file1.csv")
     File("file1.literal.csv")
   Folder("subdir2")
     Folder("subsubdir21")
       File("file1.keypair")

>>> print(directory1.to_string(indentlvl=3,file_content=True))
Folder("dir1")
   File("file1.json") Contents:
    {"key2": {"key3": 4, "key4": 5}, "key1": [1, 2, 3]}
   Folder("subdir1")
     File("file1.csv") Contents:
       # a csv file
      header1,header2,header3
      val1,val2,val3
      val4,val5,val6
      val7,val8,val9
     File("file1.literal.csv") Contents:
       # a csv file with numbers
      header1,header2,header3
      1,1.1,string1
      2,2.2,string2
      3,3.3,string3
   Folder("subdir2")
     Folder("subsubdir21")
       File("file1.keypair") Contents:
         # a key-pair file
        key1 val1
        key2 val2
        key3 val3
        key4 val4

"""

from jsonextended.utils import MockPath

jsonfile1 = MockPath('file1.json', is_file=True,
                     content='{"key2": {"key3": 4, "key4": 5}, "key1": [1, 2, 3]}')

jsonfile2 = MockPath('file2.json', is_file=True,
                     content='{"key1":{"_python_set_": [1, 2, 3]},"key2":{"_numpy_ndarray_": {"dtype": "int64", "value": [1, 2, 3]}}}')

csvfile1 = MockPath('file1.csv', is_file=True,
                    content=""" # a csv file
header1,header2,header3
val1,val2,val3
val4,val5,val6
val7,val8,val9
""")

csvfile2 = MockPath('file1.literal.csv', is_file=True,
                    content=""" # a csv file with numbers
header1,header2,header3
1,1.1,string1
2,2.2,string2
3,3.3,string3
""")

kpfile1 = MockPath('file1.keypair', is_file=True,
                   content=""" # a key-pair file
key1 val1
key2 val2
key3 val3
key4 val4
""")

directory1 = MockPath('dir1',
                      structure=[jsonfile1, {'subdir1': [csvfile1, csvfile2]},
                                 {'subdir2': [{'subsubdir21': [kpfile1]}]}]
                      )
