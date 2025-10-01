# Azure DevOps Work Items - Complete Schema Reference

## Overview
This document provides the **complete schema reference** for Azure DevOps Work Items, including all fields, comments, discussions, and additional data available through the REST API.

## Core Work Item Fields

### System Fields (Always Available)
```json
{
  "System.Id": "integer - Unique work item ID",
  "System.Title": "string - Work item title",
  "System.Description": "html - Work item description (rich text)",
  "System.State": "string - Current state (New, Active, Resolved, Closed, etc.)",
  "System.WorkItemType": "string - Bug, Task, User Story, Epic, Feature, etc.",
  "System.AssignedTo": "identity - Assigned user",
  "System.CreatedBy": "identity - User who created the work item",
  "System.ChangedBy": "identity - User who last modified",
  "System.Reason": "string - Reason for current state",
  "System.Tags": "string - Semicolon-separated tags"
}
```

### Date Fields
```json
{
  "System.CreatedDate": "datetime - When work item was created",
  "System.ChangedDate": "datetime - When work item was last modified",
  "System.ClosedDate": "datetime - When work item was closed",
  "System.ResolvedDate": "datetime - When work item was resolved",
  "System.ActivatedDate": "datetime - When work item was activated"
}
```

### Hierarchy Fields (TreePath)
```json
{
  "System.AreaPath": "treepath - Area path hierarchy",
  "System.IterationPath": "treepath - Iteration path hierarchy",
  "System.TeamProject": "string - Project name"
}
```

### History and Audit Fields
```json
{
  "System.History": "html - Rich text history/discussion field",
  "System.Rev": "integer - Revision number",
  "System.Watermark": "integer - Internal version tracking"
}
```

## Microsoft VSTS Fields

### Common Fields
```json
{
  "Microsoft.VSTS.Common.Priority": "integer - 1=Critical, 2=High, 3=Medium, 4=Low",
  "Microsoft.VSTS.Common.Severity": "integer - Bug severity level",
  "Microsoft.VSTS.Common.Triage": "string - Triage classification",
  "Microsoft.VSTS.Common.Rating": "integer - Rating value",
  "Microsoft.VSTS.Common.ValueArea": "string - Business or Architectural",
  "Microsoft.VSTS.Common.Risk": "string - Risk assessment",
  "Microsoft.VSTS.Common.StackRank": "double - Stack ranking value",
  "Microsoft.VSTS.Common.ClosedBy": "identity - User who closed",
  "Microsoft.VSTS.Common.ClosedDate": "datetime - Close date",
  "Microsoft.VSTS.Common.ResolvedBy": "identity - User who resolved",
  "Microsoft.VSTS.Common.ResolvedDate": "datetime - Resolution date",
  "Microsoft.VSTS.Common.ActivatedBy": "identity - User who activated",
  "Microsoft.VSTS.Common.ActivatedDate": "datetime - Activation date",
  "Microsoft.VSTS.Common.StateChangeDate": "datetime - Last state change"
}
```

### Scheduling Fields
```json
{
  "Microsoft.VSTS.Scheduling.Effort": "double - Story points/effort",
  "Microsoft.VSTS.Scheduling.OriginalEstimate": "double - Original time estimate",
  "Microsoft.VSTS.Scheduling.RemainingWork": "double - Remaining work",
  "Microsoft.VSTS.Scheduling.CompletedWork": "double - Completed work",
  "Microsoft.VSTS.Scheduling.StartDate": "datetime - Planned start",
  "Microsoft.VSTS.Scheduling.FinishDate": "datetime - Planned finish",
  "Microsoft.VSTS.Scheduling.TargetDate": "datetime - Target delivery"
}
```

## Comments and Discussions

### Work Item Comments API
**Endpoint**: `GET /workItems/{id}/comments`

```json
{
  "comments": [
    {
      "id": "integer - Comment ID",
      "workItemId": "integer - Work item ID", 
      "version": "integer - Comment version",
      "text": "string - Comment text (supports markdown)",
      "createdBy": {
        "displayName": "string - User display name",
        "uniqueName": "string - User email/UPN",
        "id": "guid - User ID"
      },
      "createdDate": "datetime - Comment creation time",
      "modifiedBy": {
        "displayName": "string - User display name", 
        "uniqueName": "string - User email/UPN",
        "id": "guid - User ID"
      },
      "modifiedDate": "datetime - Last modification time",
      "url": "string - API URL for this comment"
    }
  ],
  "count": "integer - Total comment count",
  "totalCount": "integer - Total including deleted"
}
```

### System.History Field
The `System.History` field contains the **discussion thread** and change history:

```json
{
  "System.History": "html - Contains:\n• All comments and discussions\n• Field change descriptions\n• State transition notes\n• Rich text formatting\n• @mentions and links"
}
```

### Partner Comments Detection
Our system identifies **partner comments** (external collaborators) by:
- Email domain analysis (external domains)
- User group membership
- Organization context
- Configurable patterns

## Current System Support

