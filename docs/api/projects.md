# Projects API Reference

The `ProjectsAPI` manages projects within a workspace. Projects are siloed areas for organizing datasets, views, and pipelines.

**Access**: `client.projects`

```python
# List projects (one page; the route caps limit at 100)
projects = await client.projects.list()
page_two = await client.projects.list(offset=100)

# Every project across pages
all_projects = await client.projects.list_all()

# Get a specific project
project = await client.projects.get(project_id=10)

# Create a new project
await client.projects.create(name="My Project", properties={"description": "..."})
```

---

::: mammoth.api.projects.ProjectsAPI
    options:
      show_root_heading: true
      heading_level: 2
