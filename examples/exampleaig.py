import argparse

from local_tseitin.aig_cnfizer import GuardedAIG
from local_tseitin.utils import *

parser = argparse.ArgumentParser()
parser.add_argument("-v", help="increase output verbosity",
                        action="store_true")
parser.add_argument("-i", help="name of AIGER (AAG format) file", required=True)
args = parser.parse_args()

aig_file = args.i
encoder = GuardedAIG()
encoder_basic = GuardedAIG()
encoder_basic.basic_tseitin = True
if args.v:
    encoder.verbose = True
cnf, important_symbols = encoder.convert(aig_file)
cnf_basic, important_symbols_basic = encoder_basic.convert(aig_file)

cnf_models, count_part = get_allsat(cnf, use_ta=True, atoms=important_symbols)
cnf_models_basic, count_part_basic = get_allsat(cnf_basic, use_ta=True, atoms=important_symbols_basic)

print("CNFIZED MODELS (BASIC TSEITIN): {}".format(count_part_basic))
for assignment in cnf_models_basic:
    print(assignment)

print("***********************************")

print("CNFIZED MODELS: {}".format(count_part))
for assignment in cnf_models:
    print(assignment)


