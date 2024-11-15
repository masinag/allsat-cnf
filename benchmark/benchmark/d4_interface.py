import re
from dataclasses import dataclass
from enum import Enum
from tempfile import NamedTemporaryFile

import networkx as nx
from matplotlib import pyplot as plt
from networkx.drawing.nx_pydot import pydot_layout
from pysmt.fnode import FNode

from allsat_cnf.utils import get_clauses
from .io.dimacs import pysmt_to_dimacs, dimacs_var_map
from .run import run_cmd_with_timeout


def find_stars(string):
    return (x.group(0) for x in re.finditer(r"\*[0-9A-Za-z']+", string))


@dataclass
class _D4Output:
    num_vars: int
    num_clauses: int
    projected_vars: int
    model_count: int
    num_decision: int
    num_partitioner_calls: int
    num_pos_hits: int
    num_neg_hits: int


class D4Interface:
    """Adapter for D4 model counter and d-DNNF compiler."""

    # Regular expressions for parsing d4 output
    RE_NUM_VARS = re.compile(r"c \[INITIAL INPUT\] Number of variables: (\d+)")
    RE_NUM_CLAUSES = re.compile(r"c \[INITIAL INPUT\] Number of clauses: (\d+)")
    RE_PROJECTED_VARS = re.compile(r"c \[PROJECTED VARIABLES\] list: (.+)")
    RE_NUM_DECISION = re.compile(r"c Number of decision: (\d+)")
    RE_NUM_PARTITIONER_CALLS = re.compile(r"c Number of paritioner calls: (\d+)")
    RE_NUM_POS_HITS = re.compile(r"c Number of positive hit: (\d+)")
    RE_NUM_NEG_HITS = re.compile(r"c Number of negative hit: (\d+)")
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

    class MODE(Enum):
        COUNTING = "counting"
        DDNNF = "dDNNF"

    def __init__(self, d4_bin: str):
        self.d4_bin = d4_bin

    def projected_model_count(self, formula: FNode, projected_vars: set[FNode], tmp_dir: str | None,
                              timeout: int | None) -> int:
        output, _ = self._invoke_d4(formula, projected_vars, self.MODE.COUNTING, tmp_dir=tmp_dir, timeout=timeout)

        return output.model_count

    def compile(self, formula: FNode, projected_vars: set[FNode], nnf_file: str, tmp_dir: str | None,
                timeout: int | None) \
            -> tuple[_D4Output, dict[FNode, int]]:
        return self._invoke_d4(formula, projected_vars, self.MODE.DDNNF, nnf_file=nnf_file, tmp_dir=tmp_dir,
                               timeout=timeout)

    def _invoke_d4(self, formula: FNode, projected_vars: set[FNode], mode: MODE,
                   nnf_file: str | None = None,
                   tmp_dir: str | None = None,
                   timeout: int | None = None) -> tuple[_D4Output, dict[FNode, int]]:
        with NamedTemporaryFile(dir=tmp_dir, delete=False, delete_on_close=False) as f:
            dimacs_file = f.name
            var_map = dimacs_var_map(formula, projected_vars)

            with open(dimacs_file, "w") as fw:
                fw.writelines(pysmt_to_dimacs(formula, projected_vars, var_map))

            cmd = [self.d4_bin, "-i", str(dimacs_file)]
            if mode == self.MODE.DDNNF:
                assert nnf_file is not None, "d-DNNF mode requires a file to dump the d-DNNF"
                cmd += ["--dump-file", nnf_file]
            elif mode == self.MODE.COUNTING:
                assert nnf_file is None, "Counting mode does not require a file to dump the d-DNNF"
                pass

            output = _D4Output(0, 0, 0, 0, 0, 0, 0, 0)
            for line in run_cmd_with_timeout(cmd, timeout=timeout):
                output = self._read_output_line(output, line)

            if mode == self.MODE.DDNNF:
                self._fix_ddnnf(nnf_file, var_map, projected_vars)

        assert output.num_vars == (nv := len(var_map)), f"{output.num_vars} != {nv}"
        assert output.num_clauses == (cc := len(get_clauses(formula))), f"{output.num_clauses} != {cc}"
        assert output.projected_vars == (pv := len(projected_vars)), f"{output.projected_vars} != {pv}"

        return output, var_map

    def _fix_ddnnf(self, nnf_file: str, var_map: dict[FNode, int], projected_vars: set[FNode]):
        """
        The d-DNNF output by d4 can contain variables that are not in the projected variables set.
        However, it should be safe to simply remove them from the d-DNNF file.
        """
        with open(nnf_file) as f:
            lines = f.readlines()

        projected_ids = {var_map[v] for v in projected_vars}
        ids_map = {v: i for i, v in enumerate(projected_ids, start=1)}

        with open(nnf_file, "w") as f:
            for line in lines:
                if m := self.RE_NNF_EDGE.match(line):
                    a, b, ll = m.groups()
                    f.write(f"{a} {b}")
                    for l in (ll or "").split():
                        i = int(l)
                        a = abs(i)
                        s = 1 if i > 0 else -1
                        if a in projected_ids:
                            f.write(f" {s * ids_map[a]}")
                    f.write(" 0\n")
                else:
                    f.write(line)

    def _read_output_line(self, output: _D4Output, line: str) -> _D4Output:
        if m := self.RE_NUM_VARS.match(line):
            output.num_vars = int(m.group(1))
        elif m := self.RE_NUM_CLAUSES.match(line):
            output.num_clauses = int(m.group(1))
        elif m := self.RE_PROJECTED_VARS.match(line):
            output.projected_vars = len(m.group(1).split())
        elif m := self.RE_NUM_DECISION.match(line):
            output.num_decision = int(m.group(1))
        elif m := self.RE_NUM_PARTITIONER_CALLS.match(line):
            output.num_partitioner_calls = int(m.group(1))
        elif m := self.RE_NUM_POS_HITS.match(line):
            output.num_pos_hits = int(m.group(1))
        elif m := self.RE_NUM_NEG_HITS.match(line):
            output.num_neg_hits = int(m.group(1))
        elif m := self.RE_MODEL_COUNT.match(line):
            output.model_count = int(m.group(1))

        return output


