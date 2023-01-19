import random

import pandas as pd
from pysmt.fnode import FNode
from pysmt.rewritings import PolarityCNFizer, nnf
from pysmt.shortcuts import *

from benchmark.random.generate_bool import random_formula
from example_template import (A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P,
                              Q, R, S, T, U, V, W, X, Y, Z, make_example)
from local_tseitin.conds_cnfizer import LocalTseitinCNFizerConds
from local_tseitin.utils import get_allsat


def count_models(phis):
    data = []
    options = {}
    for phi in phis:
        atoms = get_atoms(phi)

        # print("Pleisted CNF")
        psi = PolarityCNFizer().convert_as_formula(phi)
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append({"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "POL"})
        # print(f"\t{len(models)}/{count} models")

        # print("NNF + Pleisted CNF")
        psi = PolarityCNFizer().convert_as_formula(nnf(phi))
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append({"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "NNF_POL"})
        # print(f"\t{len(models)}/{count} models")

        # print("Guarded CNF")
        psi = LocalTseitinCNFizerConds().convert_as_formula(phi)
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append({"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "CND"})
        # print(f"\t{len(models)}/{count} models")

        # print("NNF + Guarded CNF")
        psi = LocalTseitinCNFizerConds().convert_as_formula(nnf(phi))
        models, count = get_allsat(psi, atoms=atoms, use_ta=True, options=options)
        data.append({"phi": phi, "phi_id": phi.node_id(), "count": count, "n_models": len(models), "type": "NNF_CND"})
        # print(f"\t{len(models)}/{count} models")
    return data


def main():
    # set random seed
    seed = 0
    random.seed(seed)
    atoms = [A, B, C, D, E, F]
    phis = [
        # Iff((A & B) | C, D | (E & F)),
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
        random_formula(5, atoms) for _ in range(50)
    ]
    data = count_models(phis)
    # create a dataframe with formulas on the rows and the columns are the different types
    df = pd.DataFrame(data)
    df = df.pivot(index="phi", columns="type", values="n_models")
    print(df)


if __name__ == "__main__":
    main()

#
