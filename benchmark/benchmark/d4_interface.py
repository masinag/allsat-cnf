import os.path
import re
import subprocess
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import TextIO, Iterable

from pysmt.fnode import FNode

from allsat_cnf.utils import get_clauses
from .io.dimacs import pysmt_to_dimacs, dimacs_var_map

# c Number of variables: 3
# c Number of clauses: 1
# c We are collected the projected variables ... 1 2 ... done
# c Final time: 0.000138
RE_NUM_VARS = re.compile(r"c Number of variables: (\d+)")
RE_NUM_CLAUSES = re.compile(r"c Number of clauses: (\d+)")
# capture the list of projected variables separated by spaces
RE_PROJECTED_VARS = re.compile(r"c We are collected the projected variables ... (.+) ... done")
RE_MODEL_COUNT = re.compile(r"s (\d+)")


def _write_dimacs(formula: FNode, var_map: dict[FNode, int], dimacs_file: TextIO):
    dimacs_file.writelines(pysmt_to_dimacs(formula, var_map))


def _write_projected_vars(projected_vars: Iterable[FNode], var_map: dict[FNode, int], projected_vars_file: TextIO):
    assert all(var in var_map for var in projected_vars)
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


class D4Interface:
    """Adapter for D4 model counter and d-DNNF compiler."""

    def __init__(self, d4_bin: str):
        self.d4_bin = d4_bin

    def projected_model_count(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) -> int:
        # create temporary files for dimacs, projected variables, and output
        with TemporaryDirectory() as tmpdir:
            dimacs_file = os.path.join(tmpdir, "formula.cnf")
            projected_vars_file = os.path.join(tmpdir, "projected_vars.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            var_map = dimacs_var_map(formula)
            with open(dimacs_file, "w") as f:
                _write_dimacs(formula, var_map, f)

            with open(projected_vars_file, "w") as f:
                _write_projected_vars(projected_vars, var_map, f)

            # run d4 with the temporary files with timeout
            cmd = [self.d4_bin, str(dimacs_file), "-mc", f"-fpv={projected_vars_file}"]
            with open(output_file, "w") as f:
                subprocess.check_call(cmd, stdout=f, stderr=f, timeout=timeout)
            with open(output_file) as f:
                output = _read_stdout(f)

        assert output.num_vars == (nv := len(var_map)), f"{output.num_vars} != {nv}"
        assert output.num_clauses == (cc := len(get_clauses(formula))), f"{output.num_clauses} != {cc}"
        assert output.projected_vars == (pv := len(projected_vars)), f"{output.projected_vars} != {pv}"
        return output.model_count

    def compile(self, formula: FNode, **kwargs) -> FNode:
        raise NotImplementedError()

    def enumerate(self, formula: FNode, **kwargs) -> list[set[FNode]]:
        raise NotImplementedError()
