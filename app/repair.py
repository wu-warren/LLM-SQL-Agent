# Takes in:
# error_type
# previous SQL query
# (optional) schema context

# Outputs:
# instructions for next attempt
# Example:
# {
#     "action": "revise_query",
#     "instructions": "...",
#     "constraints": [...]
# }


from typing import Dict


def get_repair_strategy(error_type: str, previous_sql_query: str, observation: Dict) -> Dict:
    """
    given an error type and execution observation,
    return a repair strategy for the LLM's next attempt
    """

    if error_type == "column_not_found":
        return {
            "action": "revise_sql_query",
            "instructions": (
                "One or more referenced columns do not exist. "
                "Review the schema and ensure all columns are valid. "
                "Add necessary joins or correct column names."
            ),
            "constraints": [
                "Use only existing columns",
                "verify joins explicitly",
            ],
        }
    if error_type == "table_not_found":
        return {
            "action": "revise_sql_query",
            "instructions": (
                "A referenced table does not exist. "
                "Check table names against the schema and correct them."
            ),
            "constraints": [
                "Use only known tables",
            ],
        }

    if error_type == "aggregation_error":
        return {
            "action": "revise_sql_query",
            "instructions": (
                "Aggregation error detected. Ensure all non-aggregated columns appear in GROUP BY."
            ),
            "constraints": [
                "Every selected non-aggregate column must be grouped",
            ],
        }

    if error_type == "ambiguous_column":
        return {
            "action": "revise_sql_query",
            "instructions": (
                "Column reference is ambiguous. Qualify column names with table aliases."
            ),
            "constraints": [
                "Use table aliases for all column references",
            ],
        }

    # Fallback
    return {
        "action": "abort",
        "reason": f"No repair strategy available for error_type='{error_type}'",
    }
