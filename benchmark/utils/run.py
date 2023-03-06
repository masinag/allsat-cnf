from multiprocessing import Queue, get_context

import psutil as psutil


def wrap_fn(fn, q, *args, **kwargs):
    q.put(fn(*args, **kwargs))


def run_with_timeout(fn, timeout, *args, **kwargs):
    q = Queue()
    timed_proc = get_context("spawn").Process(
        target=wrap_fn,
        args=[fn, q, *args],
        kwargs=kwargs,
    )
    timed_proc.start()
    timed_proc.join(timeout)
    if timed_proc.is_alive():
        kill_process_and_children(timed_proc)
        raise TimeoutError("Process was killed due to timeout")
    elif q.empty():
        raise TimeoutError("Process was killed due to exceeding resources")
    return q.get(block=False)


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
