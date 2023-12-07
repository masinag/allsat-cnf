from pprint import pprint

import aiger
from pysmt.shortcuts import And, Or, Not, Symbol

from allsat_cnf.aig_adapter import AIGAdapter
from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from allsat_cnf.utils import get_allsat, check_models, SolverOptions

atm = aiger.atom
aig = (atm('a1') & atm('a2')) | (((atm('a3') | atm('a4')) & (atm('a5') | atm('a6'))) == atm('a7'))
phi = AIGAdapter.from_boolexpr(aig).to_pysmt()

solver_options_tta = SolverOptions(with_repetitions=False, use_ta=False)
tta, mc = get_allsat(phi, phi.get_atoms(), solver_options=solver_options_tta)
# print(tta)

atoms = {atom.symbol_name(): atom for atom in phi.get_atoms()}

a1, a2, a3, a4, a5, a6, a7 = (atoms[name] for name in ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7'])
b1, b2, b3, b4, b5, b6p, b6n, b7p, b7n, b8p, b8n = [Symbol(name) for name in
                                                    ['b1', 'b2', 'b3', 'b4', 'b5', 'b6p', 'b6n', 'b7p', 'b7n', 'b8p',
                                                     'b8n']]

phi_nnfpg = And(
    Or(b2, b3),
    Or(Not(b2), a1), Or(Not(b2), a2),
    Or(Not(b3), b4, b5),
    Or(Not(b4), b6n), Or(Not(b4), Not(a7)),
    Or(Not(b5), a7), Or(Not(b5), b6p),
    Or(Not(b6p), b7p), Or(Not(b6p), b8p),
    Or(Not(b7p), a5, a6),
    Or(Not(b8p), a3, a4),
    Or(Not(b6n), b7n, b8n),
    Or(Not(b7n), Not(a5)), Or(Not(b7n), Not(a6)),
    Or(Not(b8n), Not(a3)), Or(Not(b8n), Not(a4)),
)

phi_nnfpg1 = PolarityCNFizer(nnf=True, mutex_nnf_labels=False).convert_as_formula(phi)

print(phi_nnfpg.serialize())
print(phi_nnfpg1.serialize())

solver_options_ta = SolverOptions(with_repetitions=False, use_ta=True)
ta_nnfpg, mc_nnfpg = get_allsat(phi_nnfpg, phi.get_atoms(), solver_options=solver_options_ta)

check_models(ta_nnfpg, phi)
# print(tta)
# print(ta_nnfpg)
assert mc == mc_nnfpg, "Models are different: {} vs {}".format(mc, mc_nnfpg)

phi_nnf_dup = And(
    Or(b2, Not(b3)),
    Or(Not(b2), a1), Or(Not(b2), a2),
    Or(b4, b5, b3),
    Or(Not(b5), a7), Or(Not(b5), b6p),
    Or(Not(b4), Not(b6n)), Or(Not(b4), Not(a7)),
    Or(Not(b6p), Not(b7n)), Or(Not(b6p), Not(b8n)),
    Or(b7p, b8p, b6n),
    Or(Not(b7p), Not(a5)), Or(Not(b7p), Not(a6)),
    Or(Not(b8p), Not(a3)), Or(Not(b8p), Not(a4)),
    Or(a5, a6, b7n),
    Or(a3, a4, b8n),
)
pprint(ta_nnfpg)

ta_nnf_dup, mc_nnf_dup = get_allsat(phi_nnf_dup, phi.get_atoms(), solver_options=solver_options_ta)

print()

pprint(ta_nnf_dup)

check_models(ta_nnf_dup, phi)
assert mc == mc_nnf_dup, "Models are different: {} vs {}".format(mc, mc_nnf_dup)
