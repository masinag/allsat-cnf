import argparse
import enum
from dataclasses import dataclass

from allsat_cnf.utils import SolverOptions


@dataclass
class PreprocessOptions:
    cnf_type: str
    do_nnf: bool
    mutex_nnf_labels: bool
    label_neg_polarity: bool


class Mode(enum.Enum):
    LAB = "LAB"
    NNF_LAB = "NNF_LAB"
    POL = "POL"
    NNF_POL = "NNF_POL"
    NNF_MUTEX_POL = "NNF_MUTEX_POL"
    LABELNEG_POL = "LABELNEG_POL"

    RF_LAB = "RF_LAB"
    RF_LABELNEG_POL = "RF_LABELNEG_POL"
    RF_NNF_MUTEX_POL = "RF_NNF_MUTEX_POL"

    IF_LAB = "IF_LAB"
    IF_LABELNEG_POL = "IF_LABELNEG_POL"
    IF_NNF_MUTEX_POL = "IF_NNF_MUTEX_POL"

    TTA = "TTA"


def get_options(args) -> tuple[PreprocessOptions, SolverOptions]:
    do_nnf = False
    mutex_nnf_labels = False
    label_neg_polarity = False
    phase_caching = True
    first_assign = SolverOptions.FirstAssign.NONE
    mode = args.mode

    if mode.startswith("RF_"):
        mode = remove_prefix(mode, "RF_")
        first_assign = SolverOptions.FirstAssign.RELEVANT
    elif mode.startswith("IF_"):
        mode = remove_prefix(mode, "IF_")
        first_assign = SolverOptions.FirstAssign.IRRELEVANT
    if mode.startswith("NNF_"):
        do_nnf = True
        mode = remove_prefix(mode, "NNF_")
        if mode.startswith("MUTEX_"):
            mode = remove_prefix(mode, "MUTEX_")
            mutex_nnf_labels = True
    if mode.startswith("LABELNEG_"):
        mode = remove_prefix(mode, "LABELNEG_")
        label_neg_polarity = True

    preprocess_options = PreprocessOptions(cnf_type=mode, do_nnf=do_nnf, mutex_nnf_labels=mutex_nnf_labels,
                                           label_neg_polarity=label_neg_polarity)
    solver_options = SolverOptions(timeout=args.timeout, with_repetitions=args.with_repetitions,
                                   use_ta=mode != Mode.TTA, phase_caching=phase_caching, first_assign=first_assign)

    return preprocess_options, solver_options


def remove_prefix(txt: str, prefix: str) -> str:
    if txt.startswith(prefix):
        return txt[len(prefix):]
    return txt


def get_full_name_mode(args) -> str:
    full_mode = args.mode
    if args.with_repetitions:
        full_mode += "_REP"
    return full_mode


def arg_positive_0(value: str):
    value = int(value)
    if value < 0:
        raise argparse.ArgumentTypeError('Expected positive integer, found {}'.format(value))
    return value


def arg_positive(value: str):
    int_value = int(value)
    if int_value <= 0:
        raise argparse.ArgumentTypeError('Expected positive integer (no 0), found {}'.format(value))
    return int_value


def arg_probability(value: str):
    fvalue = float(value)
    if fvalue < 0 or fvalue > 1:
        raise argparse.ArgumentTypeError('Expected probability in [0, 1], found {}'.format(value))
    return fvalue
