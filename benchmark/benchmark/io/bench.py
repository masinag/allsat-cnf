import circuitgraph as cg
from pysmt.fnode import FNode
from pysmt.shortcuts import Symbol, FALSE, TRUE, Not, And, Or, Xor, serialize


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
            args = self._sorted([nodes[i] for i in self._circuit.fanin(node)])
            nodes[node] = self._node_to_pysmt(node, args)
        inputs = self._sorted([nodes[node] for node in self._circuit.inputs()])
        outputs = self._sorted([nodes[node] for node in self._circuit.outputs()])
        return inputs, outputs

    def _node_to_pysmt(self, node: str, args: list[FNode]) -> FNode:
        match self._circuit.type(node):
            case "input":
                return Symbol(node)
            case "0":
                return FALSE()
            case "1":
                return TRUE()
            case "buf":
                return args.pop()
            case "not":
                return Not(args.pop())
            case "and":
                return And(args)
            case "nand":
                return Not(And(args))
            case "or":
                return Or(args)
            case "nor":
                return Not(Or(args))
            case "xor":
                assert len(args) == 2
                return Xor(args[0], args[1])
            case "xnor":
                assert len(args) == 2
                return Not(Xor(args[0], args[1]))
            case _:
                raise ValueError(f"unknown gate type '{self._circuit.type(node)}'")

    @staticmethod
    def _sorted(nodes):
        return sorted(nodes, key=serialize)
