import argparse
import enum
from dataclasses import dataclass
from typing import Tuple

from local_tseitin.utils import SolverOptions


@dataclass
class PreprocessOptions:
    cnf_type: str
    expand_iff: bool
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
    NOPC_POL = "NOPC_POL"
    NOPC_LABELNEG_POL = "NOPC_LABELNEG_POL"
    NOPC_NNF_POL = "NOPC_NNF_POL"
    NOPC_NNF_MUTEX_POL = "NOPC_NNF_MUTEX_POL"
    CND = "CND"
    NNF_CND = "NNF_CND"
    EXPAND_CND = "EXPAND_CND"
    TTA = "TTA"


def get_options(args) -> Tuple[PreprocessOptions, SolverOptions]:
    expand_iff = False
    do_nnf = False
    mutex_nnf_labels = False
    label_neg_polarity = False
    phase_caching = True
    mode = args.mode

    if mode.startswith("NOPC_"):
        phase_caching = False
        mode = remove_prefix(mode, "NOPC_")
    if mode.startswith("EXPAND_"):
        expand_iff = True
        mode = remove_prefix(mode, "EXPAND_")
    if mode.startswith("NNF_"):
        do_nnf = True
        mode = remove_prefix(mode, "NNF_")
        if mode.startswith("MUTEX_"):
            mode = remove_prefix(mode, "MUTEX_")
            mutex_nnf_labels = True
    if mode.startswith("LABELNEG_"):
        mode = remove_prefix(mode, "LABELNEG_")
        label_neg_polarity = True

    preprocess_options = PreprocessOptions(cnf_type=mode, expand_iff=expand_iff, do_nnf=do_nnf,
                                           mutex_nnf_labels=mutex_nnf_labels,
                                           label_neg_polarity=label_neg_polarity)
    solver_options = SolverOptions(timeout=args.timeout, with_repetitions=args.with_repetitions,
                                   use_ta=mode != Mode.TTA,
                                   phase_caching=phase_caching)

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
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError('Expected positive integer (no 0), found {}'.format(value))
    return ivalue
