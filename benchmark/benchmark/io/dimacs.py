from typing import Generator

from pysmt.fnode import FNode
from pysmt.shortcuts import get_free_variables
from pysmt.typing import BOOL

from allsat_cnf.utils import is_cnf, get_clauses, get_literals, negate


def dimacs_var_map(formula: FNode) -> dict[FNode, int]:
    """Maps variables to DIMACS variable numbers."""
    variables = get_free_variables(formula)
    assert all(var.symbol_type() == BOOL for var in variables)
    return {var: i + 1 for i, var in enumerate(sorted(variables, key=str))}


def lit_to_dimacs(lit: FNode, var_map: dict[FNode, int]) -> str:
    assert lit.is_literal()
    if lit.is_not():
        return f"-{var_map[lit.arg(0)]}"
    else:
        return f"{var_map[lit]}"


def dimacs_to_lit(lit: str, var_map: dict[int, FNode]) -> FNode:
    if lit.startswith("-"):
        return negate(var_map[int(lit[1:])])
    else:
        return var_map[int(lit)]


def clause_to_dimacs(clause: FNode, var_map: dict[FNode, int]) -> str:
    return f"{' '.join(lit_to_dimacs(lit, var_map) for lit in get_literals(clause))} 0\n"


def pysmt_to_dimacs(formula: FNode, var_map: dict[FNode, int]) -> Generator[str, None, None]:
    """Converts a CNF formula to the DIMACS format.

    Yields lines of the DIMACS format.
    """
    assert is_cnf(formula)

    n_vars = len(var_map)

    clauses = get_clauses(formula)
    n_clauses = len(clauses)
    yield f"p cnf {n_vars} {n_clauses}\n"
    for clause in clauses:
        yield clause_to_dimacs(clause, var_map)
