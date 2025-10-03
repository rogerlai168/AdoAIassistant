import traceback
import os
import sys
from typing import Any, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_api import get_ai_client
from .ado_client import AdoClient
from .normalize import normalize
from .nlp_rules import heuristic_parse
from .ai_parser import parse_with_ai
from .wiql_builder import build, build_wiql_query
from .intelligent_summarizer import freeform_analyze
from mcp.config import MAX_ITEMS_DEFAULT, MAX_ITEMS_UI_DEFAULT, MAX_ITEMS_COMMENTS

# Legacy summarization / granular analysis fully deprecated.
HAS_OPTIMIZED = False
HAS_GRANULAR = False

class Context:
    def __init__(self):
        self.llm = get_ai_client()
        self.client = AdoClient()

ctx = Context()

# Session cache to store last query results for follow-up AI analysis
_last_query_cache = {
    "items": [],
    "query": "",
    "timestamp": None
}

def tool_query_work_items(p: Dict[str, Any], cached_items: list = None):
    """
    Query work items from ADO or analyze cached items with AI.
    
    Args:
        p: Query parameters
        cached_items: Pre-loaded work items to analyze (skips ADO query)
    """
    q = p["query"]
    
    # 🎯 IMMEDIATELY ECHO USER INPUT
    print(f"🔍 Processing query: {q}")
    print("=" * (len(q) + 20))
    
    # If cached items provided, use them for AI analysis
    if cached_items is not None:
        items = cached_items
        wiql_query = f"-- cached items ({len(items)})"
        import time
        _last_query_cache["items"] = items
        _last_query_cache["query"] = p.get("query", "")
        _last_query_cache["timestamp"] = time.time()
        return {
            "wiql_query": wiql_query,
            "count": len(items),
            "items": items,
            "summary": "",
            "individual_summaries": {}
        }
    
    # Normal flow: parse query and get items from ADO
    print("🤖 Starting AI parsing...")
    
    # Try AI parser first if enabled
    if p.get("use_ai_parser", True):
        try:
            spec = parse_with_ai(ctx.llm, q)
            
            if spec.get("direct_wiql"):
                wiql_query = spec["wiql_query"]
                max_items = spec.get("max_items", 50)
            else:
                max_items = p.get("max_items") or spec.get("max_items") or 50
                spec["max_items"] = min(int(max_items), 250)
                wiql_query = build_wiql_query(spec)
                
        except Exception as e:
            print(f"❌ AI parser failed: {e}")
            raise RuntimeError("AI parser failed. Please check your query syntax.")
    else:
        spec = heuristic_parse(q)
        max_items = p.get("max_items") or spec.get("max_items") or 50
        spec["max_items"] = min(int(max_items), 250)
        wiql_query = build_wiql_query(spec)
        max_items = spec["max_items"]

    # Execute the WIQL query
    ids = ctx.client.wiql_ids(wiql_query, top=max_items)
    
    if not ids:
        return {"summary": f"No work items found for query: {q}", "items": [], "count": 0, "wiql_query": wiql_query}
    
    print(f"🔍 Found {len(ids)} work item IDs, loading details...")
    raws = ctx.client.batch(ids)
    
    # 🚀 OPTIMIZED: Use conditional comment loading (only loads when items have comments)
    if p.get("include_comments", True):
        print(f"💬 Smart loading comments (checking which items have them)...")
        comments_by_id = ctx.client.comments_conditional(raws, verbose=True, top=MAX_ITEMS_COMMENTS)
    else:
        print(f"⚡ Skipping comment loading (disabled)")
        comments_by_id = {r["id"]: [] for r in raws}
    
    # OPTIMIZATION: Parallel updates loading  
    print(f"🚀 Loading updates for {len(raws)} work items in parallel...")
    work_item_ids = [r["id"] for r in raws]
    updates_by_id = ctx.client.updates_parallel(work_item_ids, max_workers=15)
    
    # Process work items with pre-loaded comments and updates
    items = []
    for r in raws:
        c = comments_by_id.get(r["id"], [])
        u = updates_by_id.get(r["id"], [])
        items.append(normalize(r, c, u))
    
    # Cache the results
    import time
    _last_query_cache["items"] = items
    _last_query_cache["query"] = q
    _last_query_cache["timestamp"] = time.time()
    
    # Optional inline freeform summary
    freeform_prompt = spec.get("freeform_prompt")
    summary = ""
    if freeform_prompt and items:
        try:
            summary = freeform_analyze(ctx.llm, freeform_prompt, items)
        except Exception as e:
            summary = f"[Freeform analysis error: {e}]"

    return {
        "wiql_query": wiql_query,
        "count": len(items),
        "items": items,
        "summary": summary,
        "individual_summaries": {}
    }

