import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from wiql_fields import get_field_reference_name, normalize_work_item_type
except ImportError:
    # Fallback if import fails
    def get_field_reference_name(field_name: str) -> str:
        return field_name
    
    def normalize_work_item_type(wit: str) -> str:
        return wit

# WIQL-safe string pattern - allow Unicode letters, numbers, common punctuation, quotes
SAFE_STRING = re.compile(r"^[\w\s\-\.\(\)#/\\@'\"éàèùâêîôûçäëïöü,;:!?]+$", re.UNICODE)

def sanitize_literal(v: str) -> str:
    """Sanitize string literals for WIQL queries following Microsoft guidance."""
    if not isinstance(v, str):
        v = str(v)
    
    # Be more permissive with character validation - focus on preventing injection
    # Block dangerous characters but allow Unicode and common punctuation
    dangerous_chars = ['<', '>', '&', ';', '--', '/*', '*/', 'DROP ', 'DELETE ', 'INSERT ', 'UPDATE ', 'EXEC']
    v_upper = v.upper()
    
    for danger in dangerous_chars:
        if danger in v_upper:
            raise ValueError(f"Unsafe literal contains dangerous pattern: {danger}")
    
    # Escape single quotes by doubling them (WIQL standard)
    return v.replace("'", "''")

def date_macro(relative_period: str) -> Optional[str]:
    """Generate WIQL date macros following Microsoft's documented patterns."""
    date_mappings = {
        # Today variations
        "today": "@Today",
        "yesterday": "@Today - 1",
        
        # Week variations
        "last_7_days": "@Today - 7",
        "last_week": "@Today - 7", 
        "this_week": "@StartOfWeek",
        "start_of_week": "@StartOfWeek",
        
        # Custom day ranges
        "last_3_days": "@Today - 3",
        "last_5_days": "@Today - 5",
        "last_10_days": "@Today - 10",
        "last_14_days": "@Today - 14",
        "last_20_days": "@Today - 20",
        "last_21_days": "@Today - 21",
        
        # Month variations
        "last_30_days": "@Today - 30",
        "last_month": "@StartOfMonth - 1",
        "this_month": "@StartOfMonth",
        "start_of_month": "@StartOfMonth",
        
        # Year variations
        "this_year": "@StartOfYear",
        "last_year": "@StartOfYear - 1",
        "start_of_year": "@StartOfYear",
        
        # Common periods
        "last_2_weeks": "@Today - 14",
        "last_3_months": "@StartOfMonth - 3",
        "last_6_months": "@StartOfMonth - 6",
    }
    
    # Fix: Check for None before calling .lower()
    if not relative_period:
        return None
    
    return date_mappings.get(relative_period.lower())

