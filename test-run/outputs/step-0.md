I have comprehensive primary source data. Let me now synthesize this into the full analysis.

---

# A2A vs MCP: A Technical Deep-Dive

## TL;DR

> **MCP gives agents hands. A2A gives agents colleagues.**
> — *AgentRank, March 2026*

These two protocols operate at different layers of the agent stack and were designed to solve orthogonal problems. They are **complementary by design** — Google said so explicitly on launch day — though they share enough surface-level similarities (both use JSON-RPC 2.0, HTTP, SSE) to cause confusion. The clearest mental model: **MCP is vertical** (agent → tool/data), **A2A is horizontal** (agent → agent).

---

## 1. MCP — Model Context Protocol

### Origin & Positioning

Launched by **Anthropic in November 2024** as an open standard. The core insight: LLMs are powerful reasoning engines starved of context and external capability. Before MCP, every AI integration required bespoke function-calling wrappers per client — Claude needed different glue code than GPT-4, Cursor needed different glue code than Claude Desktop. MCP eliminated that M×N integration matrix.

### Architecture

MCP uses a strict **three-tier client-server architecture**:

| Tier | Role | Example |
|------|------|---------|
| **MCP Host** | The AI application that manages all client connections | Claude Desktop, VS Code, Cursor, Claude Code |
| **MCP Client** | Per-connection object instantiated by the host | One client per server, managed by the host |
| **MCP Server** | Process exposing capabilities (tools, resources, prompts) | Filesystem server, Postgres server, Sentry server |

The **data layer** is JSON-RPC 2.0 — strictly typed requests and responses with `method`, `params`, `id`, and `result`/`error`. The **transport layer** supports two mechanisms:

- **stdio**: Standard input/output streams for local process communication. Zero network overhead. Used when Claude Desktop spawns a local server.
- **Streamable HTTP**: POST for client→server messages with optional Server-Sent Events (SSE) for streaming. Used for remote servers like the official Sentry MCP server.

### Core Primitives (what makes MCP useful)

MCP servers expose three primitive types:

**Tools** — executable functions the LLM can invoke:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
// Response includes name, description, inputSchema (JSON Schema)
```

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "weather_current",
    "arguments": { "location": "San Francisco", "units": "imperial" }
  }
}
```

**Resources** — data sources for contextual information (file contents, database records, API responses)

**Prompts** — reusable interaction templates (system prompts, few-shot examples)

MCP clients also expose primitives back to servers:
- **Sampling**: Servers can request LLM completions from the client, staying model-agnostic
- **Elicitation**: Servers can request user input or confirmation
- **Tasks** (Experimental): Durable execution wrappers for long-running operations with deferred result retrieval

### Lifecycle Management

MCP is a **stateful protocol** — every connection begins with a capability negotiation handshake:
```json
// Client → Server
{
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-25",
    "capabilities": { "elicitation": {} },
    "clientInfo": { "name": "claude-code", "version": "1.0" }
  }
}

// Server → Client
{
  "result": {
    "capabilities": {
      "tools": { "listChanged": true },
      "resources": {}
    }
  }
}
```

This negotiation determines which primitives are active and whether the server can push `notifications/tools/list_changed` events when its capabilities change dynamically.

### Adoption (as of early 2026)

- **25,632 repositories** indexed in AgentRank (March 2026), growing 2x Q3→Q4 2025, 2x again Q1 2026
- **97M+ npm downloads** of the MCP SDK
- **Every major AI coding client**: Claude Code, Cursor, GitHub Copilot, Cline, Windsurf, Zed, VS Code
- **Official servers from**: Redis, MongoDB, AWS, Azure, GCP, HashiCorp, Snyk, Sentry, Neon, and dozens of others
- Current spec version: **2025-11-25** (modelcontextprotocol.io)

---

## 2. A2A — Agent2Agent Protocol

### Origin & Positioning

Launched by **Google DeepMind on April 9, 2025**, with contributions from **50+ technology partners** at announcement — including Salesforce, SAP, Atlassian, ServiceNow, LangChain, PayPal, Box, Cohere, and major SIs (Accenture, Deloitte, McKinsey, PwC, TCS, Wipro). The core insight: as agent systems grow more capable, you want *specialization*. Monolithic agents that attempt everything don't scale. You need a standard for agents to *hire* other agents.

Google's blog explicitly positioned it as complementary: *"A2A is an open protocol that complements Anthropic's Model Context Protocol (MCP), which provides helpful tools and context to agents."*

### Architecture

A2A is also built on **JSON-RPC 2.0 over HTTP(S)**, but the abstraction model is fundamentally different. It introduces four new concepts with no MCP equivalent:

