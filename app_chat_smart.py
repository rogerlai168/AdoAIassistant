import streamlit as st
import pandas as pd
import time
import os
import json
from mcp.tools import tool_query_work_items
from mcp.config import MAX_ITEMS_DEFAULT, MAX_ITEMS_UI_DEFAULT, MAX_ITEMS_UI_MIN
from ai_api import get_ai_client

st.set_page_config(page_title="AI ADO Copilot", layout="wide")
st.title("🤖 AI ADO Copilot - Intelligent Assistant")

# Get ADO configuration for creating work item links
def get_ado_config():
    """Get ADO organization and project from environment variables."""
    org = os.getenv("AZDO_ORG", "Microsoft")
    project = os.getenv("AZDO_PROJECT", "OS")
    return org, project

def create_work_item_link(item_id, org, project):
    """Create a clickable Azure DevOps work item link."""
    base_url = f"https://dev.azure.com/{org}/{project}/_workitems/edit/{item_id}"
    return f"[{item_id}]({base_url})"

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "last_query_data" not in st.session_state:
    st.session_state.last_query_data = None
if "last_query_time" not in st.session_state:
    st.session_state.last_query_time = None

# Sidebar controls - simplified
with st.sidebar:
    st.header("⚙️ Query Settings")
    max_items = st.number_input("Max items", MAX_ITEMS_UI_MIN, MAX_ITEMS_DEFAULT, MAX_ITEMS_UI_DEFAULT)
    
    # Hidden/automatic optimal defaults
    include_comments = True      # Always include - needed for AI analysis
    include_partner = False      # Default off - can be noisy
    use_ai_parser = True         # Always use - it's smarter
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.history.clear()
        st.session_state.last_query_data = None
        st.session_state.last_query_time = None
    
    st.caption("💡 Requires prior 'az login'")
    
    # Show cache status
    if st.session_state.last_query_data:
        cache_age = time.time() - st.session_state.last_query_time
        cache_items = st.session_state.last_query_data.get("count", 0)
        st.success(f"📦 Cached: {cache_items} items ({cache_age/60:.1f}m ago)")
    else:
        st.info("🔍 No cached data")

def render_message(m):
    """Render a message in the chat."""
    if m["role"] == "user":
        st.markdown(f"**🧑 You:** {m['content']}")
    elif m["role"] == "assistant":
        st.markdown(f"**🤖 Assistant:** {m['content']}")
    elif m["role"] == "tool":
        tool_name = m['meta'].get('tool', 'Unknown Tool')
        
        if tool_name == "query_work_items":
            # Format work items data in a readable way
            data = m["meta"]["data"]
            with st.expander(f"📊 Query Results", False):
                
                # Show WIQL query
                if "wiql_query" in data:
                    st.markdown("**📝 WIQL Query:**")
                    st.code(data["wiql_query"], language="sql")
                
                # Show count
                item_count = data.get("count", 0)
                st.markdown(f"**📊 Results:** {item_count} work items found")
                
                # Show work items in a readable table format with clickable links
                if "items" in data and data["items"]:
                    st.markdown("**📋 Work Items:**")
                    
                    # Get ADO configuration for creating links
                    org, project = get_ado_config()
                    
                    # Header row
                    header_cols = st.columns([1, 4, 1, 1, 2, 1])
                    with header_cols[0]:
                        st.markdown("**ID**")
                    with header_cols[1]:
                        st.markdown("**Title**")
                    with header_cols[2]:
                        st.markdown("**Type**")
                    with header_cols[3]:
                        st.markdown("**State**")
                    with header_cols[4]:
                        st.markdown("**Assigned**")
                    with header_cols[5]:
                        st.markdown("**Priority**")
                    
                    st.divider()
                    
                    # Display items as a nice formatted table with clickable links
                    for i, item in enumerate(data["items"], 1):
                        item_id = item.get("id", "N/A")
                        full_title = item.get("title", "No title")
                        work_item_url = f"https://dev.azure.com/{org}/{project}/_workitems/edit/{item_id}"
                        
                        # Create a row with clickable link and full details
                        cols = st.columns([1, 4, 1, 1, 2, 1])
                        
                        with cols[0]:
                            st.markdown(f"**[{item_id}]({work_item_url})**")
                        
                        with cols[1]:
                            st.markdown(f"{full_title}")
                        
                        with cols[2]:
                            st.markdown(item.get("type", "N/A"))
                        
                        with cols[3]:
                            state = item.get("state", "N/A")
                            if state.lower() == "active":
                                st.markdown(f"🟢 {state}")
                            elif state.lower() == "completed":
                                st.markdown(f"✅ {state}")
                            elif state.lower() == "closed":
                                st.markdown(f"🔒 {state}")
                            else:
                                st.markdown(state)
                        
                        with cols[4]:
                            st.markdown(item.get("assigned_to", "Unassigned"))
                        
                        with cols[5]:
                            priority = item.get("priority")
                            if priority is not None:
                                if priority in [0, 1, 2]:
                                    st.markdown(f"🔴 P{priority}")
                                elif priority == 3:
                                    st.markdown(f"🟡 P{priority}")
                                else:
                                    st.markdown(f"P{priority}")
                            else:
                                st.markdown("N/A")
                        
                        if i < len(data["items"]):
                            st.divider()
                    
                    # Show total count
                    st.info(f"Showing all {len(data['items'])} items")

        elif tool_name == "ai_analysis_cached":
            # Format cached analysis results
            data = m["meta"]["data"]
            with st.expander(f"🧠 AI Analysis Results", False):
                st.markdown(f"**Analysis Type:** {data.get('analysis_type', 'Full')}")
                st.markdown(f"**Items Analyzed:** {data.get('items_analyzed', 0)}")
                st.markdown(f"**Individual Summaries:** {data.get('individual_count', 0)}")
                if data.get('cached'):
                    st.success("✅ Used cached data (no new ADO query)")
        
        else:
            # Default JSON view for other tools
            with st.expander(f"🔧 Tool: {tool_name}", False):
                st.json(m["meta"]["data"])

