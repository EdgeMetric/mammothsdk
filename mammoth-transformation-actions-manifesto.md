# Mammoth Transformation & Actions Manifesto

**Version:** 1.0
**Owner:** Engineering Team
**Purpose:** Authoritative reference for AI Prompt feature intelligence — grounding the LLM in complete, accurate awareness of Mammoth's transformation and action capabilities to produce robust, high-quality pipeline suggestions.
**Last Updated:** February 2026
**Status:** Engineering Handoff — Modify and Extend as Needed

---

## Table of Contents

1. [Manifesto Objectives](#1-manifesto-objectives)
2. [Complete Capability Map](#2-complete-capability-map)
3. [Schema Awareness Protocol](#3-schema-awareness-protocol)
4. [Intent Decomposition & Creative Composition](#4-intent-decomposition--creative-composition)
5. [Sequencing & Dependency Rules](#5-sequencing--dependency-rules)
6. [Disambiguation & Clarification Protocol](#6-disambiguation--clarification-protocol)
7. [Display Changes vs Pipeline Tasks Boundary](#7-display-changes-vs-pipeline-tasks-boundary)
8. [Orchestration Awareness](#8-orchestration-awareness)
9. [Performance Optimization Rules](#9-performance-optimization-rules)
10. [Failure Mode Catalog & Guardrails](#10-failure-mode-catalog--guardrails)
11. [Testing & Validation Framework](#11-testing--validation-framework)
12. [Maintenance & Evolution Guidelines](#12-maintenance--evolution-guidelines)

---

## 1. Manifesto Objectives

### What This Document Solves

The AI Prompt feature currently suggests pipelines based on user intent but operates with incomplete awareness of Mammoth's full capability surface. This leads to:

- Suggesting only "common patterns" while missing creative multi-step solutions
- Misinterpreting intent when ambiguity exists (e.g., "clean up my data" could mean 5 different things)
- Not leveraging schema statistics to make intelligent function and parameter choices
- Producing functionally correct but poorly sequenced (slow) pipelines
- Occasional accuracy errors (e.g., network days calculation discrepancies observed in customer demos)
- No awareness of what Mammoth CANNOT do (leading to impossible suggestions)

### Success Criteria

The AI Prompt should:

1. **Know every function** — Complete awareness of all 30+ transformations, their parameters, operators, data type requirements, and edge cases
2. **Think in pipelines** — Decompose complex intents into multi-step sequences with correct dependency ordering
3. **Use the data** — Leverage Level 1 profiling statistics (column types, unique values, distributions, nulls) to make informed choices
4. **Optimize by default** — Produce pipelines that follow performance best practices (filter early, aggregate before join, remove unnecessary columns)
5. **Know its limits** — Clearly communicate what it cannot do and suggest workarounds
6. **Be testable** — Every capability claim is verifiable against a structured test suite

---

## 2. Complete Capability Map

### 2.1 Transform Menu Architecture

The Transform menu is organized into 6 categories. The AI must know every function, its category, its parameters, and its constraints.

#### Category 1: AI Powered (5 functions)

**SQL Query**
- Purpose: Run AI-assisted SQL queries directly on current dataset
- Input: Natural language description of desired query
- Output: Query results applied to dataset
- Engine: DuckDB SQL execution
- Constraints: Query must be valid against current schema; complex subqueries may have performance implications on large datasets
- When to suggest: Complex analytical queries, aggregations across multiple conditions, window-function-style calculations that don't map cleanly to other UI functions

**Generative AI**
- Purpose: Use natural language to transform or enrich data using LLM
- Input: Natural language instruction + target column(s)
- Output: New or modified column with AI-generated values
- Capacity: 50,000 row limit per execution
- When to suggest: Categorization, sentiment analysis, text summarization, data enrichment that requires reasoning, entity extraction from unstructured text
- When NOT to suggest: Simple deterministic operations (use specific functions instead); datasets exceeding 50K rows without pre-filtering

**Extract Text**
- Purpose: Pull specific text patterns from a column using AI pattern recognition
- Input: Column selection + extraction description
- Output: New column with extracted values
- When to suggest: Area codes from phone numbers, domains from emails, SKUs from product descriptions, structured data from semi-structured text
- Alternative: For simple patterns, regex-based extraction via SQL Query may be faster and more reliable

**Bulk Replace**
- Purpose: Many-to-one mapping for data standardization with AI-powered similarity detection
- Input: Column selection; AI suggests groupings based on similarity algorithms
- Algorithms: Smart (general purpose), Spelling Match (typos/OCR), Common Patterns (entity suffixes, abbreviations), Similarity (structured identifiers)
- Output: Standardized values replacing variations
- AI Behavior: Suggests groupings automatically; user reviews/modifies before applying
- When to suggest: Company name standardization, product name consolidation, department harmonization, address standardization, any column with inconsistent categorical values
- Evidence: Customer validated "47 variations of company names cleaned in 2 minutes"

**Conditional Filter**
- Purpose: Show only rows matching specific conditions
- Operators: =, ≠, >, <, ≥, ≤, IN, NOT IN, CONTAINS, STARTS WITH, ENDS WITH
- Logic: AND/OR combinations, nested conditions supported
- Type-awareness: Different operator sets for text, numeric, and date columns
- Multiple creation methods: Transform menu, Explore Card selection, Column Header filter, Convert Visual Filters
- When to suggest: Data subsetting, business rule enforcement, quality gates, isolating records for analysis
- Performance note: Most selective filters should be placed early in pipeline

#### Category 2: Filter, Label & Replace (8 functions)

**Conditional Filter** (also appears in AI Powered)
- See above for full specification

**Remove Duplicates**
- Purpose: Eliminate duplicate rows based on specified column(s)
- Input: Select column(s) that define uniqueness
- Behavior: Keeps first occurrence, removes subsequent duplicates
- Options: Exact match; fuzzy matching with configurable similarity thresholds
- When to suggest: CRM deduplication, transaction deduplication, imported data cleanup
- Important: Define "duplicate" carefully — same email but different name might not be a true duplicate

**Find & Replace**
- Purpose: Column-specific value replacement with pattern matching
- Input: Column, find value, replace value
- Options: Case-sensitive toggle, pattern matching
- When to suggest: Simple one-to-one replacements, fixing specific known values, standardizing codes
- vs. Bulk Replace: Find & Replace is for known specific replacements; Bulk Replace is for discovering and grouping unknown variations

**Label & Insert Values**
- Purpose: Create labels or insert calculated/constant values based on conditions
- Input: Condition definition + value to insert
- Output: New or modified column with labeled/inserted values
- When to suggest: Creating categorical flags ("High"/"Medium"/"Low"), inserting default values, conditional labeling based on business rules
- Usage frequency: 301 occurrences across analyzed pipelines (3rd most common)

**Show Top/Bottom**
- Purpose: Display fixed number of rows sorted by a column
- Input: Column to sort by, count, top or bottom
- When to suggest: Performance rankings, outlier investigation, sampling top/bottom performers

**Filter Data**
- Purpose: Complex condition-based row removal with multi-criteria support
- Note: Overlaps with Conditional Filter — use whichever entry point the user is most comfortable with

**Sort**
- Purpose: Order rows by one or more columns
- Input: Column(s) + ascending/descending
- When to suggest: When output order matters for reporting or downstream consumption

**Send Between Datasets**
- Purpose: Transfer selected rows or columns from one dataset to another within the same project
- Input: Source dataset/view, target dataset, column mapping
- When to suggest: Splitting datasets, routing data to different processing paths, creating derivative datasets

#### Category 3: Date, Numeric & Text (9 functions)

**Math Functions**
- Purpose: Perform calculations on numeric columns
- Arithmetic: Add, Subtract, Multiply, Divide
- Aggregates: Sum, Average, Min, Max, Count
- Advanced: Round, Ceiling, Floor, Absolute Value, Power, Square Root
- Conditional: IF statements with math operations
- Input modes: Formula builder OR text expression
- Multi-column: Yes — can reference multiple columns in one formula
- Constants: Can include constant values in formulas
- Usage frequency: 569 occurrences (HIGHEST of all functions)
- When to suggest: Any derived numeric calculation — margins, ratios, running totals, conditional calculations

**Window Functions**
- Purpose: Calculations across a set of rows related to current row (without collapsing rows)
- Available: ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, cumulative SUM, moving AVG
- Partition by: Optional grouping column(s)
- Order by: Required sort column(s)
- When to suggest: Rankings within groups, time-series analysis, running totals, period-over-period comparisons, sequence numbering
- Key distinction from Group & Pivot: Window functions preserve individual rows; Group & Pivot collapses rows

**Text Formatting**
- Purpose: Clean, standardize, format text values
- Operations: UPPERCASE, lowercase, Proper Case, TRIM (leading/trailing/all whitespace), CLEAN (remove non-printable)
- When to suggest: Standardizing case before joins or comparisons, cleaning imported data, preparing display-ready text

**Combine Multiple Columns**
- Purpose: Concatenate values from multiple columns into a single column
- Input: Column selection + delimiter/separator
- Output: New column with combined text (or overwrite existing)
- Options: Custom separator text, handle nulls (skip or include)
- When to suggest: Full names from first/last, composite keys, formatted addresses, descriptive labels

**Date Difference**
- Purpose: Calculate time difference between two date columns or between a date column and current time
- Input: Start date (column or current time), End date (column or current time), Unit (days, months, years, hours)
- Output: New numeric column with calculated difference
- When to suggest: Age calculations, tenure, days outstanding, SLA measurement, time-to-event analysis
- Known limitation: Business days / network days calculation requires careful handling — standard date difference gives calendar days only

**Date Formatting**
- Purpose: Parse, format, and standardize date values
- Operations: Format conversion, component extraction (year, month, day, quarter)
- When to suggest: Standardizing dates from multiple sources, extracting date components for grouping/analysis

**Convert Column Type**
- Purpose: Change column data type (Text → Numeric, Text → Date, Numeric → Text, etc.)
- Critical prerequisite: Often requires pre-cleaning (remove currency symbols, parentheses, etc. before Text → Numeric)
- Usage frequency: 213 occurrences across analyzed pipelines
- When to suggest: Before any math operation on text-formatted numbers, before date operations on text-formatted dates, before joins where key types don't match
- Failure mode: Conversion fails silently on incompatible values — always suggest pre-cleaning

**Extract Text** (also in AI Powered)
- When accessed from this category: Uses regex/pattern-based extraction rather than AI
- When to suggest: Well-defined patterns (area codes, domains, zip codes) where regex is more reliable than AI interpretation

**Find & Replace** (also in Filter, Label & Replace)
- Same function accessible from multiple categories

#### Category 4: Reshape, Group & Pivot (4 functions)

**Group & Pivot**
- Purpose: Aggregate data by categories with optional cross-tabulation
- Group By: Select one or more grouping columns
- Aggregations: SUM, COUNT, AVG, MIN, MAX, MEDIAN, STDEV on measure columns
- Pivot (Crosstab): Optional — rotate values from a column into column headers
- Output: Collapsed/aggregated dataset
- When to suggest: Summary reporting, KPI calculations, dimensional analysis, creating pivot-table-style outputs
- Important: This collapses rows — ensure user understands data granularity will change

**Columns to Rows (Unpivot)**
- Purpose: Transform columns into rows (wide format → long format)
- Input: Select columns to unpivot
- Output: Two new columns (attribute name, attribute value) with row multiplication
- When to suggest: Normalizing wide-format data (monthly columns → single month column), preparing data for visualization tools that expect long format

**Crosstab** (part of Group & Pivot)
- Purpose: Create cross-tabulation / pivot table output
- Input: Row grouping column, column header column, value column, aggregation function
- When to suggest: Matrix-style reporting, comparing categories across dimensions

**Flatten / Normalize**
- Purpose: Flatten nested or hierarchical data structures
- When to suggest: JSON-derived data, multi-value fields, parent-child structures

#### Category 5: Column Management (6 functions)

**Add Column**
- Purpose: Create new empty or constant-value column
- Input: Column name, optional default value
- Usage frequency: 243 occurrences across analyzed pipelines
- When to suggest: Creating flag columns, placeholder columns for subsequent calculations, constant-value columns for labeling

**Copy Columns**
- Purpose: Duplicate existing columns
- Usage frequency: 416 occurrences (2nd highest after Math Function)
- When to suggest: Preserving original values before transformation, creating working copies for calculations

**Convert Column Type**
- Also accessible from Date, Numeric & Text category — same function

**Remove Columns**
- Purpose: Permanently delete columns from pipeline output
- When to suggest: Removing PII, dropping unnecessary columns for performance, cleaning up helper/intermediate columns
- Performance value: Removing columns early reduces memory footprint for subsequent operations

**Split Into Multiple Columns**
- Purpose: Separate one column into multiple columns based on delimiter or position
- Input: Column, delimiter (or position), number of output columns
- When to suggest: Splitting full names, parsing CSV-within-CSV, separating composite codes, extracting components from structured strings

**CRITICAL: There is NO "Rename Column" function in Column Management.**
- Column renaming is done exclusively through Display Changes (right-click column header → Rename)
- The AI must NEVER suggest a "Rename Column" pipeline task — it does not exist

#### Category 6: Unify (3 functions)

**Join**
- Purpose: Combine two datasets based on matching values in specified columns
- Types: Inner Join, Left Join, Right Join, Full Outer Join
- Configuration: Select second dataset/view, choose join column(s) from each side, select join type, preview results
- Usage frequency: 201 occurrences across analyzed pipelines
- When to suggest: Enriching data with lookup tables, combining related datasets, dimensional modeling
- Common issues to warn about: Duplicate row explosion when join keys not unique, column name conflicts (auto-renamed with suffix), performance with very large datasets
- AI should consider: Which join type preserves the right rows? Are join keys unique on at least one side?

**Lookup**
- Purpose: Enrich current dataset with values from another dataset (similar to VLOOKUP)
- Input: Lookup dataset, matching columns, columns to bring in
- When to suggest: Adding reference data (e.g., customer names from customer master), enrichment without full join complexity
- vs. Join: Lookup is simpler and more intuitive for one-directional enrichment; Join is for true two-way combining

**Append (Union)**
- Purpose: Stack datasets vertically (combine rows from multiple datasets with same schema)
- Input: Second dataset with matching column structure
- Schema validation: Column names must match (enforced)
- When to suggest: Combining monthly files, stacking regional data, unioning data from multiple sources with same structure

### 2.2 Summary Capability Matrix

| Category | Functions | Most Used | Key Notes |
|----------|-----------|-----------|-----------|
| AI Powered | SQL Query, Generative AI, Extract Text, Bulk Replace, Conditional Filter | Bulk Replace, Conditional Filter | 50K row limit on Generative AI |
| Filter, Label & Replace | Conditional Filter, Remove Duplicates, Find & Replace, Label & Insert Values, Show Top/Bottom, Filter Data, Sort, Send Between Datasets | Label & Insert (301), Conditional Filter (280) | Most common entry point for business rules |
| Date, Numeric & Text | Math Functions, Window Functions, Text Formatting, Combine Columns, Date Difference, Date Formatting, Convert Column Type, Extract Text, Find & Replace | Math Functions (569), Convert Column Type (213) | Math Functions is THE most-used function |
| Reshape, Group & Pivot | Group & Pivot, Columns to Rows, Crosstab, Flatten | Group & Pivot | Collapses rows — data granularity changes |
| Column Management | Add Column, Copy Columns, Convert Column Type, Remove Columns, Split Into Multiple Columns | Copy Columns (416), Add Column (243) | NO Rename Column — use Display Changes |
| Unify | Join, Lookup, Append | Join (201) | Preview before applying joins |

---

## 3. Schema Awareness Protocol

### 3.1 What the AI Knows About the Data

When a user opens the AI Prompt, the system has access to Level 1 data profiling statistics generated automatically by DuckDB. The AI MUST use these to make informed suggestions.

**Available Statistics Per Column:**

| Statistic | What It Tells the AI |
|-----------|---------------------|
| Column name | Semantic hints about content (e.g., "email", "phone", "amount") |
| Data type | Text, Numeric, Date — determines which functions are applicable |
| Unique value count | High cardinality = likely identifier; Low cardinality = likely categorical |
| Null count / percentage | Drives data quality recommendations |
| Min / Max (numeric) | Range validation, outlier detection hints |
| Mean / StdDev (numeric) | Distribution shape, anomaly context |
| Sample values | Pattern recognition (date formats, phone formats, code structures) |
| Value distribution | Top values by frequency — reveals dominant categories and variations |

### 3.2 How the AI Should Use Schema Statistics

**Column Type → Function Eligibility:**
- Text columns: Bulk Replace, Find & Replace, Text Formatting, Extract Text, Combine Columns, Split
- Numeric columns: Math Functions, Window Functions, Conditional Filter (numeric operators)
- Date columns: Date Difference, Date Formatting, Conditional Filter (date operators)
- Before suggesting Math Functions on a text column, ALWAYS suggest Convert Column Type first

**Unique Value Count → Function Selection:**
- Very low unique count (2-10): Likely categorical → suggest Label & Insert, Conditional Filter, or Group & Pivot
- Medium unique count (10-100): Possible standardization target → suggest Bulk Replace
- High unique count (100+): Likely identifier or free-text → suggest Extract Text, Split, or leave as-is
- Unique count = row count: Likely primary key → suitable as join key

**Null Count → Pre-processing Recommendations:**
- Any nulls present: Warn user about null handling implications before aggregations (nulls excluded from AVG, COUNT varies)
- High null percentage (>20%): Suggest explicit null handling step — either filter out nulls, replace with defaults (Label & Insert), or document the impact
- Null in join key columns: Warn that null keys will not match in joins

**Sample Values → Pattern Recognition:**
- If sample values show currency formatting ("$1,234.56"): Suggest Find & Replace to strip formatting, then Convert Column Type to Numeric
- If sample values show date-like text ("12/31/2023"): Suggest Convert Column Type to Date with format specification
- If sample values show inconsistent casing ("Corp", "CORP", "corp"): Suggest Text Formatting (Proper Case or UPPERCASE) or Bulk Replace

### 3.3 Cross-Dataset Awareness for Joins

When the user's intent involves combining data, the AI should:

1. Identify potential join keys by comparing column names and types across datasets in the project
2. Assess join key quality: unique count relative to row count (is it truly a key?)
3. Recommend join type based on intent: "enrich with" → Left Join; "find matching" → Inner Join; "find all" → Full Outer Join
4. Warn about potential row explosion if join keys are not unique on at least one side

---

## 4. Intent Decomposition & Creative Composition

### 4.1 Core Principle

Most user intents map to MULTIPLE pipeline steps, not a single function. The AI's primary job is decomposing a natural language intent into an ordered sequence of Mammoth transformation tasks.

### 4.2 Intent-to-Pipeline Decomposition Patterns

**Pattern: Data Cleaning Intent**
User says: "Clean up my data" / "Fix this data" / "Prepare this for analysis"
Decomposition:
1. Identify and handle nulls (Label & Insert or Conditional Filter)
2. Remove duplicates (Remove Duplicates)
3. Standardize text values (Bulk Replace or Text Formatting)
4. Fix data types (Convert Column Type)
5. Remove unnecessary columns (Remove Columns)

**Pattern: Standardization Intent**
User says: "Standardize vendor names" / "Clean up company names" / "Consolidate categories"
Decomposition:
1. Text Formatting (normalize case first — makes Bulk Replace more effective)
2. Bulk Replace (AI-powered grouping of variations)
3. Optional: Find & Replace for any remaining known edge cases

**Pattern: Financial Calculation Intent**
User says: "Calculate margins" / "Compute net amounts" / "Create financial summary"
Decomposition:
1. Convert Column Type (ensure all monetary columns are numeric)
2. Find & Replace (strip currency symbols, parentheses if present)
3. Math Functions (compute derived values: margin = revenue - cost)
4. Optional: Window Functions (running totals, period-over-period)
5. Optional: Group & Pivot (summarize by dimension)

**Pattern: Combine & Enrich Intent**
User says: "Join with customer data" / "Add region info" / "Enrich with reference data"
Decomposition:
1. Assess join key quality in both datasets
2. Pre-clean join keys if needed (Text Formatting, Convert Column Type)
3. Join or Lookup (select appropriate type)
4. Remove duplicate columns from join result (Remove Columns)
5. Optional: Handle nulls from non-matching rows

**Pattern: Reporting & Aggregation Intent**
User says: "Summarize by region" / "Create monthly totals" / "Build a pivot table"
Decomposition:
1. Filter to relevant data subset (Conditional Filter)
2. Ensure correct data types for measures (Convert Column Type)
3. Group & Pivot with appropriate aggregation functions
4. Optional: Math Functions for derived metrics on aggregated data
5. Optional: Sort for reporting order

**Pattern: Time-Based Analysis Intent**
User says: "Calculate days between..." / "Show aging" / "Measure SLA"
Decomposition:
1. Ensure date columns are Date type (Convert Column Type)
2. Date Difference (with appropriate unit)
3. Optional: Label & Insert to create aging buckets
4. Optional: Conditional Filter to flag overdue items

**Pattern: Data Reshaping Intent**
User says: "Pivot this data" / "Make wide to long" / "Transpose months to rows"
Decomposition:
1. If wide → long: Columns to Rows (Unpivot)
2. If long → wide: Group & Pivot with Crosstab
3. Post-reshape cleanup: Rename via Display Changes, fix types if needed

### 4.3 Creative Composition Guidelines

The AI should think creatively about HOW to achieve an intent, not just which single function to use. Guidelines:

1. **Pre-processing enables accuracy**: Before the "main" operation, insert preparation steps. Cleaning before joining, converting types before calculating, filtering before aggregating.

2. **Combine functions for effects Mammoth doesn't have natively**: For example, "calculate business days" isn't a single function — it requires Date Difference + Conditional Filter (exclude weekends) + potentially a Join with a holiday calendar dataset + Math Functions to subtract holiday count.

3. **Use intermediate columns**: Copy Columns to preserve originals, Add Column for flags/helpers, then remove them at the end. This is a standard pattern — don't try to do everything in-place.

4. **Think about what DOESN'T exist and route around it**: There's no native "deduplicate and keep the most recent" — decompose into: Sort by date descending → Window Function (ROW_NUMBER partitioned by key) → Conditional Filter (keep only row_number = 1).

5. **Leverage SQL Query as escape hatch**: When the no-code functions can't express the logic (complex CASE statements, nested subqueries, CTEs), suggest SQL Query with the DuckDB-valid SQL.

### 4.4 Common Multi-Step Patterns from Real Pipelines

These patterns are derived from analysis of 200+ production customer pipelines (average 22.6 steps per pipeline):

**Standard Data Prep Sequence (8 steps):**
1. Filter to relevant date range (performance)
2. Remove test/invalid data (quality)
3. Select required columns (performance)
4. Standardize text formatting (quality)
5. Convert data types (enable analysis)
6. Handle nulls appropriately (quality)
7. Derive calculated fields (business logic)
8. Aggregate to required granularity (reporting)

**Customer Analysis Workflow:**
1. Filter to active customers and recent timeframe
2. Deduplicate customer records
3. Calculate RFM metrics (Recency, Frequency, Monetary) using Math Functions + Window Functions
4. Label customers into segments using Label & Insert
5. Group & Pivot for segment-level summary

**Financial Report Preparation (4-phase):**
- Phase 1: Data Cleaning — strip formatting, standardize text
- Phase 2: Type Conversion — text to numeric, text to date
- Phase 3: Derived Calculations — net amounts, days outstanding, period grouping
- Phase 4: Aggregation — group by account, category, period

**Complex Integration Pipeline (representative of 30+ step pipelines):**
Window Function → Conditional Filter → Join → Join → Join → Conditional Filter → Copy Columns → Extract Text → Convert Column Type → Bulk Replace → Add Column → Window Function → Math Function → Join → Copy Columns → Math Function → Crosstab → Add Column → Join

---

## 5. Sequencing & Dependency Rules

### 5.1 Core Sequencing Principle

Mammoth pipelines execute sequentially — each step operates on the output of the previous step. Order matters for both correctness and performance.

### 5.2 Hard Dependencies (Correctness)

These ordering rules are mandatory. Violating them produces wrong results or errors:

| Must Come First | Must Come After | Reason |
|----------------|-----------------|---------|
| Find & Replace (strip formatting) | Convert Column Type (Text → Numeric) | Conversion fails on "$1,234" |
| Convert Column Type (Text → Date) | Date Difference | Date functions require Date type |
| Convert Column Type (Text → Numeric) | Math Functions | Math on text produces errors |
| Join / Lookup | Any operation on joined columns | Columns don't exist until join completes |
| Copy Columns | Math Functions that overwrite source | Preserves original for audit/debugging |
| Add Column (flag) | Conditional Filter on flag | Can't filter on column that doesn't exist |
| Bulk Replace (standardize) | Group & Pivot | Grouping on unstandardized values creates fragmented groups |
| Text Formatting (normalize case) | Bulk Replace | Bulk Replace is more effective with consistent casing |
| Remove Duplicates | Aggregation (Group & Pivot) | Duplicates inflate counts/sums |

### 5.3 Soft Dependencies (Performance)

These ordering rules improve performance. Violating them produces correct but slow results:

| Optimal Position | Function | Reason |
|-----------------|----------|---------|
| As early as possible | Conditional Filter | Reduces row count for all subsequent steps |
| As early as possible | Remove Columns | Reduces memory footprint |
| Before Join | Group & Pivot (aggregate) | Smaller table = faster join |
| After all filters | Join | Don't join rows you'll filter out later |
| Last (or near last) | Group & Pivot (final aggregation) | Aggregating earlier may lose required detail |
| After cleaning | Any analytical function | Clean input = accurate output |

### 5.4 The AI's Sequencing Checklist

Before presenting a pipeline suggestion, the AI should verify:

- [ ] Are all type conversions placed before operations that require the target type?
- [ ] Are cleaning steps (Find & Replace, Bulk Replace, Text Formatting) before operations that depend on clean values?
- [ ] Are filters placed as early as possible?
- [ ] Are unnecessary columns removed early?
- [ ] Are joins performed on the smallest necessary dataset version?
- [ ] Does every column reference exist at the point in the pipeline where it's used?
- [ ] If a column is both read and overwritten, is Copy Columns used to preserve the original?

---

## 6. Disambiguation & Clarification Protocol

### 6.1 When to Ask vs When to Default

The AI should NOT ask clarifying questions for every ambiguity — that defeats the purpose of speed. Use this framework:

**Default (Don't Ask) When:**
- The intent maps to a single common pattern with clear best practices
- Schema statistics make the right choice obvious (e.g., if user says "remove duplicates" and there's an obvious key column)
- A reasonable default exists and the user can easily adjust later
- The prompt is specific enough to confidently decompose

**Ask (Clarify) When:**
- The intent is genuinely ambiguous AND the wrong interpretation would waste significant effort
- Multiple fundamentally different approaches exist (e.g., "combine these datasets" could mean Join or Append)
- Critical parameters are missing and cannot be reasonably inferred (e.g., "filter by date" — which date range?)
- The intent might require functionality that doesn't exist in Mammoth

### 6.2 Ambiguous Intent Decision Trees

**"Clean up my data"**
- If high null count visible: Default to null handling + deduplication + type fixes
- If many text variations visible: Default to Bulk Replace + Text Formatting
- If no clear quality issues: Ask "What specific issues are you seeing?" with suggested options

**"Combine these" / "Merge"**
- If datasets have same columns: Default to Append (stack vertically)
- If datasets have a shared key column: Default to Join (Left Join)
- If unclear: Ask "Do you want to stack rows (like combining monthly files) or add columns from another dataset?"

**"Remove bad data"**
- If visible nulls: Default to filter out rows with nulls in key columns
- If visible duplicates: Default to Remove Duplicates
- If specific values mentioned: Default to Conditional Filter
- If vague: Ask "What makes a row 'bad'? Missing values, duplicates, or specific conditions?"

**"Summarize" / "Aggregate"**
- Always ask (or intelligently default based on data): Which column(s) to group by, and which measure(s) to aggregate with what function (SUM, AVG, COUNT, etc.)

**"Calculate"**
- If column names suggest obvious formula (e.g., "Revenue" and "Cost"): Default to Math Function with the obvious calculation (e.g., Margin = Revenue - Cost)
- If unclear what to calculate: Ask "Which columns and what calculation?"

### 6.3 Clarification Format

When the AI does ask, it should present structured options, not open-ended questions:

GOOD: "I can help with that. Do you want to:
1. Stack these datasets vertically (same columns, more rows)
2. Join them on a matching column (add columns from the second dataset)"

BAD: "What do you mean by 'combine'?"

---

## 7. Display Changes vs Pipeline Tasks Boundary

### 7.1 The Distinction

This is a critical boundary the AI must understand and communicate:

| Aspect | Display Changes | Pipeline Tasks |
|--------|----------------|----------------|
| Layer | Presentation | Transformation |
| Persistence | View-specific metadata | Sequential pipeline logic |
| History | Final state only | Full step-by-step history |
| Scope | Per-View | Applied to all data flowing through |
| Reversibility | Toggle on/off | Revert via pipeline editing |
| Automation | Not part of automated pipelines | Part of automated pipelines |

### 7.2 What Is a Display Change (NOT a Pipeline Task)

- **Rename Column** — right-click header → Rename (the ONLY way to rename)
- **Hide Column** — removes from view display without deleting from data
- **Reorder Columns** — drag columns to rearrange display order
- **Sort (temporary)** — click column header for display-only sorting
- **Number Formatting** — decimal places, thousand separators (display-only)

### 7.3 AI Behavior Rules

- NEVER suggest "Rename Column" as a pipeline task — it does not exist
- If user says "rename this column": Respond with Display Changes instructions, not a pipeline step
- If user says "hide these columns": Clarify — "Do you want to hide them from view (Display Change) or permanently remove them from the pipeline? Removing them improves pipeline performance."
- Display-renamed columns DO appear with their new names in pipeline task dropdowns — so they work seamlessly
- When building pipeline suggestions, reference columns by their DISPLAY names if Display Changes have been applied

---

## 8. Orchestration Awareness

### 8.1 When Intent Extends Beyond Transformation

The AI Prompt is primarily for building transformation pipelines. However, users frequently express intents that include automation. The AI should recognize these signals and bridge appropriately.

**Automation Signal Phrases:**
- "Do this every day" / "Run automatically" → Dataset Refresh or schedule-based orchestration
- "Email me the results" / "Send this to my team" → Messaging orchestration
- "When new files arrive" / "Combine incoming files" → Data Consolidation orchestration
- "Pull from SFTP/Google Drive" → File Collection (coming soon — Q1 2026)
- "Extract from these PDFs" → PDF Orchestration (coming soon — Q2 2026)

### 8.2 Five Orchestration Types (Current Status)

| Type | Status | Trigger | Key Constraint |
|------|--------|---------|----------------|
| Dataset Refresh | Production | Schedule, Manual, API | Requires Live Connections (not file uploads) |
| Data Consolidation | Production | File upload detection | Schema must match (exact column names) |
| File Collection | Coming Soon (Q1 2026) | Scheduled monitoring | 8 cloud storage sources |
| Messaging | Production | Schedule-based | 100K row limit on CSV attachments |
| PDF Orchestration | Coming Soon (Q2 2026) | File pattern matching | Natural language extraction prompts |

### 8.3 AI Response When Orchestration Is Relevant

The AI should:
1. Complete the transformation pipeline suggestion first
2. Then note: "Once this pipeline is built, you can automate it using Orchestration — [specific type] would handle the [scheduling/file collection/notification] part."
3. Not attempt to configure orchestration from within the AI Prompt — direct user to the Orchestration section of the platform

---

## 9. Performance Optimization Rules

### 9.1 Default Pipeline Architecture

The AI should construct pipelines following this optimal structure by default:

```
1. Data Quality Gates (Conditional Filter) — reduce row count first
2. Column Cleanup (Remove Columns, Convert Column Type) — reduce width and fix types
3. Standardization (Bulk Replace, Text Formatting) — clean values
4. Enrichment (Join, Lookup, Add Column) — add data
5. Calculations (Math Function, Window Function) — compute
6. Aggregation (Group & Pivot) — summarize last
```

### 9.2 Specific Optimization Rules

**Rule: Filter Before Everything**
- Apply the most selective filter first
- Date range filters often reduce datasets by 90%+
- Example: 100M row dataset → filter to region + date range → 2M rows → 50x faster for all subsequent steps

**Rule: Aggregate Before Join**
- If joining a large fact table with a dimension table, aggregate the fact table first
- Example: 10M transactions JOIN 100K customers — aggregate transactions to customer level first → 100x smaller join

**Rule: Remove Columns Early**
- Drop unnecessary columns as soon as they're no longer needed
- Example: 100-column table → only need 5 columns → 95% memory reduction

**Rule: Combine Filters**
- Multiple Conditional Filter steps with AND logic should be combined into a single filter step
- Separate steps only when OR logic or different filter types require it

**Rule: Type Conversion After Cleaning, Before Calculation**
- Clean text formatting → Convert type → Then calculate
- Never convert type before cleaning (conversion will fail on dirty data)

### 9.3 Performance Red Flags

The AI should warn the user when it detects potential performance issues:

- Suggesting a Join without prior filtering on a dataset known to be very large
- Multiple sequential Generative AI steps on large datasets (50K row limit applies per step)
- Group & Pivot early in the pipeline when subsequent steps need row-level detail
- Not removing columns when the dataset is known to be wide (50+ columns)

---

## 10. Failure Mode Catalog & Guardrails

### 10.1 Things the AI Must NEVER Suggest

| Never Suggest | Why | Correct Alternative |
|--------------|-----|-------------------|
| "Rename Column" pipeline task | Does not exist | Display Changes: right-click → Rename |
| Math on text-type columns without Convert first | Will error | Find & Replace + Convert Column Type first |
| Join without addressing key mismatches | Unexpected results | Convert types / standardize keys first |
| Generative AI on >50K rows without filtering | Will hit limit | Conditional Filter first, then Generative AI |
| Aggregation before deduplication | Inflated results | Remove Duplicates, then Group & Pivot |
| Delete original column before creating derived | Irreversible data loss | Copy Columns first, then transform copy |

### 10.2 Known Accuracy Risk Areas

These are areas where the AI has historically produced incorrect or misleading suggestions:

**Business Days / Network Days Calculation**
- Risk: AI may suggest Date Difference alone, which gives calendar days, not business days
- Correct approach: Date Difference (calendar days) → Math Function (subtract weekends: roughly = calendar_days * 5/7) → For precision, Join with holiday calendar dataset → Math Function (subtract holiday count)
- Customer evidence: Network days calculation discrepancy identified during Alteryx migration demo

**Complex Conditional Logic**
- Risk: AI may oversimplify nested AND/OR conditions
- Correct approach: Build conditions step-by-step, verify with preview at each stage

**Type Conversion Edge Cases**
- Risk: Text columns with mixed formats (some valid numbers, some text) will partially fail on conversion
- Correct approach: Pre-clean with Find & Replace to handle known variations, then Convert, then check for conversion failures

**Join Type Selection**
- Risk: AI may default to Inner Join when Left Join is needed (losing rows)
- Correct approach: Always consider: "Should unmatched rows be preserved? If yes, Left or Full Outer Join"

### 10.3 Graceful Degradation

When the AI cannot confidently produce a pipeline for the intent:

1. **Partial solution + explanation**: "I can build steps 1-3, but step 4 (network days with custom holiday calendar) requires additional data. Here's what you'd need..."
2. **Multiple options with trade-offs**: "Option A uses Generative AI (simpler but 50K row limit). Option B uses SQL Query (more complex but no row limit)."
3. **Defer to manual**: "This is a complex multi-dataset operation that would benefit from manual pipeline building for precision. Here's the approach I'd recommend..."
4. **Never hallucinate a function that doesn't exist.** If Mammoth can't do it, say so clearly.

### 10.4 Guardrails Summary

The AI Prompt should enforce these hard guardrails:

- Never suggest more than 15 steps without user confirmation (complexity risk)
- Always show preview/impact analysis before applying destructive operations (Remove Columns, filter that removes significant data)
- Always disclose limitations (50K Generative AI limit, 100K Messaging limit)
- Always flag when suggestions involve "coming soon" features vs production features
- Always preserve data lineage — suggest Copy Columns before overwriting originals
- Never produce a pipeline that can't be explained step-by-step (no black boxes)

---

## 11. Testing & Validation Framework

### 11.1 Test Suite Structure

The testing framework validates AI Prompt quality across multiple dimensions:

**Dimension 1: Function Awareness (Does the AI know what exists?)**

| Test Category | Test Description | Pass Criteria |
|--------------|-----------------|---------------|
| Positive identification | For each of the 30+ functions, describe an intent that requires it | AI suggests the correct function |
| Negative identification | Describe intent requiring a non-existent function (e.g., "rename column in pipeline") | AI correctly states it doesn't exist and offers alternative |
| Category accuracy | Ask AI to list all functions in a category | 100% match with actual category contents |
| Parameter completeness | For each function, provide edge-case parameters | AI correctly identifies valid vs invalid parameters |

**Dimension 2: Intent Decomposition (Does the AI build correct pipelines?)**

| Test Category | Test Description | Pass Criteria |
|--------------|-----------------|---------------|
| Single-step intents | "Filter rows where amount > 1000" | Correct function, correct parameters |
| Multi-step intents | "Clean and standardize vendor names, then calculate totals by vendor" | Correct sequence of 3+ steps in correct order |
| Dependency ordering | "Calculate margin percentage" on text-formatted columns | AI inserts Convert Column Type BEFORE Math Function |
| Complex composition | Reproduce known pipeline patterns from app_tasks.txt (200+ examples) | Pipeline achieves stated intent |

**Dimension 3: Schema Utilization (Does the AI use data statistics?)**

| Test Category | Test Description | Pass Criteria |
|--------------|-----------------|---------------|
| Type inference | Present text column with numeric-looking values | AI suggests Convert Column Type |
| Null handling | Present column with 30% nulls before aggregation | AI warns about null impact and suggests handling |
| Join key quality | Present datasets with non-unique join keys | AI warns about potential row explosion |
| Cardinality-based choice | Present column with 5 unique values | AI considers Group & Pivot or Bulk Replace, not Extract Text |

**Dimension 4: Performance Quality (Does the AI optimize?)**

| Test Category | Test Description | Pass Criteria |
|--------------|-----------------|---------------|
| Filter placement | Intent requires filter + calculation + join | Filter appears as step 1 or 2 |
| Column removal | Intent uses 3 of 50 columns | Remove Columns suggested early |
| Aggregate-before-join | Intent aggregates fact table then joins dimension | Aggregation precedes join |
| Combined filters | Intent has 3 AND conditions | Single Conditional Filter step, not 3 separate |

**Dimension 5: Guardrail Enforcement (Does the AI respect limits?)**

| Test Category | Test Description | Pass Criteria |
|--------------|-----------------|---------------|
| Rename Column | "Rename column X to Y" | AI directs to Display Changes, never pipeline task |
| Generative AI limit | Intent on 100K row dataset using Generative AI | AI warns about 50K limit, suggests pre-filtering |
| Non-existent function | "Calculate network days" | AI decomposes into available functions, doesn't hallucinate |
| Destructive operation | Intent to remove 90% of columns | AI confirms or warns about scope |

### 11.2 Ground Truth: Test Data Sources

**Primary test corpus: app_tasks.txt**
- 200+ real customer pipeline patterns
- 13 major task categories
- 50+ detailed examples with step-by-step decomposition
- Industry applications per pattern
- Organized by: Filtering, Type Conversions, Text Operations, Math Functions, Data Combining, Reshaping, Advanced Patterns

**Secondary test corpus: Pipeline Reference Library (Doc 26)**
- 200 analyzed pipelines with complexity distribution
- Rule type usage analytics (frequency counts)
- Optimization patterns with specific examples
- Common task combinations

**Regression test cases: Known failures**
- Network days calculation (calendar days vs business days)
- Text-to-numeric conversion on dirty financial data
- Join type selection preserving unmatched rows

### 11.3 Evaluation Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Function Accuracy | % of intents where correct primary function is identified | >95% |
| Sequence Correctness | % of multi-step pipelines with correct dependency ordering | >90% |
| Decomposition Completeness | % of multi-step intents where all necessary steps are included | >85% |
| Performance Score | % of pipelines following optimization rules (filter early, etc.) | >80% |
| Guardrail Compliance | % of edge cases where guardrails are correctly enforced | 100% |
| Schema Utilization | % of suggestions that leverage available data statistics | >70% |
| False Positive Rate | % of suggestions that include non-existent functions | 0% |
| Clarification Appropriateness | % of ambiguous intents where clarification is correctly requested vs defaulted | >80% |

### 11.4 Testing Cadence

- **On every prompt engineering change**: Run full Dimension 1 + Dimension 5 (function awareness and guardrails — these are non-negotiable)
- **Weekly during active development**: Run Dimensions 2-4 on a rotating sample
- **Monthly**: Full regression across all dimensions against complete test corpus
- **On function addition**: Add new function to Dimension 1 tests, update all relevant Dimension 2 patterns

---

## 12. Maintenance & Evolution Guidelines

### 12.1 When to Update This Manifesto

- **New function added to Transform menu**: Add to Capability Map (Section 2), update test suite (Section 11)
- **Function behavior changes**: Update parameters, constraints, and edge cases in Capability Map
- **New orchestration type launched**: Update Section 8
- **New failure mode discovered**: Add to Failure Mode Catalog (Section 10), add regression test
- **Customer reports AI misinterpretation**: Analyze root cause, add to disambiguation rules (Section 6) and test suite
- **Performance optimization pattern identified**: Add to Section 9

### 12.2 Ownership & Review

- **Primary owner**: Engineering team (AI/ML and Platform)
- **Review cadence**: Monthly, synchronized with product release cycle
- **Input sources**: Customer support tickets about AI Prompt issues, customer transcript analysis, internal QA testing
- **Change process**: Update document → update test suite → validate → deploy prompt changes

### 12.3 Integration Points

This manifesto feeds into:

1. **AI Prompt system prompt / grounding context**: The capability map and rules from this document should be the authoritative source for what the LLM knows about Mammoth
2. **Test automation**: Section 11 defines the test harness; engineering owns the implementation
3. **Documentation**: Capabilities described here should align with user-facing docs
4. **Customer Success**: Patterns and disambiguation rules inform training and support materials

### 12.4 Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | February 2026 | Initial manifesto — complete capability map, testing framework, composition guidelines | Product/Engineering |

---

## Appendix A: Quick Reference — All Functions by Category

```
AI Powered (5):          SQL Query, Generative AI, Extract Text, Bulk Replace, Conditional Filter
Filter, Label & Replace (8): Conditional Filter, Remove Duplicates, Find & Replace, Label & Insert Values,
                              Show Top/Bottom, Filter Data, Sort, Send Between Datasets
Date, Numeric & Text (9):    Math Functions, Window Functions, Text Formatting, Combine Columns,
                              Date Difference, Date Formatting, Convert Column Type, Extract Text, Find & Replace
Reshape, Group & Pivot (4):  Group & Pivot, Columns to Rows (Unpivot), Crosstab, Flatten
Column Management (6):       Add Column, Copy Columns, Convert Column Type, Remove Columns,
                              Split Into Multiple Columns [NO Rename Column]
Unify (3):                   Join, Lookup, Append
```

## Appendix B: Top 10 Functions by Usage Frequency (from 200+ production pipelines)

```
1. Math Function:       569 occurrences
2. Copy Columns:        416 occurrences
3. Label & Insert:      301 occurrences
4. Conditional Filter:  280 occurrences
5. Bulk Replace:        265 occurrences
6. Add Column:          243 occurrences
7. Convert Column Type: 213 occurrences
8. Join:                201 occurrences
9. Window Function:     ~150 occurrences (estimated)
10. Group & Pivot:      ~120 occurrences (estimated)
```

## Appendix C: Orchestration Quick Reference

```
Production:    Dataset Refresh (schedule/manual/API), Data Consolidation (file upload trigger), Messaging (schedule, 100K row CSV limit)
Coming Soon:   File Collection (Q1 2026, 8 sources), PDF Orchestration (Q2 2026), Event-based triggers (Q1 2026)
Not Supported: Cascading workflows (max one-level dependency), cross-Project orchestration
```

---

*End of Manifesto*