#### Agent Card
A JSON manifest served at `/.well-known/agent.json` — analogous to a service's OpenAPI spec, but for an autonomous agent:
```json
{
  "name": "Currency Converter Agent",
  "description": "Converts between currencies using real-time exchange rates",
  "version": "1.0.0",
  "endpoints": {
    "tasks": "https://api.example.com/a2a/tasks",
    "stream": "https://api.example.com/a2a/stream"
  },
  "auth": { "type": "api_key", "in": "header", "name": "X-API-Key" },
  "capabilities": [
    {
      "id": "convert_currency",
      "parameters": { /* JSON Schema */ },
      "returns": { /* JSON Schema */ }
    }
  ]
}
```

#### Task Lifecycle
A2A organizes all inter-agent communication around **Tasks** — first-class objects with persistent state:

```
submitted → working → [needsInput] → completed
                    ↘ failed
                    ↘ canceled
```

Tasks have unique IDs, enabling long-running operations (minutes to hours/days) with mid-flight status polling and SSE streaming of intermediate updates. **Artifacts** are the outputs a task produces — text, files, structured data — streamed back via SSE.

#### Three Communication Patterns
| Method | Pattern | Use Case |
|--------|---------|----------|
| `tasks/send` | Synchronous HTTP request-response | Quick operations |
| `tasks/sendAsync` | Async with task ID + optional webhook callback | Long-running, fire-and-forget |
| `tasks/sendSubscribe` | SSE stream of live updates | Deep research, progressive results |

#### User Experience Negotiation
A2A messages include **"parts"** — typed content blocks that allow client and remote agents to negotiate format (iframes, video, web forms, images, audio). This has no MCP equivalent.

### Authentication
A2A adopts OpenAPI's authentication schemes: OAuth 2.0, API keys, JWT, and client certificates. The spec *recommends* against plaintext secrets in Agent Cards and suggests mTLS or network restrictions for sensitive cards. Authentication mechanisms are declared in the Agent Card but not enforced by the protocol itself — agents choose their schemes.

### Framework Integration (as of 2026)

| Framework | Integration |
|-----------|------------|
| **Google ADK** | Built-in. `to_a2a(agent, port=10000)` wraps any ADK agent as a FastAPI A2A service in one line. `McpToolset` for MCP tool consumption. |
| **LangGraph** | Native via `langgraph.a2a` module — graph-based workflows with A2A coordination |
| **CrewAI** | `crewai-a2a` adapter — multi-agent crews with A2A communication |
| **Semantic Kernel** | `Microsoft.SemanticKernel.A2A` plugin |

### Adoption (as of early 2026)

- **~2,400 repositories** in AgentRank (March 2026), launched April 2025 — doubling each quarter
- Concentrated in: orchestration frameworks, agent development kits, enterprise integration adapters
- Enterprise partners: Salesforce (Agentforce), SAP (Joule), Atlassian (Rovo), ServiceNow, Google Agentspace
- Production-ready release: Q3 2025 per roadmap; Q4 2025 added formalized authorization schemes
- GitHub: `github.com/a2aproject/A2A` — Apache 2.0 license

---

## 3. Head-to-Head Comparison

| Dimension | **MCP** | **A2A** |
|-----------|---------|---------|
| **Primary purpose** | Agent ↔ tools/data | Agent ↔ agent |
| **Core metaphor** | Agent using a tool | Agent hiring a contractor |
| **Core abstraction** | Tools, Resources, Prompts | Tasks, Artifacts, Agent Cards |
| **Capability model** | Deterministic functions with JSON Schema inputs | Autonomous services with declared skills |
| **Discovery** | `tools/list` at runtime over the connection | `GET /.well-known/agent.json` over HTTP (out-of-band) |
| **State model** | Stateful connections with capability negotiation | Stateless HTTP with stateful Task objects |
| **Long-running ops** | Tasks primitive (experimental); mostly synchronous | Native: `submitted→working→completed` lifecycle |
| **Streaming** | SSE (Streamable HTTP transport) | SSE (`tasks/sendSubscribe`) |
| **Transport** | stdio (local) or Streamable HTTP (remote) | HTTP only |
| **Multimodality** | Text, images in tool results | Text, images, audio, video, UX negotiation |
| **Auth** | Transport-level (env vars, headers) | Protocol-level declaration (OAuth, JWT, API key, mTLS) |
| **Originator** | Anthropic | Google DeepMind |
| **Launch** | November 2024 | April 2025 |
| **GitHub repos (March 2026)** | 25,632 | ~2,400 |
| **Best fit** | Tools, APIs, file systems, databases | Multi-agent orchestration, cross-vendor collaboration |

---

## 4. What A2A Solves That MCP Does Not

### **i. True Multi-Agent Delegation**
MCP treats everything as a tool — a deterministic callable with a schema. This works well for a Postgres query or a Slack message, but breaks down when the "tool" is itself an LLM-powered agent with uncertainty, multi-step reasoning, and its own internal tool loop. A2A is designed for exactly this: delegating to an autonomous process that may take an indeterminate number of steps to complete.

