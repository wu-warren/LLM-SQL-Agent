from dataclasses import asdict
import psycopg2
import os
from app.errors import classify_error, ErrorResult, SuccessResult


MAX_ROWS_RETURNED = 5
QUERY_TIMEOUT_MS = 5_000

# database info


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        dbname=os.getenv("DB_NAME", "llm_sql_agent"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
    )


# actual execution logic


def execute_sql(sql_query: str, iteration: int) -> dict:
    """
    Execute a SQL query and return a structured observation
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # safety: statement timeout
                cur.execute(f"SET statement_timeout = {QUERY_TIMEOUT_MS}")

                cur.execute(sql_query)

                # If the query returns rows, i.e. no syntax error
                if cur.description is not None:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchmany(MAX_ROWS_RETURNED)
                    row_count = len(rows)

                    result = SuccessResult(
                        status="success",
                        iteration=iteration,
                        row_count=row_count,
                        columns=columns,
                        rows=[list(r) for r in rows],
                    )
                else:
                    # nothing returned (SELECT query not used)
                    result = ErrorResult(
                        status="error",
                        iteration=iteration,
                        error_type="permission_error",
                        message="This query did not return rows",
                        hint="Remove DDL/DML statements",
                    )

        # convert dataclass to dict before passing to agent loop 
        return asdict(result)

    except Exception as exc:
        error_type = classify_error(exc)
        message = str(exc).split("\n")[0]

        result = ErrorResult(
            status="error",
            iteration=iteration,
            error_type=error_type,
            message=message,
            hint="Check schema, joins, and aggregation"
            if error_type != "syntax_error"
            else "Fix SQL syntax",
        )
        return asdict(result)
