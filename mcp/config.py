"""
Centralized configuration for Azure DevOps AI Assistant
"""

# Work item limits
MAX_ITEMS_DEFAULT = 250        # Maximum items for comprehensive analysis
MAX_ITEMS_UI_DEFAULT = 150     # Default shown in UI (updated from 50 to 150)
MAX_ITEMS_UI_MIN = 5          # Minimum items user can select
MAX_ITEMS_COMMENTS = 50        # Comments per work item limit

# Token limits (for AI analysis)
MAX_TOKENS_ANALYSIS = 10000     # GPT-5-mini analysis token limit
MAX_TOKENS_WIQL = 2000        # WIQL parsing token limit

# API limits
WIQL_DEFAULT_TOP = 150         # Align with UI default for consistency
WIQL_MAX_RETRIES = 3         # WIQL retry attempts