import itertools
from enum import Enum
from typing import Any, Collection, Generator, Iterable

import numpy as np
from allsat_cnf.utils import get_clauses, get_literals, is_cnf
from pysmt.fnode import FNode
from pysmt.formula import FormulaManager
from pysmt.shortcuts import get_env, get_free_variables
from pysmt.typing import BOOL


class HeaderMode(Enum):
    WITH_NUM_PROJECTED_VARS = 0
    ZERO_TERMINATED = 1


class CustomIndexArray:
    """
    A numpy array that supports custom indexing.
    """

    def __init__(self, arr: np.ndarray, start_index: int = 0):
        self._arr = arr
        self._start_index = start_index

    def _shift_slice(self, index: slice) -> slice:
        start = index.start - self._start_index if index.start is not None else None
        stop = index.stop - self._start_index if index.stop is not None else None
        step = index.step
        return slice(start, stop, step)

    def __getitem__(self, index: int | np.ndarray | slice) -> Any | np.ndarray:
        if isinstance(index, slice):
            return self._arr[self._shift_slice(index)]
        else:
            return self._arr[index - self._start_index]

    def __setitem__(self, index: int | np.ndarray | slice, value: Any | np.ndarray) -> None:
        if isinstance(index, slice):
            self._arr[self._shift_slice(index)] = value
        else:
            self._arr[index - self._start_index] = value

    def __len__(self) -> int:
        return len(self._arr)


class DimacsInterface:

    def __init__(self, environment=None, header_mode: HeaderMode = HeaderMode.ZERO_TERMINATED):
        self._env = environment or get_env()
        self._header_mode = header_mode
        self._int_to_lit: CustomIndexArray | None = None
        self._lit_to_int: dict[FNode, int] | None = None

    @property
    def mgr(self) -> FormulaManager:
        return self._env.formula_manager

    def _init_lit_map(self, variables: Collection[FNode]) -> None:
        self._int_to_lit = CustomIndexArray(np.empty((len(variables) + 1) * 2 + 1, dtype=object),
                                            start_index=-len(variables))
        # fill from 1 to n with sorted variables, and from -1 to -n with their negations
        sorted_vars = sorted(variables, key=str)
        not_fn = self.mgr.Not
        not_sorted_vars = [not_fn(var) for var in reversed(sorted_vars)]
        self._int_to_lit[1:len(variables) + 1] = sorted_vars
        self._int_to_lit[-len(variables):0] = not_sorted_vars
        self._lit_to_int = dict(itertools.chain(zip(not_sorted_vars, range(-len(variables), 0)),
                                                zip(sorted_vars, range(1, len(variables) + 1))))

    def pysmt_to_dimacs(self, formula: FNode, projected_vars: list[FNode]) -> Generator[str, None, None]:
        """Converts a CNF formula to the DIMACS format.
        Yields lines of the DIMACS format.
        """
        assert is_cnf(formula)
        variables = get_free_variables(formula) | set(projected_vars)
        assert all(var.symbol_type() == BOOL for var in variables)

        self._init_lit_map(variables)

        n_vars = len(self._lit_to_int) // 2
        clauses = get_clauses(formula)
        n_clauses = len(clauses)

        pv = [self._lit_to_int[var] for var in projected_vars]
        match self._header_mode:
            case HeaderMode.WITH_NUM_PROJECTED_VARS:
                yield f"p cnf {n_vars} {n_clauses} {len(pv)}\n"
                yield f"c p show {' '.join(map(str, pv))}\n"
            case HeaderMode.ZERO_TERMINATED:
                yield f"p cnf {n_vars} {n_clauses}\n"
                yield f"c p show {' '.join(map(str, pv))} 0\n"
        yield from map(self._clause_to_str, clauses)

    def _clause_to_str(self, clause: FNode) -> str:
        return "{} 0\n".format(' '.join(str(self._lit_to_int[lit]) for lit in get_literals(clause)))

    def int_list_to_model(self, int_list: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Converts a list of integers to a model over FNodes."""
        vars_ = self._int_to_lit[abs(int_list)]
        vals = int_list > 0
        return vars_, vals

    def lits_to_int_list(self, lits: list[FNode]) -> list[int]:
        return [self._lit_to_int[lit] for lit in lits]


    def dimacs_to_pysmt(self, dimacs_file: Iterable[str]) -> tuple[FNode, list[FNode]]:
        """Reads a exetenal CNF file in DIMACS format and returns a pysmt formula."""
        clauses = []
        ii = iter(dimacs_file)
        for line in ii:
            if line.startswith('p cnf'):
                parts = line.split()
                n_vars, n_clauses = int(parts[2]), int(parts[3])
                break
        else:
            raise ValueError("Header not found")
        n_digits_dec = int(np.log10(n_vars) + 1)
        var_name_template = f"v{{:0{n_digits_dec}d}}"
        variables = [self.mgr.Symbol(var_name_template.format(i + 1), BOOL) for i in range(n_vars)]

        self._init_lit_map(variables)

        projected_vars = []
        for line in ii:
            if line.startswith('c p show'):
                parts = line.split()
                match self._header_mode:
                    case HeaderMode.WITH_NUM_PROJECTED_VARS:
                        projected_vars = [self._int_to_lit[int(var)] for var in parts[4:]]
                    case HeaderMode.ZERO_TERMINATED:
                        projected_vars = [self._int_to_lit[int(var)] for var in parts[3:-1]]
                    case _:
                        raise ValueError("Unknown header mode")
                break
            else:
                raise ValueError("Projection not found")

        for line in ii:
            if line.startswith('c') or line.startswith('p'):
                continue
            parts = line.split()
            if parts and parts[-1] == '0':
                clause = self._dimacs_to_clause(line)
                clauses.append(clause)

        assert len(clauses) == n_clauses, f"Expected {n_clauses} clauses, got {len(clauses)}"
        cnf = self.mgr.And(clauses)

        return cnf, projected_vars

    def _dimacs_to_clause(self, clause: str) -> FNode:
        return self.mgr.Or(self._int_to_lit[int(lit)] for lit in clause.split()[:-1])
