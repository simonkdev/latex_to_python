"""API routes for LaTeX to Python conversion."""

from functools import lru_cache
import logging

from fastapi import APIRouter, HTTPException
from .schemas import ConvertRequest, ConvertResponse
from core.parser import parse_latex_detailed, get_variables
from core.generator import GenerationError, build_symbol_map, generate_python

router = APIRouter(prefix="/api/v1", tags=["convert"])
logger = logging.getLogger(__name__)


@router.post("/convert", response_model=ConvertResponse)
async def convert_latex(request: ConvertRequest) -> ConvertResponse:
    """
    Convert LaTeX expression to Python code.

    Example:
    ```json
    {
        "latex": "\\frac{x+1}{x-1}",
        "mode": "function",
        "func_name": "my_func"
    }
    ```
    """
    response = _convert_cached(
        request.latex,
        request.mode,
        request.func_name,
        request.backend,
    )
    return response.model_copy(deep=True)


@lru_cache(maxsize=256)
def _convert_cached(
    latex: str,
    mode: str,
    func_name: str,
    backend: str,
) -> ConvertResponse:
    """Convert a validated request tuple and cache deterministic results."""
    try:
        # Parse LaTeX to SymPy expression
        parse_result = parse_latex_detailed(latex)
        expr = parse_result.expression

        if expr is None:
            return ConvertResponse(
                python="",
                variables=[],
                error=parse_result.error_message or "Failed to parse LaTeX expression.",
                error_code=parse_result.error_code or "INVALID_LATEX",
                support_level="unsupported",
                backend=backend,
            )

        # Get variables from expression
        variables = [str(v) for v in sorted(get_variables(expr), key=lambda x: str(x))]

        # Generate Python code
        try:
            symbol_map = build_symbol_map(expr)
            python_code = generate_python(
                expr=expr,
                mode=mode,
                backend=backend,
                func_name=func_name,
            )
        except GenerationError as e:
            logger.info("Generation rejected: %s", e.message)
            return ConvertResponse(
                python="",
                variables=variables,
                error=e.message,
                error_code=e.code,
                support_level="unsupported",
                backend=backend,
            )

        support_level = "symbolic" if "sp.sympify(" in python_code else "computed"
        return ConvertResponse(
            python=python_code,
            variables=variables,
            symbol_map=symbol_map,
            support_level=support_level,
            backend=backend,
            required_imports=_extract_required_imports(python_code),
        )

    except Exception as e:
        logger.exception("Unexpected conversion error")
        raise HTTPException(
            status_code=400,
            detail={
                "code": "CONVERSION_ERROR",
                "message": "Conversion failed.",
            },
        ) from e


def _extract_required_imports(code: str) -> list[str]:
    """Extract top-level import statements from generated code."""
    return [line for line in code.splitlines() if line.startswith("import ")]