def build_wiql_query(spec: Dict[str, Any]) -> str:
    """
    Build complete WIQL query following Microsoft's syntax reference.
    Returns a complete SELECT statement, not just WHERE clause.
    """
    # Handle direct ID queries
    if spec.get("ids"):
        ids_str = ",".join(str(i) for i in spec["ids"])
        return f"""SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType], [System.AssignedTo], [System.ChangedDate]
FROM WorkItems 
WHERE [System.TeamProject] = @Project AND [System.Id] IN ({ids_str})
ORDER BY [System.ChangedDate] DESC"""
    
    # Build WHERE clauses
    where_clauses = ["[System.TeamProject] = @Project"]
    filters = spec.get("filters", {})
    
    # Work item types
    if filters.get("work_item_types"):
        types_str = ",".join(f"'{sanitize_literal(t)}'" for t in filters["work_item_types"])
        where_clauses.append(f"[System.WorkItemType] IN ({types_str})")
    else:
        # Exclude empty work item types (WIQL best practice)
        where_clauses.append("[System.WorkItemType] <> ''")
    
    # States (included)
    if filters.get("states_in"):
        states_str = ",".join(f"'{sanitize_literal(s)}'" for s in filters["states_in"])
        where_clauses.append(f"[System.State] IN ({states_str})")
    
    # States (excluded)
    if filters.get("states_not_in"):
        states_str = ",".join(f"'{sanitize_literal(s)}'" for s in filters["states_not_in"])
        where_clauses.append(f"[System.State] NOT IN ({states_str})")
    
    # Priority filters using proper reference names
    if filters.get("priority_max") is not None:
        priority = int(filters["priority_max"])
        where_clauses.append(f"[Microsoft.VSTS.Common.Priority] <= {priority}")
    
    if filters.get("priority_min") is not None:
        priority = int(filters["priority_min"])
        where_clauses.append(f"[Microsoft.VSTS.Common.Priority] >= {priority}")
    
    # Tags using CONTAINS operator (WIQL standard)
    for tag in filters.get("tags_include", []):
        where_clauses.append(f"[System.Tags] CONTAINS '{sanitize_literal(tag)}'")
    
    # Area paths using UNDER operator (WIQL standard for TreePath fields)
    for area_path in filters.get("area_paths", []):
        where_clauses.append(f"[System.AreaPath] UNDER '{sanitize_literal(area_path)}'")
    
    # Iteration paths using UNDER operator
    for iteration_path in filters.get("iteration_paths", []):
        where_clauses.append(f"[System.IterationPath] UNDER '{sanitize_literal(iteration_path)}'")
    
    # Assigned to filters
    if filters.get("assigned_to"):
        if filters["assigned_to"].lower() in ["me", "@me", "current user"]:
            where_clauses.append("[System.AssignedTo] = @Me")
        else:
            where_clauses.append(f"[System.AssignedTo] = '{sanitize_literal(filters['assigned_to'])}'")
    
    # Date window filters
    date_window = spec.get("date_window", {})
    if date_window:
        # Default to CreatedDate (discovery focus)
        field = date_window.get("field", "System.CreatedDate")
        # Ensure proper field reference format
        if not field.startswith("["):
            field = f"[{field}]"
        if date_window.get("relative"):
            rel = date_window["relative"]
            # Pattern: last_<n>_days
            import re
            m = re.match(r"last_(\d+)_days$", rel or "")
            if m:
                days = m.group(1)
                where_clauses.append(f"{field} >= @Today - {days}")
            elif rel == "last_week":
                where_clauses.append(f"{field} >= @Today - 7")
            elif rel == "last_2_weeks":
                where_clauses.append(f"{field} >= @Today - 14")
            elif rel == "last_month" or rel == "last_30_days":
                where_clauses.append(f"{field} >= @Today - 30")
            elif rel == "today":
                where_clauses.append(f"{field} >= @Today")
            elif rel and ("@Today" in rel or "@StartOf" in rel):
                # Already a macro expression
                where_clauses.append(f"{field} >= {rel}")
            else:
                # No recognized pattern—do not silently inject 30-day filter
                pass
        elif date_window.get("start_date") or date_window.get("end_date"):
            if date_window.get("start_date"):
                start_date = date_window['start_date'].split('T')[0] if 'T' in str(date_window['start_date']) else str(date_window['start_date'])
                where_clauses.append(f"{field} >= '{start_date}'")
            if date_window.get("end_date"):
                end_date = date_window['end_date'].split('T')[0] if 'T' in str(date_window['end_date']) else str(date_window['end_date'])
                where_clauses.append(f"{field} <= '{end_date}'")
    
    # Free text search in title and description
    free_text_terms = spec.get("free_text_terms", [])
    if free_text_terms:
        # Use OR grouping for multiple search terms
        if len(free_text_terms) == 1:
            term = sanitize_literal(free_text_terms[0])
            where_clauses.append(f"([System.Title] CONTAINS '{term}' OR [System.Description] CONTAINS '{term}')")
        else:
            term_conditions = []
            for term in free_text_terms:
                clean_term = sanitize_literal(term)
                term_conditions.append(f"([System.Title] CONTAINS '{clean_term}' OR [System.Description] CONTAINS '{clean_term}')")
            where_clauses.append(f"({' OR '.join(term_conditions)})")
    
    # Removed automatic 30-day default; allow full range unless explicitly constrained.

    # Build complete WIQL query
    where_clause = " AND ".join(where_clauses)
    
    # Handle sorting - support the new sort field
    sort_info = spec.get("sort")
    if sort_info and isinstance(sort_info, dict):
        sort_field = sort_info.get("field", "System.ChangedDate")
        sort_direction = sort_info.get("direction", "DESC").upper()
        order_by = f"ORDER BY [{sort_field}] {sort_direction}"
    else:
        # Default sort (CreatedDate to match discovery orientation)
        order_by = "ORDER BY [System.CreatedDate] DESC"
    
    query = f"""SELECT [System.Id], [System.Title], [System.State], [System.WorkItemType], [System.AssignedTo], [System.CreatedDate], [Microsoft.VSTS.Common.Priority]
FROM WorkItems
WHERE {where_clause}
{order_by}"""
    
    return query

def build(spec: dict):
    """Legacy function - builds WHERE clause only for backward compatibility."""
    if spec.get("ids"): 
        return f"[System.Id] IN ({','.join(str(i) for i in spec['ids'])})"
    
    filters = spec.get("filters", {})
    clauses = []
    
    if filters.get("work_item_types"): 
        clauses.append("[System.WorkItemType] IN ({})".format(
            ','.join(f"'{sanitize_literal(t)}'" for t in filters['work_item_types'])
        ))
    
    if filters.get("states_in"): 
        clauses.append("[System.State] IN ({})".format(
            ','.join(f"'{sanitize_literal(x)}'" for x in filters['states_in'])
        ))
    
    if filters.get("states_not_in"): 
        clauses.append("[System.State] NOT IN ({})".format(
            ','.join(f"'{sanitize_literal(x)}'" for x in filters['states_not_in'])
        ))
    
    if filters.get("priority_max") is not None: 
        clauses.append(f"[Microsoft.VSTS.Common.Priority] <= {int(filters['priority_max'])}")
    
    if filters.get("priority_min") is not None: 
        clauses.append(f"[Microsoft.VSTS.Common.Priority] >= {int(filters['priority_min'])}")
    
    for tag in filters.get("tags_include", []): 
        clauses.append(f"[System.Tags] CONTAINS '{sanitize_literal(tag)}'")
    
    for ap in filters.get("area_paths", []): 
        clauses.append(f"[System.AreaPath] UNDER '{sanitize_literal(ap)}'")
    
    for ip in filters.get("iteration_paths", []): 
        clauses.append(f"[System.IterationPath] UNDER '{sanitize_literal(ip)}'")
    
    # Assigned to filters
    if filters.get("assigned_to"):
        if filters["assigned_to"].lower() in ["me", "@me", "current user"]:
            clauses.append("[System.AssignedTo] = @Me")
        else:
            clauses.append(f"[System.AssignedTo] = '{sanitize_literal(filters['assigned_to'])}'")
    
    date_window = spec.get("date_window", {})
    if date_window and date_window.get("relative"):
        macro = date_macro(date_window["relative"])
        if macro: 
            field = date_window.get("field", "System.ChangedDate")
            clauses.append(f"[{field}] >= {macro}")
    
    for t in spec.get("free_text_terms", []): 
        clauses.append(f"[System.Title] CONTAINS '{sanitize_literal(t)}'")
    
    if not clauses: 
        clauses.append("[System.ChangedDate] >= @Today - 30")
    
    return " AND ".join(clauses)