The Google blog explicitly lists as a design principle: *"enabling true multi-agent scenarios without limiting an agent to a 'tool.'"*

### **ii. Long-Running Task State**
MCP tool calls are effectively synchronous RPC — you fire a request and wait for a result. The experimental "Tasks" primitive in MCP 2025-11-25 is still new and not widely adopted. A2A's entire design centers on tasks that may run for hours with intermediate status updates, human-in-the-loop `needsInput` states, and webhook callbacks when SSE isn't viable. This is the difference between a function call and a job queue.

### **iii. Cross-Vendor Agent Interoperability**
A2A is specifically engineered for the enterprise case where a Salesforce CRM agent needs to collaborate with a Google Workspace agent built by a different team on a different stack. The Agent Card is a vendor-neutral contract. Two agents that have never met can discover each other's capabilities and coordinate without custom integration code. MCP provides no mechanism for this — it assumes the host controls both the client and the server configuration.

### **iv. Rich Capability Discovery Before Connection**
MCP discovery is *in-band* — you connect to a server and then ask `tools/list`. You have to connect first. A2A's Agent Card is *out-of-band* — any HTTP client can `GET /.well-known/agent.json` and learn everything about an agent before deciding whether to engage it. This enables agent marketplaces, dynamic orchestration, and capability-based routing without establishing a connection upfront.

### **v. UX and Modality Negotiation**
A2A's `parts` model allows client and remote agents to negotiate content format — iframes, video streams, web forms, audio. An orchestrator agent can tell a sub-agent "my user's client supports iframes" and receive a response formatted accordingly. MCP has no equivalent mechanism; it returns tool results in structured text or images without negotiating UI capabilities.

---

## 5. What MCP Solves That A2A Does Not

### **i. Standardized Tool Access (The Integration Layer)**
MCP is what makes agents tool-rich without engineering overhead. The Alpha Vantage MCP server exposes 60+ financial data tools — a single `McpToolset(url=MCP_URL)` instantiation gives an ADK agent all of them, with auto-discovery on startup and automatic updates when the server adds new tools. A2A has no concept of this. It handles *who does work*, not *what capabilities they use*.

### **ii. Resource Context (RAG Layer)**
MCP's Resources primitive provides structured access to data sources as context — file contents, database records, API responses, document collections. This is the RAG layer: giving the LLM grounding in real-time data. A2A has no analogue; it's purely a coordination protocol, not a context protocol.

### **iii. Prompt Templates**
MCP's Prompts primitive enables servers to advertise reusable interaction templates — system prompts, few-shot examples, structured conversation starters. This allows tool authors to package the *best way to use their tool* alongside the tool itself. A2A doesn't address prompt engineering.

### **iv. Model-Agnostic Sampling**
MCP's Sampling primitive allows an MCP server to request LLM completions from the client's model — without embedding any LLM SDK in the server itself. This enables server authors to build model-agnostic, intelligent tools. A2A assumes agents already have their own LLM; it doesn't address how they access inference.

### **v. Local Process Integration**
MCP's stdio transport is purpose-built for local processes — the AI application spawns a local server, and they communicate with zero network overhead over stdin/stdout. Claude Code's filesystem server, your company's internal database server, your local dev environment — all accessible without any HTTP infrastructure. A2A is HTTP-only, making it unsuitable for tight local integration.

### **vi. Mature Ecosystem (by 10x)**
With 25,632 repositories vs ~2,400, MCP has a dramatically larger ecosystem of existing integrations. Every major AI coding client natively supports MCP. If you need an agent to access a specific SaaS product today — Jira, GitHub, Postgres, Slack, AWS — there is almost certainly an MCP server already written and maintained. A2A's ecosystem is growing rapidly but lags by roughly 18 months of head start.

---

## 6. Complementary or Competing?

**Complementary. Definitively.** The evidence is unambiguous:

1. **Google said so explicitly** at A2A's launch: *"A2A is an open protocol that complements Anthropic's Model Context Protocol (MCP)."*
2. **The reference architecture uses both**: In Google's ADK, `McpToolset` is how an agent accesses tools; `to_a2a()` is how it gets exposed as a service to other agents. The stack is MCP at the bottom, A2A at the top.
3. **They solve different layers**: A2A answers "which agent should do this?"; MCP answers "what tools does that agent need?". You cannot substitute one for the other.
4. **Real implementations use both**: The ADK+A2A+MCP financial agent from Google Cloud (March 2026) is the canonical example — MCP for Alpha Vantage's 60+ tools, A2A for exposing the agent to external callers.

The **reference architecture** that is emerging across LangGraph, CrewAI, and ADK:

