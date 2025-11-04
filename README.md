# Agent Integration with MCP Servers (Notion + GitHub)

## Project Objective

Design an intelligent agent that connects to two Model Context Protocol (MCP) servers — Notion and GitHub — using the provided OpenAI API key to retrieve, interpret, and correlate information from both sources to answer contextual queries.

## Project Goals

* Connect successfully to both MCP servers (Notion and GitHub)
* Access and interpret Notion data such as pages, databases, and documentation
* Access and interpret GitHub data such as files, commits, and repository structure
* Use OpenAI API reasoning to combine retrieved data into coherent, contextual responses
* Show attribution for all sourced content from Notion and GitHub

## Architecture

This project implements an MCP-integrated AI agent that:
- Connects to Notion and GitHub via custom MCP clients
- Ingests content from both sources into a vector store
- Performs semantic search and retrieval
- Uses OpenAI for reasoning and summarization
- Returns structured JSON responses with citations

## Project Structure

```
.
├── app.py                      # Main MCP stdio server entrypoint
├── smithery.yaml              # Smithery deployment configuration
├── requirements.txt           # Python dependencies
├── mcp_clients/               # MCP client implementations
│   ├── __init__.py
│   ├── notion_client.py      # Notion API integration
│   └── github_client.py      # GitHub API integration
└── utils/                     # Utility modules
    ├── __init__.py
    ├── config_loader.py      # Environment variable loading
    ├── rate_limiter.py        # Rate limiting and retry logic
    └── vector_store.py       # Vector embeddings and search
```

## Core Expectations

### Server Connectivity
- Authenticate with Notion and GitHub MCP servers using environment tokens
- Validate that both servers are reachable and data retrieval works securely

### Notion Integration
- List available databases, pages, and documents
- Retrieve structured data and text from Notion content
- Understand relationships between pages/databases (e.g., linked sections)
- Interpret metadata like titles, tags, and properties
- **Example actions:** Identify open tasks, fetch full content of a page, find pages about specific topics

### GitHub Integration
- Connect to GitHub repository via MCP interface
- Retrieve repository details — files, commits, folder structure
- Locate relevant files (e.g., containing 'payment' or 'auth')
- Interpret purpose of files and align them with Notion documentation
- **Example actions:** Find where a feature is implemented, match GitHub files to Notion docs

### Contextual Reasoning
- Analyze data from both servers to produce meaningful insights
- Summarize and correlate Notion documentation with GitHub implementations
- Use OpenAI API for reasoning and natural language understanding
- Ensure responses are clear, contextual, and confident (indicating strength of correlation)

## Query Scenarios

### Scenario A: Project Traceability
**Query Example:** "Show me all the active Notion tasks for 'API v2' and where their implementation exists in GitHub."

**Agent Actions:**
- Retrieve Notion tasks labeled 'API v2'
- Find related implementation files in GitHub
- Produce merged summary with task title, GitHub file/folder, and short description

### Scenario B: Documentation vs Implementation Check
**Query Example:** "According to the Notion page titled 'User Authentication Flow', does the GitHub repository show a matching implementation?"

**Agent Actions:**
- Retrieve the 'User Authentication Flow' page from Notion
- Search GitHub for related terms ('login', 'JWT', 'authentication controller')
- Compare and highlight alignment or discrepancies between docs and code

## Output Format Requirements

- Responses must cite all sources (Notion pages and GitHub files)
- Output should be concise, professional, and human-readable
- Results are returned as structured JSON: `{answer, sources, confidence_score}`

## Setup and Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Notion integration token
- GitHub personal access token

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/saksham-jain177/Agent-Integration-with-MCP-Servers.git
cd Agent-Integration-with-MCP-Servers
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
# On Linux/Mac:
export OPENAI_API_KEY=your_openai_api_key
export NOTION_TOKEN=your_notion_token
export GITHUB_TOKEN=your_github_token

# On Windows PowerShell:
$env:OPENAI_API_KEY="your_openai_api_key"
$env:NOTION_TOKEN="your_notion_token"
$env:GITHUB_TOKEN="your_github_token"
```

5. Test the server locally:
```bash
# Run the test script
python test_mcp_local.py

# Or run the server directly (for stdio JSON-RPC)
python app.py
```

### Local Testing & Demonstration

The MCP server is designed to work via stdio JSON-RPC. For assignment demonstration:

1. **Test locally** using `test_mcp_local.py`:
   ```bash
   python test_mcp_local.py
   ```

2. **Connect via MCP client** (Claude Desktop, Cursor, etc.):
   - Configure your MCP server path
   - Test all tools and functionality

3. **Demonstrate workflow**:
   - Show Notion data retrieval
   - Show GitHub data retrieval
   - Show RAG query with reasoning
   - Show source citations

See `DEPLOYMENT_ALTERNATIVES.md` for more details on local testing and alternative deployment options.

### Smithery Deployment

The project is configured for deployment on Smithery. Ensure:
- All files are committed to the repository
- `smithery.yaml` is in the root directory
- Environment variables are configured in Smithery UI
- GitHub repository is connected in Smithery deployment settings

## MCP Server Interface

The server implements a JSON-RPC 2.0 interface over stdio with the following methods:

### `list_tools`
Returns available tools:
- `notion.list_pages` - List Notion pages
- `notion.fetch_page` - Fetch a Notion page
- `notion.query_database` - Query a Notion database
- `github.list_repos` - List GitHub repositories
- `github.fetch_file_content` - Fetch file content from GitHub
- `github.search_code` - Search code on GitHub
- `agent.ingest` - Ingest content into vector index
- `agent.query` - Query RAG index and generate answer

### `call_tool`
Execute a tool with provided arguments.

## Security and Guardrails

- Rate limiting on all external API calls with exponential backoff
- Input validation and sanitization to prevent prompt injection
- PII redaction before sending data to OpenAI
- Environment variables only (no hard-coded secrets)
- Robust error handling and retries for network failures

## Deliverables

1. **Conceptual explanation**: Full workflow (query → retrieval → reasoning → response)
2. **Demonstration**: Agent connecting to both MCP servers and answering example scenarios
3. **Summary write-up**: 
   - How the OpenAI API key is used
   - How the agent correlates Notion and GitHub data
   - The biggest technical challenge and how it was solved

## Key Notes

- Only OpenAI API key, Notion token, and GitHub token are required
- Uses MCP-compatible environment via Smithery
- Focus is on conceptual correctness and reasoning
- Demonstrates multi-connector reasoning and contextual retrieval

## Current Development Status

✅ **Completed:**
- Project structure and scaffolding
- MCP stdio server implementation
- Notion and GitHub client integrations
- Vector store with OpenAI embeddings
- RAG pipeline with ingestion and query
- Rate limiting and security guardrails
- Smithery configuration file

⚠️ **In Progress:**
- Resolving Smithery deployment issues (`smitheryConfigError`)
- Verifying branch and file commit status
- Ensuring all configuration files are properly validated

## Troubleshooting

### Smithery Deployment Issues

If encountering `smitheryConfigError` or "Failed to fetch repo files":
1. Ensure all files are committed and pushed to the correct branch
2. Verify `smithery.yaml` is in the repository root
3. Check that the branch specified in Smithery matches your default branch
4. Confirm all environment variables are set in Smithery UI
5. Verify GitHub app permissions are correctly configured

## License

[Add your license here]

## Author

Saksham Jain

