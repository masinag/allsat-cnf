from pysmt.shortcuts import *

# initialize bool variables
boolean_variables = [Symbol(chr(i), BOOL)
                     for i in range(ord("A"), ord("Z") + 1)]
