from fastapi import FastAPI, WebSocket
from github import Github
import os, json

GITHUB_TOKEN = "GIT TOKEN"
if not GITHUB_TOKEN:
    raise ValueError("Please set GITHUB_TOKEN environment variable.")

gh = Github(GITHUB_TOKEN)
app = FastAPI(title="GitHub MCP Server")

TOOLS = [
    {
        "name": "list_repos",
        "description": "List all repositories for the authenticated user",
        "inputSchema": {},
    },
    {
        "name": "list_issues",
        "description": "List issues for a repository",
        "inputSchema": {
            "repo": "string",
            "state": "string"
        },
    },
    {
        "name": "create_issue",
        "description": "Create an issue in a repository",
        "inputSchema": {
            "repo": "string",
            "title": "string",
            "body": "string"
        },
    },
    {
        "name": "close_issue",
        "description": "Close an existing issue",
        "inputSchema": {
            "repo": "string",
            "number": "integer"
        },
    },
    {
        "name": "create_repo",
        "description": "Create a new repository",
        "inputSchema": {
            "name": "string",
            "description": "string"
        },
    },
    {
        "name": "delete_repo",
        "description": "Delete a repository",
        "inputSchema": {
            "repo": "string"
        },
    },
]

def get_repo(name):
    return gh.get_repo(name)

@app.websocket("/mcp")
async def mcp(ws: WebSocket):
    await ws.accept()
    while True:
        raw = await ws.receive_text()
        req = json.loads(raw)

        if req.get("method") == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": req.get("id"),
                "result": {
                    "protocolVersion": "0.1",
                    "serverInfo": {
                        "name": "GitHub-MCP-Server",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {tool["name"]: tool for tool in TOOLS}
                    }
                }
            }
            await ws.send_text(json.dumps(resp))
            continue

        if req.get("method") == "callTool":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            result = None

            if name == "list_repos":
                result = [repo.full_name for repo in gh.get_user().get_repos()]
            elif name == "list_issues":
                repo = get_repo(args["repo"])
                result = [i.title for i in repo.get_issues(state=args.get("state", "open"))]
            elif name == "create_issue":
                repo = get_repo(args["repo"])
                issue = repo.create_issue(title=args["title"], body=args.get("body", ""))
                result = {"number": issue.number, "url": issue.html_url}
            elif name == "close_issue":
                repo = get_repo(args["repo"])
                issue = repo.get_issue(number=args["number"])
                issue.edit(state="closed")
                result = {"status": "closed"}
            elif name == "create_repo":
                repo = gh.get_user().create_repo(name=args["name"], description=args.get("description", ""))
                result = {"name": repo.full_name, "url": repo.html_url}
            elif name == "delete_repo":
                repo = get_repo(args["repo"])
                repo.delete()
                result = {"status": "deleted"}

            resp = {
                "jsonrpc": "2.0",
                "id": req.get("id"),
                "result": {"content": result}
            }
            await ws.send_text(json.dumps(resp))