class D4EnumeratorInterface:
    """Adapter for D4 enumerator."""

    def __init__(self, enumerator_bin: str):
        self.enumerator_bin = enumerator_bin

    def enumerate_paths(self, nnf_file: str, var_map: dict[FNode, int], projected_vars: set[FNode],
                        timeout: int | None = None) -> tuple[int, int]:
        cmd = [self.enumerator_bin, "model-enumeration", "--compact-free-vars", "--input", nnf_file]

        count, n_paths = 0, 0
        projected_ids = {var_map[v] for v in projected_vars}
        for line in run_cmd_with_timeout(cmd, timeout=timeout):
            c, n = self._read_output_line(line, projected_ids)
            count += c
            n_paths += n

        return count, n_paths

    def _read_output_line(self, line: str, projected_ids: set[int]) -> tuple[int, int]:
        """
        Each line represents a model.
        Count the number K of "*" chars for each model, and increase the count by 2^K.

        Return the number of models and the total count.
        """
        count, n_paths = 0, 0
        if line.startswith("v "):
            # count stars only in the projected variables
            k = sum(1 for var in find_stars(line))
            count += 2 ** k
            n_paths += 1

        return count, n_paths


def visualize(nnf_file: str, var_map: dict[FNode, int], output_file: str | None = None):
    inverse_var_map = {v: k for k, v in var_map.items()}

    g = nx.DiGraph()
    labels = {}

    with open(nnf_file) as f:
        for line in f:
            if m := D4Interface.RE_NNF_OR.match(line):
                g.add_node(m.group(1))
                labels[m.group(1)] = "OR"
            elif m := D4Interface.RE_NNF_AND.match(line):
                g.add_node(m.group(1))
                labels[m.group(1)] = "AND"
            elif m := D4Interface.RE_NNF_TRUE.match(line):
                g.add_node(m.group(1))
                labels[m.group(1)] = "TRUE"
            elif m := D4Interface.RE_NNF_FALSE.match(line):
                g.add_node(m.group(1))
                labels[m.group(1)] = "FALSE"
            elif m := D4Interface.RE_NNF_EDGE.match(line):
                from_id, to_id, ll = m.groups()
                ll = [int(i) for i in (ll or "").split()]
                literals = []
                for l in ll:
                    v = inverse_var_map[abs(l)]
                    s = (f"!{v}" if l < 0 else str(v))
                    literals.append(s)
                    labels[s] = s

                # make a fresh AND node
                and_node = f"AND{from_id}_{to_id}_{'_'.join(literals)}"
                g.add_node(and_node)
                labels[and_node] = "AND"
                g.add_edge(from_id, and_node)
                g.add_edge(and_node, to_id)
                for l in literals:
                    g.add_edge(and_node, l)

        # visualize the graph. the graph is a rooted DAG

        pos = pydot_layout(g, prog="dot", root=4)
        nx.draw(g, pos, labels=labels, node_size=500, alpha=0.5, font_size=10)

        if output_file is not None:
            plt.savefig(output_file)
        else:
            plt.show()

        plt.close()
