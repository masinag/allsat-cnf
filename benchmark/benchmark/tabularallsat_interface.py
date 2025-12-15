import re
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Callable

import numpy as np
from pysmt.fnode import FNode

from allsat_cnf.utils import SolverOptions, get_clauses
from .io.dimacs import DimacsInterface, HeaderMode
from .run import run_cmd_with_timeout

# Regular expressions for parsing tabularallsat output
RE_HEADER = re.compile(r"^c parsed header 'p cnf (\d+) (\d+) (\d+)'")
RE_NUM_CLAUSES = re.compile(r"^c parsed all (\d+) clauses")
RE_MODEL_COUNT = re.compile(r"^s MODEL COUNT")
RE_NUM_PARTIAL_ASSIGNMENTS = re.compile(r"^c n-partial-assignments (\d+)")


@dataclass
class _Output:
    num_vars: int
    num_clauses: int
    projected_vars: int
    model_count: int
    num_partial_assignments: int
    partial_assignments: list[dict[FNode, bool]]


class TabularAllSATInterface:
    """Adapter for TabularAllSAT"""

    def __init__(self, ta_bin: str, solver_options: SolverOptions):
        self.ta_bin = ta_bin
        self.next_line_mc = False
        self.solver_options_cmd = self._get_solver_options_cmd(solver_options)

    @staticmethod
    def _get_solver_options_cmd(solver_options: SolverOptions) -> list[str]:
        options_list = []
        if not solver_options.use_ta:
            options_list.append("--enum_total")
        return options_list

    def projected_allsat(self, formula: FNode, projected_vars: list[FNode], timeout: int | None = None) \
            -> tuple[list[dict[FNode, bool]], int]:
        output = self._invoke_solver(formula, projected_vars, timeout)
        return output.partial_assignments, output.model_count

    def _invoke_solver(self, formula: FNode, projected_vars: list[FNode], timeout: int | None = None) -> _Output:
        with TemporaryDirectory(delete=True) as tmpdir:
            dimacs_file = f"{tmpdir}/input.dimacs"

            dimacs = DimacsInterface(header_mode=HeaderMode.WITH_NUM_PROJECTED_VARS)

            with open(dimacs_file, "w") as fw:
                fw.writelines(dimacs.pysmt_to_dimacs(formula, projected_vars))

            cmd = [self.ta_bin] + self.solver_options_cmd + ["--output-file=1"]
            cmd += [dimacs_file]

            output = _Output(0, 0, 0, 0, 0, [])

            for line in run_cmd_with_timeout(cmd, tmpdir, timeout=timeout):
                output = self._read_output_line(output, line)

            output.partial_assignments = self._read_models(f"{tmpdir}/output.txt", dimacs.int_list_to_model)

        # assert output.num_vars == (nv := len(a)), f"{output.num_vars} != {nv}"
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

    @staticmethod
    def _read_models(model_file: str, int_list_to_model: Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]]) -> list[
        dict[FNode, bool]]:
        # only for rectangular data
        # data = np.loadtxt(model_file, dtype=np.int32)
        # Ensure data is 2D, even if there's only one model
        data = []
        with open(model_file, "r") as f:
            for line in f:
                if line.strip() == "":
                    continue
                data.append(np.fromstring(line.strip(), dtype=np.int32, sep=' '))
        return [dict(zip(*int_list_to_model(row))) for row in data]
