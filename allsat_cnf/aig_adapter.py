from typing import Dict, Tuple, Iterable

import funcy as fn
from aiger import AIG as _AIG, to_aig as _to_aig
from aiger.aig import Input as _Input
from pysmt.fnode import FNode
from pysmt.shortcuts import Symbol, And, Not, Bool
from pysmt.typing import BOOL


class AIGAdapter:
    """Reads an AIG from a .aig or .aag file and converts it to a PySMT formula."""
    def __init__(self, aig: _AIG):
        assert len(aig.outputs) == 1
        # assert len(aig.latches) == 0
        self.aig = aig
        self.inputs: Dict[_Input, Symbol] = {}

    def __repr__(self):
        return repr(self.aig)

    @classmethod
    def from_file(cls, file) -> "AIGAdapter":
        return cls(_to_aig(file))

    def gates(self) -> Tuple[Dict[int, str], int, Iterable[Tuple[int, int, int]]]:
        gates = []
        count = 0

        class NodeAlg:
            def __init__(self, lit: int):
                self.lit = lit

            @fn.memoize
            def __and__(self, other):
                nonlocal count
                nonlocal gates
                count += 1
                new = NodeAlg(count << 1)
                right, left = sorted([self.lit, other.lit])
                gates.append((new.lit, left, right))
                return new

            def __invert__(self):
                return NodeAlg(self.lit ^ 1)

        def lift(obj) -> NodeAlg:
            if isinstance(obj, bool):
                return NodeAlg(int(obj))
            elif isinstance(obj, NodeAlg):
                return obj
            raise NotImplementedError

        circ = self.aig
        start = 1
        inputs = {k: NodeAlg(i << 1) for i, k in enumerate(sorted(circ.inputs), start)}
        count += len(inputs)

        # Interpret circ over Algebra.
        omap, _ = circ(inputs=inputs, lift=lift)
        output = omap.get(next(iter(circ.outputs))).lit
        inputs = {inputs[k].lit: k for k in sorted(circ.inputs)}

        return inputs, output, gates

    def to_pysmt(self) -> FNode:
        count = 0

        class NodeAlg:
            def __init__(self, node: FNode):
                self.node = node

            @fn.memoize
            def __and__(self, other):
                return NodeAlg(And(self.node, other.node))

            def __invert__(self):
                return NodeAlg(Not(self.node))

        def lift(obj) -> NodeAlg:
            if isinstance(obj, bool):
                return NodeAlg(Bool(obj))
            if isinstance(obj, FNode):
                return NodeAlg(obj)
            elif isinstance(obj, NodeAlg):
                return obj
            raise NotImplementedError

        circ = self.aig

        inputs = {}
        start = 1
        for i, k in enumerate(sorted(circ.inputs), start):
            inputs[k] = NodeAlg(Symbol(k, BOOL))
        count += len(inputs)

        # Interpret circ over Algebra.
        omap, _ = circ(inputs=inputs, lift=lift)
        output = omap.get(next(iter(circ.outputs))).node

        return output
