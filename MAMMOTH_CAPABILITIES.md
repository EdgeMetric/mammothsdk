# Mammoth Analytics — Platform Capabilities Reference

## Platform Overview

**Mammoth Analytics** is an enterprise no-code data preparation and analytics platform that enables business users to clean, transform, and analyze data at scale without writing code.

- **Tagline**: "Data prep for the rest of us"
- **Scale**: Handles datasets from thousands to 1B+ rows
- **Target users**: Data analysts, business analysts, operations teams, data engineers
- **Compliance**: SOC 2 Type II, ISO 27001, HIPAA-ready
- **Deployment**: Cloud-hosted (SaaS) with enterprise SSO support

---

## Data Hierarchy

```
Profile (User Account)
  └── Workspace (billing, members, settings)
        └── Project (groups related datasets)
              └── Dataset (uploaded CSV, Excel, or connected source)
                    ├── Batch (data refresh / append)
                    └── View (transformable lens on the data)
                          └── Dashboard (visual reports)
```

- **Workspace**: Top-level container. Owns billing, members, API keys, and integrations (e.g., OpenAI).
- **Project**: Groups related datasets. Auto-discovered when accessing views by ID.
- **Dataset**: One uploaded file or connected data source. Always has at least one view.
- **View**: An independent transformation pipeline on a dataset. Views share underlying data but each has its own pipeline. Every transformation is a reversible **pipeline task**.
- **Dashboard**: Visual reports built from view data (charts, tables, KPIs).

---

## MCP Transformation Tools (26 Total)

### Navigation & Data Access (6 tools)

| Tool | Purpose |
|------|---------|
| `list_projects` | List all projects in the workspace |
| `list_datasets` | List datasets in the active project |
| `get_dataset` | Get dataset details including its views |
| `list_views` | List views in a dataset |
| `get_view` | Get view metadata: columns, types, internal names, row count |
| `get_data` | Fetch row data (max 400 per call, supports filtering/pagination) |

### Column Structure (5 tools)

| Tool | Purpose |
|------|---------|
| `add_column` | Create empty columns (TEXT, NUMERIC, DATE) |
| `delete_columns` | Remove columns from a view |
| `copy_columns` | Duplicate columns with optional type changes |
| `combine_columns` | Merge multiple columns with separator |
| `convert_type` | Change column types (TEXT ↔ NUMERIC ↔ DATE ↔ DATETIME) |

### Value Transformations (8 tools)

| Tool | Purpose |
|------|---------|
| `filter_rows` | Keep/remove rows by conditions (AND/OR, nested) |
| `set_values` | Populate columns based on conditions (classification, labeling) |
| `math_transform` | Arithmetic expressions (SUM, AVG, MIN, MAX, COUNT, ABS, INT) |
| `text_transform` | Case changes (UPPER/LOWER/TITLE), whitespace trimming |
| `replace_values` | Find and replace text with case/word matching |
| `bulk_replace` | Standardize multiple value variations at once |
| `split_column` | Split text by delimiter into new columns |
| `substring` | Extract substrings by position, delimiter, keyword, or regex |

### Aggregation & Reshaping (7 tools)

| Tool | Purpose |
|------|---------|
| `pivot` | Group + aggregate (SUM, AVG, COUNT, MAX, MIN) |
| `window` | Row-aware calculations: RANK, ROW_NUMBER, LAG, LEAD, running totals |
| `crosstab` | Pivot values into column headers (matrix view) |
| `unnest` | Wide → long format (unpivot) |
| `fill_missing` | Fill blanks from nearest non-empty cell (up/down) |
| `limit_rows` | Keep top/bottom N rows |
| `discard_duplicates` | Remove duplicate rows |

### Advanced (3 tools)

| Tool | Purpose |
|------|---------|
| `join_views` | Combine views (LEFT/RIGHT/INNER/OUTER join) |
| `lookup` | VLOOKUP-style: fetch column from reference view by key |
| `json_extract` | Parse JSON text into structured columns/rows |

### Date Operations (3 tools)

| Tool | Purpose |
|------|---------|
| `extract_date` | Extract components (year, month, day, quarter, weekday, etc.) |
| `date_diff` | Calculate time difference between two date columns |
| `increment_date` | Add/subtract time units from dates |

