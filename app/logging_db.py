import os
import time
import json

import psycopg2


def connect():
    return psycopg2.connect(
        host=os.environ["SUPABASE_DB_HOST"],
        port=int(os.environ.get("SUPABASE_DB_PORT", "5432")),
        dbname=os.environ.get("SUPABASE_DB_NAME", "postgres"),
        user=os.environ.get("SUPABASE_DB_USER", "postgres"),
        password=os.environ["SUPABASE_DB_PASSWORD"],
    )


def create_run(nl_query: str, created_at: time, provider: str | None, model: str | None) -> int:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_runs 
                    (nl_query, created_at, provider, model, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING run_id
                """,
                (nl_query, created_at, provider, model, "running"),
            )
            run_id = cur.fetchone()[0]
            return run_id


def log_step(run_id: int, iteration: int, sql_query: str | None, obs: dict, elapsed_ms: int, llm_output: dict | None):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO agent_steps
                (run_id,
                iteration,
                sql_query,
                status,
                error_type,
                message,
                row_count,
                elapsed_ms,
                rows,
                llm_output)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
            (
                run_id,
                iteration,
                sql_query,
                obs.get("status"),
                obs.get("error_type"),
                obs.get("message"),
                obs.get("row_count"),
                elapsed_ms,
                json.dumps(obs.get("rows"), default=str),
                json.dumps(llm_output, default=str),
            ),
        )


def finish_run(run_id: int, status: str, final_obs: dict, sql_query: str | None) -> int:
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE agent_runs
                SET status = %s, final_error_type = %s, final_message = %s, final_rows = %s, final_query = %s
                WHERE run_id = %s;
                """,
                (
                    status,
                    final_obs.get("error_type"),
                    final_obs.get("message"),
                    json.dumps(final_obs.get("rows"), default=str),
                    sql_query,
                    run_id,
                ),
            )
            updated = cur.rowcount
            conn.commit()
            return updated  # 1 if updated, 0 if no matching row
    except Exception as e:
        # log exception somewhere visible
        print("finish_run error:", e)
        # if conn exists and is open, rollback
        try:
            conn.rollback()
        except Exception:
            pass
        raise
