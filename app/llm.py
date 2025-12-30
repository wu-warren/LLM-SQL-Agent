from __future__ import annotations

import json

# import os
from typing import Any, Dict, Optional

# Schema for output

SQL_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "sql_query": {"type": "string"},
        "reasoning": {
            "type": "string",
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },
    },
    "required": ["sql_query", "reasoning", "confidence"],
}

# building prompt


def build_prompt(
    nl_query: str,
    schema_context: str,
    previous_sql_query: Optional[str] = None,
    previous_observation: Optional[Dict[str, Any]] = None,
    repair: Optional[Dict[str, Any]] = None,
) -> str:
    parts = [
        "You are a SQL assistant for PostgreSQL.",
        "Return ONLY JSON with keys: sql_query, reasoning, confidence.",
        "Rules:",
        "- Only generate a single SELECT query (no INSERT/UPDATE/DELETE/DDL).",
        "- Use table/column names exactly as in the schema.",
        "- Prefer explicit JOINs and explicit GROUP BY when aggregating.",
        "",
        "DATABASE SCHEMA:",
        schema_context,
        "",
        f"NATURAL LANGUAGE QUESTION:\n{nl_query}",
    ]

    # if this is not the first prompt
    if previous_sql_query:
        parts.append(f"\nPREVIOUS SQL QUERY:\n{previous_sql_query}")

    if previous_observation:
        obs = {
            "status": previous_observation.get("status"),
            "error_type": previous_observation.get("error_type"),
            "message": previous_observation.get("message"),
            "columns": previous_observation.get("columns"),
            "row_count": previous_observation.get("row_count"),
        }
        parts.append(f"\nLAST OBSERVATION:\n{obs}")

    if repair:
        parts.append(f"\nREPAIR STRATEGY:\n{repair}")

    # Give LLM an example
    parts.append(
        '\nOutput format example:\n{"sql_query":"SELECT ...","reasoning":"...","confidence":0.7}'
    )

    return "\n".join(parts)


def validate_and_normalize(prompt, llm_output: Dict[str, Any]) -> Dict[str, Any]:
    # minimal validation

    for k in ("sql_query", "reasoning", "confidence"):
        if k not in llm_output:
            print(llm_output)
            raise ValueError(f"LLM output missing key: {k}")

    sql_query = str(llm_output["sql_query"]).strip()
    if not sql_query.lower().startswith("select") and not (sql_query is None):
        print(llm_output)
        raise ValueError("Model return non-SELECT SQL query, blocked.")

    conf = float(llm_output["confidence"])
    if conf < 0 or conf > 1:
        raise ValueError("confidence must be between 0 and 1")

    return {
        "sql_query": sql_query,
        "reasoning": str(llm_output["reasoning"]),
        "confidence": conf,
    }


# actual prompting of the LLM, with validation and normalization
def gemini_backend(
    prompt: str,
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    from google import genai

    client = genai.Client()

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )

    raw = response.text
    llm_output = json.loads(raw)

    return validate_and_normalize(prompt, llm_output)


def generate_sql_query_with_llm(
    nl_query: str,
    schema_context: str,
    previous_sql_query: Optional[str] = None,
    previous_observation: Optional[Dict[str, Any]] = None,
    repair: Optional[Dict[str, Any]] = None,
    *,
    provider: str = "gemini",
    model: str = "gemini-2.5-flash",
) -> Dict[str, Any]:
    prompt = build_prompt(
        nl_query=nl_query,
        schema_context=schema_context,
        previous_sql_query=previous_sql_query,
        previous_observation=previous_observation,
        repair=repair,
    )

    if provider == "gemini":
        model = model
        return gemini_backend(prompt=prompt, model=model)

    raise ValueError(f"Unknown LLM provider: {provider}")
