# ATHL Analytics Agent — AI-Powered Data Analyst

## Overview

ATHL Analytics Agent is an AI-driven analytics assistant that translates natural language questions into SQL queries and returns actionable insights from structured data.

The system leverages Retrieval-Augmented Generation (RAG) to provide schema-aware, context-rich query generation, enabling users to interact with data without writing SQL.

This project demonstrates how modern LLM systems can be combined with data engineering principles to build scalable, intelligent analytics tools.

---

## Key Features

- Natural language → SQL query generation
- Semantic schema retrieval using vector embeddings
- Metric-aware querying (business logic understanding)
- Self-correction loop for SQL error handling
- Interactive UI for querying and exploration
- Query history and debugging visibility
- Clean modular architecture (RAG-based pipeline)

---

## Architecture
User Input
↓
Retriever (ChromaDB)
↓
Context Builder
↓
LLM (SQL Generation)
↓
SQL Validator
↓
PostgreSQL Execution
↓
Results + Explanation

ARCHITECTURE

          ┌──────────────┐
          │  User Query  │
          └──────┬───────┘
                 ↓
        ┌─────────────────────┐
        │   Embedding Model   │
        └────────┬────────────┘
                 ↓
        ┌─────────────────────┐
        │   Vector DB (RAG)   │
        └────────┬────────────┘
                 ↓
        ┌─────────────────────┐
        │ Context Builder     │
        └────────┬────────────┘
                 ↓
        ┌─────────────────────┐
        │ LLM → SQL           │
        └────────┬────────────┘
                 ↓
        ┌─────────────────────┐
        │ SQL Validator       │
        └────────┬────────────┘
                 ↓
        ┌─────────────────────┐
        │ Query Execution     │
        └────────┬────────────┘
                 ↓
        ┌─────────────────────┐
        │ Self-Correction     │
        └─────────────────────┘


---

## System Design Highlights

### 1. Retrieval-Augmented Generation (RAG)
Instead of passing the entire schema to the LLM, the system:
- Embeds schema metadata into a vector database
- Retrieves only relevant tables and metrics per query
- Improves accuracy and scalability

### 2. Metric-Aware Reasoning
Metrics are treated as first-class entities:
- Embedded alongside schema
- Retrieved contextually
- Used by LLM to generate correct aggregations

### 3. Self-Correction Loop
- Detects SQL execution errors
- Re-prompts LLM with error + schema context
- Automatically retries with corrected SQL

### 4. Modular Pipeline
Each component is isolated:
- Retriever
- Context Builder
- SQL Generator
- Validator
- Query Runner

This makes the system extensible and production-ready.

---

## Tech Stack

- Python
- OpenAI API (LLM + embeddings)
- ChromaDB (vector database)
- PostgreSQL
- Streamlit (UI)

---

## Example Queries

- "total trades"
- "average trades per user"
- "total trades by signup date"
- "trades per athlete"
- "top users by trading activity"

---

## UI Preview

(Add screenshots here)

Suggested screenshots:
- Query → SQL → Results
- Retrieved context (debug)
- Query history sidebar

---

## How to Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```


### 2. Set environment variables

Create .env file:
`OPENAI_API_KEY=your_api_key`

### 3. Run the app
`python -m streamlit run app/ui.py`

Key Challenges Solved
1. Schema Scalability

Problem:
Large schemas overwhelm LLM context

Solution:
Vector search retrieves only relevant tables

2. Incorrect Aggregations

Problem:
LLMs often mis-handle metrics like averages

Solution:
Metric definitions embedded and retrieved
Prompt enforces correct aggregation patterns

3. SQL Failures

Problem:
Invalid SQL generation

Solution:
Validation layer + self-correction loop

4. Join Reasoning

Problem:

Multi-table queries are error-prone

Solution:
Schema-aware prompting + retrieval context

### Future Improvements
#### Planned (Next Phase)
* Hybrid SQL Builder (deterministic query generation)
* Dynamic join resolver using schema relationships
* Query planning layer (multi-step reasoning)
* Caching + performance optimization
#### Product Enhancements
* Dashboarding layer
* User authentication
* Query saving and sharing
* Real-time data connections

### Deployment
#### Recommended: Streamlit Cloud
1. Push to GitHub
2. Deploy via Streamlit Cloud
3. Add secret:

`OPENAI_API_KEY=your_key`

### Why This Project Matters

This project demonstrates:

* Applied LLM engineering
* Data system design (RAG + DB integration)
* Handling real-world AI limitations (hallucination, errors)
* Building end-to-end data products

It bridges:

`Data Engineering + AI + Product Thinking`

### Author
**Ali Khanzadi**

# Conceptual Architecture

                ┌──────────────────────────┐
                │        User (UI)         │
                │    Streamlit (ui.py)     │
                └────────────┬─────────────┘
                             │ user question
                             ↓
                ┌──────────────────────────┐
                │   Retriever (RAG)        │
                │   retriever.py           │
                └────────────┬─────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
        ↓                                         ↓
