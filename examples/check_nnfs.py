import random
from pprint import pprint

import pandas as pd
from pysmt.rewritings import nnf
from pysmt.shortcuts import *

from example_template import (boolean_atoms)
from local_tseitin.cnfizer import Preprocessor
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.polarity_cnfizer import PolarityCNFizer
from local_tseitin.utils import get_allsat

A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z = boolean_atoms


def count_models(phis):
    data = []
    options = {"dpll.branching_initial_phase": "0"}
    for phi in phis:
        atoms = get_atoms(phi)

        models, count = get_allsat(phi, use_ta=True, atoms=atoms, options=options)
        data.append({"phi": phi, "phi_id": phi.node_id(), "type": "1.MathSAT(Tseitin)", "n_models": count})

        # print("Pleisted CNF")

        psi = PolarityCNFizer().convert_as_formula(phi)
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append({"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "2.POL"})
        # pprint(models)
        # print("NNF + Pleisted CNF")

        psi = PolarityCNFizer().convert_as_formula(nnf(phi))
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append(
            {"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "3.NNF_POL"})
        # print(f"\t{len(models)}/{count} models")
        # pprint(models)

        # print("############## Guarded CNF")
        psi = LocalTseitinCNFizerConds().convert_as_formula(phi)
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append({"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "4.CND"})
        # pprint(models)

        # print("############## Guarded CNF (EXPAND IFF)")
        psi = Preprocessor(expand_iff=True).convert_as_formula(phi)
        psi = LocalTseitinCNFizerConds(verbose=False).convert_as_formula(psi)
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append(
            {"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "4a.CND+EXP"})
        # pprint(models)

        # print("NNF + Guarded CNF")
        psi = LocalTseitinCNFizerConds().convert_as_formula(nnf(phi))
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append(
            {"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "5.NNF_CND"})
        # pprint(models)

        # print("Shared CNF")
        # psi = LocalTseitinCNFizerShared().convert_as_formula(phi)
        # models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        # data.append({"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "6.SHARED"})
        # print(psi.serialize())
        # # print(f"\t{len(models)}/{count} models")
        # pprint(models)
    return data


def main():
    # set random seed
    seed = 0
    random.seed(seed)
    phis = [
        Or(Iff(C, And(Or(D, E), Or(F, G))), And(A, B))
        # Iff((A & B) | C, D | (E & F)),
        # Iff((A & B) | C, (D & E) | F),
        # Iff((A & B) | (C & D), (E & F) | (G & H)),
        # Iff((A | B) & (C | D), (E | F) & (G | H)),
        # Iff((A & B) | (C & D), (~A & C) | (B & ~D)),
        # Iff((A & B) | (C & D), (~A & ~C) | (~B & ~D)),
        # Iff((A & B) | (C & D), (~A & ~C) | (B & D)),
        # Iff((A & B) | (C & D), (~A & C) | (~B & D)),
        # (A & B) | (C & D),
        # (A & B) | (C & D) | (E & F),
        # (A & B) | (C & D) | (E & F) | (G & H),
        # (A & B) | (C & D) | (E & F) | (G & H) | (I & J),
        # (A & B) | (C & D) | (E & F) | (G & H) | (I & J) | (K & L),
        # random_formula(5, atoms) for _ in range(50)
        # ((A & B) | C) & Or((A & B), D)
    ]
    data = count_models(phis)
    # create a dataframe with formulas on the rows and the columns are the different types
    df = pd.DataFrame(data)
    df = df.pivot(index="phi_id", columns="type", values="n_models")
    print(df[["1.MathSAT(Tseitin)", "2.POL", "3.NNF_POL", "4.CND", "4a.CND+EXP", "5.NNF_CND"]])

    for phi in sorted(phis, key=lambda x: x.node_id()):
        print(f"{phi.node_id():3} {phi.serialize()}")


if __name__ == "__main__":
    main()

#
