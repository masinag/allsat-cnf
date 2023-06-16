import argparse
import os
import random
import time
from math import log10
from os import path

from pysmt.shortcuts import Symbol, BOOL, Or, Not, And, Iff, write_smtlib, LT, Real, Bool, Times, Plus
from pysmt.typing import REAL

from allsat_cnf.utils import check_sat
from benchmark.utils.fileio import check_output_input
from benchmark.utils.parsing import arg_positive_0, arg_positive, arg_probability

DESCRIPTION = '''Generates random SMT(LRA) formulas.
        
The boolean variables are named A0, A1, ...
The real variables are named x0, x1, ...
The domains of the real variables are [0, 1]
The LRA atoms are linear inequalities of the form
    c1 * x1 + c2 * x2 + ... + cn * xn < b
where c1, ..., cn are random coefficients in [-1, 1] and b is a random integer in [-n, n].'''


class FormulaGenerator:
    TEMPL_REALS = "x{}"
    TEMPL_BOOLS = "A{}"

    # maximum (absolute) value a variable can take
    DOMAIN_BOUNDS = [0, 1]

    def __init__(self, n_bools, n_reals, seed):
        assert n_bools + n_reals > 0

        # initialize the real/boolean variables
        self.reals = []
        for i in range(n_reals):
            self.reals.append(Symbol(self.TEMPL_REALS.format(i), REAL))
        self.bools = []
        for i in range(n_bools):
            self.bools.append(Symbol(self.TEMPL_BOOLS.format(i), BOOL))

        self.domain_bounds = dict()
        # set the seed number, if specified
        random.seed(seed)

    def generate_random_formula(self, depth):
        domain = []

        # generate the domains of the real variables
        for var in self.reals:
            lower, upper = self.DOMAIN_BOUNDS
            dom_formula = And(LT(Real(lower), var), LT(var, Real(upper)))
            domain.append(dom_formula)
        domain = And(domain)

        # generate the support
        formula = Bool(False)
        while not check_sat(formula):
            formula = And(domain, self.random_formula(depth))
        return formula

    def random_formula(self, depth, operators, neg_prob=0.5, theta=0.5):
        """
        Generate a random formula of the given depth.
        :param depth: the depth of the formula
        :param operators: a dictionary of operators and their weights
        :param neg_prob: the probability of negating a formula
        :param theta: the probability of generating a Boolean atom rather than a LRA atom
        """
        if depth <= 0:
            leaf = self._random_atom(theta)
            if random.random() < neg_prob:
                leaf = Not(leaf)
            return leaf
        else:
            operator = random.choices(list(operators.keys()), weights=list(operators.values()))[0]

            left = self.random_formula(depth - 1, operators, neg_prob, theta)
            right = self.random_formula(depth - 1, operators, neg_prob, theta)
            node = operator(left, right)
            negate = random.random() < neg_prob
            if negate:
                node = Not(node)
            return node

    def _random_atom(self, theta=0.5):
        if len(self.bools) == 0 or (len(self.reals) > 0 and random.random() < theta):
            return self._random_inequality()
        else:
            return self._random_boolean()

    def _random_boolean(self):
        return random.choice(self.bools)

    def _random_inequality(self, minsize=None, maxsize=None):
        n_reals = len(self.reals)
        minsize = max(1, minsize) if minsize else 1
        maxsize = min(maxsize, n_reals) if maxsize else n_reals
        size = random.randint(minsize, maxsize)
        r_vars = random.sample(self.reals, size)
        monomials = []
        for r_var in r_vars:
            coefficient = self._random_coefficient(-1, 1)
            monomials.append(Times(coefficient, r_var))

        bound = self._random_coefficient(-len(r_vars), len(r_vars))
        return LT(Plus(monomials), bound)

    @staticmethod
    def _random_coefficient(min_value=-1, max_value=1):
        coefficient = 0
        while coefficient == 0:
            coefficient = random.uniform(min_value, max_value)
        return Real(coefficient)


def parse_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-o', '--output', default=os.getcwd(),
                        help='Folder where all models will be created (default: cwd)')
    parser.add_argument('-b', '--booleans', default=3, type=arg_positive_0,
                        help='Maximum number of bool variables (default: 3)')
    parser.add_argument('-r', '--reals', default=3, type=arg_positive_0,
                        help='Maximum number of real variables (default: 3)')
    parser.add_argument('-t', '--theta', default=0.5, type=arg_probability,
                        help='Probability of generating a Boolean atom rather than a LRA atom (default: 0.5)')
    parser.add_argument('-d', '--depth', default=3, type=arg_positive,
                        help='Depth of the formula tree (default: 3)')
    parser.add_argument('--xnnf', action='store_true', default=False,
                        help='Set this flag to generate formulas in XNNF, i.e. formulas where negations occur only '
                             'at literal level (default: False)')
    parser.add_argument('-m', '--models', default=20, type=arg_positive,
                        help='Number of model files (default: 20)')
    parser.add_argument('-s', '--seed', type=arg_positive_0, required=True,
                        help='Random seed')

    return parser.parse_args()


def main():
    args = parse_args()

    output_dir = 'problems_b{}_r{}_d{}_m{}_s{}'.format(args.booleans, args.reals, args.depth, args.models, args.seed)
    output_dir = path.join(args.output, output_dir)

    check_output_input(args.output, output_dir)
    os.mkdir(output_dir)

    # init generator
    generator = FormulaGenerator(args.booleans, args.reals, args.seed)

    # generate formulas
    print("Starting creating problems")
    time_start = time.time()
    digits = int(log10(args.models)) + 1
    template = "b{b}_d{d}_r{r}_s{s}_{templ}.smt2".format(b=args.booleans, r=args.reals, d=args.depth, s=args.seed,
                                                         templ="{n:0{d}}")

    operators = {
        Iff: 1 / 10,
        Or: 9 / 20,
        And: 9 / 20,
    }
    weights_sum = sum(operators.values())
    for k in operators:
        operators[k] /= weights_sum
    neg_prob = 0.0 if args.xnnf else 0.5

    for i in range(args.models):
        problem = generator.random_formula(args.depth, operators, neg_prob, args.theta)
        file_name = path.join(output_dir, template.format(n=i + 1, d=digits))
        write_smtlib(problem, file_name)
        print("\r" * 100, end='')
        print("Problem {}/{}".format(i + 1, args.models), end='')

    print()
    time_end = time.time()
    seconds = time_end - time_start
    print("Done! {:.3f}s".format(seconds))


if __name__ == '__main__':
    main()
