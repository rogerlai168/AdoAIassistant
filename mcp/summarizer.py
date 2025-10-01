import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_api import AzureAIClient

def force_individual_ai_retry(client: AzureAIClient, item):
    """Force individual AI summary with aggressive retry - absolutely no fallback."""
    import time
    
    item_id = item.get("id")
    print(f"🔄 Forcing individual AI retry for item {item_id}...")
    
    prompt = f"""Create a professional 2-3 sentence summary for this Azure DevOps work item:

ID: {item_id}
Title: {item.get('title', '')[:150]}
Type: {item.get('type', 'Unknown')}
State: {item.get('state', 'Unknown')}
Priority: P{item.get('priority') if item.get('priority') is not None else 'N/A'}
Assigned: {item.get('assigned_to', 'Unassigned')}
Comments: {item.get('comment_count', 0)}

Provide a detailed, professional summary explaining the work item's purpose and current status."""

    messages = [
        {"role": "system", "content": "You are a professional Azure DevOps analyst. Create detailed, professional 2-3 sentence summaries."},
        {"role": "user", "content": prompt}
    ]
    
    # Aggressive retry with large token limits
    token_sizes_str = os.getenv("AZURE_OPENAI_RETRY_TOKEN_SIZES", "800,1200,1800,2500,3500,5000")
    token_sizes = [int(x.strip()) for x in token_sizes_str.split(",")]
    
    for max_tokens in token_sizes:
        try:
            print(f"🔄 Individual retry for item {item_id} with {max_tokens} tokens...")
            response = client.chat_completion(messages, max_tokens=max_tokens)
            
            if response and len(response.strip()) > 100:
                print(f"✅ Individual success for item {item_id}")
                return response.strip()
            else:
                print(f"⚠️ Short response, trying larger tokens...")
                
        except Exception as e:
            print(f"❌ Individual error with {max_tokens} tokens: {e}")
            time.sleep(0.5)
            continue
    
    # Absolutely no fallback - return error message
    print(f"🚨 Complete AI failure for item {item_id}")
    return f"AI analysis completely failed for work item {item_id} after all retry attempts."

def generate_fallback_summary(item):
    """Generate a professional fallback summary for a work item."""
    state = item.get("state", "Unknown")
    assigned = item.get("assigned_to", "Unassigned") 
    priority = item.get("priority")
    item_type = item.get("type", "Item")
    comment_count = item.get("comment_count", 0)
    partner_count = item.get("partner_comment_count", 0)
    tags = item.get("tags", [])
    
    # Determine urgency/importance indicators
    is_high_priority = priority in [1, 2] if priority else False
    has_active_discussion = comment_count > 5
    has_external_engagement = partner_count > 0
    
    # Build professional summary
    status_parts = []
    
    # State and assignment
    if state.lower() == "active":
        status_parts.append("Active work item")
    elif state.lower() == "completed":
        status_parts.append("Completed work item")
    elif state.lower() == "closed":
        status_parts.append("Closed work item")
    else:
        status_parts.append(f"{state} work item")
    
    if assigned != "Unassigned":
        status_parts.append(f"assigned to {assigned}")
    else:
        status_parts.append("currently unassigned")
    
    # Priority and engagement indicators
    context_parts = []
    
    if is_high_priority:
        context_parts.append(f"marked as P{priority} priority")
    
    if has_external_engagement:
        context_parts.append(f"with {partner_count} external comment{'s' if partner_count != 1 else ''}")
    elif has_active_discussion:
        context_parts.append(f"with active discussion ({comment_count} comments)")
    elif comment_count > 0:
        context_parts.append(f"with {comment_count} comment{'s' if comment_count != 1 else ''}")
    
    # Combine parts into professional sentences
    first_sentence = f"{status_parts[0]} {status_parts[1]}"
    if context_parts:
        second_sentence = f"This {item_type.lower()} is {', '.join(context_parts)}"
    else:
        second_sentence = f"This {item_type.lower()} requires attention to move forward"
    
    return f"{first_sentence}. {second_sentence}."
SUM_SYSTEM = ("You are an Azure DevOps work item status summarizer. "
              "Group by state, highlight risks (unassigned, stale >7d, blocked tags), be concise.")

INDIVIDUAL_SUMMARY_SYSTEM = """You are a professional Azure DevOps analyst. Create a concise, professional 2-sentence summary for work items.

FOCUS ON:
- Current status and assignment 
- Key business purpose or issue being addressed
- Any risks, blockers, or urgent attention needed
- Recent activity or collaboration indicators

FORMAT: Exactly 2 sentences. Be direct, technical but accessible. Avoid repeating the ID or title verbatim."""

