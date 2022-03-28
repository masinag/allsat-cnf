from pysmt.shortcuts import *


class LocalTseitinCNFizer():
    VAR_TEMPLATE = "T{:d}"

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.vars = 0

    def _new_label(self):
        self.vars += 1
        return Symbol(LocalTseitinCNFizer.VAR_TEMPLATE.format(self.vars))

    def convert(self, phi):
        raise NotImplemented

    def is_atom(self, atom):
        return atom.is_symbol(BOOL) or atom.is_theory_relation()

    def is_literal(self, literal):
        return self.is_atom(literal) or (literal.is_not() and self.is_atom(literal.arg(0)))

    def is_cnf(self, phi):
        if self.is_literal(phi):
            return True
