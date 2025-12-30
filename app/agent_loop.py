from app.executor import execute_sql
from app.repair import get_repair_strategy
from app.llm import generate_sql_query_with_llm

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

# placeholder database schema context
schema_context = """
customers(customer_id, customer_unique_id, customer_zip_code_prefix,
customer_city, customer_state)
orders(order_id, customer_id, order_status, order_purchase_timestamp,
order_approved_at, order_delivered_carrier_date,
order_delivered_customer_date, order_estimated_delivery_date)
products(product_id, product_category_name, product_name_length,
product_description_length, product_photos_qty)
order_items(order_id, order_item_id, product_id, seller_id,
shipping_limit_date, price, freight_value) PK(order_id, order_item_id)
order_payments(order_id, payment_sequential, payment_type,
payment_installments, payment_value) PK(order_id, payment_sequential)

FKs:
orders.customer_id -> customers.customer_id
order_items.order_id -> orders.order_id
order_items.product_id -> products.product_id
order_payments.order_id -> orders.order_id
"""


# def mock_llm_generate_sql(
#     nl_query: str,
#     previous_sql_query: str | None,
#     observation: dict | None,
#     repair: dict | None,
# ) -> str:
#     # temporary stub to simulate an llm to test loop deterministically

#     if observation is None:
#         # first attempt (intentionally flawed)
#         return """
#         SELECT customer_id, SUM(price)
#         FROM orders
#         GROUP BY customer_id;
#         """

#     # If we have a repair strategy, follow it (simulate an LLM using 
# feedback)
#     if repair and repair.get("action") == "revise_sql_query":
#         # For this dataset, a correct "revenue per customer"
#         # query goes through order_payments
#         return """
#         SELECT o.customer_id, SUM(p.payment_value) AS total_revenue
#         FROM orders o
#         JOIN order_payments p ON o.order_id = p.order_id
#         GROUP BY o.customer_id
#         ORDER BY total_revenue DESC
#         LIMIT 5;
#         """

#     return "SELECT 1;"


def run_agent_loop(nl_query: str) -> dict:
    iteration = 1
    previous_error = None
    error_repeats = 0

    previous_observation = None
    previous_sql_query = None
    repair = None

    # first attempt to generate query
    sql_query = generate_sql_query_with_llm(
        nl_query=nl_query,
        schema_context=schema_context,
        previous_sql_query=previous_sql_query,
        previous_observation=previous_observation,
        repair=repair,
    )["sql_query"]

    observation = execute_sql(sql_query, iteration)

    if observation["status"] == "success":
        return observation

    while iteration < MAX_ITERATIONS and observation["status"] == "error":
        # otherwise: error
        error_type = observation.get("error_type", "unknown_error")

        if error_type == previous_error:
            error_repeats += 1
        else:
            error_repeats = 1

        # termination conditions
        if error_repeats >= MAX_REPEAT_ERRORS:
            break
        if error_type not in RECOVERABLE_ERROR_TYPES:
            break

        # get repair strategy
        repair = get_repair_strategy(
            error_type=error_type,
            previous_sql_query=sql_query,
            observation=observation,
        )

        # if the query cannot be repaired
        if repair.get("action") != "revise_sql_query":
            break

        # start the loop again with (maybe) new error and +1 iteration
        previous_error = error_type
        previous_observation = observation
        previous_sql_query = sql_query
        iteration += 1

        # generate revised query
        sql_query = generate_sql_query_with_llm(
            nl_query=nl_query,
            schema_context=schema_context,
            previous_sql_query=previous_sql_query,
            previous_observation=previous_observation,
            repair=repair,
        )["sql_query"]

        observation = execute_sql(sql_query, iteration)

        # Success
        if observation["status"] == "success":
            return observation

    return {
        "status": "error",
        "message": "Query failed after multiple attempts",
        "last_observation": observation,
        "query": sql_query
    }
