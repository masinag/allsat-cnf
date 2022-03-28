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
