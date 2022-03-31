from local_tseitin.utils import *
from pysmt.shortcuts import *

# initialize bool variables
for i in range(ord("A"), ord("Z") + 1):
    name = chr(i)
    a = Symbol(name, BOOL)
    globals()[name] = a
