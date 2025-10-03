import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_api import AzureAIClient
from mcp.config import MAX_TOKENS_WIQL, MAX_ITEMS_UI_DEFAULT  # <-- ADD MAX_ITEMS_UI_DEFAULT

def parse_with_ai(client: AzureAIClient, user_query: str):
    """Parse user query using AI to detect WIQL generation AND summarization intent."""
    try:
        # Enhanced system prompt for combined intent detection
        enhanced_system = """You are an intelligent Azure DevOps query parser. Analyze user requests for two types of intent:

1. **WIQL Generation**: Extract work items from Azure DevOps
2. **AI Analysis**: Provide intelligent summaries or analysis

🎯 **OUTPUT FORMAT**: Always return JSON with this structure:
{
  "wiql_query": "SELECT ... (full WIQL query)",
  "max_items": """ + str(MAX_ITEMS_UI_DEFAULT) + """,
  "direct_wiql": true,
  "has_analysis_request": false,
  "analysis_prompt": null
}

If user requests BOTH listing AND analysis (like "list tickets... and summarize"), set:
- "has_analysis_request": true  
- "analysis_prompt": "user's analysis request (e.g., 'summarize the comments like newsletter')"

🔧 **WIQL RULES**: [Include existing WIQL rules from system_parser.txt]

📝 **ANALYSIS DETECTION**:
- Words like "summarize", "analyze", "newsletter", "insights" = analysis request
- Extract the analysis part as analysis_prompt
- Combined requests: "list X and then summarize Y" → both WIQL + analysis

⚡ **EXAMPLES**:

Input: "list tickets with tag he_swe_wat for past 14 days"  
Output: {"wiql_query": "SELECT...", "has_analysis_request": false}

Input: "list tickets with tag he_swe_wat for past 14 days and then summarize the comments like newsletter"
Output: {
  "wiql_query": "SELECT...", 
  "has_analysis_request": true,
  "analysis_prompt": "summarize the comments like newsletter"
}
"""

        messages = [
            {"role": "system", "content": enhanced_system},
            {"role": "user", "content": user_query}
        ]
        
        raw = client.chat_completion(messages, max_tokens=MAX_TOKENS_WIQL, auto_retry=True)
        
        # Parse the JSON response
        result = json.loads(raw.strip())
        
        # If has analysis request, set freeform_prompt for tool_query_work_items
        if result.get("has_analysis_request") and result.get("analysis_prompt"):
            result["freeform_prompt"] = result["analysis_prompt"]
            
        return result
        
    except Exception as e:
        # Fallback to WIQL-only mode with current system
        try:
            # Load the system prompt fresh each time to pick up changes
            with open("prompts/system_parser.txt", "r", encoding="utf-8") as f:
                parser_system = f.read()
                
            messages = [
                {"role": "system", "content": parser_system},
                {"role": "user", "content": user_query}
            ]
            
            # Get WIQL query directly from AI
            # Use configured WIQL parsing token limit
            parser_tokens = int(os.getenv("AZURE_OPENAI_PARSER_TOKENS", str(MAX_TOKENS_WIQL)))
            raw = client.chat_completion(messages, max_tokens=parser_tokens, auto_retry=True)
            
            if not raw or raw.strip() == "":
                raise ValueError("AI parser returned empty response")
            
            # Clean up the response - extract WIQL if wrapped in markdown or other text
            wiql = raw.strip()
            
            # Remove markdown code blocks if present
            if "```" in wiql:
                lines = wiql.split('\n')
                in_code_block = False
                wiql_lines = []
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not in_code_block and line.strip().startswith('SELECT')):

                        wiql_lines.append(line)
                wiql = '\n'.join(wiql_lines).strip()
            
            # Validate it looks like WIQL
            if not wiql.upper().startswith('SELECT'):
                raise ValueError("AI response doesn't appear to be valid WIQL")
                
            # Return as a spec that tools.py expects, but with direct WIQL
            return {
                "wiql_query": wiql,
                "max_items": MAX_ITEMS_UI_DEFAULT,  # Default
                "direct_wiql": True  # Flag to indicate this is direct WIQL
            }
            
        except Exception as e:
            raise ValueError(f"AI WIQL generation failed: {e}") from e