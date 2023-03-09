import enum


class Mode(enum.Enum):
    LAB = "LAB"
    NNF_LAB = "NNF_LAB"
    POL = "POL"
    NNF_POL = "NNF_POL"
    NNF_MUTEX_POL = "NNF_MUTEX_POL"
    NNF_LABELNEG_POL = "NNF_LABELNEG_POL"
    CND = "CND"
    NNF_CND = "NNF_CND"
    EXPAND_CND = "EXPAND_CND"
    TTA = "TTA"


def parse_mode(mode):
    expand_iff = False
    do_nnf = False
    mutex_nnf_labels = False
    label_neg_polarity = False

    if mode.startswith("EXPAND_"):
        expand_iff = True
        mode = mode.lstrip("EXPAND_")
    if mode.startswith("NNF_"):
        do_nnf = True
        mode = mode.lstrip("NNF_")
        if mode.startswith("MUTEX_"):
            mode = mode.lstrip("MUTEX_")
            mutex_nnf_labels = True
        if mode.startswith("LABELNEG_"):
            mode = mode.lstrip("LABELNEG_")
            label_neg_polarity = True

    return mode, expand_iff, do_nnf, mutex_nnf_labels, label_neg_polarity


def get_full_name_mode(args):
    full_mode = args.mode
    if args.with_repetitions:
        full_mode += "_REP"
    return full_mode
