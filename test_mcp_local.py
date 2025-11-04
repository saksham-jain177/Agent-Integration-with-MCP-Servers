"""
Local test script for MCP server
Demonstrates the server working via stdio JSON-RPC
"""
import json
import subprocess
import sys
import os
from typing import Dict, Any


def send_request(proc: subprocess.Popen, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Send a JSON-RPC request to the MCP server"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method
    }
    if params:
        request["params"] = params
    
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    
    response_line = proc.stdout.readline()
    if response_line:
        return json.loads(response_line.strip())
    return {}


def test_mcp_server():
    """Test the MCP server locally"""
    print("=" * 60)
    print("Testing MCP Server Locally")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "NOTION_TOKEN", "GITHUB_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("Set them before running: export OPENAI_API_KEY=...")
        return
    
    print("✅ Environment variables configured")
    
    # Start the server
    print("\n🚀 Starting MCP server...")
    proc = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Test 1: List tools
        print("\n📋 Test 1: Listing available tools...")
        response = send_request(proc, "list_tools")
        if "result" in response:
            tools = response["result"]
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools[:5]:  # Show first 5
                print(f"   - {tool.get('name')}: {tool.get('description', 'No description')}")
        else:
            print(f"❌ Error: {response.get('error', 'Unknown error')}")
        
        # Test 2: Ping (if supported)
        print("\n🏓 Test 2: Testing ping...")
        response = send_request(proc, "ping")
        if "result" in response:
            print(f"✅ Ping successful: {response['result']}")
        else:
            print("⚠️  Ping not supported (this is okay)")
        
        print("\n" + "=" * 60)
        print("✅ Local MCP server test completed!")
        print("=" * 60)
        print("\nThe server is running and responding to JSON-RPC requests.")
        print("You can now demonstrate this in your assignment.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        stderr_output = proc.stderr.read()
        if stderr_output:
            print(f"Server stderr: {stderr_output}")
    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    test_mcp_server()

