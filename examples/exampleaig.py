from local_tseitin.aig_cnfizer import GuardedAIG
from local_tseitin.utils import *

aig_file = "circuit.aig" 
encoder = GuardedAIG()
cnf, important_symbols = encoder.convert(aig_file)

cnf_models, count_part = get_allsat(cnf, use_ta=True, atoms=important_symbols)
print("CNFIZED MODELS: {}".format(len(cnf_models)))
for assignment in cnf_models:
    print(assignment)


