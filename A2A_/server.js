import { createInterface } from 'readline';
import fetch from 'node-fetch';

const GITHUB_TOKEN = "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";
if (!GITHUB_TOKEN) {
  console.error("Error: GITHUB_TOKEN environment variable not set.");
  process.exit(1);
}

function handleMessage(msg) {
  const message = JSON.parse(msg);

  if (message.method === "initialize") {
    sendMessage({
      jsonrpc: "2.0",
      id: message.id,
      result: {
        protocolVersion: "2024-02-01", 
        serverInfo: {
          name: "github-mcp-server",
          version: "0.1.0"
        },
        capabilities: {
          tools: {
            "github.search": {
              description: "Search GitHub repositories by keyword",
              parameters: {
                type: "object",
                properties: { query: { type: "string" } },
                required: ["query"]
              }
            },
            "github.listRepos": {
              description: "List repositories for the authenticated user",
              parameters: { type: "object", properties: {} }
            },
            "github.createRepo": {
              description: "Create a new repository",
              parameters: {
                type: "object",
                properties: {
                  name: { type: "string" },
                  private: { type: "boolean" }
                },
                required: ["name"]
              }
            },
            "github.deleteRepo": {
              description: "Delete a repository",
              parameters: {
                type: "object",
                properties: {
                  owner: { type: "string" },
                  repo: { type: "string" }
                },
                required: ["owner", "repo"]
              }
            },
            "github.createIssue": {
              description: "Create an issue in a repository",
              parameters: {
                type: "object",
                properties: {
                  owner: { type: "string" },
                  repo: { type: "string" },
                  title: { type: "string" },
                  body: { type: "string" }
                },
                required: ["owner", "repo", "title"]
              }
            }
          }
        }
      }
    });
  }

  else if (message.method === "github.search") {
    searchGitHub(message.params.query).then(res => sendResult(message.id, res)).catch(err => sendError(message.id, err));
  }
  else if (message.method === "github.listRepos") {
    callGitHub("/user/repos").then(res => sendResult(message.id, res)).catch(err => sendError(message.id, err));
  }
  else if (message.method === "github.createRepo") {
    callGitHub("/user/repos", "POST", { name: message.params.name, private: message.params.private || false })
      .then(res => sendResult(message.id, res))
      .catch(err => sendError(message.id, err));
  }
  else if (message.method === "github.deleteRepo") {
    callGitHub(`/repos/${message.params.owner}/${message.params.repo}`, "DELETE")
      .then(res => sendResult(message.id, res))
      .catch(err => sendError(message.id, err));
  }
  else if (message.method === "github.createIssue") {
    callGitHub(`/repos/${message.params.owner}/${message.params.repo}/issues`, "POST", {
      title: message.params.title,
      body: message.params.body || ""
    }).then(res => sendResult(message.id, res)).catch(err => sendError(message.id, err));
  }

  else {
    sendError(message.id, { message: "Method not found" });
  }
}

async function searchGitHub(query) {
  return callGitHub(`/search/repositories?q=${encodeURIComponent(query)}`);
}

async function callGitHub(path, method = "GET", body = null) {
  const res = await fetch(`https://api.github.com${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${GITHUB_TOKEN}`,
      'Accept': 'application/vnd.github+json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) throw new Error(`GitHub API error: ${res.status} ${res.statusText}`);
  return res.status === 204 ? {} : await res.json();
}

function sendMessage(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}
function sendResult(id, result) {
  sendMessage({ jsonrpc: "2.0", id, result });
}
function sendError(id, error) {
  sendMessage({ jsonrpc: "2.0", id, error: { code: -32000, message: error.message || error } });
}

const rl = createInterface({ input: process.stdin, output: process.stdout, terminal: false });
rl.on('line', (line) => {
  try { handleMessage(line); }
  catch (e) { console.error("Failed to handle message:", e); }
});

console.error("GitHub MCP server started. Waiting for MCP requests...");
