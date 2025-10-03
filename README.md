# 🤖 AI Azure DevOps Copilot

An intelligent Azure DevOps assistant that combines natural language processing, AI-powered intent detection, and advanced work item analysis capabilities. Built with modern AI architecture for enterprise-scale Azure DevOps integration.

## ✨ Features

### 🧠 AI-Powered Intent Detection
- **Smart Query Understanding**: AI automatically detects whether you want new data or analysis of cached results
- **Context-Aware Processing**: Understands data availability, cache freshness, and user intent
- **Natural Language Interface**: No need to learn query syntax - just ask in plain English

### 🔍 Advanced Azure DevOps Integration  
- **Intelligent WIQL Generation**: AI converts natural language to optimized WIQL queries
- **Microsoft Documentation Compliant**: Follows official Azure DevOps REST API best practices
- **Enterprise Scale Ready**: Tested with 58M+ work items in Microsoft/OS project
- **Smart Caching**: 10-minute cache with intelligent reuse detection

### 📊 Flexible Analysis Workflows

#### 🚀 New Query Mode
- **Fast Data Retrieval**: Optimized for quick work item listing
- **Real-time Results**: Direct Azure DevOps API integration
- **Smart Defaults**: Automatically includes comments and uses AI parsing

#### 🧠 Cached Analysis Mode  
- **AI-Powered Insights**: Generate newsletters, summaries, and reports from cached data
- **Format-Aware**: Recognizes specific output formats (newsletter, executive summary, etc.)
- **Granular Analysis**: Focus on comments, timeline, updates, or full analysis

#### ⚡ Combined Mode
- **One-Step Workflow**: "List tickets and summarize them" 
- **Intelligent Sequencing**: Fetches data then applies AI analysis automatically

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Azure CLI (`az login` required)
- Access to Azure DevOps organization
- Azure OpenAI endpoint (for AI features)

### Installation

1. **Clone and Setup Environment**
```powershell
git clone https://github.com/rogerlai168/AdoAIassistant.git
cd AdoAIassistant\AdoCopy
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Configure Environment Variables**

Create a `.env` file in the project root with the following configuration:

```env
# Azure DevOps Configuration
AZDO_ORG=yourorganization
AZDO_PROJECT=yourproject
AZDO_API_VERSION=7.1
AZDO_RESOURCE_ID=499b84ac-1321-427f-aa17-267ca6975798

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-5-mini
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# AI Token Configuration (Optional - uses smart defaults)
AZURE_OPENAI_MAX_TOKENS_DEFAULT=8000
AZURE_OPENAI_MAX_RETRY_TOKENS=10000
AZURE_OPENAI_MIN_TOKENS_GPT5=1000
AZURE_OPENAI_RETRY_MULTIPLIER=1.5
AZURE_OPENAI_TEST_TOKENS=600
```

3. **Authenticate and Run**
```powershell
az login
streamlit run app_chat_smart.py
```

## 💡 Usage Examples

### 🔍 Data Queries
```
"List tickets with tag he_swe_wat for the last 14 days"
"Show me high priority bugs assigned to me"
"Find active tasks in the authentication component"
```

### 🧠 AI Analysis  
```
"Summarize cache data for WAT newsletter"
"Analyze those tickets for development trends"
"Create executive summary from the results"
"Generate newsletter with format: Executive Summary, What's New, What's Next"
```

### ⚡ Combined Workflows
```
"List my bugs from last week and create a status report"
"Show sprint tasks and analyze timeline patterns"
"Find priority issues and summarize for stakeholders"
```

## 🏗️ Architecture

### Core Components

- **[`app_chat_smart.py`](app_chat_smart.py)**: Modern Streamlit UI with AI-powered intent detection
- **[`ai_api.py`](ai_api.py)**: Azure OpenAI client with environment-based configuration
- **[`AzureAPI.py`](AzureAPI.py)**: Azure DevOps authentication and API utilities
- **[`mcp/ai_parser.py`](mcp/ai_parser.py)**: Intelligent natural language to WIQL conversion
- **[`mcp/intelligent_summarizer.py`](mcp/intelligent_summarizer.py)**: Advanced AI analysis with newsletter generation
- **[`mcp/tools.py`](mcp/tools.py)**: MCP tool integration layer
- **[`mcp/ado_client.py`](mcp/ado_client.py)**: Azure DevOps REST API client with parallel processing
- **[`mcp/wiql_builder.py`](mcp/wiql_builder.py)**: Microsoft-compliant WIQL query generation
- **[`mcp/config.py`](mcp/config.py)**: Centralized configuration with environment variable support
- **[`wiql_fields.py`](wiql_fields.py)**: Comprehensive Azure DevOps field mappings
- **[`mcp/normalize.py`](mcp/normalize.py)**: Work item data normalization and partner detection

### Configuration Management

All configuration is managed through environment variables in the `.env` file:

#### Azure DevOps Settings
- `AZDO_ORG`: Organization name (e.g., "Microsoft")
- `AZDO_PROJECT`: Project name (e.g., "OS")
- `AZDO_API_VERSION`: REST API version (default: "7.1")
- `AZDO_RESOURCE_ID`: Azure AD resource ID (Microsoft constant)

#### Azure OpenAI Settings
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_MODEL`: Model name (e.g., "gpt-5-mini")
- `AZURE_OPENAI_DEPLOYMENT`: Deployment name
- `AZURE_OPENAI_API_VERSION`: OpenAI API version