### Our JSON Schema Extension
```json
{
  "ids": "[int] | null - Specific work item IDs",
  "filters": {
    "work_item_types": "[string] - Bug, Task, User Story, etc.",
    "states_in": "[string] - Include these states",
    "states_not_in": "[string] - Exclude these states",
    "priority_min": "int | null - Minimum priority",
    "priority_max": "int | null - Maximum priority", 
    "assigned_to": "string | null - me, specific user",
    "tags_include": "[string] - Required tags",
    "area_paths": "[string] - Area path filters",
    "iteration_paths": "[string] - Iteration filters"
  },
  "date_window": {
    "field": "string - System.CreatedDate, System.ChangedDate, etc.",
    "relative": "string - last_7_days, last_30_days, etc.",
    "start_date": "string | null - Absolute start",
    "end_date": "string | null - Absolute end"
  },
  "free_text_terms": "[string] - Text search terms",
  
  // Comment and Discussion Support
  "include_comments": "boolean - Fetch comment data",
  "include_partner_comments": "boolean - Include external comments",
  "include_repro_steps": "boolean - Include repro steps",
  "comment_date_filter": "string - Filter comments by date",
  "comment_author_filter": "string - Filter by comment author"
}
```

## Extended Fields by Work Item Type

### Bug-Specific Fields
```json
{
  "Microsoft.VSTS.TCM.ReproSteps": "html - Steps to reproduce",
  "Microsoft.VSTS.TCM.SystemInfo": "html - System information",
  "Microsoft.VSTS.Common.Severity": "integer - Bug severity",
  "Microsoft.VSTS.Build.FoundIn": "string - Found in build",
  "Microsoft.VSTS.Build.IntegrationBuild": "string - Integration build"
}
```

### User Story/PBI Fields
```json
{
  "Microsoft.VSTS.Common.AcceptanceCriteria": "html - Acceptance criteria",
  "Microsoft.VSTS.Scheduling.StoryPoints": "double - Story point estimate",
  "Microsoft.VSTS.Common.BusinessValue": "integer - Business value"
}
```

### Task-Specific Fields
```json
{
  "Microsoft.VSTS.Scheduling.RemainingWork": "double - Hours remaining",
  "Microsoft.VSTS.Scheduling.CompletedWork": "double - Hours completed",
  "Microsoft.VSTS.Scheduling.OriginalEstimate": "double - Original estimate"
}
```

## Enhanced AI Prompt Schema

For AI parsing with full comment and discussion support:

```json
{
  "ids": "[int] | null",
  "filters": {
    "work_item_types": "[string]",
    "states_in": "[string]",
    "states_not_in": "[string]", 
    "priority_min": "int | null",
    "priority_max": "int | null",
    "assigned_to": "string | null",
    "tags_include": "[string]",
    "area_paths": "[string]",
    "iteration_paths": "[string]",
    "created_by": "string | null",
    "changed_by": "string | null",
    "severity_min": "int | null",
    "severity_max": "int | null"
  },
  "date_window": {
    "field": "string - System.CreatedDate|System.ChangedDate|System.ClosedDate",
    "relative": "string | null",
    "start_date": "string | null", 
    "end_date": "string | null"
  },
  "free_text_terms": "[string]",
  "content_search": {
    "search_title": "boolean - Search in titles",
    "search_description": "boolean - Search in descriptions", 
    "search_comments": "boolean - Search in comments",
    "search_history": "boolean - Search in System.History",
    "search_repro_steps": "boolean - Search in repro steps"
  },
  "include_comments": "boolean - Fetch comment data",
  "include_partner_comments": "boolean - Include external comments",
  "include_repro_steps": "boolean - Include reproduction steps",
  "include_acceptance_criteria": "boolean - Include acceptance criteria",
  "comment_filters": {
    "author": "string | null - Filter comments by author",
    "date_range": "object | null - Comment date filtering",
    "content_contains": "string | null - Comment content search"
  }
}
```

## Usage Examples

### Query with Comments
```
"show me bugs with partner comments from last week"
```
→ 
```json
{
  "filters": {"work_item_types": ["Bug"]},
  "date_window": {"relative": "last_7_days", "field": "System.ChangedDate"},
  "include_comments": true,
  "include_partner_comments": true
}
```

### Search in Discussions
```
"find tickets with 'login issue' mentioned in comments"
```
→
```json
{
  "content_search": {"search_comments": true},
  "free_text_terms": ["login issue"],
  "include_comments": true
}
```

### Bug with Repro Steps
```
"show me critical bugs with reproduction steps"
```
→
```json
{
  "filters": {
    "work_item_types": ["Bug"],
    "priority_min": 1,
    "priority_max": 1
  },
  "include_repro_steps": true
}
```

## API Limitations and Best Practices

### Comment API Limits
- **Default**: Returns 200 comments per request
- **Maximum**: 10,000 comments per request  
- **Pagination**: Use `$skip` and `$top` parameters
- **Performance**: Comments are loaded separately (additional API call)

### Content Search Performance
- **System.History**: Contains full discussion thread but is expensive to search
- **Comments API**: Separate endpoint, better for comment-specific queries
- **Text Search**: Use WIQL `CONTAINS WORDS` for better performance

### Best Practices
1. **Selective Loading**: Only request comments when needed
2. **Date Filtering**: Use date ranges to limit comment volume  
3. **Pagination**: Handle large comment threads with pagination
4. **Caching**: Cache comment data for frequently accessed items
5. **Partner Detection**: Configure partner domain patterns for your organization

## References
- [Work Item Fields Reference](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/work-item-fields)
- [Comments REST API](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/comments)
- [WIQL Syntax Reference](https://learn.microsoft.com/en-us/azure/devops/boards/queries/wiql-syntax)
- [Work Item Updates API](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/updates)
