import circuitgraph as cg
from pysmt.fnode import FNode
from pysmt.shortcuts import Symbol, FALSE, TRUE, Not, And, Or, Xor


class BenchAdapter:
    """Reads a circuit from a .bench file and converts it to a PySMT formula."""

    def __init__(self, circuit: cg.Circuit):
        self._circuit = circuit

    @staticmethod
    def from_file(path: str) -> 'BenchAdapter':
        return BenchAdapter(cg.io.from_file(path))

    def to_pysmt(self) -> tuple[list[FNode], list[FNode]]:
        nodes = {}
        for node in self._circuit.topo_sort():
            args = [nodes[i] for i in self._circuit.fanin(node)]
            if self._circuit.type(node) == "input":
                formula = Symbol(node)
            elif self._circuit.type(node) == "0":
                formula = FALSE()
            elif self._circuit.type(node) == "1":
                formula = TRUE()
            elif self._circuit.type(node) == "buf":
                formula = args.pop()
            elif self._circuit.type(node) == "not":
                formula = Not(args.pop())
            elif self._circuit.type(node) == "and":
                formula = And(args)
            elif self._circuit.type(node) == "nand":
                formula = Not(And(args))
            elif self._circuit.type(node) == "or":
                formula = Or(args)
            elif self._circuit.type(node) == "nor":
                formula = Not(Or(args))
            elif self._circuit.type(node) == "xor":
                assert len(args) == 2
                formula = Xor(args[0], args[1])
            elif self._circuit.type(node) == "xnor":
                assert len(args) == 2
                formula = Not(Xor(args[0], args[1]))
            else:
                raise ValueError(f"unknown gate type '{self._circuit.type(node)}'")
            nodes[node] = formula
        inputs = [nodes[node] for node in self._circuit.inputs()]
        outputs = [nodes[node] for node in self._circuit.outputs()]
        return inputs, outputs
