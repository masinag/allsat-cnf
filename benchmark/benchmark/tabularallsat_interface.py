import re
from dataclasses import dataclass
from tempfile import NamedTemporaryFile

from pysmt.fnode import FNode

from allsat_cnf.utils import get_clauses
from .io.dimacs import pysmt_to_dimacs, dimacs_var_map, HeaderMode
from .run import run_cmd_with_timeout

# Regular expressions for parsing tabularallsat output
RE_HEADER = re.compile(r"c parsed header 'p cnf (\d+) (\d+) (\d+)'")
RE_NUM_CLAUSES = re.compile(r"c parsed all (\d+) clauses")
RE_MODEL_COUNT = re.compile(r"s MODEL COUNT")
RE_NUM_PARTIAL_ASSIGNMENTS = re.compile(r"c n-partial-assignments (\d+)")


@dataclass
class _Output:
    num_vars: int
    num_clauses: int
    projected_vars: int
    model_count: int
    num_partial_assignments: int


class TabularAllSATInterface:
    """Adapter for TabularAllSAT"""

    def __init__(self, ta_bin: str):
        self.ta_bin = ta_bin
        self.next_line_mc = False

    def projected_allsat(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) \
            -> tuple[int, int]:
        output = self._invoke_solver(formula, projected_vars, timeout)
        return output.num_partial_assignments, output.model_count

    def _invoke_solver(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) -> _Output:
        with NamedTemporaryFile() as f:
            dimacs_file = f.name

            var_map = dimacs_var_map(formula, projected_vars)
            with open(dimacs_file, "w") as fw:
                fw.writelines(pysmt_to_dimacs(formula, projected_vars, var_map, HeaderMode.WITH_NUM_PROJECTED_VARS))

            cmd = [self.ta_bin, dimacs_file]
            output = _Output(0, 0, 0, 0, 0)

            for line in run_cmd_with_timeout(cmd, timeout=timeout):
                output = self._read_output_line(output, line)

        assert output.num_vars == (nv := len(var_map)), f"{output.num_vars} != {nv}"
        assert output.num_clauses == (cc := len(get_clauses(formula))), f"{output.num_clauses} != {cc}"
        assert output.projected_vars == (pv := len(projected_vars)), f"{output.projected_vars} != {pv}"

        return output

    def _read_output_line(self, output: _Output, line: str) -> _Output:
        if self.next_line_mc:
            self.next_line_mc = False
            output.model_count = int(line)
        elif m := RE_HEADER.match(line):
            output.num_vars = int(m.group(1))
            output.num_clauses = int(m.group(2))
            if m.group(3) is not None:
                output.projected_vars = int(m.group(3))
        elif RE_MODEL_COUNT.match(line):
            self.next_line_mc = True
        elif m := RE_NUM_CLAUSES.match(line):
            assert output.num_clauses == int(m.group(1)), f"{output.num_clauses} != {m.group(1)}"
        elif m := RE_NUM_PARTIAL_ASSIGNMENTS.match(line):
            output.num_partial_assignments = int(m.group(1))

        return output
