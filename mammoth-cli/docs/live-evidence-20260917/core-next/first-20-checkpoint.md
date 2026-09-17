# First-20 capability checkpoint (2026-09-17)

This is a row-order checkpoint, not a criticality ranking. No destructive
operation was attempted; `REL-018` (delete self) remains untested.

| ID | Capability | Group | CLI / SDK mapping | Status | Live evidence or reason |
|---|---|---|---|---|---|
| REL-001 | Delete an agent chat session | MISCELLANEOUS_API | `agent.session.delete` / `AgentsAPI.session_delete` | Unassessed | No owned session fixture; destructive delete not authorized for preexisting resources. |
| REL-002 | Delete a tag | CLI_CORE_WORKFLOW | `dashboard.tags.delete` / `DashboardsAPI.delete_tag` | Unassessed | No owned tag fixture; destructive delete not attempted. |
| REL-003 | Delete a context | CLI_CORE_WORKFLOW | `dashboard.context.delete` / `DashboardsAPI.context_delete` | Unassessed | No owned context fixture; destructive delete not attempted. |
| REL-004 | Delete a signature | CLI_CORE_WORKFLOW | `dashboard.signature.delete` / `DashboardsAPI.signature_delete` | Unassessed | No owned signature fixture; destructive delete not attempted. |
| REL-005 | Delete a custom style | CLI_CORE_WORKFLOW | `dashboard.style.custom.delete` / `DashboardsAPI.style_custom_delete` | Unassessed | No owned style fixture; destructive delete not attempted. |
| REL-006 | Undo an import | MISCELLANEOUS_API | no CLI binding / no SDK symbol | Unassessed | No owned import; route not exposed by typed CLI. |
| REL-007 | Remove curated template picture | MISCELLANEOUS_API | no CLI binding / no SDK symbol | Unassessed | Admin-only destructive route; no authorized fixture. |
| REL-008 | Remove saved template picture | MISCELLANEOUS_API | no CLI binding / no SDK symbol | Unassessed | No owned template fixture; route not exposed by typed CLI. |
| REL-009 | Delete saved workspace template | CLI_CORE_WORKFLOW | `dashboard.template.delete` / `DashboardsAPI.template_delete` | Unassessed | No owned template fixture; destructive delete not attempted. |
| REL-010 | Delete Dashboard | CLI_CORE_WORKFLOW | `dashboard.delete` / `DashboardsAPI.delete` | Unassessed | No owned dashboard fixture; destructive delete not attempted. |
| REL-011 | Revoke embedding origin | MISCELLANEOUS_API | no CLI binding / `DashboardsAPI.revoke_origin` | Unassessed | No owned origin fixture; destructive revoke not attempted. |
| REL-012 | Delete Q&A session | CLI_CORE_WORKFLOW | `dashboard.qa.session.delete` / `DashboardsAPI.qa_session_delete` | Unassessed | No owned Q&A fixture; destructive delete not attempted. |
| REL-013 | Delete comment | CLI_CORE_WORKFLOW | `dashboard.qa.comment.delete` / `DashboardsAPI.qa_comment_delete` | Unassessed | No owned comment fixture; destructive delete not attempted. |
| REL-014 | Delete data app | MISCELLANEOUS_API | `data-app.delete` / `DataAppsAPI.delete` | Unassessed | No owned data-app fixture; destructive delete not attempted. |
| REL-015 | Remove data-app user | MISCELLANEOUS_API | `data-app.user.remove` / `DataAppsAPI.user_remove` | Unassessed | No owned membership fixture; destructive mutation not attempted. |
| REL-016 | Delete notifications batch | MISCELLANEOUS_API | `notification.delete-batch` / `NotificationsAPI.delete_batch` | Unassessed | No owned notification fixture; destructive delete not attempted. |
| REL-017 | Delete notification | MISCELLANEOUS_API | `notification.delete` / `NotificationsAPI.delete` | Unassessed | No owned notification fixture; destructive delete not attempted. |
| REL-018 | Delete self | MISCELLANEOUS_API | `user.delete-account` / `UsersAPI.delete_account` | Unassessed | Explicitly not tested: account destruction is outside release verification scope. |
| REL-019 | Delete profile picture | MISCELLANEOUS_API | `user.avatar.delete` / `UsersAPI.avatar_delete` | Unassessed | No owned avatar fixture; destructive mutation not attempted. |
| REL-020 | Delete connector profile | MISCELLANEOUS_API | `support.connector-profile.delete` / `SupportAPI.connector_profile_delete` | Unassessed | No owned connector-profile fixture; destructive delete not attempted. |
