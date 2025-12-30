# SQL Agent Execution & Repair Subsystem

## Goal
Build a backend service that improves the reliability of LLM-generated SQL by re-prompting LLM with repairs when queries are incorrect.

## Non-goals
- Building a full multi-table agent
- Query optimization

## Data Flow
User Query
→ LLM generates SQL
→ PostgreSQL executes SQL
→ Error classification
→ LLM repair
→ Retry
→ Logs output in Supabase

## Modules
- main.py: API only (for now)
- agent_loop.py: Runs the whole agent loop
- executor.py: SQL execution
- errors.py: error classification
- repair.py: LLM repair logic
- llm.py: Prompts LLM (Gemini) to generate SQL query using natural language
- logging_db.py: Logs agent loop runs and prompting steps into Supabase DB



## Evaluation
Compare baseline vs corrected execution using a fixed query set. (WIP)