def tool_get_work_item(p):
    wid = int(p["id"])
    include_comments = p.get("include_comments", True)
    print(f"Getting work item {wid} with comments: {include_comments}")
    raws = ctx.client.batch([wid])
    if not raws:
        return {"error": "Work item not found"}
    r = raws[0]
    
    # OPTIMIZATION: Use optimized comment loading
    if include_comments:
        c = ctx.client.comments(wid, top=MAX_ITEMS_COMMENTS, verbose=True)  # Limit to 50 comments
    else:
        c = []
        
    u = ctx.client.updates(wid)
    item = normalize(r, c, u)
    
    return {"item": item}

def tool_summarize_items(p):
    """
    Deprecated wrapper retained for backward compatibility.
    Uses freeform analysis on provided items.
    Params:
      - p['items']: list of work items
      - p['prompt'] or p['original_query']: user instruction
    """
    items = p.get("items") or []
    prompt = p.get("prompt") or p.get("original_query") or "Provide a professional overview of these work items."
    try:
        result = freeform_analyze(ctx.llm, prompt, items)
    except Exception as e:
        result = f"[Freeform analysis failed: {e}]"
    return {"summary": result}

def tool_summarize_cached_items(p):
    """Freeform AI analysis over provided items list (cache-aware upstream)."""
    user_prompt = p.get("query") or p.get("prompt") or "Provide a professional overview."
    items = p.get("items") or []
    
    # DEBUG: Add logging to see what we're actually getting
    print(f"🔍 DEBUG tool_summarize_cached_items:")
    print(f"   📝 User prompt: {user_prompt}")
    print(f"   📊 Items count: {len(items)}")
    if items:
        print(f"   📋 Sample item keys: {list(items[0].keys())[:5]}...")
        # Check if items have comment data
        sample_comments = items[0].get("comments", [])
        print(f"   💬 Sample item comments: {len(sample_comments)}")
    
    try:
        ai_response = freeform_analyze(ctx.llm, user_prompt, items)
        
        # DEBUG: Log the actual AI response
        print(f"🤖 DEBUG AI Response:")
        print(f"   📏 Length: {len(ai_response) if ai_response else 0}")
        print(f"   📝 Content: {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}")
        
    except Exception as e:
        ai_response = f"[Freeform analysis failed: {e}]"
        print(f"❌ DEBUG AI Error: {e}")
    
    return {
        "summary": ai_response,
        "count": len(items),
        "individual_summaries": {},
    }

def tool_explain_field(p):
    field = p["field"]
    explanations = {
        "Microsoft.VSTS.Common.Priority": "Numeric priority (1 highest).",
        "System.State": "Lifecycle state.",
        "System.IterationPath": "Sprint/backlog path."
    }
    return {"field": field, "explanation": explanations.get(field, "Unknown field.")}

TOOLS = {
    "query_work_items": tool_query_work_items,
    "get_work_item": tool_get_work_item,
    "summarize_items": tool_summarize_items,
    "summarize_cached_items": tool_summarize_cached_items,
    "explain_field": tool_explain_field
}

def invoke(name, params):
    fn = TOOLS.get(name)
    if not fn:
        return {"error": "unknown_tool"}
    try:
        return fn(params or {})
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()[:4000]}