Now I have the full reference document. Let me synthesize a comprehensive, citation-backed analysis.

---

# Google A2A vs. Anthropic MCP: A Technical Comparative Analysis

---

## I. The Problem Both Protocols Address

Both protocols attack a specific version of the **M×N integration problem** — connecting M models/agents to N capabilities without writing M×N custom integrations — but at different layers of the agent stack.

- **MCP** (Anthropic, November 2024) reduces model-to-tool integration from M×N → M+N
- **A2A** (Google, announced April 9, 2025 at Cloud Next '25) reduces agent-to-agent integration from M×N → M+N

The layer distinction is the key architectural insight: MCP standardizes the *vertical* interface (agent ↔ resource), A2A standardizes the *horizontal* interface (agent ↔ agent). Everything else flows from this.

---

## II. MCP: Architecture & Design

### 2.1 Core Architecture

MCP uses a **three-component Host–Client–Server model** (Anthropic, 2024, *modelcontextprotocol.io/specification/2025-03-26*):

| Component | Role |
|-----------|------|
| **Host** | User-facing AI application (e.g., Claude Desktop, Claude Code, IDEs). Manages permissions, initiates connections, controls LLM access. |
| **Client** | Lives inside the Host. Maintains a **stateful, one-to-one** connection per Server. Handles protocol negotiation and session. |
| **Server** | External program (local or remote) exposing capabilities via MCP. Wraps APIs, filesystems, databases, SDKs. |

The orientation is clear: a single AI application seeking capabilities from multiple external servers. The Server is subordinate to the Host.

### 2.2 Three Primitives

MCP standardizes three capability types that Servers expose (Anthropic spec, 2025-03-26):

1. **Tools** — Executable functions (API calls, DB writes, script execution). Require JSON schema for parameters. Conceptually equivalent to LLM function calling.
2. **Resources** — Read-only data streams (files, logs, DB records, API responses). Accessed via URI. Analogous to HTTP GET — no significant side effects.
3. **Prompts** — Reusable instruction templates for common workflows. Typically user-selected before model invocation.

Plus one advanced feature: **Sampling** — the Server can request an LLM completion *from the Host*, reversing the normal flow. This is the most agent-like behavior in MCP, and creates a blurry edge with A2A.

### 2.3 Transport

| Scenario | Transport |
|----------|-----------|
| Local (same machine) | **stdio** (stdin/stdout) |
| Remote | **HTTP + Server-Sent Events (SSE)** |

Messages are formatted as **JSON-RPC 2.0**. Connections are stateful (persistent sessions).

### 2.4 Security Model

MCP's security model is **consent-based and local-first**:
- User must explicitly approve every tool execution and resource access
- Default posture: Servers run locally, minimizing data exposure
- Protocol specification does *not* enforce security at the protocol level — implementers are responsible (Anthropic spec, §Security Considerations)
- Remote security (OAuth 2.0) is an **evolving addition**, not part of the initial design (Cloudflare blog, 2025)
- MCP deliberately hides backend credentials from the LLM: the Server handles auth to downstream services

⚠️ **Inference**: The local-first, consent-first security design reflects MCP's origin context — connecting a desktop app to user-permissioned resources — rather than inherently untrusted network communications. This creates real friction for enterprise deployment at scale.

---

## III. A2A: Architecture & Design

### 3.1 Core Architecture

A2A uses a **client-server model where both sides are agents** (google/A2A GitHub repo):

| Component | Role |
|-----------|------|
| **Client Agent** | Agent (or app) initiating task delegation. Sends Tasks to remote agents. |
| **Server Agent** | Agent exposing HTTP endpoints implementing A2A methods. Accepts Tasks, manages execution, returns results. |

Crucially: **a single agent can be both Client and Server simultaneously**, enabling genuine peer-to-peer topologies. This is fundamentally different from MCP's asymmetric Host-controls-Server model.

### 3.2 Core Concepts

A2A introduces four primary abstractions (google/A2A GitHub, April 2025):

| Concept | Description |
|---------|-------------|
| **Agent Card** | JSON metadata served at `/.well-known/agent.json`. Contains: identity, endpoint URL, skills, auth requirements, supported modalities, protocol features. Acts as a "digital business card" for machine-readable discovery. |
| **Task** | Central unit of work. Has a unique ID and progresses through states: `submitted → working → input-required → completed / failed / canceled`. |
| **Message** | Single turn in dialogue within a Task. Roles: `user` (client) or `agent` (server). Contains one or more Parts. |
| **Part** | Atomic content unit. Types: `TextPart`, `FilePart` (inline base64 or URI), `DataPart` (structured JSON). The foundation of multimodal support. |
| **Artifact** | Tangible Task output (generated doc, structured result, image). Also composed of Parts. |

### 3.3 Communication Mechanisms

A2A offers **three asynchronous patterns** (google/A2A spec):

| Pattern | Method | Use Case |
|---------|--------|----------|
| Synchronous | `tasks/send` | Quick, short-lived tasks |
| Streaming | `tasks/sendSubscribe` + SSE | Real-time feedback, incremental results |
| Push/Webhook | `tasks/pushNotification/set` + HTTP POST | Long-running tasks (hours/days), disconnected clients |

Transport: HTTP/HTTPS with modern TLS. Message format: JSON-RPC style. The dual SSE + webhook support is architecturally significant — it directly acknowledges that multi-agent workflows often run over timescales where persistent connections are impractical.

### 3.4 Security Model

A2A takes an **enterprise-grade, authentication-first** approach:
- "Secure by default" is a stated design principle (Google Developers Blog, April 2025)
- Agent Card specifies required authentication methods, aligned with **OpenAPI auth schemes** (OAuth 2.0, API Keys, etc.)
- Focus: securing interactions between potentially untrusted, independent agents
- This reflects an enterprise-deployment-first design, contrasting with MCP's user-consent-first posture

---

## IV. Feature Comparison Matrix

| Feature | MCP (Anthropic, Nov 2024) | A2A (Google, Apr 2025) |
|---------|--------------------------|------------------------|
| **Primary abstraction** | Agent ↔ Resource (tool/data) | Agent ↔ Agent |
| **Architecture** | Host–Client–Server (asymmetric) | Client-Server where both sides are agents (symmetric) |
| **Discovery** | Host-initiated, after connection is established | Decentralized via `/.well-known/agent.json` (pre-connection) |
| **Core units** | Tools, Resources, Prompts | Tasks, Messages, Parts, Artifacts |
| **Async support** | SSE via stateful connections | Explicit: request/response + SSE streaming + webhook push |
| **Long-running tasks** | Not explicitly addressed | First-class: webhook push notifications for hours/days-long tasks |
| **Multimodality** | Data exchange via Resources/Tool params; no explicit media primitives | Native: TextPart, FilePart, DataPart; audio/video in roadmap |
| **UX negotiation** | Not present | Agent-to-agent negotiation of UI requirements (forms, video, etc.) |
| **Opaque agent support** | N/A (Server internals irrelevant to protocol) | Explicit design goal: agents need not share internal state/memory |
| **Security model** | User consent + local-first; remote OAuth evolving | Enterprise auth from day one; OpenAPI-aligned; Agent Card declares requirements |
| **State management** | Client-side; session per connection | Server-side Task lifecycle with explicit state machine |
| **Peer-to-peer** | No (Host is always orchestrator) | Yes (same agent can be Client and Server) |
| **Message format** | JSON-RPC 2.0 | JSON-RPC style |
| **Transport** | stdio (local), HTTP+SSE (remote) | HTTP/HTTPS, SSE, webhooks |

---

## V. What Each Protocol Solves That the Other Doesn't

### 5.1 Problems MCP Solves That A2A Does Not

**1. Standardized tool/resource access for individual agents**
MCP's three primitives (Tools, Resources, Prompts) provide a clean, language-agnostic contract for connecting one agent to many external services. A2A has no equivalent mechanism for a single agent accessing non-agent external systems.

**2. The M+N tool integration problem at the model layer**
MCP's value proposition is explicit: N tool builders write MCP Servers once, M agent builders write MCP Clients once. Before MCP, each (model, tool) pair needed a custom integration. There is no A2A equivalent for this.

**3. Credential isolation from the LLM**
MCP's design explicitly prevents LLM access to backend API keys — the Server handles auth to downstream services. A2A doesn't address this (it operates at the agent-agent boundary, not agent-backend boundary).

**4. Local execution with minimal surface area**
MCP's stdio transport and local-first model allows tools to run with no network exposure. A2A is inherently network-based.

**5. Prompt templating and workflow scaffolding**
MCP's Prompts primitive provides reusable instruction templates that the Host surfaces to users. A2A has no equivalent.

### 5.2 Problems A2A Solves That MCP Does Not

**1. Agent discovery at runtime**
The Agent Card (`/.well-known/agent.json`) enables an agent to find collaborators it has never been configured to know about. MCP has no discovery mechanism — the Host must know about Servers in advance.

**2. Peer-to-peer agent collaboration across vendors/frameworks**
A2A's core purpose: a LangChain agent, a Google ADK agent, and a CrewAI agent can interoperate without any shared infrastructure. MCP has no mechanism for agent-to-agent communication — it only connects agents to tools.

**3. Long-running task state management**
The A2A Task state machine (`submitted → working → input-required → completed/failed/canceled`) provides a standardized lifecycle contract. MCP has no equivalent; tool calls are stateless from the protocol's perspective.

**4. Human-in-the-loop coordination**
The `input-required` Task state explicitly signals that a human decision is needed mid-workflow, with the connection persisted or resumable. MCP has no such mechanism.

**5. Asynchronous task completion over hours/days**
A2A's webhook push notifications allow a Client to register a callback URL and disconnect — the Server POSTs results when done. MCP's SSE-based connections are persistent and would break for multi-hour tasks.

**6. Multimodal agent communication**
FilePart and DataPart primitives enable structured file exchange, form submission, and structured data between agents. MCP can transfer data but has no standardized multimodal dialogue protocol between agents.

**7. "Opaque" interoperability**
A2A is designed for agents that are black boxes to each other — no shared memory, no shared tool access. This is the enterprise reality: you integrate with a vendor's agent, not its internals. MCP's design assumes the Host has configuration-level access to all Servers.

---

## VI. Are They Complementary or Competing?

**Google's official position**: Complementary. Google published documentation explicitly titled "A2A ❤️ MCP" illustrating hybrid architectures where both protocols coexist. The stated analogy: MCP provides the tools each mechanic (agent) uses; A2A provides the language for mechanics to coordinate.

**The layered hybrid architecture** (this is the technically correct reading):

```
[User]
  ↓
[Orchestrator Agent]
  ↓ A2A (task delegation, discovery, coordination)
[Specialized Agent A]        [Specialized Agent B]
  ↓ MCP (tool access)          ↓ MCP (tool access)
[DB Server] [API Server]    [Search] [Calendar API]
```

In the HR recruiting example (google/A2A docs): the primary HR agent uses A2A to discover and task a sourcing agent; the sourcing agent uses MCP internally to connect to LinkedIn's API and the ATS database; the sourcing agent returns candidate profiles as an A2A Artifact; a scheduling agent is tasked via A2A and uses MCP to access calendar APIs. Both protocols are active simultaneously at different layers.

**Where competition exists** (inference, not consensus):

The protocols have functional overlap at their edges:
- An A2A Server can act as a thin wrapper around a tool, making it functionally equivalent to an MCP Tool. If a developer needs to call a Python function remotely, they could implement it as either.
- MCP's Sampling feature (Server requests LLM completion from Host) creates dialogue-like patterns that approach A2A's conversational model.
- Developer choice of framing — "is this capability an *agent* or a *tool*?" — determines which protocol applies. That framing is often subjective.

The absence of Anthropic and OpenAI from A2A's April 2025 launch partner list (despite 50+ other companies signing on) is a concrete signal of tension, not just complementarity (Koyeb blog, "A2A and MCP: Start of the AI Agent Protocol Wars?"). Whether this reflects genuine architectural disagreement or competitive positioning is unclear.

**Verdict**: They are **architecturally complementary** (different layers) but **competitively positioned** (overlapping at the margins, with different vendor backing). The market outcome will likely be determined by developer adoption velocity — MCP has an ~5-month head start and broad community traction; A2A has stronger enterprise backing and more explicit async/multimodal features.

---

## VII. Adoption Status (as of April 2026)

### MCP
- Launched: November 2024 (Anthropic, *anthropic.com/news/model-context-protocol*)
- Official spec: `modelcontextprotocol.io/specification/2025-03-26`
- Adopters: Claude Desktop, Claude Code, Zed, Replit, Codeium, and a large community MCP server ecosystem
- SDKs: Python, TypeScript (official); community SDKs for Go, Rust, Java, C#
- Notable: Hundreds of MCP Servers published for GitHub, PostgreSQL, Slack, Google Drive, Blender, etc.
- ⚠️ **[Potentially outdated — 5+ months of evolution not captured here]**

### A2A
- Launched: April 9, 2025 (Google Cloud Next '25)
- Spec repo: `github.com/google/A2A`
- Launch partners: 50+ companies including Salesforce, SAP, ServiceNow, Workday, Deloitte, Accenture (Google Developers Blog, 2025)
- Framework integrations: Google ADK, LangGraph, CrewAI, Semantic Kernel, LlamaIndex announced at launch
- Notable absent: Anthropic, OpenAI
- arXiv preprint on secure A2A implementation: arxiv.org/html/2504.16902 (April 2025)
- ⚠️ **[Newer protocol — adoption trajectory requires more recent data]**

---

## VIII. Specific Implementation Details Worth Tracking

**MCP Server skeleton** (FastMCP pattern, as used in this workshop's `step-3-tool/mcp-servers/arxiv_server.py`):
```python
from fastmcp import FastMCP
mcp = FastMCP("arxiv")

@mcp.tool()
def search_arxiv(query: str, max_results: int = 10) -> list[dict]:
    # returns structured paper metadata
```

**A2A Agent Card** (served at `/.well-known/agent.json`):
```json
{
  "name": "Candidate Sourcing Agent",
  "description": "Searches and ranks job candidates",
  "url": "https://agent.example.com/",
  "skills": [{"id": "source-candidates", "name": "Source Candidates"}],
  "authentication": {"schemes": ["Bearer"]},
  "capabilities": {"streaming": true, "pushNotifications": true}
}
```

**A2A Task initiation** (`tasks/send` method):
```json
{
  "jsonrpc": "2.0", "method": "tasks/send",
  "params": {
    "id": "task-123",
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "Find 10 senior ML engineers in NYC"}]
    }
  }
}
```

---

## IX. Summary

| Dimension | MCP | A2A |
|-----------|-----|-----|
| **Layer** | Agent → Tool/Resource | Agent → Agent |
| **Key innovation** | M+N integration for tools | Dynamic discovery + Task lifecycle |
| **Killer feature** | Simplicity — 3 primitives, works locally | Async (webhooks) + opaque agent interop |
| **Security design** | Consent-first, local-first | Auth-first, enterprise-first |
| **Head start** | ~5 months; broad community traction | Strong enterprise partner list |
| **Relationship** | Vertical (tool layer) | Horizontal (coordination layer) |
| **Verdict** | Best for: single agent + tool access | Best for: multi-agent orchestration |

MCP solves "how does my agent use tools." A2A solves "how do my agents use each other." A production multi-agent system needs both.

---

## References

1. Anthropic (2024). *Introducing the Model Context Protocol*. anthropic.com/news/model-context-protocol
2. Anthropic (2025). *MCP Specification 2025-03-26*. modelcontextprotocol.io/specification/2025-03-26
3. Google (2025). *Announcing the Agent2Agent Protocol (A2A)*. developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
4. google/A2A GitHub repository. github.com/google/A2A
5. Blott Studio (2025). *How the Agent2Agent Protocol (A2A) Actually Works*. blott.studio/blog/post/how-the-agent2agent-protocol-a2a-actually-works-a-technical-breakdown
6. Koyeb (2025). *A2A and MCP: Start of the AI Agent Protocol Wars?* koyeb.com/blog/a2a-and-mcp-start-of-the-ai-agent-protocol-wars
7. Cloudflare (2025). *Build and deploy Remote MCP servers*. blog.cloudflare.com/remote-model-context-protocol-servers-mcp/
8. Humanloop (2025). *Model Context Protocol (MCP) Explained*. humanloop.com/blog/mcp
9. ResearchGate (2025). *Comprehensive Analysis of Google's Agent2Agent (A2A) Protocol*. DOI via researchgate.net/publication/390694531
10. arXiv (2025). *Building A Secure Agentic AI Application Leveraging Google's A2A Protocol*. arxiv.org/html/2504.16902
11. W&B (2025). *Google's Agent2Agent (A2A) protocol: A new standard for AI agent collaboration*. wandb.ai/onlineinference/mcp/reports/...
