"""Pydantic models for request/response validation."""

from pydantic import BaseModel, Field
from typing import Literal

SupportLevel = Literal["computed", "symbolic", "unsupported", "ambiguous"]
OutputBackend = Literal["python", "numpy", "sympy"]
VariableType = Literal["scalar", "list", "vector", "matrix", "set"]


class ConvertRequest(BaseModel):
    """Request model for LaTeX conversion."""

    latex: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="LaTeX string to convert",
    )
    mode: Literal["expression", "function"] = Field(
        default="function", description="Output mode: expression or function"
    )
    func_name: str = Field(default="f", description="Function name for function output")
    backend: OutputBackend = Field(
        default="python",
        description="Code generation backend: python, numpy, or sympy",
    )
    variable_types: dict[str, VariableType] = Field(
        default_factory=dict,
        description="Optional variable type hints keyed by source variable name",
    )


class ConvertResponse(BaseModel):
    """Response model for LaTeX conversion."""

    python: str = Field(..., description="Generated Python code")
    variables: list[str] = Field(
        default_factory=list, description="List of variables in the expression"
    )
    error: str | None = Field(
        default=None, description="Error message if conversion failed"
    )
    error_code: str | None = Field(
        default=None,
        description="Stable error code if conversion failed",
    )
    symbol_map: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from source symbols to generated Python identifiers",
    )
    support_level: SupportLevel = Field(
        default="computed",
        description="Whether output is computed Python, symbolic fallback, unsupported, or ambiguous",
    )
    backend: OutputBackend = Field(
        default="python",
        description="Backend used for generated code",
    )
    required_imports: list[str] = Field(
        default_factory=list,
        description="Import statements required by generated code",
    )
    variable_types: dict[str, VariableType] = Field(
        default_factory=dict,
        description="Variable type hints applied during generation",
    )
