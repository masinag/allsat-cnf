from multiprocessing import get_context
from queue import Empty

import psutil as psutil


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
