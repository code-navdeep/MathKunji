"""
Matrix operations: determinant, inverse, eigenvalues, etc.
"""

from sympy import Matrix, simplify
from utils.parser import parse_matrix
from utils.latex_formatter import to_latex, to_latex_inline


def matrix_determinant(matrix_string):
    """
    Calculate the determinant of a matrix.

    Args:
        matrix_string (str): Matrix in format "[[1, 2], [3, 4]]"

    Returns:
        str: Formatted result with determinant
    """
    success, matrix = parse_matrix(matrix_string)
    if not success:
        return f"❌ {matrix}"

    try:
        det = matrix.det()

        output = "### Matrix Determinant\n\n"
        output += f"**Matrix:**\n{to_latex(matrix)}\n\n"
        output += f"**Determinant:** {to_latex(det)}\n"

        return output

    except Exception as e:
        return f"❌ Error calculating determinant: {str(e)}"


def matrix_inverse(matrix_string):
    """
    Calculate the inverse of a matrix.

    Args:
        matrix_string (str): Matrix in format "[[1, 2], [3, 4]]"

    Returns:
        str: Formatted result with inverse matrix
    """
    success, matrix = parse_matrix(matrix_string)
    if not success:
        return f"❌ {matrix}"

    try:
        # Check if matrix is square
        if matrix.rows != matrix.cols:
            return f"❌ Matrix must be square to have an inverse. Current shape: {matrix.rows}×{matrix.cols}"

        # Check if matrix is singular. simplify() first so symbolic
        # determinants that are structurally non-zero but mathematically
        # zero (e.g. "a - a") are still caught.
        if simplify(matrix.det()) == 0:
            return f"❌ Matrix is singular (determinant = 0). No inverse exists."

        inverse = matrix.inv()

        output = "### Matrix Inverse\n\n"
        output += f"**Original Matrix:**\n{to_latex(matrix)}\n\n"
        output += f"**Inverse:**\n{to_latex(inverse)}\n"

        return output

    except Exception as e:
        return f"❌ Error calculating inverse: {str(e)}"


def matrix_transpose(matrix_string):
    """
    Calculate the transpose of a matrix.

    Args:
        matrix_string (str): Matrix in format "[[1, 2], [3, 4]]"

    Returns:
        str: Formatted result with transposed matrix
    """
    success, matrix = parse_matrix(matrix_string)
    if not success:
        return f"❌ {matrix}"

    try:
        transposed = matrix.T

        output = "### Matrix Transpose\n\n"
        output += f"**Original Matrix:**\n{to_latex(matrix)}\n\n"
        output += f"**Transposed:**\n{to_latex(transposed)}\n"

        return output

    except Exception as e:
        return f"❌ Error calculating transpose: {str(e)}"


def matrix_eigenvalues(matrix_string):
    """
    Calculate eigenvalues of a matrix.

    Args:
        matrix_string (str): Matrix in format "[[1, 2], [3, 4]]"

    Returns:
        str: Formatted result with eigenvalues
    """
    success, matrix = parse_matrix(matrix_string)
    if not success:
        return f"❌ {matrix}"

    try:
        # Check if matrix is square
        if matrix.rows != matrix.cols:
            return f"❌ Matrix must be square to have eigenvalues. Current shape: {matrix.rows}×{matrix.cols}"

        eigenvals = matrix.eigenvals()

        output = "### Matrix Eigenvalues\n\n"
        output += f"**Matrix:**\n{to_latex(matrix)}\n\n"
        output += "**Eigenvalues:**\n\n"

        for eigenval, multiplicity in eigenvals.items():
            output += f"- λ = {to_latex_inline(eigenval)} (multiplicity: {multiplicity})\n"

        return output

    except Exception as e:
        return f"❌ Error calculating eigenvalues: {str(e)}"


def matrix_eigenvectors(matrix_string):
    """
    Calculate eigenvectors of a matrix.

    Args:
        matrix_string (str): Matrix in format "[[1, 2], [3, 4]]"

    Returns:
        str: Formatted result with eigenvectors
    """
    success, matrix = parse_matrix(matrix_string)
    if not success:
        return f"❌ {matrix}"

    try:
        # Check if matrix is square
        if matrix.rows != matrix.cols:
            return f"❌ Matrix must be square to have eigenvectors. Current shape: {matrix.rows}×{matrix.cols}"

        eigenvects = matrix.eigenvects()

        output = "### Matrix Eigenvectors\n\n"
        output += f"**Matrix:**\n{to_latex(matrix)}\n\n"
        output += "**Eigenvectors:**\n\n"

        for eigenval, multiplicity, eigenvectors in eigenvects:
            output += f"For λ = {to_latex_inline(eigenval)} (multiplicity: {multiplicity}):\n\n"
            for vec in eigenvectors:
                output += f"{to_latex(vec)}\n\n"

        return output

    except Exception as e:
        return f"❌ Error calculating eigenvectors: {str(e)}"


def matrix_rank(matrix_string):
    """
    Calculate the rank of a matrix.

    Args:
        matrix_string (str): Matrix in format "[[1, 2], [3, 4]]"

    Returns:
        str: Formatted result with rank
    """
    success, matrix = parse_matrix(matrix_string)
    if not success:
        return f"❌ {matrix}"

    try:
        rank = matrix.rank()

        output = "### Matrix Rank\n\n"
        output += f"**Matrix:**\n{to_latex(matrix)}\n\n"
        output += f"**Rank:** {rank}\n"

        return output

    except Exception as e:
        return f"❌ Error calculating rank: {str(e)}"


def matrix_rref(matrix_string):
    """
    Calculate the reduced row echelon form (RREF) of a matrix.

    Args:
        matrix_string (str): Matrix in format "[[1, 2], [3, 4]]"

    Returns:
        str: Formatted result with RREF
    """
    success, matrix = parse_matrix(matrix_string)
    if not success:
        return f"❌ {matrix}"

    try:
        rref_matrix, pivot_cols = matrix.rref()

        output = "### Reduced Row Echelon Form (RREF)\n\n"
        output += f"**Original Matrix:**\n{to_latex(matrix)}\n\n"
        output += f"**RREF:**\n{to_latex(rref_matrix)}\n\n"
        output += f"**Pivot Columns:** {pivot_cols}\n"

        return output

    except Exception as e:
        return f"❌ Error calculating RREF: {str(e)}"


def matrix_multiply(matrix_a_string, matrix_b_string):
    """
    Multiply two matrices.

    Args:
        matrix_a_string (str): First matrix
        matrix_b_string (str): Second matrix

    Returns:
        str: Formatted result with product
    """
    success_a, matrix_a = parse_matrix(matrix_a_string)
    if not success_a:
        return f"❌ Matrix A: {matrix_a}"

    success_b, matrix_b = parse_matrix(matrix_b_string)
    if not success_b:
        return f"❌ Matrix B: {matrix_b}"

    try:
        # Check dimensions
        if matrix_a.cols != matrix_b.rows:
            return f"❌ Cannot multiply: A is {matrix_a.rows}×{matrix_a.cols}, B is {matrix_b.rows}×{matrix_b.cols}. A.cols must equal B.rows."

        product = matrix_a * matrix_b

        output = "### Matrix Multiplication\n\n"
        output += f"**Matrix A:**\n{to_latex(matrix_a)}\n\n"
        output += f"**Matrix B:**\n{to_latex(matrix_b)}\n\n"
        output += f"**A × B:**\n{to_latex(product)}\n"

        return output

    except Exception as e:
        return f"❌ Error multiplying matrices: {str(e)}"