### AI & SQL (2 tools)

| Tool | Purpose |
|------|---------|
| `ai_transform` | OpenAI LLM generates a new column from natural language prompt |
| `sql_query` | DuckDB SQL via natural language intent or direct raw SQL |

### Management & Export (6 tools)

| Tool | Purpose |
|------|---------|
| `create_view` | Create or clone a view |
| `delete_view` | Permanently delete a view |
| `upload_file` | Upload CSV/Excel to create a dataset |
| `export_data` | Export to CSV, S3, email, or another dataset |
| `export_to_database` | Export to PostgreSQL, MySQL, BigQuery, Redshift, Elasticsearch |
| `get_help` | On-demand guidance (6 topics: overview, transformations, conditions, data_cleaning, ai_transform, sql_query) |

---

## AI Capabilities Deep Dive

### ai_transform — AI-Powered Column Generation

- **Provider**: OpenAI LLM (GPT)
- **Prerequisite**: Requires an OpenAI API key configured in workspace settings (Settings → Integrations → OpenAI)
- **What it does**: Creates a NEW column where each row's value is generated by the AI based on a prompt and context columns
- **Row limit**: 50,000 rows (hard limit)
- **Context columns**: Up to 20 per transform
- **Null handling**: Null inputs produce null outputs

#### Performance

| Task Complexity | Time per 10K Rows |
|----------------|-------------------|
| Simple (yes/no, sentiment, category) | 30–60 seconds |
| Medium (extraction, standardization) | 1–3 minutes |
| Complex (generation, multi-sentence) | 2–5 minutes |

#### Validated Use Cases

1. **Sentiment analysis** — Classify text as Positive/Negative/Neutral
2. **Geographic enrichment** — Derive regions, countries, or coordinates from addresses
3. **Categorization** — Classify transactions, products, or support tickets
4. **Content generation** — Product descriptions, summaries, email templates
5. **Data standardization** — Normalize company names, abbreviations, formats
6. **Entity extraction** — Pull names, dates, amounts from unstructured text

#### Prompt Best Practices

- **Constrain outputs**: "Output exactly one of: High, Medium, Low"
- **Provide examples**: "Examples: 'Great service!' → Positive, 'Awful' → Negative"
- **Specify format**: "Return only the city name with no extra text"
- **Minimize context**: Include only columns the AI needs
- **Test first**: Apply to a small filtered subset before full dataset

### sql_query — SQL-Powered Transformations

- **Engine**: DuckDB (columnar, high-performance analytical SQL)
- **SQL generation**: ~20 seconds (intent mode)
- **Two modes**:
  - **Intent**: Natural language → auto-generated DuckDB SQL
  - **Raw SQL**: Direct DuckDB SQL (reference columns by display name)

#### DuckDB SQL Capabilities

- String functions: `||`, `concat()`, `ILIKE`, `regexp_matches()`, `replace()`
- Date functions: `date_diff()`, `date_trunc()`, `extract()`, `strftime()`
- Aggregates: `SUM`, `AVG`, `COUNT`, `MEDIAN`, `PERCENTILE_CONT`, `STRING_AGG`
- Window functions: `ROW_NUMBER()`, `RANK()`, `LAG()`, `LEAD()`, `NTILE()`
- CTEs (`WITH`), subqueries, `CASE WHEN`, `GROUP BY` + `HAVING`
- Set operations: `UNION`, `INTERSECT`, `EXCEPT`
- Type casting: `CAST()`, `::` syntax
- No stored procedures or UDFs — single-statement queries only

### Bulk Replace AI Algorithms

Available through the bulk_replace tool's mapping feature:
- **Smart Match**: AI-powered fuzzy matching for semantic similarity
- **Spelling**: Corrects typos and spelling variations
- **TF-IDF**: Term frequency-based matching for document-like text
- **PDist**: Phonetic distance matching for names and proper nouns

### Extract Text AI Custom Prompt

Available in the platform's Extract Text feature (PDF/image processing):
- **Prerequisite**: Requires an OpenAI API key configured in workspace settings
- 17 extraction methods including OCR, table extraction, and custom AI prompts
- 95% success rate on structured document extraction

---

## Data Connectors

Mammoth supports 200+ data connectors including:

