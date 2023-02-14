def parse_mode(mode):
    expand_iff = False
    do_nnf = False
    if mode.startswith("EXPAND_"):
        expand_iff = True
        mode.lstrip("EXPAND_")
    if mode.startswith("NNF_"):
        do_nnf = True
        mode.lstrip("NNF_")

    return mode, expand_iff, do_nnf


def get_full_name_mode(args):
    full_mode = args.mode
    if args.with_repetitions:
        full_mode += "_REP"
    return full_mode
