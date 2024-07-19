import itertools
import os.path
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from tempfile import TemporaryDirectory
from typing import TextIO, Generator

from pysmt.fnode import FNode
from pysmt.operators import OR, AND, NOT, SYMBOL
from pysmt.shortcuts import TRUE, FALSE, get_env, And
from pysmt.walkers import handles, DagWalker

from allsat_cnf.utils import get_clauses, is_literal
from .io.dimacs import pysmt_to_dimacs, dimacs_var_map, dimacs_to_lit

# Regular expressions for parsing d4 output
RE_NUM_VARS = re.compile(r"c \[INITIAL INPUT\] Number of variables: (\d+)")
RE_NUM_CLAUSES = re.compile(r"c \[INITIAL INPUT\] Number of clauses: (\d+)")
RE_PROJECTED_VARS = re.compile(r"c \[PROJECTED VARIABLES\] list: (.+)")
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
            node_id = int(m.group(1))
            node_types[node_id] = OR
        elif m := RE_NNF_AND.match(line):
            node_id = int(m.group(1))
            node_types[node_id] = AND
        elif m := RE_NNF_TRUE.match(line):
            node_id = int(m.group(1))
            nodes[node_id] = TRUE()
            root = node_id
        elif m := RE_NNF_FALSE.match(line):
            node_id = int(m.group(1))
            nodes[node_id] = FALSE()
            root = node_id
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
    if root not in nodes:
        nodes[root] = get_env().formula_manager.create_node(node_type=node_types[root], args=tuple(graph[root]))
    return nodes[root]


class D4Interface:
    """Adapter for D4 model counter and d-DNNF compiler."""

    class MODE(Enum):
        MC = "mc"
        DDNNF = "dDNNF"

    def __init__(self, d4_bin: str):
        self.d4_bin = d4_bin

    def projected_model_count(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) -> int:
        output, ddnnf = self._invoke_d4(formula, projected_vars, self.MODE.MC, timeout)
        assert ddnnf is None

        return output.model_count

    def compile(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) -> FNode:
        output, ddnnf = self._invoke_d4(formula, projected_vars, self.MODE.DDNNF, timeout)
        assert ddnnf is not None

        return ddnnf

    def count_true_paths(self, formula: FNode) -> int:
        """Count true paths of a d-DNNF formula."""
        counter = DdnnfPathsCounter()
        return counter.walk(formula)

    def enumerate(self, formula: FNode, projected_vars: set[FNode]) -> Generator[list[FNode], None, None]:
        """Return an iterator over true paths of a d-DNNF formula."""
        if formula.is_true():
            yield []
        elif formula.is_false():
            yield None
        elif is_literal(formula):
            var = formula.arg(0) if formula.is_not() else formula
            if var in projected_vars:
                yield [formula]
            else:
                yield []
        elif formula.is_or():
            for arg in formula.args():
                for model in self.enumerate(arg, projected_vars):
                    if model is not None:
                        yield model
        elif formula.is_and():
            # Cartesian product of all paths
            args_models = [self.enumerate(arg, projected_vars) for arg in formula.args()]

            # pick one model from each argument
            for models in itertools.product(*args_models):
                if any(model is None for model in models):
                    yield None
                else:
                    yield list(itertools.chain(*models))
        else:
            raise ValueError(f"Invalid formula: {formula}")

    def _invoke_d4(self, formula: FNode, projected_vars: set[FNode], mode: MODE,
                   timeout: int | None = None) -> tuple[_D4Output, FNode | None]:
        with TemporaryDirectory() as tmpdir:
            dimacs_file = os.path.join(tmpdir, "formula.cnf")
            output_file = os.path.join(tmpdir, "output.txt")
            nnf_file = os.path.join(tmpdir, "formula.nnf")
            ddnnf = None

            var_map = dimacs_var_map(formula, projected_vars)
            with open(dimacs_file, "w") as f:
                f.writelines(pysmt_to_dimacs(formula, projected_vars, var_map))

            cmd = [self.d4_bin, "-i", str(dimacs_file)]
            if mode == self.MODE.DDNNF:
                cmd += ["--method", "ddnnf-compiler", "--dump-ddnnf", nnf_file]
            if mode == self.MODE.MC:
                cmd += ["--method", "counting"]

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


class DdnnfPathsCounter(DagWalker):
    """
    Count the number of true paths of a d-DNNF formula.
    """

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
