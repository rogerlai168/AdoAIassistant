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
- Azure OpenAI endpoint (optional, for AI features)

### Installation

1. **Clone and Setup Environment**
```powershell
git clone <repository-url>
cd AdoAIassistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Configure Environment**
```powershell
# Copy example configuration
cp .env.example .env
```

3. **Edit `.env` Configuration**
```env
# Azure DevOps Configuration
AZDO_ORG=yourorganization
AZDO_PROJECT=yourproject

# Azure OpenAI Configuration (for AI features)
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_MODEL=gpt-5-mini
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# API Configuration
AZDO_API_VERSION=7.1
```

4. **Authenticate and Run**
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

- **`app_chat_smart.py`**: Modern Streamlit UI with AI-powered intent detection
- **`mcp/ai_parser.py`**: Intelligent natural language to WIQL conversion
- **`mcp/intelligent_summarizer.py`**: Advanced AI analysis with newsletter generation
- **`mcp/tools.py`**: MCP tool integration layer
- **`mcp/ado_client.py`**: Azure DevOps REST API client

### AI Pipeline

1. **Intent Detection**: AI analyzes user request to determine action type
2. **Query Generation**: Natural language converted to optimized WIQL
3. **Data Retrieval**: Enterprise-scale Azure DevOps API integration  
4. **Smart Caching**: Intelligent data reuse with freshness tracking
5. **Analysis Generation**: Context-aware AI summaries and reports

### Enterprise Features

- **Microsoft Compliance**: Follows Azure DevOps documentation standards
- **Performance Optimized**: Query limiting and smart pagination
- **Security Ready**: Azure AD authentication with proper scoping
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

### Centralized Settings (`mcp/config.py`)
```python
MAX_ITEMS_DEFAULT = 250        # Maximum items to retrieve
MAX_ITEMS_UI_DEFAULT = 150     # UI default for user queries
MAX_TOKENS_ANALYSIS = 10000    # AI analysis token limit
WIQL_DEFAULT_TOP = 150         # WIQL query result limit
```

### UI Optimization
- **Wide Layout**: Full-screen work item display
- **Smart Defaults**: Optimal settings without manual configuration  
- **Input Echo**: Clear conversation flow with user query confirmation
- **Collapsible Details**: Clean interface with expandable technical info

## 🧪 Testing & Validation

### Automated Testing Suite
- **Unit Tests**: Core WIQL generation and parsing validation
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

### Field Coverage
- **Core Fields**: ID, Title, State, Type, Assigned To, Priority
- **Dates**: Created, Changed, Closed, Resolved dates with smart filtering
- **Hierarchy**: Area Path, Iteration Path with tree operations
- **Custom Fields**: Organization-specific field support
- **Comments**: Full discussion history with partner comment filtering

## 🎯 Benefits

### For Development Teams
- **Faster Insights**: AI-generated summaries replace manual analysis
- **Context Awareness**: System understands team workflow and data freshness
- **Natural Interface**: No need to learn WIQL syntax or query operators

### For Project Managers  
- **Automated Reporting**: Newsletter and executive summary generation
- **Trend Analysis**: AI identifies patterns in work item data
- **Stakeholder Communication**: Professional formatted reports

### For Organizations
- **Enterprise Scale**: Handles millions of work items efficiently
- **Security Compliant**: Azure AD integration with proper access controls
- **Standards Based**: Microsoft documentation compliant implementation

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

- **[WIQL Compliance](WIQL_COMPLIANCE.md)**: Microsoft documentation alignment details
- **[Copilot Design](COPILOT_DESIGN.md)**: AI-powered granular analysis architecture
- **[Performance Guide](CONDITIONAL_AI_SUMMARY.md)**: Speed vs intelligence optimization
- **[Two-Step Workflow](TWO_STEP_WORKFLOW.md)**: Advanced workflow patterns

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Run tests** (`python -m pytest`)
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to branch** (`git push origin feature/amazing-feature`)
6. **Open Pull Request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Issues**: [GitHub Issues](https://github.com/yourorg/AdoAIassistant/issues)
- **Documentation**: [Wiki](https://github.com/yourorg/AdoAIassistant/wiki)
- **Community**: [Discussions](https://github.com/yourorg/AdoAIassistant/discussions)

---

**Built with ❤️ for Azure DevOps teams who want intelligent, AI-powered work item analysis.**