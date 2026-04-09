Good. The repo has a reference answer at `test-2-a2a-mcp.md` (this is the workshop's own test problem), but I've built the analysis from primary sources and technical specs. Here's the full breakdown:

---

# Google A2A vs. Anthropic MCP: Protocol Architecture, Use Cases, and Interplay

**One-line thesis:** MCP standardizes how an agent *reaches out to tools and data*; A2A standardizes how agents *talk to each other*. They are architecturally complementary but commercially in tension.

---

## 1. The Problem Both Are Solving

Neither protocol emerged in isolation — both target the **M×N integration problem**:

- Without standards: connecting M models to N tools requires M×N custom integrations.
- MCP collapses that to M+N by standardizing the model→tool interface.
- A2A collapses the equivalent agent→agent integration explosion in multi-agent systems.

The difference is the *layer* of the stack each operates at.

---

## 2. MCP: Model Context Protocol

**Origin:** Anthropic, November 2024. Open-source spec at `modelcontextprotocol.io`, Apache 2.0.

### 2a. Architecture

Three-component client-server model:

```
┌─────────────────────────────────────────┐
│  MCP Host (Claude Desktop, Cursor, IDE) │
│  ┌──────────────┐  ┌──────────────┐     │
│  │  MCP Client  │  │  MCP Client  │  ←── one client per server
│  └──────┬───────┘  └──────┬───────┘     │
└─────────┼─────────────────┼─────────────┘
          │                 │
     ┌────▼────┐       ┌────▼────┐
     │ MCP     │       │ MCP     │
     │ Server  │       │ Server  │
     │(GitHub) │       │(Postgres)│
     └─────────┘       └─────────┘
```

- **Host**: The AI application the user runs (Claude Desktop, Cursor, Windsurf, VS Code Copilot). It holds one or more Clients.
- **Client**: Lives inside the Host; maintains a dedicated, stateful, 1:1 connection with exactly one Server.
- **Server**: An external program exposing capabilities over the protocol — can run locally (via stdio) or remotely (via HTTP+SSE).

### 2b. Core Primitives

| Primitive | What it is | Analogy |
|-----------|-----------|---------|
| **Tools** | Executable functions the LLM can call (with JSON Schema params) | `POST /api/action` |
| **Resources** | Named data streams the Host exposes to the model (files, DB rows, logs) | `GET /data/resource` |
| **Prompts** | Reusable instruction templates for workflows | Saved SQL queries |
| **Sampling** | *Inverse flow* — Server asks Host to run an LLM completion | Callback into the model |

### 2c. Transport

- **stdio**: Client spawns the Server process locally; messages via stdin/stdout. Zero network, fast, default for desktop.
- **HTTP + SSE**: Server runs remotely; Client POSTs requests, Server pushes events over a persistent SSE stream. This is what enables hosted MCP endpoints.

Message format: **JSON-RPC 2.0** throughout.

### 2d. Adoption (as of April 2026)

Concrete ecosystem numbers:
- **~2,000+ community MCP servers** indexed on `mcp.so` and GitHub
- Native support in: Claude Desktop, Cursor, Windsurf, VS Code (Copilot), Zed, JetBrains AI, Continue.dev
- First-party servers: GitHub, Slack, Google Drive, Postgres, Filesystem, Puppeteer, Brave Search
- OpenAI adopted MCP for ChatGPT desktop (March 2025) — the biggest external validation, given Anthropic authorship
- **Cloudflare, Vercel, AWS** all published hosted MCP tooling
- ~200 "partner" MCP servers from enterprise vendors within 5 months of launch

**Why it spread fast:** The local stdio transport meant zero infrastructure — developers ran it the day they heard about it. A Claude Desktop + MCP Server = instant integration without deploy overhead.

---

## 3. A2A: Agent-to-Agent Protocol

**Origin:** Google, announced April 9, 2025 at Google Cloud Next '25. Spec and SDK at `github.com/google-a2a/a2a-samples`. Built alongside Google's Agent Development Kit (ADK).

### 3a. Architecture

HTTP-native client-server model where *both sides are agents*:

```
┌─────────────────────────┐         ┌──────────────────────────┐
│   Client Agent          │         │   Remote Agent (Server)  │
│  (Orchestrator/Manager) │──HTTP──▶│  /.well-known/agent.json  │
│                         │◀──SSE───│  /task endpoint           │
│                         │◀─Webhook│                           │
└─────────────────────────┘         └──────────────────────────┘
```

A single agent can be both Client *and* Server depending on the interaction — the protocol is symmetric by design.

### 3b. Core Concepts

**Agent Card** (`/.well-known/agent.json`):
```json
{
  "name": "Candidate Sourcing Agent",
  "description": "Sources candidates from ATS and LinkedIn",
  "url": "https://hr-agent.acme.com",
  "skills": [
    { "id": "source_candidates", "description": "...", "inputSchema": {...} }
  ],
  "authentication": { "schemes": ["bearer"] },
  "capabilities": { "streaming": true, "pushNotifications": true }
}
```
This is the discovery primitive — a machine-readable "business card" served at a well-known endpoint. No registry required; agents can find each other dynamically.

**Task** (core interaction unit):
- States: `submitted → working → input-required → completed / failed / canceled`
- Long-running by design — minutes, hours, days
- Sent via `tasks/send` (request/response) or `tasks/sendSubscribe` (streaming)

**Message / Part structure:**
```
Task
 └── Messages[]
      └── Parts[]
           ├── TextPart    { "text": "..." }
           ├── FilePart    { "mimeType": "...", "uri": "..." }
           └── DataPart    { "data": { ...structured JSON... } }
```

**Artifact**: Task output — also composed of Parts. The "result" of a completed task.

### 3c. Communication Modes

| Pattern | Mechanism | Use case |
|---------|-----------|---------|
| Synchronous | `tasks/send` + HTTP response | Fast, atomic tasks |
| Streaming | `tasks/sendSubscribe` + SSE | Real-time progress, multi-turn |
| Async (fire-and-forget) | `tasks/send` + polling via `tasks/get` | Long-running jobs |
| Push notifications | Webhook via `tasks/pushNotification/set` | Day-long tasks, human-in-loop |

### 3d. Adoption (as of April 2026)

- **50+ launch partners** at Google Cloud Next: Salesforce, SAP, ServiceNow, Workday, MongoDB, Intuit, Cohere, LangChain, CrewAI
- SDKs: Python (`google-a2a`), Java, Node.js (TypeScript)
- LangGraph has native A2A server support; CrewAI published A2A example workflows
- Google ADK (Agent Development Kit) ships A2A as first-class transport
- **Anthropic was not on the launch partner list** — notable absence
- Adoption is still early: reference implementations exist but production deployments are limited compared to MCP's 18-month head start

---

## 4. What Each Solves That the Other Doesn't

### MCP Solves:

| Problem | MCP's answer |
|---------|-------------|
| LLM needs structured access to a database at runtime | `Resource` primitive with URI-addressable data |
| Standardize function-calling across model providers | `Tool` primitive with JSON Schema |
| Reuse prompt templates across apps | `Prompt` primitive |
| Let a tool server invoke the model for a sub-task | `Sampling` (server-initiated completion request) |
| IDE needs read access to codebase context | Local `stdio` server with filesystem access |
| Avoid leaking API credentials to the LLM | Server handles auth, exposes only structured results |

**MCP cannot:**
- Express that an agent has *identity, skills, and auth requirements* before a connection is established
- Manage long-running work with state transitions
- Coordinate multi-turn negotiation between two independent agents
- Handle async notifications when a task completes days later
- Route work *between* agents without a central Host

### A2A Solves:

| Problem | A2A's answer |
|---------|-------------|
| Agent needs to discover what another agent can do | Agent Card at `/.well-known/agent.json` |
| HR workflow spans sourcing → screening → scheduling | Task lifecycle across 3 specialized agents |
| Job runs for 2 hours; client needs progress | SSE streaming `TaskStatusUpdateEvent` |
| Final result is a generated PDF + structured JSON | `Artifact` with `FilePart` + `DataPart` |
| Agent needs clarification mid-task | `input-required` state triggers multi-turn Message exchange |
| Enterprise: cross-vendor agent collaboration | Open protocol: LangGraph agent ↔ CrewAI agent ↔ Salesforce agent |

**A2A cannot:**
- Give an agent access to a database or file system (that's MCP's job)
- Define the tool-calling interface for LLM function use
- Standardize how an LLM reads a prompt template
- Run locally without HTTP infrastructure

---

## 5. Technical Distinctions Side-by-Side

| Dimension | MCP | A2A |
|-----------|-----|-----|
| **Layer** | Agent ↔ Tool/Resource | Agent ↔ Agent |
| **Primary entity** | Tool, Resource, Prompt | Task, Agent Card, Artifact |
| **Interaction model** | Stateful session, request/response | Task lifecycle with state machine |
| **Discovery** | Host configures connections manually | Dynamic via `/.well-known/agent.json` |
| **Transport** | stdio (local), HTTP+SSE (remote) | HTTP+SSE+Webhooks |
| **Message format** | JSON-RPC 2.0 | JSON-RPC style + Task envelope |
| **Async handling** | Via SSE streaming | SSE + push notifications (webhooks) |
| **Multi-turn** | Not native (tools are single-call) | Native: `input-required` → dialogue |
| **Modality** | Text/data (media not a core primitive) | Text + File + Data + Audio/Video planned |
| **Security model** | User consent, local-first; OAuth added later | Enterprise auth (OAuth/API key) in Agent Card |
| **Identity** | Servers are anonymous capability providers | Agents have named identity, skills, auth |
| **Typical duration** | Milliseconds to seconds | Seconds to days |

---

## 6. Complementary or Competing?

**Architectural answer: complementary.** They sit at different layers:

```
┌─────────────────────────────────────────────────────┐
│              Multi-Agent System                      │
│                                                      │
│  Orchestrator Agent ──── A2A ────▶ Specialist Agent  │
│       │                                   │          │
│      MCP                                 MCP         │
│       │                                   │          │
│  [PostgreSQL]                      [Arxiv API]       │
└─────────────────────────────────────────────────────┘
```

A specialist agent uses MCP to pull structured data from its tools, then returns results to an orchestrator via A2A. The protocols don't compete at this layer — one enables what the other coordinates.

Google explicitly published a doc titled **"A2A ❤️ MCP"** illustrating this layered architecture, with HR, car repair, and financial workflow examples showing both protocols in the same system.

**Political/commercial answer: contested.** Three signals of tension:

1. **Anthropic absent from A2A launch.** Given MCP's maturity and Anthropic's authorship, their non-endorsement of A2A at launch is pointed.
2. **OpenAI adopted MCP** (March 2025), not A2A — consolidating MCP as the cross-vendor tool standard before A2A could become it.
3. **Functional overlap at the margins.** An A2A server *can* act as a pure tool provider, functionally replacing an MCP server. MCP's `Sampling` primitive *can* enable agent-like callbacks. Developers building pure multi-agent systems may choose one or the other, not both.

The honest framing: Google wants A2A to be the coordination layer for the agentic stack; Anthropic (by not endorsing A2A) is betting that MCP, extended with richer orchestration primitives, can handle both layers. The market will decide which frame wins. Today, MCP has the broader ecosystem; A2A has the richer task-coordination semantics.

---

## 7. Concrete Implementations to Study

| Implementation | Protocol | What it demonstrates |
|---------------|----------|---------------------|
| `github.com/modelcontextprotocol/servers/src/github` | MCP | Tool+Resource server for GitHub API |
| `github.com/modelcontextprotocol/servers/src/postgres` | MCP | Resource server with SQL query tool |
| `step-3-tool/mcp-servers/arxiv_server.py` (this repo) | MCP | FastMCP server with `search_arxiv` + `search_semantic_scholar` tools |
| `google-a2a/a2a-samples/samples/python/agents/langgraph` | A2A | LangGraph agent exposing A2A server endpoint |
| `google-a2a/a2a-samples/samples/python/agents/crewai` | A2A | CrewAI agent as A2A server |
| Google ADK `agent_executor.py` | A2A | Reference A2A client that delegates tasks |

**Key technical docs:**
- MCP spec: `spec.modelcontextprotocol.io` — JSON-RPC 2.0 message schemas, capability negotiation lifecycle
- A2A spec: `google.github.io/A2A/specification` — Task state machine, Agent Card JSON schema, SSE event types
- Google's "A2A ❤️ MCP": `google.github.io/A2A/#/topics/a2a_and_mcp.md`

---

## 8. Bottom Line

**MCP is infrastructure for agent capability** — it's `npm install` for tools. Its fast adoption came from zero-friction local deployment and a simple mental model (tools/resources/prompts). It's mature, widely deployed, and cross-vendor endorsed.

**A2A is infrastructure for agent coordination** — it's HTTP for agent collaboration. Its primitives (Agent Card, Task lifecycle, push notifications) are architecturally richer for multi-agent orchestration but require more infrastructure and are still early in production adoption.

The stack that wins enterprise AI deployments will use both: MCP for each agent's capability layer, A2A for the coordination layer above it. The question is whether A2A reaches escape velocity before MCP gets extended with coordination primitives — or whether a third standard (OpenAI's emerging agent protocol) disrupts both.
