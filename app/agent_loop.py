from app.executor import execute_sql
# from app.errors import ERROR_TYPE_MAP

MAX_ITERATIONS = 4
MAX_REPEAT_ERRORS = 2

RECOVERABLE_ERROR_TYPES = {
    "syntax_error",
    "column_not_found",
    "table_not_found",
    "ambiguous_column",
    "aggregation_error",
}


def mock_llm_generate_sql(nl_query: str, observation: dict | None) -> str:
    # temporary stub to simulate an llm to test loop deterministically

    if observation is None:
        # first attempt (intentionally flawed)
        return """
        SELECT customer_id, SUM(price) 
        FROM orders 
        GROUP BY customer_id;
        """

    if observation["error_type"] == "column_not_found":
        # manually correcting
        return """
        SELECT c.customer_id, SUM(p.payment_value)
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_payments p ON o.order_id = p.order_id
        GROUP BY c.customer_id;
        """

    return "SELECT 1;"


def run_agent_loop(nl_query: str) -> dict:
    iteration = 1
    previous_error = None
    error_repeats = 0
    previous_observation = None

    while iteration <= MAX_ITERATIONS:
        sql_query = mock_llm_generate_sql(nl_query, previous_observation)
        observation = execute_sql(sql_query, iteration)

        # Success
        if observation["status"] == "success":
            return observation

        # otherwise: error
        error_type = observation.get("error_type")

        if error_type == previous_error:
            error_repeats += 1
        else:
            error_repeats = 1

        # termination conditions
        if error_repeats >= MAX_REPEAT_ERRORS:
            break

        # start the loop again with (maybe) new error and +1 iteration
        previous_error = error_type
        previous_observation = observation
        iteration += 1

    return {
        "status": "error",
        "message": "Query failed after multiple attempts",
        "last_observation": observation,
    }