#### Token Configuration (Optional)
- `AZURE_OPENAI_MAX_TOKENS_DEFAULT`: Default max tokens (default: 2000)
- `AZURE_OPENAI_MAX_RETRY_TOKENS`: Max tokens for retries (default: 8000)
- `AZURE_OPENAI_MIN_TOKENS_GPT5`: Minimum tokens for GPT-5 (default: 500)
- `AZURE_OPENAI_RETRY_MULTIPLIER`: Token increase multiplier (default: 1.5)

### Cache Configuration

Control how long query results are cached for follow-up AI analysis:

```bash
# Unlimited cache (default) - cached until next query
CACHE_TTL_SECONDS=0

# 10 minutes cache
CACHE_TTL_SECONDS=600

# 30 minutes cache
CACHE_TTL_SECONDS=1800

# 1 hour cache
CACHE_TTL_SECONDS=3600
```

**Behavior:**
- `0` or negative value = **Unlimited cache** (cache persists until you run a new query)
- Positive value = Cache expires after specified seconds
- Invalid/missing value = Falls back to unlimited cache with warning

### AI Pipeline

1. **Intent Detection**: AI analyzes user request to determine action type
2. **Query Generation**: Natural language converted to optimized WIQL
3. **Data Retrieval**: Enterprise-scale Azure DevOps API integration  
4. **Smart Caching**: Intelligent data reuse with freshness tracking
5. **Analysis Generation**: Context-aware AI summaries and reports

### Enterprise Features

- **Microsoft Compliance**: Follows Azure DevOps documentation standards
- **Performance Optimized**: Parallel comment/update loading, query limiting
- **Security Ready**: Azure AD authentication with proper scoping
- **Environment-Based Configuration**: No hardcoded values, all settings in `.env`
- **Unicode Support**: International team and content compatibility

## 🎯 Advanced Features

### AI Intent Detection System
```python
# Automatically detects user intent
{
    "intent_type": "CACHED_ANALYSIS|NEW_QUERY|COMBINED",
    "confidence": 0.95,
    "analysis_request": {
        "analysis_type": "newsletter",
        "format_requirements": "Executive Summary, What's New, What's Next"
    }
}
```

### Intelligent Caching
- **10-minute cache TTL** with automatic freshness detection
- **Context-aware reuse** - AI knows when cached data is relevant
- **Transparent cache status** in UI sidebar

### Format-Aware Analysis
- **Newsletter Generation**: Professional team newsletter format
- **Executive Summaries**: High-level stakeholder reports  
- **Technical Deep-Dives**: Detailed analysis for development teams
- **Timeline Analysis**: Development velocity and pattern insights

## 🔧 Configuration

### Centralized Settings ([`mcp/config.py`](mcp/config.py))
```python
MAX_ITEMS_DEFAULT = 250        # Maximum items to retrieve
MAX_ITEMS_UI_DEFAULT = 150     # UI default for user queries
MAX_TOKENS_ANALYSIS = 10000    # AI analysis token limit (configurable via env)
MAX_TOKENS_WIQL = 2000         # WIQL parsing token limit (configurable via env)
WIQL_DEFAULT_TOP = 150         # WIQL query result limit
```

### Environment Variable Priority
1. **`.env` file values** (highest priority)
2. **System environment variables**
3. **Sensible defaults** (fallback)

### UI Optimization
- **Wide Layout**: Full-screen work item display
- **Smart Defaults**: Optimal settings without manual configuration  
- **Input Echo**: Clear conversation flow with user query confirmation
- **Collapsible Details**: Clean interface with expandable technical info

## 🧪 Testing & Validation

### Automated Testing Suite
- **WIQL Compliance**: Complete validation of Microsoft documentation compliance
- **Integration Tests**: End-to-end pipeline with live API calls
- **Performance Tests**: Large-scale dataset handling (58M+ items)
- **Unicode Tests**: International character support validation

### Real-World Validation  
- ✅ **Microsoft/OS Project**: Successfully queries enterprise-scale dataset
- ✅ **WIQL Compliance**: Follows Microsoft documentation standards
- ✅ **AI Accuracy**: High-confidence intent detection and analysis
- ✅ **Performance**: Sub-2-second query response times

## 📋 Work Item Support

