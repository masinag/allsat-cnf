from pysmt.environment import Environment, get_env
from pysmt.fnode import FNode
from pysmt.formula import FormulaManager
from pysmt.typing import BOOL


class AIGAdapter:
    """Reads an AIG from a .aig or .aag file and converts it to a PySMT formula."""

    def __init__(self, expr: FNode | None = None, env: Environment | None = None):
        self.aig = expr
        if env is None:
            env = get_env()
        self.env = env
        self.mgr = self.env.formula_manager

    def __repr__(self):
        return self.aig.serialize()

    @staticmethod
    def _read_inputs(filename: str, mgr: FormulaManager) -> dict[int, FNode]:
        inputs = {}
        with open(filename, "r") as f:
            fmt, m, i, l, o, a = f.readline().strip().split()
            assert fmt == "aag"
            for line in f:
                if line.startswith("i"):
                    index, name = line[1:].strip().split()
                    inputs[int(index)] = mgr.Symbol(name, BOOL)
        for index in range(1, int(i) + 1):
            if index not in inputs:
                inputs[index] = mgr.Symbol(f"i{index}")

        return inputs

    @staticmethod
    def _parse_lit(lit: int) -> tuple[int, bool]:
        return lit // 2, lit % 2 == 1

    @classmethod
    def _read_aag(cls, filename: str, inputs: dict[int, FNode], mgr: FormulaManager) -> FNode:
        nodes = {}
        with open(filename, "r") as f:
            # read first line
            fmt, m, i, l, o, a = f.readline().strip().split()
            m, i, l, o, a = map(int, (m, i, l, o, a))
            assert l == 0, "Latches are not supported"
            assert o == 1, "Only one output is supported"

            # read inputs
            for j in range(i):
                lit = int(f.readline().strip())
                index, neg = cls._parse_lit(lit)
                assert not neg, "Negated inputs are not supported"
                nodes[index] = inputs[j]

            # read outputs (only one supported)
            lit = int(f.readline().strip())
            output_idx, output_neg = cls._parse_lit(lit)
            # read AND gates
            for _ in range(a):
                lit, left, right = map(int, f.readline().strip().split())
                and_idx, and_neg = cls._parse_lit(lit)
                left_idx, left_neg = cls._parse_lit(left)
                right_idx, right_neg = cls._parse_lit(right)

                left_node = nodes[left_idx]
                if left_neg:
                    left_node = mgr.Not(left_node)

                right_node = nodes[right_idx]
                if right_neg:
                    right_node = mgr.Not(right_node)

                and_node = mgr.And(left_node, right_node)
                if and_neg:
                    and_node = mgr.Not(and_node)

                nodes[and_idx] = and_node

        output_node = nodes[output_idx]
        if output_neg:
            output_node = mgr.Not(output_node)

        return output_node

    @classmethod
    def from_file(cls, file: str, env: Environment | None = None):
        if env is None:
            env = get_env()
        mgr = env.formula_manager

        if not file.endswith(".aag"):
            raise ValueError("Only .aag files are supported")

        inputs = cls._read_inputs(file, mgr)

        return AIGAdapter(cls._read_aag(file, inputs, mgr), env)

    def to_pysmt(self) -> FNode:
        return self.aig
