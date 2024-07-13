import itertools
import os.path
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from tempfile import TemporaryDirectory
from typing import TextIO, Iterable

from pysmt.fnode import FNode
from pysmt.operators import OR, AND, NOT, SYMBOL
from pysmt.shortcuts import TRUE, FALSE, get_env, And
from pysmt.walkers import handles, DagWalker

from allsat_cnf.utils import get_clauses
from .io.dimacs import pysmt_to_dimacs, dimacs_var_map, dimacs_to_lit

# Regular expressions for parsing d4 output
RE_NUM_VARS = re.compile(r"c Number of variables: (\d+)")
RE_NUM_CLAUSES = re.compile(r"c Number of clauses: (\d+)")
RE_PROJECTED_VARS = re.compile(r"c We are collected the projected variables ... (.+) ... done")
RE_MODEL_COUNT = re.compile(r"s (\d+)")

# Regular expressions for parsing d4 NNF file
# o <id> 0 : OR gate with index <id>
# a <id> 0 : AND gate with index <id> and variable <var>
# t <id> 0 : TRUE gate with index <id> and variable <var>
# f <id> 0 : FALSE gate with index <id> and variable <var>
RE_NNF_OR = re.compile(r"o (\d+) 0")
RE_NNF_AND = re.compile(r"a (\d+) 0")
RE_NNF_TRUE = re.compile(r"t (\d+) 0")
RE_NNF_FALSE = re.compile(r"f (\d+) 0")
# NNF edges: <number> <number> <possibly empty list of numbers separated by spaces> 0
RE_NNF_EDGE = re.compile(r"(\d+) (\d+)( .+)? 0")


def _write_dimacs(formula: FNode, var_map: dict[FNode, int], dimacs_file: TextIO):
    dimacs_file.writelines(pysmt_to_dimacs(formula, var_map))


def _write_projected_vars(projected_vars: Iterable[FNode], var_map: dict[FNode, int], projected_vars_file: TextIO):
    assert all(var in var_map for var in projected_vars), f"{projected_vars} not in {var_map}"
    projected_vars_file.write(",".join(str(var_map[var]) for var in projected_vars))
    projected_vars_file.write("\n")


@dataclass
class _D4Output:
    num_vars: int
    num_clauses: int
    projected_vars: int
    model_count: int


def _read_stdout(output_file: TextIO) -> _D4Output:
    output = _D4Output(0, 0, 0, 0)
    for line in output_file:
        if m := RE_NUM_VARS.match(line):
            output.num_vars = int(m.group(1))
        elif m := RE_NUM_CLAUSES.match(line):
            output.num_clauses = int(m.group(1))
        elif m := RE_PROJECTED_VARS.match(line):
            output.projected_vars = len(m.group(1).split())
        elif m := RE_MODEL_COUNT.match(line):
            output.model_count = int(m.group(1))
    return output


def _nnf_to_ddnnf(nnf_file: TextIO, var_map: dict[FNode, int]) -> FNode:
    # assume it is given as a DAG (bottom up)
    var_map_inv = {v: k for k, v in var_map.items()}
    node_types: dict[int, int] = {}
    nodes: dict[int, FNode] = {}
    graph: dict[int, list[FNode]] = defaultdict(list)
    root = None
    for line in nnf_file:
        if m := RE_NNF_OR.match(line):
            node_types[int(m.group(1))] = OR
        elif m := RE_NNF_AND.match(line):
            node_types[int(m.group(1))] = AND
        elif m := RE_NNF_TRUE.match(line):
            nodes[int(m.group(1))] = TRUE()
            assert isinstance(nodes[int(m.group(1))], FNode)
        elif m := RE_NNF_FALSE.match(line):
            nodes[int(m.group(1))] = FALSE()
            assert isinstance(nodes[int(m.group(1))], FNode)
        elif m := RE_NNF_EDGE.match(line):
            from_id = int(m.group(1))
            to_id = int(m.group(2))
            if to_id not in nodes:
                assert to_id in node_types
                nodes[to_id] = get_env().formula_manager.create_node(
                    node_type=node_types[to_id], args=tuple(graph[to_id])
                )
                assert isinstance(nodes[to_id], FNode)
            literals = []
            if m.group(3) is not None:
                literals = [dimacs_to_lit(lit, var_map_inv) for lit in m.group(3).split()]
            assert all(isinstance(lit, FNode) for lit in literals)
            assert isinstance(nodes[to_id], FNode)
            child = And(literals + [nodes[to_id]])
            graph[from_id].append(child)
            root = from_id
        else:
            raise ValueError(f"Invalid line: {line}")

    assert root is not None
    nodes[root] = get_env().formula_manager.create_node(node_type=node_types[root], args=tuple(graph[root]))
    return nodes[root]


