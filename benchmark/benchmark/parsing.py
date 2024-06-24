import argparse


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
