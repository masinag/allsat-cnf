import os.path
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from tempfile import TemporaryDirectory
from typing import TextIO, Generator

import pysmt.operators as op
from pysmt.fnode import FNode
from pysmt.shortcuts import TRUE, FALSE, And, Or
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


def _make_node(node_type: int, children: list[FNode]) -> FNode:
    match node_type:
        case op.OR:
            if any(child.is_true() for child in children):
                return TRUE()
            new_children = [child for child in children if not child.is_false()]
            if len(new_children) == 0:
                return FALSE()
            if len(new_children) == 1:
                return new_children[0]
            return Or(new_children)
        case op.AND:
            if any(child.is_false() for child in children):
                return FALSE()
            new_children = [child for child in children if not child.is_true()]
            if len(new_children) == 0:
                return TRUE()
            if len(new_children) == 1:
                return new_children[0]
            return And(new_children)
        case _:
            raise ValueError(f"Invalid node type: {node_type}")


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
            node_types[node_id] = op.OR
        elif m := RE_NNF_AND.match(line):
            node_id = int(m.group(1))
            node_types[node_id] = op.AND
        elif m := RE_NNF_TRUE.match(line):
            node_id = int(m.group(1))
            nodes[node_id] = TRUE()
            root = node_id
        elif m := RE_NNF_FALSE.match(line):
            node_id = int(m.group(1))
            nodes[node_id] = FALSE()
            root = node_id
        elif m := RE_NNF_EDGE.match(line):
            parent_id = int(m.group(1))
            child_id = int(m.group(2))

            if child_id not in nodes:
                assert child_id in node_types
                nodes[child_id] = _make_node(node_types[child_id], graph[child_id])

            literals = []
            if m.group(3) is not None:
                literals = [dimacs_to_lit(lit, var_map_inv) for lit in m.group(3).split()]
                assert all(isinstance(lit, FNode) for lit in literals)

            assert not any(lit.is_false() or lit.is_true() for lit in literals)
            if nodes[child_id].is_false():
                graph[parent_id].append(FALSE())
            elif nodes[child_id].is_true():
                graph[parent_id].append(And(literals))
            else:
                graph[parent_id].append(And(nodes[child_id], *literals))
            root = parent_id
        else:
            raise ValueError(f"Invalid line: {line}")

    assert root is not None
    if root not in nodes:
        nodes[root] = _make_node(node_types[root], graph[root])
    return nodes[root]


class D4Interface:
    """Adapter for D4 model counter and d-DNNF compiler."""

    class MODE(Enum):
        COUNTING = "counting"
        PROJMC = "projMC"
        DDNNF = "dDNNF"

    def __init__(self, d4_bin: str):
        self.d4_bin = d4_bin

    def projected_model_count(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None,
                              mode: MODE = MODE.COUNTING) -> int:
        output, ddnnf = self._invoke_d4(formula, projected_vars, mode, timeout)
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

    def _enum_cross_product(self, args: list[FNode], projected_vars: set[FNode]) -> Generator[list[FNode], None, None]:
        # print("Cross product", args)
        stack = [(0, self.enumerate(args[0], projected_vars))]
        model = []

        while stack:
            # assert len(stack) == len(model) + 1, f"{len(stack)} {len(model)}"
            model_len, it = stack[-1]
            try:
                m = next(it)
            except StopIteration:
                # print("CP", args, "Popping", model)
                stack.pop()
                if model:
                    model = model[:model_len]
                continue
            model_len = len(model)
            model.extend(m)
            #             print("CP", args, "Model", model)
            if len(stack) == len(args):
                #                 print("CP", args, "Yielding", model)
                yield model
                model = model[:model_len]
            else:
                assert len(stack) < len(args), f"{model} {args}"
                stack.append((model_len, self.enumerate(args[len(stack)], projected_vars)))

    def enumerate(self, formula: FNode, projected_vars: set[FNode]) -> Generator[list[FNode], None, None]:
        """Return an iterator over true paths of a d-DNNF formula."""
        #         print("Enumerating", formula)
        assert not formula.is_true() and not formula.is_false()
        if is_literal(formula):
            var = formula.arg(0) if formula.is_not() else formula
            if var in projected_vars:
                yield [formula]
            else:
                yield []
        elif formula.is_or():
            for arg in formula.args():
                #                 print("OR:, enumerate", arg)
                yield from self.enumerate(arg, projected_vars)
        elif formula.is_and():
            # Cartesian product of all paths

            # pick one model from each argument
            yield from self._enum_cross_product(formula.args(), projected_vars)
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
            if mode == self.MODE.COUNTING:
                cmd += ["--method", "counting"]
            if mode == self.MODE.PROJMC:
                cmd += ["--method", "projMC"]

            with open(output_file, "w") as f:
                try:
                    subprocess.check_call(cmd, stdout=f, stderr=f, timeout=timeout)
                except subprocess.CalledProcessError as e:
                    with open(output_file) as fout:
                        out = fout.read()
                    raise RuntimeError(f"d4 failed with exit code {e.returncode}\n{out}") from e
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

    @handles(op.SYMBOL, op.NOT)
    def walk_literal(self, formula, **kwargs):
        return 1

    def walk_bool_constant(self, formula, **kwargs):
        if formula.is_true():
            return 1
        return 0