### Supported Types
- **Tasks**: Standard development work items
- **Bugs**: Issue tracking and resolution
- **User Stories**: Feature requirements and specifications  
- **Deliverables**: Project milestones and deliverables
- **Scenarios**: Test cases and user scenarios
- **Epics/Features**: Portfolio-level work items

### Field Coverage
- **Core Fields**: ID, Title, State, Type, Assigned To, Priority
- **Dates**: Created, Changed, Closed, Resolved dates with smart filtering
- **Hierarchy**: Area Path, Iteration Path with tree operations
- **Scheduling**: Effort, Original Estimate, Remaining Work, Completed Work
- **Custom Fields**: Organization-specific field support
- **Comments**: Full discussion history with partner comment filtering
- **Updates**: Complete change history and state transitions

## 🎯 Benefits

### For Development Teams
- **Faster Insights**: AI-generated summaries replace manual analysis
- **Context Awareness**: System understands team workflow and data freshness
- **Natural Interface**: No need to learn WIQL syntax or query operators
- **Environment-Based Config**: Easy deployment across dev/test/prod

### For Project Managers  
- **Automated Reporting**: Newsletter and executive summary generation
- **Trend Analysis**: AI identifies patterns in work item data
- **Stakeholder Communication**: Professional formatted reports

### For Organizations
- **Enterprise Scale**: Handles millions of work items efficiently
- **Security Compliant**: Azure AD integration with proper access controls
- **Standards Based**: Microsoft documentation compliant implementation
- **Configuration Management**: Centralized `.env` based configuration

## 🛠️ Technical Implementation

### Configuration Best Practices
- **No Hardcoded Values**: All settings via environment variables
- **Validation on Startup**: Configuration validated when app initializes
- **Sensible Fallbacks**: Works with minimal configuration
- **Environment-Specific**: Easy to maintain dev/test/prod configs

### WIQL Compliance Engine
- **Field Reference Mapping**: Complete System.* and Microsoft.VSTS.* field support
- **Operator Validation**: Proper operators by field type (String, DateTime, TreePath, etc.)
- **Date Macros**: @Today, @StartOfWeek, @StartOfMonth, @StartOfYear support
- **Unicode Safety**: International character handling with SQL injection prevention

### MCP (Model Context Protocol) Server
- **Tool Integration**: Standardized tool calling interface
- **State Management**: Session context and caching
- **Error Handling**: Comprehensive error reporting and recovery

### Performance Optimizations
- **Parallel Processing**: Concurrent comment and update loading
- **Smart Caching**: Intelligent data reuse with TTL management
- **Query Optimization**: Result limiting and pagination
- **Conditional Loading**: Load comments only when likely to exist

## 🔮 Future Enhancements

### Planned Features
- **Real-time Updates**: WebSocket integration for live work item changes
- **Advanced Analytics**: Machine learning insights on development patterns  
- **Custom Dashboards**: Personalized work item visualization
- **Integration APIs**: REST API for external system integration

### Architecture Extensions
- **Multi-Project Support**: Cross-project analysis and reporting
- **Historical Analytics**: Trend analysis over time periods
- **Predictive Insights**: AI-powered project timeline predictions
- **Custom Field Framework**: Extensible organization-specific field support

## 📚 Documentation

- **[Azure DevOps Schema Reference](ADO_FULL_SCHEMA_REFERENCE.md)**: Complete field and API documentation
- **[WIQL Implementation Update](WIQL_UPDATE_SUMMARY.md)**: Microsoft compliance achievements
- **[Environment Configuration](.env.example)**: Setup and configuration guide

## 🔧 Dependencies

### Core Dependencies
- **Streamlit**: Modern web UI framework
- **Pandas**: Data processing and analysis
- **Requests**: HTTP client for Azure DevOps APIs
- **Azure-Identity**: Azure AD authentication
- **Azure-Core**: Azure SDK core functionality
- **OpenAI**: AI analysis and query generation
- **Python-dotenv**: Environment configuration management

All dependencies managed via `requirements.txt` - no manual package tracking needed!

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Update `.env` for your environment** (copy from `.env.example`)
4. **Run tests** (`python -m pytest`)
5. **Commit changes** (`git commit -m 'Add amazing feature'`)
6. **Push to branch** (`git push origin feature/amazing-feature`)
7. **Open Pull Request**

## 🔒 Security Best Practices

- **Never commit `.env` files** - they contain sensitive credentials
- **Use Azure AD authentication** - no API keys in code
- **Validate environment variables** on startup
- **Follow least-privilege principle** for Azure DevOps access

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Issues**: [GitHub Issues](https://github.com/rogerlai168/AdoAIassistant/issues)
- **Documentation**: [GitHub Wiki](https://github.com/rogerlai168/AdoAIassistant/wiki)
- **Community**: [GitHub Discussions](https://github.com/rogerlai168/AdoAIassistant/discussions)

---

**Built with ❤️ for Azure DevOps teams who want intelligent, AI-powered work item analysis with enterprise-grade configuration management.**