def analyze_user_intent_with_ai(query, cached_data):
    """
    AI-powered intent detection to replace primitive keyword matching.
    Determines whether user wants new data or analysis of cached data.
    """
    client = get_ai_client()
    
    # Create context-aware prompt
    cache_context = ""
    if cached_data:
        cache_count = cached_data.get("count", 0)
        cache_age_minutes = (time.time() - st.session_state.last_query_time) / 60 if st.session_state.last_query_time else 0
        cache_context = f"CACHED DATA AVAILABLE: {cache_count} work items ({cache_age_minutes:.1f} minutes old)"
    else:
        cache_context = "NO CACHED DATA AVAILABLE"
        
    intent_prompt = f"""You are an intelligent intent detection system for an Azure DevOps assistant.

CONTEXT: {cache_context}

USER QUERY: "{query}"

Analyze the user's intent and determine the appropriate action. Return JSON only:

{{
    "intent_type": "NEW_QUERY|CACHED_ANALYSIS|COMBINED",
    "confidence": 0.0-1.0,
    "analysis_request": {{
        "is_analysis": true/false,
        "analysis_type": "newsletter|summary|insights|comments|timeline|report|full",
        "format_requirements": "specific format requests from user",
        "analysis_prompt": "extracted analysis instruction for AI"
    }},
    "reasoning": "brief explanation of decision"
}}

INTENT TYPES:
- NEW_QUERY: User wants fresh data from Azure DevOps ("show me bugs", "list tickets") 
- CACHED_ANALYSIS: User wants to analyze existing cached data ("summarize that", "create newsletter from cache", "analyze those tickets")
- COMBINED: User wants both fresh data AND analysis ("list tickets and summarize them")

KEY INDICATORS:
- References to cached data: "cache", "that data", "those tickets", "above results", "previous query"
- Analysis requests: "summarize", "analyze", "newsletter", "insights", "report", "tell me about"
- Format specifications: "newsletter format", "executive summary", "bullet points"
- Time references: "from today", "last week" (usually NEW_QUERY unless referring to cached data)

EXAMPLES:
"show me bugs from today" → NEW_QUERY
"summarize cache data for WAT newsletter" → CACHED_ANALYSIS  
"analyze those tickets for trends" → CACHED_ANALYSIS
"list tasks and create summary" → COMBINED"""

    try:
        messages = [
            {"role": "system", "content": "You are an expert intent detection AI. Return only valid JSON with the exact structure requested."},
            {"role": "user", "content": intent_prompt}
        ]
        
        response = client.chat_completion(messages, max_tokens=500, auto_retry=True)
        intent_result = json.loads(response.strip())
        
        # Validate the response structure
        required_fields = ["intent_type", "confidence", "analysis_request", "reasoning"]
        if not all(field in intent_result for field in required_fields):
            raise ValueError("Invalid AI response structure")
            
        return intent_result
        
    except Exception as e:
        st.warning(f"AI intent detection failed: {e}. Using fallback logic.")
        
        # Fallback to improved heuristics
        query_lower = query.lower()
        
        # Check for cached data references
        cached_refs = ["cache", "that", "those", "above", "previous", "these"]
        has_cache_ref = any(ref in query_lower for ref in cached_refs)
        
        # Check for analysis requests  
        analysis_terms = ["summarize", "analyze", "newsletter", "insights", "report", "tell me about", "create", "generate"]
        has_analysis = any(term in query_lower for term in analysis_terms)
        
        if cached_data and has_cache_ref and has_analysis:
            return {
                "intent_type": "CACHED_ANALYSIS",
                "confidence": 0.8,
                "analysis_request": {
                    "is_analysis": True,
                    "analysis_type": "summary",
                    "format_requirements": "newsletter" if "newsletter" in query_lower else "",
                    "analysis_prompt": query
                },
                "reasoning": "Fallback: detected cache reference + analysis terms"
            }
        else:
            return {
                "intent_type": "NEW_QUERY", 
                "confidence": 0.7,
                "analysis_request": {"is_analysis": False},
                "reasoning": "Fallback: no clear cache analysis pattern"
            }