def summarize_individual_items(client: AzureAIClient, items: list):
    """Generate professional summaries for individual work items."""
    summaries = {}
    
    # Process items individually for more reliable results
    for item in items:
        try:
            # Prepare item context for AI
            item_context = {
                "id": item.get("id"),
                "title": item.get("title", "")[:120],  # Truncate long titles
                "type": item.get("type", "Unknown"),
                "state": item.get("state", "Unknown"),
                "priority": item.get("priority"),
                "assigned_to": item.get("assigned_to", "Unassigned"),
                "tags": item.get("tags", [])[:3],  # Limit tags to first 3
                "changed_date": item.get("changed_date"),
                "comment_count": item.get("comment_count", 0),
                "partner_comment_count": item.get("partner_comment_count", 0),
                "area_path": item.get("area_path", "").split("\\")[-1] if item.get("area_path") else None,  # Last part only
                "recent_activity": get_recent_activity_summary(item)
            }
            
            # Get recent comment snippet for context
            recent_comment = get_recent_comment_snippet(item)
            if recent_comment:
                item_context["recent_comment"] = recent_comment
            
            # Generate summary with focused prompt
            messages = [
                {"role": "system", "content": INDIVIDUAL_SUMMARY_SYSTEM},
                {"role": "user", "content": f"Analyze this Azure DevOps work item and provide a 2-sentence professional summary:\n\n{item_context}"}
            ]
            
            response = client.chat_completion(messages, max_tokens=300)  # Removed temperature
            
            if response and response.strip():
                # Clean up the response
                summary = response.strip()
                # Remove any work item ID references that might have been added
                import re
                summary = re.sub(r'^\d+[:\-\s]*', '', summary)
                summaries[item.get("id")] = summary
            else:
                # Force individual AI retry instead of fallback
                print(f"🔄 Empty AI response for item {item.get('id')}, forcing aggressive retry...")
                summaries[item.get("id")] = force_individual_ai_retry(client, item)
                
        except Exception as e:
            # Force individual AI retry instead of fallback
            print(f"❌ Exception for item {item.get('id')}: {e}, forcing aggressive retry...")
            summaries[item.get("id")] = force_individual_ai_retry(client, item)
    
    return summaries

def get_recent_comment_snippet(item):
    """Get a snippet of the most recent comment for context."""
    comments = item.get("comments", [])
    if not comments:
        return None
        
    # Get the most recent comment
    latest_comment = comments[-1]
    text = latest_comment.get("text", "")
    
    # Strip HTML and get first 100 characters
    import re
    text = re.sub(r'<[^>]+>', ' ', text)  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    
    if len(text) > 100:
        text = text[:97] + "..."
    
    author = latest_comment.get("createdBy", {}).get("displayName", "Unknown")
    return f"Latest: '{text}' by {author}"

def get_recent_activity_summary(item):
    """Extract key recent activity indicators."""
    activity = []
    
    # Comment activity
    comment_count = item.get("comment_count", 0)
    partner_count = item.get("partner_comment_count", 0)
    
    if comment_count > 0:
        activity.append(f"{comment_count} comments")
    if partner_count > 0:
        activity.append(f"{partner_count} external")
    
    # State transitions
    transitions = item.get("state_transitions", [])
    if transitions:
        activity.append(f"last: {transitions[-1].get('to', 'unknown')}")
    
    # Recent updates
    if item.get("last_update_author"):
        activity.append(f"by {item.get('last_update_author')}")
    
    return " | ".join(activity) if activity else "minimal activity"

def parse_batch_summaries(response, batch, client: AzureAIClient):
    """Parse AI response to extract individual work item summaries."""
    summaries = {}
    
    # Split response by work item ID patterns
    import re
    lines = response.split('\n')
    current_id = None
    current_summary = []
    
    for line in lines:
        # Look for work item ID patterns
        id_match = re.search(r'\b(\d{8})\b', line)
        if id_match:
            # Save previous summary if exists
            if current_id and current_summary:
                summaries[current_id] = ' '.join(current_summary).strip()
            
            # Start new summary
            current_id = int(id_match.group(1))
            current_summary = []
            
            # Add the rest of the line after ID
            rest = line.split(str(current_id), 1)
            if len(rest) > 1:
                current_summary.append(rest[1].strip(' -:').strip())
        elif current_id and line.strip():
            # Continue building current summary
            current_summary.append(line.strip())
    
    # Don't forget the last one
    if current_id and current_summary:
        summaries[current_id] = ' '.join(current_summary).strip()
    
    # Ensure all batch items have summaries
    for item in batch:
        item_id = item.get("id")
        if item_id not in summaries:
            summaries[item_id] = force_individual_ai_retry(client, item)
    
    return summaries

def summarize(client: AzureAIClient, original_query: str, items: list):
    """Generate a summary of Azure DevOps work items using AI."""
    compact = []
    for it in items[:40]:
        slim = {k: it.get(k) for k in ("id", "title", "type", "state", "priority", 
                                       "assigned_to", "tags", "changed_date", 
                                       "closed_date", "resolved_date")}
        slim["comment_count"] = it.get("comment_count") 
        slim["partner_comment_count"] = it.get("partner_comment_count")
        compact.append(slim)
    
    messages = [
        {"role": "system", "content": SUM_SYSTEM},
        {"role": "user", "content": f"Query: {original_query}\\nItems JSON: {compact}"}
    ]
    
    return client.chat_completion(messages, max_tokens=600)  # Removed temperature parameter