- **Files**: CSV, Excel (XLS/XLSX), JSON, XML, PDF
- **Databases**: PostgreSQL, MySQL, SQL Server, Oracle, BigQuery, Redshift, Snowflake
- **Cloud storage**: AWS S3, Google Cloud Storage, Azure Blob
- **APIs**: REST API connections with authentication
- **SaaS**: Salesforce, HubSpot, Google Sheets, Google Analytics, Shopify
- **Collaboration**: Slack, Microsoft Teams

---

## Dashboard Capabilities

- Bar charts, line charts, pie charts, scatter plots, area charts
- KPI cards and summary metrics
- Geo maps (heatmaps and point maps)
- Pivot tables and data grids
- Filter widgets for interactive exploration
- Scheduled email delivery of dashboard snapshots

---

## Export Destinations

| Format | Details |
|--------|---------|
| **CSV** | Download to local file |
| **S3** | Export to Amazon S3 bucket |
| **Email** | Send data as attachment to recipients |
| **Dataset** | Branch into another Mammoth dataset |
| **PostgreSQL** | Direct database export |
| **MySQL** | Direct database export |
| **BigQuery** | Google BigQuery export |
| **Redshift** | Amazon Redshift export |
| **Elasticsearch** | Index data for search |

---

## Performance Characteristics

| Operation | Typical Speed | Notes |
|-----------|--------------|-------|
| `get_view` | < 1 sec | Metadata only |
| `get_data` (100 rows) | 1–3 sec | Scales with column count |
| Simple transforms | 2–10 sec | filter, set_values, math |
| Aggregate transforms | 5–30 sec | pivot, window, crosstab |
| `sql_query` (intent) | ~20 sec | SQL generation overhead |
| `sql_query` (raw_sql) | 2–15 sec | Direct execution |
| `ai_transform` | 30 sec–5 min | Depends on rows and complexity |
| `join_views` | 5–60 sec | Depends on dataset sizes |
| File upload | 5–60 sec | Depends on file size |

---

## Tool Selection Decision Tree

```
Is the logic deterministic (rules, conditions, arithmetic)?
├── YES → Use a structured tool:
│     ├── Filter rows by condition → filter_rows
│     ├── Classify by rules → set_values
│     ├── Calculate values → math_transform
│     ├── Change case / trim → text_transform
│     ├── Find/replace text → replace_values
│     ├── Standardize variations → bulk_replace
│     ├── Group + aggregate → pivot
│     ├── Rank / running total → window
│     └── Look up reference data → lookup or join_views
│
├── COMPLEX QUERY (multi-step, subqueries, CTEs)?
│     └── sql_query (intent for exploratory, raw_sql for precise)
│
└── REQUIRES LANGUAGE UNDERSTANDING (sentiment, extraction, generation)?
      └── ai_transform (with OpenAI API key configured)
```

---

## Customer Success Stories

- **Starbucks**: Streamlined supply chain data preparation across global markets
- **Rethink First**: Automated clinical data processing and reporting workflows
- **Arla Foods**: Unified product data from multiple ERP systems
- **Everest Detection**: Processed sensor data at scale for anomaly detection

---

## Security & Compliance

- **SOC 2 Type II** certified
- **ISO 27001** certified
- **HIPAA-ready** with BAA available
- Data encryption at rest (AES-256) and in transit (TLS 1.2+)
- Role-based access control (RBAC) with workspace-level permissions
- Enterprise SSO (SAML 2.0, OAuth 2.0)
- Audit logging for all data operations
- Data residency options available

---

## MCP Architecture

The Mammoth MCP server uses a **3-tier progressive disclosure model** to manage LLM context efficiently:

1. **System instructions** (`instructions.py`): ~60 lines loaded into every session. Contains workflow patterns, key rules, and navigation guidance.
2. **Tool docstrings**: Each of the 26 tools has a focused description with parameters. Loaded only when the LLM considers using that tool.
3. **On-demand help** (`get_help`): 6 deep-dive topics (overview, transformations, conditions, data_cleaning, ai_transform, sql_query) loaded only when explicitly requested. Contains detailed examples, best practices, and reference material.

This design keeps the base context small (~2K tokens) while providing access to comprehensive documentation (~15K+ tokens) on demand.