```
User request
    │
    ▼
Orchestrator agent  ◄──── A2A discovery (/.well-known/agent.json)
    │
    ├──► Research agent (via A2A task delegation)
    │         └──► Web search MCP server
    │         └──► News API MCP server
    │
    ├──► Code agent (via A2A task delegation)
    │         └──► GitHub MCP server
    │         └──► File system MCP server
    │
    └──► Analysis agent (via A2A task delegation)
              └──► Database MCP server
              └──► Internal API MCP server
```

A2A routes *between* agents. MCP equips *each* agent with its tools.

---

## 7. Criticisms and Limitations

### A2A Criticisms

**Scalability at N² connections**: A2A defaults to point-to-point HTTP connections. As agent count grows, connections scale as N². A 2025 analysis (*"Why Google's A2A Protocol Needs Apache Kafka"*) argues that large-scale deployments require complementary event meshes (Kafka, etc.) to decouple agents — the protocol doesn't solve the routing/fanout problem natively.

**Security attack surface expansion**: Security researcher Chamuditha Kekulawala (May 2025) documented the *compounded attack surface*: A2A discovery can be exploited to find agents, which then expose MCP tool connections as indirect attack paths. "Tool squatting" (registering malicious tools) becomes more dangerous when A2A enables dynamic discovery. The spec *recommends* protecting sensitive Agent Cards but doesn't *enforce* authentication mechanisms.

**Task-to-Tool translation gap**: High-level A2A tasks ("summarize this") must be translated into specific MCP tool commands at each sub-agent. A2A's skill descriptions often lack the detail of MCP's `inputSchema`, creating ambiguity at integration boundaries. No standard negotiation layer exists for semantic alignment between agents.

**Debugging and observability**: Cross-protocol tracing (A2A task → agent reasoning → MCP tool call → result → A2A artifact) requires integrated monitoring that doesn't yet exist as a standard tooling layer.

**Still a beta standard**: The April 2025 announcement explicitly said production-readiness was targeted for Q3 2025. The spec remains a draft at github.com/a2aproject/A2A. Framework integration (LangGraph, CrewAI) is functional but not at the same maturity level as MCP integrations.

### MCP Criticisms

**No agent-to-agent coordination**: MCP has no concept of delegating to an autonomous process. If you try to wrap an LLM-powered agent as an MCP tool, you lose task state, long-running status updates, and the ability to handle uncertainty or multi-step reasoning natively.

**Stateful connections are operationally heavy**: Each MCP client maintains a persistent connection to each server. At scale, managing hundreds of concurrent stateful connections per host is more complex than A2A's stateless HTTP + task ID model.

**Auth is an afterthought**: MCP's authentication is transport-level — API keys injected as environment variables or HTTP headers. There is no protocol-level auth negotiation equivalent to A2A's Agent Card auth declaration. This makes enterprise access control more implementation-dependent.

**No cross-client agent coordination**: If you want a Claude agent and a Copilot agent to collaborate on a task, MCP provides no mechanism. They share no task state, no result artifacts, no capability discovery protocol between them.

---

## 8. The Third Player: ACP

Worth noting: **Microsoft's Agent Communication Protocol (ACP)** was introduced in 2026 as a third option, focused on enterprise workflow governance — audit trails, compliance, complex orchestration patterns, and deep Microsoft ecosystem integration (Azure, M365). The WebMCPGuide comparison (2026) characterizes it as HTTP/WebSocket-based, higher complexity than either MCP or A2A, and still at Alpha maturity. ACP targets the same problem space as A2A but with enterprise IT governance as the primary design constraint rather than cross-vendor interoperability.

The emerging picture is a three-protocol stack:
- **MCP**: Agent ↔ tools/data (Anthropic-led, dominant)
- **A2A**: Agent ↔ agent (Google-led, fast-growing)
- **ACP**: Enterprise orchestration + governance (Microsoft-led, early)

---

## Summary Table

| Question | Answer |
|----------|--------|
| What layer does MCP operate at? | Agent-to-tool: gives agents access to external capabilities |
| What layer does A2A operate at? | Agent-to-agent: enables agents to delegate to other agents |
| Are they competing? | No — they are different layers of the same stack |
| Which has more adoption? | MCP by 10x in repos; A2A growing faster from a smaller base |
| Which came first? | MCP (Nov 2024), then A2A (Apr 2025) |
| Who builds on both? | Google ADK, LangGraph, CrewAI — all use A2A+MCP together |
| Can A2A replace MCP? | No — A2A has no tool access, resource, or prompt primitives |
| Can MCP replace A2A? | No — MCP has no agent delegation, task state, or cross-vendor discovery |
| Reference implementation? | Google ADK financial agent: MCP for tool access, A2A for service exposure |
| Key A2A gap vs MCP | No local process support (HTTP-only), 10x smaller ecosystem, beta status |
| Key MCP gap vs A2A | No task state, no agent delegation, no cross-vendor interoperability |
