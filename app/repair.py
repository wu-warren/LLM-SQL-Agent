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


def get_repair_strategy(
    error_type: str, previous_sql_query: str, observation: Dict
) -> Dict:
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
            ]
        }
    raise NotImplementedError
