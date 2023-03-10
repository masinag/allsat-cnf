import enum


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


def parse_mode(mode):
    expand_iff = False
    do_nnf = False
    mutex_nnf_labels = False
    label_neg_polarity = False
    phase_caching = True

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

    return mode, expand_iff, do_nnf, mutex_nnf_labels, label_neg_polarity, phase_caching


def remove_prefix(txt, prefix):
    if txt.startswith(prefix):
        return txt[len(prefix):]
    return txt


def get_full_name_mode(args):
    full_mode = args.mode
    if args.with_repetitions:
        full_mode += "_REP"
    return full_mode
