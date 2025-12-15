import re
from dataclasses import dataclass
from tempfile import NamedTemporaryFile

from allsat_cnf.utils import SolverOptions, get_solver_options_dict
from pysmt.fnode import FNode
from pysmt.shortcuts import to_smtlib, write_smtlib

from .run import run_cmd_with_timeout

# Regular expressions for parsing tabularallsmt output
RE_NUM_PARTIAL_ASSIGNMENTS = re.compile(r"s NUMBER OF PARTIAL ASSIGNMENTS")
RE_MODEL_COUNT = re.compile(r"s MODEL COUNT")

# Regular expressions for smt2 file
RE_ASSERT = re.compile(r"\(assert .*\)")
RE_CHECK_SAT = re.compile(r"\(check-sat\)")


@dataclass
class _Output:
    num_partial_assignments: int


class TabularAllSMTInterface:
    """Adapter for TabularAllSMT"""

    def __init__(self, ta_bin: str, solver_options: SolverOptions):
        self.ta_bin = ta_bin
        self.next_line_mc = False
        self.solver_options_dict = get_solver_options_dict(solver_options)

    def projected_allsmt(self, formula: FNode, projected_vars: set[FNode], timeout: int | None = None) \
            -> int:
        output = self._invoke_solver(formula, projected_vars, timeout)
        return output.num_partial_assignments

    def _invoke_solver(self, formula: FNode, projected_atoms: set[FNode], timeout: int | None = None) -> _Output:
        with NamedTemporaryFile() as f:
            smt2_file = f.name

            write_smtlib(formula, smt2_file)

            # replace (check-sat) with (check-allsat (...projected_vars...))
            with open(smt2_file, "r") as fr:
                smt2_str = fr.read()

            smt2_str = smt2_str.replace("(check-sat)",
                                        f"(check-allsat ({' '.join(to_smtlib(a, daggify=False) for a in projected_atoms)}))")

            with open(smt2_file, "w") as fw:
                fw.write(smt2_str)

            cmd = [
                self.ta_bin,
                "--preprocessor.simplification=0",
                "--preprocessor.toplevel_propagation=false",
                "--dpll.allsat_minimize_model=true",
                smt2_file,
            ]
            output = _Output(0)
            for line in run_cmd_with_timeout(cmd, timeout=timeout):
                output = self._read_output_line(output, line)

        return output

    def _read_output_line(self, output: _Output, line: str) -> _Output:
        if self.next_line_mc:
            self.next_line_mc = False
            output.num_partial_assignments = int(line)
        elif RE_NUM_PARTIAL_ASSIGNMENTS.match(line) or RE_MODEL_COUNT.match(line):
            self.next_line_mc = True

        return output
