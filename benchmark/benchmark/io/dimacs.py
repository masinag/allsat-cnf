from typing import Generator

from pysmt.fnode import FNode
from pysmt.shortcuts import get_free_variables
from pysmt.typing import BOOL

from allsat_cnf.utils import is_cnf, get_clauses, get_literals


def dimacs_var_map(formula: FNode) -> dict[FNode, int]:
    """Maps variables to DIMACS variable numbers."""
    variables = get_free_variables(formula)
    assert all(var.symbol_type() == BOOL for var in variables)
    return {var: i + 1 for i, var in enumerate(sorted(variables, key=str))}


def _dimacs_lit(lit: FNode, var_map: dict[FNode, int]) -> str:
    assert lit.is_literal()
    if lit.is_not():
        return f"-{var_map[lit.arg(0)]}"
    else:
        return f"{var_map[lit]}"


def _dimacs_clause(clause: FNode, var_map: dict[FNode, int]) -> str:
    return f"{' '.join(_dimacs_lit(lit, var_map) for lit in get_literals(clause))} 0\n"


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
        yield _dimacs_clause(clause, var_map)
