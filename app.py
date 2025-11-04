import sys
import json
import threading
import logging
from typing import Any, Dict, List, Optional, Iterable

from utils.config_loader import load_config
from utils.rate_limiter import rate_limited_session
from utils.vector_store import VectorStore
from mcp_clients.notion_client import NotionMCPClient
from mcp_clients.github_client import GitHubMCPClient


def setup_logging() -> None:
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
		handlers=[logging.StreamHandler(sys.stderr)],
	)


class JsonRpcIO:
	def __init__(self) -> None:
		self._write_lock = threading.Lock()

	def read(self) -> Optional[Dict[str, Any]]:
		line = sys.stdin.readline()
		if not line:
			return None
		try:
			return json.loads(line)
		except Exception:
			logging.exception("Failed to parse incoming JSON")
			return None

	def write(self, obj: Dict[str, Any]) -> None:
		with self._write_lock:
			sys.stdout.write(json.dumps(obj) + "\n")
			sys.stdout.flush()


def _chunk_text(text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
	if not text:
		return []
	chunks: List[str] = []
	start = 0
	while start < len(text):
		end = min(len(text), start + max_chars)
		segment = text[start:end]
		chunks.append(segment)
		start = end - overlap
		if start < 0:
			start = 0
		if end == len(text):
			break
	return chunks


class MCPServer:
	def __init__(self, config: Dict[str, str]) -> None:
		self.io = JsonRpcIO()
		self.logger = logging.getLogger("MCPServer")
		self.session = rate_limited_session()
		self.vector_store = VectorStore()
		self.notion = NotionMCPClient(config["NOTION_TOKEN"], self.session)
		self.github = GitHubMCPClient(config["GITHUB_TOKEN"], self.session)
		self.openai_api_key = config["OPENAI_API_KEY"]

	def list_tools(self) -> List[Dict[str, Any]]:
		return [
			{"name": "notion.list_pages", "description": "List Notion pages"},
			{"name": "notion.fetch_page", "description": "Fetch a Notion page"},
			{"name": "notion.query_database", "description": "Query a Notion database"},
			{"name": "github.list_repos", "description": "List GitHub repositories"},
			{"name": "github.fetch_file_content", "description": "Fetch file content from GitHub"},
			{"name": "github.search_code", "description": "Search code on GitHub"},
			{"name": "agent.ingest", "description": "Ingest Notion and GitHub content into vector index"},
			{"name": "agent.query", "description": "Query RAG index and generate answer"},
		]

	def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
		if name.startswith("notion."):
			return self._call_notion(name, arguments)
		if name.startswith("github."):
			return self._call_github(name, arguments)
		if name == "agent.ingest":
			return self._call_agent_ingest(arguments)
		if name == "agent.query":
			return self._call_agent_query(arguments)
		raise ValueError(f"Unknown tool: {name}")

	def _call_notion(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
		if name == "notion.list_pages":
			return {"items": self.notion.list_pages(args.get("page_size", 10))}
		if name == "notion.fetch_page":
			return self.notion.fetch_page(args["page_id"])
		if name == "notion.query_database":
			return {"items": self.notion.query_database(args["database_id"], args.get("filter"))}
		raise ValueError(f"Unknown Notion tool: {name}")

	def _call_github(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
		if name == "github.list_repos":
			return {"items": self.github.list_repos(args.get("visibility", "all"))}
		if name == "github.fetch_file_content":
			return {"content": self.github.fetch_file_content(args["owner"], args["repo"], args["path"], args.get("ref"))}
		if name == "github.search_code":
			return {"items": self.github.search_code(args["query"], args.get("per_page", 10))}
		raise ValueError(f"Unknown GitHub tool: {name}")

	def _call_agent_ingest(self, args: Dict[str, Any]) -> Dict[str, Any]:
		notion_limit = int(args.get("notion_limit", 5))
		github_owner = args.get("github_owner")
		github_repo = args.get("github_repo")
		github_paths: List[str] = args.get("github_paths", ["README.md"]) if isinstance(args.get("github_paths"), list) else ["README.md"]

		added = 0
		# Ingest Notion pages
		npages = self.notion.list_pages(notion_limit)
		for p in npages:
			pid = p.get("id")
			if not pid:
				continue
			page = self.notion.fetch_page(pid)
			blocks = page.get("blocks", [])
			full_text = "\n".join(_extract_notion_block_text(b) for b in blocks)
			for chunk in _chunk_text(full_text):
				self.vector_store.add([(chunk, {"source": "notion", "page_id": pid})], api_key=self.openai_api_key)
				added += 1

		# Ingest GitHub files if provided
		if github_owner and github_repo:
			for path in github_paths:
				try:
					content = self.github.fetch_file_content(github_owner, github_repo, path)
					for chunk in _chunk_text(content):
						self.vector_store.add([(chunk, {"source": "github", "owner": github_owner, "repo": github_repo, "path": path})], api_key=self.openai_api_key)
						added += 1
				except Exception:
					self.logger.warning("Failed to ingest GitHub path: %s", path, exc_info=True)

		return {"status": "ok", "chunks_indexed": added}

	def _call_agent_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
		from utils.vector_store import redact_pii, summarize_with_openai

		query = str(args.get("query", "")).strip()
		if not query:
			return {"error": "query is required"}

		results = self.vector_store.search(query_text=query, top_k=8)
		sources = [{"source": r.metadata, "score": float(r.score)} for r in results]

		redacted_context = redact_pii("\n\n".join(r.text for r in results))
		answer, confidence = summarize_with_openai(
			api_key=self.openai_api_key,
			query=query,
			context=redacted_context,
		)
		return {"answer": answer, "sources": sources, "confidence_score": confidence}

	def _handle_message(self, msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
		method = msg.get("method")
		msg_id = msg.get("id")
		try:
			if method == "list_tools":
				result = self.list_tools()
				return {"jsonrpc": "2.0", "id": msg_id, "result": result}
			if method == "call_tool":
				params = msg.get("params", {})
				name = params.get("name")
				arguments = params.get("arguments", {})
				result = self.call_tool(name, arguments)
				return {"jsonrpc": "2.0", "id": msg_id, "result": result}
			if method == "ping":
				return {"jsonrpc": "2.0", "id": msg_id, "result": "pong"}
		except Exception as e:
			self.logger.exception("Error handling message")
			return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": str(e)}}
		return None

	def serve(self) -> None:
		self.logger.info("MCP stdio server started")
		while True:
			msg = self.io.read()
			if msg is None:
				break
			resp = self._handle_message(msg)
			if resp is not None:
				self.io.write(resp)


def _extract_notion_block_text(block: Dict[str, Any]) -> str:
	try:
		bt = block.get("type")
		if not bt:
			return ""
		inner = block.get(bt, {})
		rich = inner.get("rich_text", [])
		return "".join(seg.get("plain_text", "") for seg in rich)
	except Exception:
		return ""


def main() -> None:
	setup_logging()
	config = load_config()
	server = MCPServer(config)
	server.serve()


if __name__ == "__main__":
	main()
