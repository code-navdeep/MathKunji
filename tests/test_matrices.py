from core.matrices import (
    matrix_determinant,
    matrix_inverse,
    matrix_transpose,
    matrix_eigenvalues,
    matrix_eigenvectors,
    matrix_rank,
    matrix_rref,
    matrix_multiply,
)


def assert_ok(result):
    assert not result.startswith("❌"), f"unexpected error: {result}"


def test_determinant():
    result = matrix_determinant("[[1, 2], [3, 4]]")
    assert_ok(result)
    assert "-2" in result


def test_inverse():
    assert_ok(matrix_inverse("[[1, 2], [3, 4]]"))


def test_inverse_rejects_structurally_singular_matrix():
    result = matrix_inverse("[[1, 1], [1, 1]]")
    assert result.startswith("❌")
    assert "singular" in result


def test_inverse_rejects_symbolically_singular_matrix():
    """
    Regression for A12: det() == 0 previously used structural equality,
    which misses a determinant that is non-zero as a raw expression but
    simplifies to zero (e.g. via the sin^2+cos^2=1 identity).
    """
    result = matrix_inverse("[[1, sin(a)^2 + cos(a)^2], [1, 1]]")
    assert result.startswith("❌")
    assert "singular" in result


def test_transpose():
    assert_ok(matrix_transpose("[[1, 2], [3, 4]]"))


def test_eigenvalues():
    result = matrix_eigenvalues("[[2, -1], [-1, 2]]")
    assert_ok(result)
    assert "multiplicity" in result


def test_eigenvectors():
    assert_ok(matrix_eigenvectors("[[2, -1], [-1, 2]]"))


def test_rank():
    assert_ok(matrix_rank("[[1, 2], [3, 4]]"))


def test_rref():
    assert_ok(matrix_rref("[[1, 2], [3, 4]]"))


def test_multiply():
    result = matrix_multiply("[[1, 2], [3, 4]]", "[[1, 0], [0, 1]]")
    assert_ok(result)


def test_multiply_dimension_mismatch():
    result = matrix_multiply("[[1, 2, 3]]", "[[1, 2, 3]]")
    assert result.startswith("❌")