def handle_cached_analysis(query, cached_data, intent_result):
    """Handle AI analysis of cached data."""
    import time
    from mcp.tools import tool_summarize_cached_items

    if not cached_data or "items" not in cached_data:
        return None

    analysis_request = intent_result.get("analysis_request", {})
    analysis_type = analysis_request.get("analysis_type", "summary")
    format_requirements = analysis_request.get("format_requirements", "")
    
    # Enhanced analysis prompt with format requirements
    enhanced_prompt = query
    if format_requirements:
        enhanced_prompt = f"{query}\n\nFormat Requirements: {format_requirements}"
    
    st.info(f"🧠 AI-powered {analysis_type} analysis of cached results")

    start = time.time()
    result = tool_summarize_cached_items({
        "query": enhanced_prompt,
        "items": cached_data["items"]
    })
    elapsed = time.time() - start

    if result.get("error"):
        return {
            "result": {"summary": f"Error: {result['error']}", "individual_summaries": {}},
            "elapsed": elapsed,
            "info": f"❌ AI analysis failed"
        }

    return {
        "result": result,
        "elapsed": elapsed,
        "info": f"🧠 AI {analysis_type} analysis of {result.get('count', 0)} cached items"
    }

# Display chat history
for message in st.session_state.history:
    render_message(message)

# Chat input
prompt = st.chat_input("💬 Ask about ADO work items...")

