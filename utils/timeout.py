"""
Wall-clock timeout guard for potentially long-running SymPy computations.

A pathological input -- simplify() on a huge expression, a high-order Taylor
series, eigenvalues of a large symbolic matrix -- can otherwise occupy a
worker indefinitely. This module provides one shared helper so every call
site enforces the same bound.

Why processes and not threads
-----------------------------
This used to submit to a fixed ``ThreadPoolExecutor(max_workers=8)`` and, on
timeout, simply abandon the thread -- because Python has no supported way to
kill one. The abandoned thread kept its pool slot forever, so eight
pathological inputs were enough to fill the pool permanently: every later
request, however trivial, queued behind work that would never finish. The app
was then wedged until restart. That is a denial of service, not the "bounds
response time, not CPU" trade-off the old docstring described.

Processes can be terminated. When a computation blows its deadline its worker
is killed outright, which frees both the slot and the CPU, and a replacement
is created on demand. The pool therefore cannot degrade over time.

Values crossing the process boundary must be picklable. Everything this app
returns is: ``core/*`` operations return markdown strings, and graphing
returns matplotlib ``Figure`` objects, which pickle cleanly (a 3D surface is
roughly 1 MB).
"""

import importlib
import multiprocessing
import queue
import threading

# Generous on purpose. On an older or slower machine a legitimate computation
# -- a large simplify(), a high-order Taylor series, symbolic eigenvalues --
# can genuinely take longer than a few seconds, and cutting it off means the
# user gets an error for work that would have succeeded.
#
# A budget this long is only safe because the pool is process-based: an
# over-running computation is terminated and its worker replaced, so a long
# deadline no longer risks wedging the app the way the old thread pool did.
# The container's mem_limit is the backstop for anything that allocates
# heavily during those 60 seconds.
DEFAULT_TIMEOUT_SECONDS = 60

# Small on purpose: this is a single-user desktop app. The old fixed pool was
# a problem because slots were lost permanently, not because there were eight
# of them -- a killed worker here always returns its slot.
MAX_WORKERS = 4

# Modules a freshly forked worker should already have imported.
_PRELOAD = [
    'core.algebra',
    'core.calculus',
    'core.matrices',
    'core.graphing',
    'core.special_functions',
]


class ComputationTimeoutError(Exception):
    """Raised when a wrapped computation exceeds its time budget."""


def _worker_loop(connection):
    """
    Body of a worker process: import-and-call, forever, until told to stop.

    Tasks arrive as ``(module_name, function_name, args, kwargs)`` rather than
    as a pickled callable. Sending the name and importing it on this side keeps
    the protocol independent of how the parent happens to have imported things,
    and avoids pickling function objects entirely.
    """
    while True:
        try:
            task = connection.recv()
        except (EOFError, OSError):
            return
        if task is None:
            return

        module_name, function_name, args, kwargs = task
        try:
            function = getattr(importlib.import_module(module_name), function_name)
            connection.send(('ok', function(*args, **kwargs)))
        except Exception as exc:
            # Send a plain string, never the exception object: an arbitrary
            # exception is not guaranteed picklable, and a failure to pickle
            # it here would hang the parent waiting for a reply that never
            # arrives.
            connection.send(('error', f"{type(exc).__name__}: {exc}"))


def _start_method():
    """
    Prefer 'forkserver' where the platform has it, otherwise 'spawn'.

    This is a meaningful performance difference, not a stylistic one. 'spawn'
    re-imports the parent's ``__main__`` in every new worker -- and this app's
    ``__main__`` is app.py, which pulls in Gradio. That measured 1.87s per
    worker start. 'forkserver' forks from a clean server process that imports
    only ``_PRELOAD`` (0.31s), and never touches ``__main__`` at all.

    'forkserver' is Unix-only, which covers both local use here and the Linux
    Docker image; 'spawn' keeps a native Windows run working.
    """
    available = multiprocessing.get_all_start_methods()
    return 'forkserver' if 'forkserver' in available else 'spawn'


_context = multiprocessing.get_context(_start_method())
if _start_method() == 'forkserver':
    _context.set_forkserver_preload(_PRELOAD)


class _Worker:
    """One long-lived child process plus the pipe used to talk to it."""

    def __init__(self):
        self._connection, child_connection = _context.Pipe()
        self._process = _context.Process(
            target=_worker_loop,
            args=(child_connection,),
            daemon=True,
        )
        self._process.start()
        # The parent keeps only its own end; leaving the child's end open here
        # would stop recv() from ever raising EOF when the child dies.
        child_connection.close()

    def is_alive(self):
        return self._process.is_alive()

    def kill(self):
        try:
            self._process.terminate()
            self._process.join(timeout=1)
        finally:
            try:
                self._connection.close()
            except OSError:
                pass

    def run(self, module_name, function_name, args, kwargs, timeout):
        self._connection.send((module_name, function_name, args, kwargs))

        if not self._connection.poll(timeout):
            raise ComputationTimeoutError(
                f"Computation timed out after {timeout}s — try a smaller/simpler input."
            )

        status, payload = self._connection.recv()
        if status == 'error':
            raise RuntimeError(payload)
        return payload


_idle_workers = queue.Queue()
_worker_count_lock = threading.Lock()
_worker_count = 0


def _acquire(timeout):
    """Check out an idle worker, creating one if the pool has room."""
    global _worker_count

    try:
        return _idle_workers.get_nowait()
    except queue.Empty:
        pass

    with _worker_count_lock:
        may_create = _worker_count < MAX_WORKERS
        if may_create:
            _worker_count += 1

    if may_create:
        try:
            return _Worker()
        except BaseException:
            with _worker_count_lock:
                _worker_count -= 1
            raise

    # Every worker is busy. Waiting is bounded, because each in-flight task is
    # itself bounded by its own timeout and its worker is killed if it exceeds
    # it -- so a slot always comes back.
    try:
        return _idle_workers.get(timeout=timeout)
    except queue.Empty:
        raise ComputationTimeoutError(
            f"Server busy — no free worker within {timeout}s. Please try again."
        )


def _release(worker):
    """Return a healthy worker to the pool; drop it if it died."""
    global _worker_count

    if worker.is_alive():
        _idle_workers.put(worker)
        return

    with _worker_count_lock:
        _worker_count -= 1


def _discard(worker):
    """Kill a worker and free its slot."""
    global _worker_count

    worker.kill()
    with _worker_count_lock:
        _worker_count -= 1


def run_with_timeout(func, *args, timeout=DEFAULT_TIMEOUT_SECONDS, **kwargs):
    """
    Run func(*args, **kwargs) in a worker process under a wall-clock timeout.

    On expiry the worker is terminated, so the computation genuinely stops and
    its slot is returned to the pool -- unlike the previous thread-based
    implementation, where a timed-out computation ran on forever and its slot
    was never recoverable.

    Raises ComputationTimeoutError on expiry.
    """
    module_name = getattr(func, '__module__', None)
    function_name = getattr(func, '__qualname__', None)
    if not module_name or not function_name or '.<locals>.' in function_name:
        raise ValueError(
            "run_with_timeout needs a module-level function so the worker can "
            f"import it by name; got {func!r}"
        )

    worker = _acquire(timeout)
    try:
        result = worker.run(module_name, function_name, args, kwargs, timeout)
    except ComputationTimeoutError:
        _discard(worker)
        raise
    except BaseException:
        _discard(worker)
        raise
    _release(worker)
    return result