class D4Interface:
    """Adapter for D4 model counter and d-DNNF compiler."""

    class MODE(Enum):
        MC = "-mc"
        DDNNF = "-dDNNF"

    def __init__(self, d4_bin: str):
        self.d4_bin = d4_bin

    def projected_model_count(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) -> int:
        output, ddnnf = self._invoke_d4(formula, projected_vars, self.MODE.MC, timeout)
        assert ddnnf is None

        return output.model_count

    def compile(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) -> tuple[int, FNode]:
        # TO CHECK: The given d-DNNF is not projected!
        output, ddnnf = self._invoke_d4(formula, projected_vars, self.MODE.DDNNF, timeout)
        assert ddnnf is not None

        return output.model_count, ddnnf

    def enumerate(self, formula: FNode, projected_vars: set[FNode]) -> tuple[tuple[FNode]]:
        """Enumerate true paths of a d-DNNF formula."""
        enumerator = DdnnfEnumerator(projected_vars)
        return enumerator.walk(formula)

    def count_true_paths(self, formula: FNode, projected_vars: set[FNode]) -> int:
        """Count true paths of a d-DNNF formula."""
        counter = DdnnfPathsCounter(projected_vars)
        return counter.walk(formula)

    def _invoke_d4(self, formula: FNode, projected_vars: set[FNode], mode: MODE,
                   timeout: int | None = None) -> tuple[_D4Output, FNode | None]:
        with TemporaryDirectory() as tmpdir:
            dimacs_file = os.path.join(tmpdir, "formula.cnf")
            projected_vars_file = os.path.join(tmpdir, "projected_vars.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            nnf_file = os.path.join(tmpdir, "formula.nnf")
            ddnnf = None

            var_map = dimacs_var_map(formula, projected_vars)
            with open(dimacs_file, "w") as f:
                _write_dimacs(formula, var_map, f)

            with open(projected_vars_file, "w") as f:
                _write_projected_vars(projected_vars, var_map, f)

            cmd_opts = [mode.value]
            cmd = [self.d4_bin, str(dimacs_file), f"-fpv={projected_vars_file}", f"-out={nnf_file}"] + cmd_opts
            with open(output_file, "w") as f:
                try:
                    subprocess.check_call(cmd, stdout=f, stderr=f, timeout=timeout)
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(f"d4 failed with exit code {e.returncode}") from e
                except subprocess.TimeoutExpired:
                    raise TimeoutError("d4 timed out")
            with open(output_file) as f:
                output = _read_stdout(f)

            if mode == self.MODE.DDNNF:
                with open(nnf_file, "r") as f:
                    ddnnf = _nnf_to_ddnnf(f, var_map)

        assert output.num_vars == (nv := len(var_map)), f"{output.num_vars} != {nv}"
        assert output.num_clauses == (cc := len(get_clauses(formula))), f"{output.num_clauses} != {cc}"
        assert output.projected_vars == (pv := len(projected_vars)), f"{output.projected_vars} != {pv}"

        return output, ddnnf


class DdnnfEnumerator(DagWalker):
    """
    Enumerate all true paths of a d-DNNF formula.
    """

    FALSE_MODEL = None
    NO_MODELS = (None,)
    TRUE_MODEL = ()

    def __init__(self, projected_vars: set[FNode]):
        super().__init__()
        self.projected_vars = projected_vars

    def walk_and(self, formula, args, **kwargs):
        ans = []
        if self.NO_MODELS in args:
            return self.NO_MODELS
        for model_set in itertools.product(*args):
            ans.append(tuple(itertools.chain(*model_set)))
        return tuple(ans)

    def walk_or(self, formula, args, **kwargs):
        ans = []
        for model_set in args:
            if model_set is not self.NO_MODELS:
                ans.extend(model_set)
        return tuple(ans)

    @handles(SYMBOL, NOT)
    def walk_literal(self, formula, **kwargs):
        var = formula.arg(0) if formula.is_not() else formula
        if var not in self.projected_vars:
            return (self.TRUE_MODEL,)
        assert var in self.projected_vars
        return ((formula,),)

    def walk_bool_constant(self, formula, **kwargs):
        if formula.is_true():
            return (self.TRUE_MODEL,)
        return (None,)


class DdnnfPathsCounter(DagWalker):
    """
    Count the number of true paths of a d-DNNF formula.
    """

    def __init__(self, projected_vars: set[FNode]):
        super().__init__()
        self.projected_vars = projected_vars

    def walk_and(self, formula, args, **kwargs):
        count = 1
        for n_paths in args:
            count *= n_paths

        return count

    def walk_or(self, formula, args, **kwargs):
        return sum(args)

    @handles(SYMBOL, NOT)
    def walk_literal(self, formula, **kwargs):
        return 1

    def walk_bool_constant(self, formula, **kwargs):
        if formula.is_true():
            return 1
        return 0
