import math
import re
from typing import Generator, TextIO

from pysmt.fnode import FNode
from pysmt.shortcuts import get_free_variables, And, Or, Symbol
from pysmt.typing import BOOL

from allsat_cnf.utils import is_cnf, get_clauses, get_literals, negate


def dimacs_var_map(formula: FNode, project_vars: set[FNode]) -> dict[FNode, int]:
    """Maps variables to DIMACS variable numbers."""
    variables = get_free_variables(formula) | project_vars
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


def dimacs_to_clause(clause: str, var_map: dict[int, FNode]) -> FNode:
    return Or(dimacs_to_lit(lit, var_map) for lit in clause.split()[:-1])


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


RE_HEADER = re.compile(r"p cnf (\d+) (\d+)")
RE_PROJECTION = re.compile(r"c p show (.+) 0")
RE_CLAUSE = re.compile(r"(-?\d+ )+0")


def dimacs_to_pysmt(dimacs_file: TextIO) -> tuple[FNode, set[FNode], dict[int, FNode]]:
    """Reads a exetenal CNF file in DIMACS format and returns a pysmt formula."""
    var_map = {}
    clauses = []
    projected_vars = set()

    ii = iter(dimacs_file)
    # read header
    for line in ii:
        m = RE_HEADER.match(line)
        if m is not None:
            n_vars, n_clauses = map(int, m.groups())
            break
    else:
        raise ValueError("Header not found")

    n_digits_dec = int(math.log10(n_vars) + 1)
    var_name_template = f"v{{:0{n_digits_dec}d}}"

    var_map = {i + 1: Symbol(var_name_template.format(i+1), BOOL) for i in range(n_vars)}

    # read projection
    for line in ii:
        m = RE_PROJECTION.match(line)
        if m is not None:
            projected_vars = {var_map[int(var)] for var in m.group(1).split()}
            break
    else:
        raise ValueError("Projection not found")

    # read clauses
    for line in ii:
        m = RE_CLAUSE.match(line)
        if m is None:
            continue
        clause = dimacs_to_clause(line, var_map)
        clauses.append(clause)
    assert len(clauses) == n_clauses, f"Expected {n_clauses} clauses, got {len(clauses)}"

    cnf = And(clauses)

    return cnf, projected_vars, var_map
