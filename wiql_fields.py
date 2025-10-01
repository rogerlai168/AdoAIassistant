# Azure DevOps Work Item Fields Reference
# Based on Microsoft's official documentation

# System Fields (Reference Names)
SYSTEM_FIELDS = {
    # Core Identity Fields
    "id": "System.Id",
    "title": "System.Title",
    "description": "System.Description",
    "state": "System.State",
    "workitemtype": "System.WorkItemType",
    "assignedto": "System.AssignedTo",
    "createdby": "System.CreatedBy",
    "changedby": "System.ChangedBy",
    
    # Date Fields
    "createddate": "System.CreatedDate",
    "changeddate": "System.ChangedDate",
    "closeddate": "System.ClosedDate",
    "resolveddate": "System.ResolvedDate",
    "activateddate": "System.ActivatedDate",
    
    # Path Fields (TreePath type)
    "areapath": "System.AreaPath",
    "iterationpath": "System.IterationPath",
    "teamproject": "System.TeamProject",
    
    # Other Core Fields
    "reason": "System.Reason",
    "tags": "System.Tags",
    "history": "System.History",
    "rev": "System.Rev",
    "watermark": "System.Watermark",
}

# Microsoft VSTS Common Fields
VSTS_COMMON_FIELDS = {
    "priority": "Microsoft.VSTS.Common.Priority",
    "severity": "Microsoft.VSTS.Common.Severity",
    "triage": "Microsoft.VSTS.Common.Triage",
    "rating": "Microsoft.VSTS.Common.Rating",
    "valuearea": "Microsoft.VSTS.Common.ValueArea",
    "risk": "Microsoft.VSTS.Common.Risk",
    "stackrank": "Microsoft.VSTS.Common.StackRank",
    "closedby": "Microsoft.VSTS.Common.ClosedBy",
    "closeddate": "Microsoft.VSTS.Common.ClosedDate",
    "resolvedby": "Microsoft.VSTS.Common.ResolvedBy",
    "resolveddate": "Microsoft.VSTS.Common.ResolvedDate",
    "activatedby": "Microsoft.VSTS.Common.ActivatedBy",
    "activateddate": "Microsoft.VSTS.Common.ActivatedDate",
    "statechangedate": "Microsoft.VSTS.Common.StateChangeDate",
}

# Microsoft VSTS Scheduling Fields
VSTS_SCHEDULING_FIELDS = {
    "effort": "Microsoft.VSTS.Scheduling.Effort",
    "originalestimate": "Microsoft.VSTS.Scheduling.OriginalEstimate",
    "remainingwork": "Microsoft.VSTS.Scheduling.RemainingWork",
    "completedwork": "Microsoft.VSTS.Scheduling.CompletedWork",
    "activity": "Microsoft.VSTS.Scheduling.Activity",
    "startdate": "Microsoft.VSTS.Scheduling.StartDate",
    "finishdate": "Microsoft.VSTS.Scheduling.FinishDate",
    "targetdate": "Microsoft.VSTS.Scheduling.TargetDate",
    "duedate": "Microsoft.VSTS.Scheduling.DueDate",
    "baselinestart": "Microsoft.VSTS.Scheduling.BaselineStart",
    "baselinefinish": "Microsoft.VSTS.Scheduling.BaselineFinish",
}

# Common WIQL Operators by Field Type
FIELD_TYPE_OPERATORS = {
    "String": ["=", "<>", ">", "<", ">=", "<=", "CONTAINS", "NOT CONTAINS", "IN", "NOT IN"],
    "Integer": ["=", "<>", ">", "<", ">=", "<=", "IN", "NOT IN", "WAS EVER"],
    "DateTime": ["=", "<>", ">", "<", ">=", "<=", "IN", "NOT IN", "WAS EVER"],
    "TreePath": ["=", "<>", "UNDER", "NOT UNDER", "IN", "NOT IN"],
    "Identity": ["=", "<>", "CONTAINS", "NOT CONTAINS", "IN", "NOT IN", "IN GROUP", "NOT IN GROUP"],
    "Boolean": ["=", "<>"],
    "Double": ["=", "<>", ">", "<", ">=", "<=", "IN", "NOT IN", "WAS EVER"],
    "PlainText": ["CONTAINS WORDS", "NOT CONTAINS WORDS", "IS EMPTY", "IS NOT EMPTY"],
}

# Standard Work Item Types
WORK_ITEM_TYPES = {
    # Agile Process
    "epic": "Epic",
    "feature": "Feature", 
    "userstory": "User Story",
    "story": "User Story",
    "task": "Task",
    "bug": "Bug",
    "issue": "Issue",
    
    # Scrum Process
    "productbacklogitem": "Product Backlog Item",
    "pbi": "Product Backlog Item",
    
    # CMMI Process
    "requirement": "Requirement",
    "changerequest": "Change Request",
    "review": "Review",
    "riskassessment": "Risk Assessment",
    
    # Basic Process
    "item": "Item",
}

# Common States by Work Item Type
COMMON_STATES = {
    "User Story": ["New", "Active", "Resolved", "Closed", "Removed"],
    "Task": ["New", "Active", "Closed", "Removed"],
    "Bug": ["New", "Active", "Resolved", "Closed"],
    "Epic": ["New", "In Progress", "Done"],
    "Feature": ["New", "In Progress", "Done"],
    "Product Backlog Item": ["New", "Approved", "Committed", "Done", "Removed"],
    "Issue": ["Active", "Resolved", "Closed"],
}

# WIQL Macros
WIQL_MACROS = [
    "@Me",
    "@Today", 
    "@Project",
    "@CurrentIteration",
    "@StartOfDay",
    "@StartOfWeek", 
    "@StartOfMonth",
    "@StartOfYear",
]

def get_field_reference_name(field_name: str) -> str:
    """Get the proper reference name for a field."""
    field_lower = field_name.lower().replace(" ", "").replace("-", "").replace("_", "")
    
    # Check system fields first
    if field_lower in SYSTEM_FIELDS:
        return SYSTEM_FIELDS[field_lower]
    
    # Check VSTS common fields
    if field_lower in VSTS_COMMON_FIELDS:
        return VSTS_COMMON_FIELDS[field_lower]
    
    # Check VSTS scheduling fields
    if field_lower in VSTS_SCHEDULING_FIELDS:
        return VSTS_SCHEDULING_FIELDS[field_lower]
    
    # If not found, assume it's already a reference name
    if "." in field_name:
        return field_name
    
    # Default to System namespace
    return f"System.{field_name}"

def normalize_work_item_type(wit: str) -> str:
    """Normalize work item type names."""
    wit_lower = wit.lower().replace(" ", "").replace("-", "")
    return WORK_ITEM_TYPES.get(wit_lower, wit)

def validate_operator_for_field_type(field_type: str, operator: str) -> bool:
    """Check if an operator is valid for a given field type."""
    return operator.upper() in FIELD_TYPE_OPERATORS.get(field_type, [])
