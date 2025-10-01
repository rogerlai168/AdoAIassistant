"""
Freeform AI Work Item Analysis
Minimal interface: user supplies prompt + raw items → AI answer.
All prior intent/mode detection removed for simplicity.
"""

import os
import sys
import json  # Added missing import
from typing import List, Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_api import AzureAIClient
from mcp.config import MAX_ITEMS_DEFAULT, MAX_TOKENS_ANALYSIS

MAX_TITLE_LEN = 160
INCLUDE_FIELDS = [
    "System.State",
    "System.AssignedTo",
    "Microsoft.VSTS.Common.Priority",
    "System.Tags",
    "System.WorkItemType",
    "System.ChangedDate",
    "System.CreatedDate"
]

def _compact_items(items: List[Dict], max_items: int = MAX_ITEMS_DEFAULT):
    """Produce a compact representation safe for prompt injection."""
    compact = []
    for it in items[:max_items]:
        raw_fields = it.get("fields", {})
        # Detect if this is normalized (flattened) or raw Azure DevOps shape
        normalized = not raw_fields and (
            "title" in it or "state" in it or "assigned_to" in it or "priority" in it
        )
        
        # Extract comments content for AI analysis - let AI handle HTML cleanup
        comments = it.get("comments", [])
        comment_summary = []
        if comments:
            # Include recent comment details (limit to last 5 for token efficiency)
            for comment in comments[-5:]:
                raw_text = comment.get("text", "")
                # Just truncate, let AI handle HTML cleanup
                comment_text = raw_text[:300] if len(raw_text) > 300 else raw_text
                
                author = comment.get("createdBy", {}).get("displayName", "Unknown")
                date = comment.get("createdDate", "")[:10]  # Just date, not time
                
                comment_summary.append({
                    "author": author,
                    "date": date,
                    "text": comment_text  # Raw text - AI will clean it
                })
        
        if normalized:
            # Normalized shape from normalize.py
            tags = it.get("tags")
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(";") if tag.strip()]
            elif not isinstance(tags, list):
                tags = []
            
            compact.append({
                "id": it.get("id"),
                "shape": "normalized",
                "title": (it.get("title") or "")[:MAX_TITLE_LEN],
                "type": it.get("type"),
                "state": it.get("state"),
                "assigned": it.get("assigned_to"),
                "priority": it.get("priority"),
                "tags": tags[:3],  # Limit to first 3 tags
                "comment_count": it.get("comment_count"),
                "partner_comment_count": it.get("partner_comment_count"),
                "recent_comments": comment_summary,  # Raw comments - AI will clean
                "created_date": it.get("created_date"),
                "changed_date": it.get("changed_date"),
            })
        else:
            # Raw Azure DevOps shape with full field map
            assigned = raw_fields.get("System.AssignedTo")
            if isinstance(assigned, dict):
                assigned = assigned.get("displayName")
            compact.append({
                "id": it.get("id"),
                "shape": "raw",
                "title": (raw_fields.get("System.Title") or "")[:MAX_TITLE_LEN],
                "type": raw_fields.get("System.WorkItemType"),
                "state": raw_fields.get("System.State"),
                "assigned": assigned,
                "priority": raw_fields.get("Microsoft.VSTS.Common.Priority"),
                "tags": raw_fields.get("System.Tags"),
                "comment_count": len(it.get("comments", [])),
                "partner_comment_count": len(it.get("partner_comments", [])),
                "recent_comments": comment_summary,  # Raw comments - AI will clean
                "created_date": raw_fields.get("System.CreatedDate"),
                "changed_date": raw_fields.get("System.ChangedDate"),
            })
    return compact

def freeform_analyze(client: AzureAIClient, user_prompt: str, items: List[Dict], max_items: int = MAX_ITEMS_DEFAULT) -> str:
    """
    Direct freeform analysis. No classification, no mode logic.
    """
    if not items:
        return "No work items available for analysis."
    
    compact = _compact_items(items, max_items=max_items)
    
    system = (
        "You are an Azure DevOps work item analysis assistant.\n"
        "Input: compact JSON list of items (each has 'shape': 'normalized' or 'raw').\n"
        "If shape == 'normalized' and id/title/state exist, do NOT claim metadata is missing.\n"
        "Never fabricate fields. Highlight only evidence-supported patterns (state distribution, priority hotspots, stale, unassigned, comment activity).\n"
        "Respond directly to the user prompt with structured, insight-dense output (sections / bullets / concise narrative as appropriate).\n"
        "Be professional, direct, and avoid unnecessary hedging or apologies.\n"
        "\n"
        "IMPORTANT: Comment text may contain HTML markup and Azure DevOps @mention tags. "
        "When displaying comments, automatically clean up HTML tags and convert mention markup to readable @username format. "
        "Extract the meaningful content and present it in a clean, readable format."
    )
    
    user_content = f"""
User Request: {user_prompt}

Work Items Data (JSON):
{json.dumps(compact, indent=2)}

Please analyze this data according to the user's request above.
When showing comment content, clean up any HTML markup and present it in readable format.
"""
    
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content}
    ]
    
    print(f"🤖 Freeform AI Analysis starting (max_items: {max_items})")
    
    return client.chat_completion(
        messages, 
        max_tokens=MAX_TOKENS_ANALYSIS,
        auto_retry=True
    )

# Backward compatibility shims
def intelligent_analyze(client: AzureAIClient, user_query: str, work_items: List[Dict]) -> str:
    return freeform_analyze(client, user_query, work_items)

def intelligent_analyze_individual_items(client: AzureAIClient, user_query: str, work_items: List[Dict]):
    # Return dict mapping id -> generic note pointing to global analysis
    analysis = freeform_analyze(client, user_query, work_items)
    return {it.get("id"): "See overall analysis section.\n" for it in work_items}, analysis