# SQL Agent Execution & Repair Subsystem

## Goal
Build a backend service that improves the reliability of LLM-generated SQL by re-prompting LLM with repairs when queries are incorrect.

## Non-goals
- Building a full multi-table agent
- Competing with SOTA research
- Query optimization
- Frontend product UI

## Data Flow
User Query
→ LLM generates SQL
→ PostgreSQL executes SQL
→ Error classification
→ LLM repair
→ Retry
→ Return results + metrics

## Modules
- main.py: API + orchestration
- executor.py: SQL execution
- errors.py: error taxonomy
- repair.py: LLM repair logic
- schema.py: schema ingestion

## Evaluation
Compare baseline vs corrected execution using a fixed query set.
