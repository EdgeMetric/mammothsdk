---
name: mammoth-analytics
description: Use when the user wants to explore, clean, transform, total or export data in Mammoth Analytics.
---

# Working with Mammoth Analytics

Data is organised as workspace, project, dataset, view. A view is a pipeline of steps over a dataset.

1. Find the data first: `list_workspaces`, `list_projects`, `list_datasets`, `list_views`.
2. Answer with numbers from Mammoth. Use `aggregate_data`, or the values `get_dashboard` reports. Never add up rows yourself.
3. Before adding a step, call `get_schema` for its settings, then `add_transformations`.
4. Ask the user before anything that sends data out, publishes or keeps running: an export, a published dashboard, an automation.
5. When a result carries `mammoth_url` or `share_url`, give the user that link.