┌──────────────────────┐             ┌────────────────────────┐
│ schema_docs.json     │             │ vector_store.py        │
│ (data source)        │             │ Chroma DB              │
└──────────┬───────────┘             └──────────┬─────────────┘
           │                                    │
           │ load + format                      │ similarity search
           ↓                                    ↓
     ┌────────────────────────────────────────────┐
     │ embeddings.py                              │
     │ → text chunks + embeddings                 │
     └────────────────────────────────────────────┘
                             │
                             ↓
                ┌──────────────────────────┐
                │  context_builder.py      │
                │  → clean schema context  │
                └────────────┬─────────────┘
                             │
                             ↓
                ┌──────────────────────────┐
                │   generate_sql.py        │
                │   (LLM)                  │
                └────────────┬─────────────┘
                             │ SQL
                             ↓
                ┌──────────────────────────┐
                │   validator.py           │
                │   → safe SQL only        │
                └────────────┬─────────────┘
                             │
                             ↓
                ┌──────────────────────────┐
                │   query_runner.py        │
                │   → Postgres execution   │
                └────────────┬─────────────┘
                             │ results / error
                 ┌───────────┴────────────┐
                 ↓                        ↓
   ┌──────────────────────────┐   ┌──────────────────────────┐
   │ explain_results.py       │   │ generate_sql.fix_sql()   │
   │ → natural language       │   │ → retry on failure       │
   └────────────┬─────────────┘   └────────────┬─────────────┘
                │                              │
                └──────────────┬───────────────┘
                               ↓
                ┌──────────────────────────┐
                │ UI (Streamlit)           │
                │ → SQL + table + explain  │
                └──────────────────────────┘

Key clarifications
* schema_docs.json is the semantic layer (tables + metrics)
* embeddings.py converts schema → vectors
* vector_store.py persists them in Chroma
* retriever.py mixes:
    * deterministic metric matching
    * vector similarity for tables
* context_builder.py turns raw docs → clean prompt text
* generate_sql.py is the core reasoning step (LLM)
* validator.py enforces read-only SQL safety
* query_runner.py executes against Postgres                

# Execution Pipeline (Function-Level Flow when main.py runs)

This shows actual function calls and interactions.
User Input (Streamlit UI)
        │
        ↓
retrieve_relevant_docs(question)
        │
        ├── load_schema_docs()                [embeddings.py]
        ├── format_doc()
        ├── OpenAI embeddings (question)
        ├── get_collection()                 [vector_store.py]
        ├── query_collection()
        └── return relevant docs
        │
        ↓
build_context(docs)                          [context_builder.py]
        │
        └── returns formatted schema text
        │
        ↓
generate_sql(question)                       [generate_sql.py]
        │
        ├── retrieve_relevant_docs()   (called AGAIN internally)
        ├── build_context()
        ├── construct prompt
        ├── OpenAI chat.completions()
        └── clean_sql()
        │
        ↓
validate_sql(sql)                            [validator.py]
        │
        ├── check starts with SELECT
        └── block unsafe keywords
        │
        ↓
enforce_limit(sql)
        │
        └── append LIMIT if missing
        │
        ↓
PostgresClient.run_query(sql)                [query_runner.py]
        │
        ├── psycopg2 execute
        └── return results OR error
        │
        ├───────────────┐
        │               │
        ↓               ↓
SUCCESS           ERROR PATH
        │               │
        │         fix_sql(question, sql, error, context)
        │               │
        │         ├── OpenAI call
        │         └── corrected SQL
        │               │
        │         run_query() again
        │
        ↓
explain_results(question, sql, results)      [explain_results.py]
        │
        └── OpenAI explanation
        │
        ↓
Streamlit UI Rendering
        ├── SQL
        ├── DataFrame
        ├── Explanation
        └── Debug context

--------------
FROM DAY 11
# ATHL Analytics Agent — AI-Powered Data Analyst

## Overview

ATHL Analytics Agent is an AI-driven analytics assistant that translates natural language questions into SQL queries and returns actionable insights from structured data.

The system leverages Retrieval-Augmented Generation (RAG) to provide schema-aware, context-rich query generation, enabling users to interact with data without writing SQL.

This project demonstrates how modern LLM systems can be combined with data engineering principles to build scalable, intelligent analytics tools.

---

## Key Features

- Natural language → SQL query generation
- Semantic schema retrieval using vector embeddings
- Metric-aware querying (business logic understanding)
- Self-correction loop for SQL error handling
- Interactive UI for querying and exploration
- Query history and debugging visibility
- Clean modular architecture (RAG-based pipeline)

---

## Architecture


User Input
↓
Retriever (ChromaDB)
↓
Context Builder
↓
LLM (SQL Generation)
↓
SQL Validator
↓
PostgreSQL Execution
↓
Results + Explanation


---

## System Design Highlights

### 1. Retrieval-Augmented Generation (RAG)
Instead of passing the entire schema to the LLM, the system:
- Embeds schema metadata into a vector database
- Retrieves only relevant tables and metrics per query
- Improves accuracy and scalability

### 2. Metric-Aware Reasoning
Metrics are treated as first-class entities:
- Embedded alongside schema
- Retrieved contextually
- Used by LLM to generate correct aggregations

### 3. Self-Correction Loop
- Detects SQL execution errors
- Re-prompts LLM with error + schema context
- Automatically retries with corrected SQL

### 4. Modular Pipeline
Each component is isolated:
- Retriever
- Context Builder
- SQL Generator
- Validator
- Query Runner

This makes the system extensible and production-ready.

---

## Tech Stack

- Python
- OpenAI API (LLM + embeddings)
- ChromaDB (vector database)
- PostgreSQL
- Streamlit (UI)

---

## Example Queries

- "total trades"
- "average trades per user"
- "total trades by signup date"
- "trades per athlete"
- "top users by trading activity"

---

## UI Preview

(Add screenshots here)

Suggested screenshots:
- Query → SQL → Results
- Retrieved context (debug)
- Query history sidebar

---

## How to Run Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt        