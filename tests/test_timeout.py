"""
Tests for utils/timeout.py.

The bug these exist for: the old implementation used a fixed
ThreadPoolExecutor and, on timeout, abandoned the thread -- Python cannot kill
one. The abandoned thread kept its pool slot forever, so a handful of
pathological inputs filled the pool permanently and every later request, however
trivial, queued behind work that would never finish. The app was wedged until
restart. Measured before the fix: after 8 hung submits, a plain 1+1 timed out
at the full budget.

Nothing in the rest of the suite touches run_with_timeout, so without these a
regression to a thread pool would reintroduce a total denial of service with
every other test still green.
"""

import io

import pytest

from core.algebra import simplify_expression
from core.calculus import taylor_series
from core.graphing import plot_2d, plot_3d
from utils.timeout import (
    MAX_WORKERS,
    ComputationTimeoutError,
    run_with_timeout,
)

# An expression whose series expansion is far too slow to finish in the short
# budgets used below, so the timeout path is exercised deterministically.
PATHOLOGICAL = ("exp(sin(exp(x)))", "x", "0", 80)


def test_runs_a_normal_computation():
    result = run_with_timeout(simplify_expression, "x + x")
    assert not result.startswith("❌")
    assert "2 x" in result or "2x" in result


def test_raises_on_timeout():
    with pytest.raises(ComputationTimeoutError):
        run_with_timeout(taylor_series, *PATHOLOGICAL, timeout=1)


def test_pool_recovers_after_being_saturated_with_timeouts():
    """
    THE regression test for this module.

    Fire more pathological inputs than there are workers, then check that an
    ordinary computation still completes promptly. Under the old thread pool
    this hung until the process was restarted.
    """
    for _ in range(MAX_WORKERS * 2):
        with pytest.raises(ComputationTimeoutError):
            run_with_timeout(taylor_series, *PATHOLOGICAL, timeout=1)

    result = run_with_timeout(simplify_expression, "x + x", timeout=20)
    assert not result.startswith("❌"), "pool did not recover after timeouts"


@pytest.mark.parametrize("call", [
    (plot_2d, (["sin(x)"], -10, 10)),
    (plot_3d, ("x^2 + y^2", -5, 5, -5, 5, "x", "y")),
])
def test_figures_survive_the_process_boundary(call):
    """
    Results now cross a process boundary, so everything returned has to be
    picklable. Markdown strings trivially are; matplotlib Figures are the
    interesting case -- and they must still be usable once they arrive.
    """
    function, arguments = call
    figure, status = run_with_timeout(function, *arguments, timeout=30)
    assert figure is not None, status
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png")
    assert buffer.getvalue().startswith(b"\x89PNG")


def test_rejects_functions_a_worker_could_not_import():
    """
    Tasks are sent as a module/function name rather than a pickled callable, so
    anything not importable by name has to be refused clearly rather than
    failing somewhere inside a worker.
    """
    with pytest.raises(ValueError):
        run_with_timeout(lambda: 1)
