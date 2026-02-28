# Projects API Reference

The `ProjectsAPI` manages projects within a workspace. Projects are siloed areas for organizing datasets, views, and pipelines.

**Access**: `client.projects`

```python
# List all projects
projects = client.projects.list()

# Get a specific project
project = client.projects.get(project_id=10)

# Create a new project
client.projects.create(name="My Project", properties={"description": "..."})
```

---

::: mammoth.api.projects.ProjectsAPI
    options:
      show_root_heading: true
      heading_level: 2
