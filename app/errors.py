from dataclasses import dataclass
from typing import Any, List, Optional

import psycopg2.errors


@dataclass
class ExecutionResult:
    status: str  # "success" | "error"
    iteration: int


@dataclass
class SuccessResult(ExecutionResult):
    row_count: int
    columns: List[str]
    rows: List[List[Any]]


@dataclass
class ErrorResult(ExecutionResult):
    error_type: str
    message: str
    hint: Optional[str] = None


ERROR_TYPE_MAP = {
    psycopg2.errors.SyntaxError: "syntax_error",
    psycopg2.errors.UndefinedTable: "table_not_found",
    psycopg2.errors.UndefinedColumn: "column_not_found",
    psycopg2.errors.AmbiguousColumn: "ambiguous_column",
    psycopg2.errors.GroupingError: "aggregation_error",
    psycopg2.errors.InsufficientPrivilege: "permission_error",
    psycopg2.errors.QueryCanceled: "timeout",
}

# helper to classify errors


def classify_error(exc: Exception) -> str:
    for error_cls, err_type in ERROR_TYPE_MAP.items():
        if isinstance(exc, error_cls):
            return err_type
    return "UnknownError"
