import signal
import subprocess
from dataclasses import dataclass
from multiprocessing import get_context
from queue import Empty
from typing import Iterator

import psutil as psutil

from allsat_cnf.utils import SolverOptions
from .mode import Mode
from .parsing import remove_prefix


def wrap_fn(fn, q, *args, **kwargs):
    res = fn(*args, **kwargs)
    q.put(res, block=True)


def run_with_timeout(fn, timeout, *args, **kwargs):
    ctx = get_context("spawn")
    q = ctx.Queue()
    timed_proc = ctx.Process(
        target=wrap_fn,
        args=[fn, q, *args],
        kwargs=kwargs,
    )
    timed_proc.start()
    try:
        return q.get(block=True, timeout=timeout)
    except Empty:
        kill_process_and_children(timed_proc)
        raise TimeoutError("Process was killed due to timeout")


def kill_process_and_children(timed_proc):
    pid = timed_proc.pid
    proc = psutil.Process(pid)
    for subproc in proc.children(recursive=True):
        try:
            subproc.kill()
        except psutil.NoSuchProcess:
            continue
    try:
        proc.kill()
    except psutil.NoSuchProcess:
        pass


def run_cmd_with_timeout(
        cmd: list[str],
        timeout: int | None = None
) -> Iterator[str]:
    """
    Run a command with a timeout and yield its output line by line.
    """
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=lambda: signal.alarm(timeout),
    )

    try:
        for line in iter(process.stdout.readline, ''):
            yield line.rstrip()
        process.stdout.close()

    except subprocess.TimeoutExpired as te:
        process.kill()
        raise TimeoutError(f"Process timed out after {timeout} seconds") from te

    if process.returncode is not None and process.returncode != 0:
        raise RuntimeError(f"Process failed with exit code {process.returncode}: {process.stderr}")


@dataclass
class PreprocessOptions:
    cnf_type: str
    do_nnf: bool
    mutex_nnf_labels: bool
    label_neg_polarity: bool


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

    with_repetitions = args.with_repetitions if "with_repetitions" in args else False

    preprocess_options = PreprocessOptions(cnf_type=mode, do_nnf=do_nnf, mutex_nnf_labels=mutex_nnf_labels,
                                           label_neg_polarity=label_neg_polarity)
    solver_options = SolverOptions(timeout=args.timeout, with_repetitions=with_repetitions,
                                   use_ta=mode != Mode.TTA, phase_caching=phase_caching, first_assign=first_assign)

    return preprocess_options, solver_options