if prompt:
    # 🎯 IMMEDIATELY ECHO USER INPUT
    st.session_state.history.append({"role": "user", "content": prompt})
    
    # Show the user input right away
    with st.chat_message("user"):
        st.write(f"🔍 **Processing query:** {prompt}")
    
    # AI-powered intent detection
    cache_ttl = 600  # 10 minutes cache
    cache_valid = (
        st.session_state.last_query_data and 
        st.session_state.last_query_time and 
        (time.time() - st.session_state.last_query_time) < cache_ttl
    )
    
    with st.chat_message("assistant"):
        with st.spinner("🧠 Analyzing your request..."):
            intent_result = analyze_user_intent_with_ai(prompt, st.session_state.last_query_data if cache_valid else None)
        
        intent_type = intent_result.get("intent_type")
        confidence = intent_result.get("confidence", 0.0)
        reasoning = intent_result.get("reasoning", "")
        
        # Show AI reasoning for transparency
        with st.expander("🤖 AI Intent Analysis", expanded=False):
            st.write(f"**Intent:** {intent_type}")
            st.write(f"**Confidence:** {confidence:.1%}")
            st.write(f"**Reasoning:** {reasoning}")
        
        # Execute based on AI-detected intent
        if intent_type == "CACHED_ANALYSIS" and cache_valid:
            # Handle cached data analysis
            with st.spinner(f"🧠 Analyzing cached data: {prompt}"):
                analysis_result = handle_cached_analysis(prompt, st.session_state.last_query_data, intent_result)
        
            if analysis_result:
                # Process and display results similar to existing code
                summary_content = analysis_result["result"].get("summary", "Analysis completed.")
                individual_summaries = analysis_result["result"].get("individual_summaries", {})
                cached_items = st.session_state.last_query_data["items"]
                
                analysis_type = intent_result.get("analysis_request", {}).get("analysis_type", "full")
                
                # Create a lightweight tool entry
                tool_data = {
                    "analysis_type": analysis_type,
                    "items_analyzed": len(cached_items),
                    "summary": summary_content,
                    "individual_count": len(individual_summaries),
                    "cached": True
                }
                
                # Add tool call to history
                st.session_state.history.append({
                    "role": "tool",
                    "content": "AI analysis of cached data",
                    "meta": {
                        "tool": "ai_analysis_cached",
                        "data": tool_data
                    }
                })
                
                # Create response with individual ticket summaries
                response_parts = [summary_content]
                
                if individual_summaries and any(v.strip() for v in individual_summaries.values()):
                    response_parts.append("\n\n## 📋 Individual Ticket Summaries:")
                    
                    for item_id, summary in individual_summaries.items():
                        if summary and len(summary.strip()) > 0:
                            # Find the ticket title for better context
                            ticket_title = "Unknown"
                            for item in cached_items:
                                if str(item.get("id")) == str(item_id):
                                    ticket_title = item.get("title", "Unknown")[:60]
                                    if len(item.get("title", "")) > 60:
                                        ticket_title += "..."
                                    break
                            
                            response_parts.append(f"\n**#{item_id} - {ticket_title}**")
                            response_parts.append(f"\n{summary}\n")
                
                response_content = "".join(response_parts)
                
                st.session_state.history.append({
                    "role": "assistant",
                    "content": response_content
                })
            else:
                st.session_state.history.append({
                    "role": "assistant",
                    "content": "❌ Failed to analyze cached data. Please try a new query."
                })
        
        elif intent_type == "CACHED_ANALYSIS" and not cache_valid:
            # User wants cached analysis but no valid cache
            st.session_state.history.append({
                "role": "assistant", 
                "content": "⚠️ No cached data available for analysis. Please run a query first to get data, then ask for analysis."
            })
        
        else:
            # Handle new query (NEW_QUERY or COMBINED or low confidence CACHED_ANALYSIS)
            with st.spinner(f"🔍 Querying Azure DevOps: {prompt}"):
                start = time.time()
                
                data = tool_query_work_items({
                    "query": prompt,
                    "max_items": max_items,
                    "include_comments": include_comments,
                    "include_partner_comments": include_partner,  
                    "use_ai_parser": use_ai_parser
                })
                
                elapsed = time.time() - start
            
            # Cache the results
            st.session_state.last_query_data = data
            st.session_state.last_query_time = time.time()
            
            # Add to history
            st.session_state.history.append({
                "role": "tool",
                "content": "tool output",
                "meta": {
                    "tool": "query_work_items",
                    "data": data
                }
            })
            
            # Add assistant response
            summary = data.get("summary") or "No summary available."
            
            # If this was a COMBINED intent, add note about follow-up analysis
            if intent_type == "COMBINED":
                summary += "\n\n💡 *Data retrieved and cached. You can now ask for analysis of these results.*"
            
            st.session_state.history.append({
                "role": "assistant", 
                "content": summary
            })
    
    # Refresh the page to show new messages
    st.rerun()

# Show help in sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💡 Usage Tips")
    st.markdown("""
    **🤖 AI-Powered Intent Detection**
    The system automatically understands your intent:
    
    **🔍 New Queries:**
    - "List tickets with tag he_swe_wat"
    - "Show me bugs from today"
    - "Find high priority tasks"
    
    **🧠 Cached Analysis:**
    - "Summarize cache data for newsletter"
    - "Analyze those tickets for trends" 
    - "Create WAT newsletter from that data"
    
    **⚡ Combined:**
    - "List tickets and summarize them"
    - "Show bugs and create insights report"
    """)
